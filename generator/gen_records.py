#!/usr/bin/env python3
"""
gen_records.py - builds data/records.csv and data/expectations.csv from the published tables.

Every expected grade is derived from data/criteria.csv (the machine-readable CTCAE transcription) read
through data/conventions.csv (reading rules and alternative profiles); the test master, default normal
ranges and reporting precision come from data/analytes.csv, unit conversions from data/units.csv. No CTCAE
threshold is written in this file: the boundary values of a subject are the thresholds of the criteria
rows that apply to it, exercised exactly at, one reporting step above and one step below the bound.

Rule engine (conventions.csv names the readings; the profile column says which ones a profile flips)
  * The clauses of a version x test x direction are filtered by baseline arm (NORMAL / ABNORMAL /
    BELOW_LLN after BASELINE_ABNORMAL_DEF and BASELINE_RANGE_FALLBACK), by qualifier (CLINICAL_QUALIFIERS,
    ENZYME_SYMPTOM_WORST) and by baseline availability (a clause compared with the baseline is not
    applicable when the subject has no baseline; a ">baseline" condition is waived, ABOVE_BASELINE_WAIVED).
  * Each applicable clause is True, False or unevaluable (a needed limit is missing). Grades are read from
    the top: the highest grade with a satisfied clause is the grade; if none is satisfied and a clause was
    unevaluable the grade is missing, otherwise 0 (MISSING_LIMIT).
  * Profiles: BESTCASE_ENZYMES flips ENZYME_SYMPTOM_WORST, HYPERGLY_NUMERIC_V5 flips HYPERGLY_V5_LABONLY
    (v6 glucose rows under v5), PRESENT_NOT_LAB flips PRESENT_AS_LIMIT (no grade, no term),
    UNGRADABLE_ZERO flips MISSING_LIMIT and UNIT_GUARD (0 instead of missing), BASELINE_STRICT flips
    ABOVE_BASELINE_WAIVED. expectations.csv publishes an alternative profile only where it changes a record.

records.csv tagging
  * RULE_IDS: the rules that gave the grade (grade >= 1), the lowest applicable rule whose bound the value
    did not cross (grade 0) or the rules that were unevaluable (grade missing), for both versions.
  * CONVENTIONS: the GRADING conventions of those clauses (INCLUSIVE_START and PROTEINURIA_24H only when the
    value sits exactly on the inclusive bound, INTEGER_RANGE only for a non-integer value, SODIUM_V5_GAP only
    inside the gap, CRCL_V6_BELOW_RANGE only below the printed range, ABOVE_BASELINE_WAIVED only when
    waived, HGB_INCREASE_REF only when the baseline is the reference, FIBRINOGEN_ARMS only in the
    abnormal-baseline arm, BASELINE_ABNORMAL_DEF only when the baseline is outside the range in the opposite
    direction), the qualified clauses of a higher grade the value would satisfy, and the DATA conventions
    the record state relies on. CONVENTION_DEP = Y when any of them has CONVENTION_DEP = Y in conventions.csv.

Usage:  python3 generator/gen_records.py [--data data]      exit code 0 = written and self-checks passed
The output is deterministic: a rerun rewrites identical files.
"""
import csv, datetime as dt, json, os, re, sys
from collections import defaultdict, Counter
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else os.path.join(ROOT, 'data')
REF_DATE = dt.date(2026, 1, 15)
VERSIONS = (5, 6)
DIRNAME = {'H': 'HIGH', 'L': 'LOW'}
PROFILES = ['DEFAULT', 'BESTCASE_ENZYMES', 'HYPERGLY_NUMERIC_V5', 'PRESENT_NOT_LAB', 'UNGRADABLE_ZERO', 'BASELINE_STRICT']
NOT_DONE = 'NOT DONE'

# ============================================================================= tables
def read(name):
    with open(os.path.join(DATA, name + '.csv'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def unorm(u):
    """unit spelling normalisation (conventions.csv UNIT_GUARD note): case, blanks, x10^9 / 10*9 / 10E9,
    IU/L = U/L, cells/uL = /uL, s = sec, /24h = /day, 1.73 m2 = 1.73m2"""
    u = (u or '').strip().replace('µ', 'u').replace('μ', 'u').upper().replace(' ', '')
    u = u.replace('*', '^').replace('^^', '^').replace('X10^', '10^').replace('10E', '10^')
    u = u.replace('IU/L', 'U/L').replace('CELLS/', '/').replace('M^2', 'M2')
    u = u.replace('/24HRS', '/DAY').replace('/24HR', '/DAY').replace('/24H', '/DAY')
    if u.endswith('/D'): u = u[:-2] + '/DAY'
    if u in ('S', 'SEC', 'SECS', 'SECOND', 'SECONDS'): u = 'S'
    return u

AN = {r['LBTESTCD']: r for r in read('analytes')}
CV = {r['CONVENTION']: r for r in read('conventions')}
UNITS = {(r['LBTESTCD'], unorm(r['FROM_UNIT'])): r['FACTOR'] for r in read('units')}
# which convention codes a profile flips (conventions.csv ALTERNATIVE_PROFILE)
FLIPS = defaultdict(set)
for r in CV.values():
    if r['ALTERNATIVE_PROFILE']: FLIPS[r['ALTERNATIVE_PROFILE']].add(r['CONVENTION'])
DEP_Y = {c for c, r in CV.items() if r['CONVENTION_DEP'] == 'Y'}

THR_RX = re.compile(r'^(-?\d+(?:\.\d+)?)$|^(?:(\d+(?:\.\d+)?)\*)?(ULN|LLN|BASE)$')
class Clause:
    __slots__ = ('rule_id', 'seq', 'ver', 'test', 'dir', 'arm', 'grade', 'cmp', 'operand', 'cond', 'qual', 'conv',
                 'clause', 'num', 'ref', 'mult', 'unit')
    def __init__(self, r):
        self.rule_id, self.seq, self.ver, self.test = r['RULE_ID'], int(r['CLAUSE_SEQ']), int(r['VERSION']), r['LBTESTCD']
        self.dir, self.arm, self.grade, self.cmp = r['DIRECTION'], r['BASELINE_ARM'], int(r['GRADE']), r['COMPARATOR']
        self.operand, self.cond, self.qual = r['OPERAND'], r['CONDITION'], r['QUALIFIER']
        self.conv, self.clause, self.unit = set(r['CONVENTION'].split()), r['CLAUSE'], r['THRESHOLD_UNIT']
        m = THR_RX.match(r['THRESHOLD'])
        if m.group(1) is not None: self.num, self.ref, self.mult = m.group(1), None, None       # numeric (string, exact)
        else: self.num, self.ref, self.mult = None, m.group(3), (m.group(2) or '1')
    @property
    def needs_base(self): return self.ref == 'BASE' or self.operand == 'PCHG'
    @property
    def key(self): return (self.rule_id, self.seq)

CRIT = defaultdict(list)                 # (version, LBTESTCD, 'HIGH'|'LOW') -> lab-derivable clauses
ALL_CLAUSES = []
for r in read('criteria'):
    if r['LAB_DERIVABLE'] == 'Y':
        cl = Clause(r); CRIT[(cl.ver, cl.test, cl.dir)].append(cl); ALL_CLAUSES.append(cl)

def qualifier_applied(cl, flipped):
    """CLINICAL_QUALIFIERS: asymptomatic / no-intervention clauses apply, symptomatic / anticoagulation ones do not;
    ENZYME_SYMPTOM_WORST reverses that for amylase and lipase unless the profile flips it (BESTCASE_ENZYMES)"""
    q = cl.qual
    if q == 'ON_ANTICOAGULATION': return False
    worst = 'ENZYME_SYMPTOM_WORST' in cl.conv and 'ENZYME_SYMPTOM_WORST' not in flipped
    if q == 'SYMPTOMATIC': return worst
    if q == 'ASYMPTOMATIC': return not worst
    return True

def coverable(cl):
    """clause applied under at least one published profile"""
    return qualifier_applied(cl, set()) or qualifier_applied(cl, FLIPS['BESTCASE_ENZYMES'])

def unit_class(test):
    """NONE = unitless (INR), ABS = a numeric threshold exists (unit must be known), RATIO = only ULN/LLN/baseline multiples"""
    if AN[test]['UNIT_SI'] == 'RATIO': return 'NONE'
    for v in VERSIONS:
        for d in ('HIGH', 'LOW'):
            if any(cl.num is not None and cl.operand != 'PCHG' for cl in CRIT.get((v, test, d), ())): return 'ABS'
    return 'RATIO'

def analyte_spec(test, spec):
    """the record's specimen is the analyte's (or its graded-alike alternative): the SI and conventional views apply"""
    a = AN[test]
    return spec in (a['LBSPEC'], a['LBSPEC_ALT'])

def has_term(test, spec):
    return analyte_spec(test, spec) and AN[test]['DIRECTIONS'] != ''

def convert(test, unit):
    """-> (status, factor): OK = unit is UNIT_SI (or ignored, unitless test), CONV = units.csv factor, ACCEPTED = unknown
    unit on a ratio-only test (graded as received, SI view blank), UNKNOWN / BLANK = not gradable (UNIT_GUARD)"""
    cls = unit_class(test)
    if cls == 'NONE': return 'OK', '1'
    u, si = unorm(unit), unorm(AN[test]['UNIT_SI'])
    if u == '': return 'BLANK', None
    if u == si: return 'OK', '1'
    f = UNITS.get((test, u))
    if f is not None: return 'CONV', f
    if cls == 'RATIO': return 'ACCEPTED', None
    return 'UNKNOWN', None

# ============================================================================= rule engine
def cmpf(op, x, t):
    if x is None or t is None: return None
    return {'>': x > t, '>=': x >= t, '<': x < t, '<=': x <= t}[op]

def AND(a, b):
    if a is False or b is False: return False
    if a is None or b is None: return None
    return True

class Ctx:
    """one record for grading: value, its range, the subject's baseline (value + its range), everything in UNIT_SI
    (N = float for the published expectations, Fraction for the exact-arithmetic self-check)"""
    def __init__(self, val, lo, hi, base, blo, bhi, unit_status='OK', N=float):
        self.N = N
        self.val, self.lo, self.hi, self.base, self.blo, self.bhi = val, lo, hi, base, blo, bhi
        self.unit_status = unit_status
        self.hi_ref = bhi if bhi is not None else hi                       # BASELINE_RANGE_FALLBACK
        self.lo_ref = blo if blo is not None else lo
        self.base_high = base is not None and self.hi_ref is not None and base > self.hi_ref
        self.base_low = base is not None and self.lo_ref is not None and base < self.lo_ref
        self.range_fallback = base is not None and ((bhi is None and hi is not None) or (blo is None and lo is not None))

def evaluate(cl, c, flipped):
    """-> (truth, operand value, threshold value)"""
    N = c.N
    if cl.operand == 'VALUE': x = c.val
    elif cl.operand == 'PCHG':
        x = None if c.val is None or c.base in (None, 0) else (c.val - c.base) / abs(c.base) * 100
    elif cl.operand == 'EXCESS_ULN': x = None if c.val is None or c.hi is None else c.val - c.hi
    elif cl.operand == 'EXCESS_BASE_OR_ULN':
        ref = c.base if c.base_high else c.hi
        x = None if c.val is None or ref is None else c.val - ref
    if cl.num is not None: t = N(cl.num)
    else:
        ref = {'ULN': c.hi, 'LLN': c.lo, 'BASE': c.base}[cl.ref]
        t = None if ref is None else N(cl.mult) * ref
    r = cmpf(cl.cmp, x, t)
    if cl.cond == 'VALUE>BASE':
        if c.base is None: cc = 'ABOVE_BASELINE_WAIVED' not in flipped                 # waived unless BASELINE_STRICT
        else: cc = None if c.val is None else c.val > c.base
        r = AND(r, cc)
    return r, x, t

def ladder(evals):
    grades = sorted({cl.grade for cl, _ in evals}, reverse=True)
    indet = False
    for g in grades:
        ts = [e[1] for e in evals if e[0].grade == g]
        if any(t is True for t in ts): return g, 'GRADED'
        if any(t is None for t in ts): indet = True
    return (None, 'UNEVALUABLE') if indet else (0, 'GRADED')

class Result:
    __slots__ = ('grade', 'status', 'term', 'rules', 'convs', 'fired')
    def __init__(self):
        self.grade, self.status, self.term, self.rules, self.convs, self.fired = None, 'NO_TERM', '', set(), set(), []

def is_int_value(x):
    return x is not None and x == int(x)

def tag_codes(cl, c, x, t, fired, direction):
    """GRADING convention codes of a clause the record's expectation relies on (see module docstring)"""
    out = set()
    for code in cl.conv:
        if code in ('INCLUSIVE_START', 'PROTEINURIA_24H'):
            if fired and x is not None and t is not None and x == t: out.add(code)
        elif code == 'INTEGER_RANGE':
            if not is_int_value(c.val): out.add(code)
        elif code == 'SODIUM_V5_GAP':
            gap = [g for g in CRIT[(cl.ver, cl.test, cl.dir)] if 'SODIUM_V5_GAP' in g.conv and g.cmp == '<=']
            if gap and c.val is not None and c.N(gap[0].num) < c.val < c.N(gap[0].num) + 1: out.add(code)
        elif code == 'CRCL_V6_BELOW_RANGE':
            low = re.match(r'\s*(\d+(?:\.\d+)?)', cl.clause)
            if low and c.val is not None and c.val < c.N(low.group(1)): out.add(code)
        elif code == 'ABOVE_BASELINE_WAIVED':
            if cl.cond and c.base is None: out.add(code)
        elif code == 'HGB_INCREASE_REF':
            if cl.operand == 'EXCESS_BASE_OR_ULN' and c.base_high: out.add(code)
        elif code == 'FIBRINOGEN_ARMS':
            if c.base_low: out.add(code)
        elif code == 'BASELINE_ABNORMAL_DEF':
            opposite = (direction == 'HIGH' and c.base_low) or (direction == 'LOW' and c.base_high)
            if opposite: out.add(code)
        elif code == 'ALT_V6_G3_CAP':
            if c.base is not None and c.hi is not None and c.base > 5 * c.hi: out.add(code)
        else:
            out.add(code)
    return out

def grade_direction(ver, test, spec, d, c, profile, tag=False):
    """expected grade of one version x direction for the record context c under a profile name"""
    res = Result()
    if not has_term(test, spec): return res
    term = AN[test]['TERM_V%d_%s' % (ver, d)]
    if not term: return res
    flipped = FLIPS[profile]
    rows = list(CRIT[(ver, test, d)])
    if 'HYPERGLY_V5_LABONLY' in flipped and any('HYPERGLY_V5_LABONLY' in cl.conv for cl in rows):
        rows = [cl for cl in rows if 'HYPERGLY_V5_LABONLY' not in cl.conv] + list(CRIT[(6, test, d)])
    if 'PRESENT_AS_LIMIT' in flipped:
        rows = [cl for cl in rows if 'PRESENT_AS_LIMIT' not in cl.conv]
        if not rows: res.status = 'NOT_LAB'; return res
    res.term = term
    if c.val is None:
        res.status = 'NO_VALUE'
        if 'UNIT_GUARD' in flipped and c.unit_status in ('UNKNOWN', 'BLANK'): res.grade, res.status = 0, 'GRADED'
        return res
    abn = c.base_high if d == 'HIGH' else c.base_low
    evals, skipped = [], []
    for cl in rows:
        if cl.arm == 'NORMAL' and abn: continue
        if cl.arm == 'ABNORMAL' and not abn: continue
        if cl.arm == 'BELOW_LLN' and not c.base_low: continue
        if cl.needs_base and c.base is None: continue
        if not qualifier_applied(cl, flipped): skipped.append(cl); continue
        evals.append((cl, evaluate(cl, c, flipped)))
    g, status = ladder([(cl, e[0]) for cl, e in evals])
    if status == 'UNEVALUABLE' and 'MISSING_LIMIT' in flipped: g, status = 0, 'GRADED'
    res.grade, res.status = g, status
    if not tag: return res
    # ---- rule ids and convention codes (DEFAULT profile)
    if status == 'GRADED' and g > 0:
        fired = [(cl, e) for cl, e in evals if cl.grade == g and e[0] is True]
        res.fired = [cl for cl, _ in fired]
        res.rules |= {cl.rule_id for cl, _ in fired}
        for cl, e in fired: res.convs |= tag_codes(cl, c, e[1], e[2], True, d)
        higher = [cl.grade for cl, _ in evals if cl.grade > g]
        if higher:
            nxt = min(higher)
            for cl, e in evals:
                if cl.grade == nxt: res.convs |= tag_codes(cl, c, e[1], e[2], False, d)
    elif status == 'GRADED':
        if evals:
            lowest = min(cl.grade for cl, _ in evals)
            for cl, e in evals:
                if cl.grade == lowest:
                    res.rules.add(cl.rule_id); res.convs |= tag_codes(cl, c, e[1], e[2], False, d)
    else:
        for cl, e in evals:
            if e[0] is None:
                res.rules.add(cl.rule_id); res.convs |= tag_codes(cl, c, e[1], e[2], False, d)
    if any(e[0] is None for _, e in evals): res.convs.add('MISSING_LIMIT')
    for cl in skipped:                                # a qualified clause of a higher grade the value satisfies
        if (g is None or cl.grade > g) and evaluate(cl, c, flipped)[0] is True:
            res.convs |= {x for x in cl.conv if x in ('CLINICAL_QUALIFIERS', 'ENZYME_SYMPTOM_WORST')}
    if c.range_fallback and any(cl.arm != 'ANY' or cl.operand == 'EXCESS_BASE_OR_ULN' for cl in rows):
        res.convs.add('BASELINE_RANGE_FALLBACK')
    return res

def worst_of(rl, rh):
    """single worst grade and its term (records.schema.json EXP_GRADE_Vn / EXP_TERM_Vn)"""
    gl, gh = rl.grade, rh.grade
    if gl is None and gh is None: return None, ''
    if gh is None: g, t = gl, rl.term
    elif gl is None: g, t = gh, rh.term
    elif gh >= gl: g, t = gh, rh.term
    else: g, t = gl, rl.term
    if g == 0 and rl.term and rh.term: t = ''
    return g, t

# ============================================================================= records
def fmt(v, dec):
    return '' if v is None else f'{v:.{dec}f}'

def fnum(v):
    """derived number (converted view): up to 6 decimals, trailing zeros stripped"""
    if v is None: return ''
    s = f'{round(v, 6):.6f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s

def rnd(v, dec):
    return None if v is None else float(fmt(v, dec))

class Rec:
    __slots__ = ('subject', 'scenario', 'module', 'test', 'spec', 'dur', 'val', 'unit', 'lo', 'hi', 'date', 'status',
                 'desc', 'dec', 'base', 'baseline_flag', 'ustatus', 'factor', 'gval', 'glo', 'ghi', 'res', 'convs', 'id')
    def __init__(self, **kw):
        for k in self.__slots__: setattr(self, k, kw.get(k))
        self.res, self.convs = {}, set()
        if self.status is None: self.status = ''
        if self.dur is None: self.dur = AN[self.test]['LBDUR'] if self.spec == AN[self.test]['LBSPEC'] else ''
    @property
    def day(self):
        d = (self.date - REF_DATE).days
        return d + 1 if d >= 0 else d
    @property
    def graded_spec(self): return has_term(self.test, self.spec)

def spec_of(test): return AN[test]['LBSPEC']

# ----------------------------------------------------------------------------- boundary points from criteria.csv
def point_label(cl, c):
    m = cl.mult
    if cl.ref is not None:
        name = {'ULN': 'ULN', 'LLN': 'LLN', 'BASE': 'baseline'}[cl.ref]
        return name if float(m) == 1 else f'{float(m):g} x {name}'
    n = float(cl.num)
    if cl.operand == 'VALUE': return f'{n:g} {cl.unit}'
    if cl.operand == 'PCHG': return 'baseline' if n == 0 else f'baseline {n:+g}%'
    ref = 'baseline' if (cl.operand == 'EXCESS_BASE_OR_ULN' and c.base_high) else 'ULN'
    return ref if n == 0 else f'{ref} + {n:g}'

def points(test, d, lo, hi, base, blo, bhi):
    """boundary values of a subject: every threshold of every applicable, coverable clause of both versions"""
    c = Ctx(None, lo, hi, base, blo, bhi)
    abn = c.base_high if d == 'HIGH' else c.base_low
    out = []
    for ver in VERSIONS:
        for cl in CRIT.get((ver, test, d), ()):
            if not coverable(cl): continue
            if cl.arm == 'NORMAL' and abn: continue
            if cl.arm == 'ABNORMAL' and not abn: continue
            if cl.arm == 'BELOW_LLN' and not c.base_low: continue
            if cl.needs_base and base is None: continue
            if cl.num is not None:
                n = float(cl.num)
                if cl.operand == 'VALUE': v = n
                elif cl.operand == 'PCHG': v = base * (1 + n / 100)
                elif cl.operand == 'EXCESS_ULN': v = None if hi is None else hi + n
                else: v = None if (ref := (base if c.base_high else hi)) is None else ref + n
            else:
                ref = {'ULN': hi, 'LLN': lo, 'BASE': base}[cl.ref]
                v = None if ref is None else float(cl.mult) * ref
            if v is not None: out.append((point_label(cl, c), v))
            if cl.cond == 'VALUE>BASE' and base is not None and hi is not None and base > hi:
                out.append(('baseline', base))
    return out

# ----------------------------------------------------------------------------- subject catalogue
# (test, direction, arm, baseline value, options) - arm: N normal baseline, Y abnormal baseline in the graded
# direction, M no baseline, LO / HI baseline below LLN / above ULN; options: mini = one value per grade only
# (alias code), extra = additional values with their own precision
SUBJECTS = [
    ('ALB', 'L', 'N', 42, {}),
    ('ALP', 'H', 'N', 80, {}), ('ALP', 'H', 'Y', 240, {}), ('ALP', 'H', 'M', None, {}),
    ('ALT', 'H', 'N', 25, {}), ('ALT', 'H', 'Y', 80, {}), ('ALT', 'H', 'M', None, {}), ('ALT', 'H', 'LO', 5, {}),
    ('AMYLASE', 'H', 'N', 70, {}),
    ('AST', 'H', 'N', 25, {}), ('AST', 'H', 'Y', 80, {}),
    ('BICARB', 'L', 'N', 25, {}),
    ('BILI', 'H', 'N', 10, {}), ('BILI', 'H', 'Y', 40, {}),
    ('CACR', 'H', 'N', 2.35, {}), ('CACR', 'L', 'N', 2.35, {}),
    ('CAION', 'H', 'N', 1.22, {}), ('CAION', 'L', 'N', 1.22, {}),
    ('CHOL', 'H', 'N', 4.5, {}),
    ('CK', 'H', 'N', 100, {}),
    ('CREAT', 'H', 'N', 80, {}), ('CREAT', 'H', 'LO', 30, {}), ('CREAT', 'H', 'HI', 120, {}), ('CREAT', 'H', 'M', None, {}),
    ('CREATCLR', 'L', 'N', 100, {'extra': [('9', 'below the printed v6 grade 3 range (10 - 25 mL/min)')]}),
    ('GFRBSCRT', 'L', 'N', 100, {}),
    ('GFR', 'L', 'N', 100, {'mini': True}),
    ('GGT', 'H', 'N', 30, {}), ('GGT', 'H', 'Y', 120, {}),
    ('GLUC', 'H', 'N', 5.5, {}), ('GLUC', 'H', 'Y', 7.0, {}), ('GLUC', 'H', 'M', None, {}), ('GLUC', 'L', 'N', 5.5, {}),
    ('HAPTOG', 'L', 'N', 1.0, {}),
    ('HDL', 'L', 'N', 1.4, {}),
    ('K', 'H', 'N', 4.2, {}), ('K', 'L', 'N', 4.2, {}),
    ('LDH', 'H', 'N', 180, {}),
    ('LDL', 'H', 'N', 2.5, {}),
    ('LIPASET', 'H', 'N', 30, {}),
    ('MG', 'H', 'N', 0.85, {}), ('MG', 'L', 'N', 0.85, {}),
    ('PHOS', 'H', 'N', 1.1, {}), ('PHOS', 'L', 'N', 1.1, {}),
    ('SODIUM', 'H', 'N', 140, {}), ('SODIUM', 'L', 'N', 140, {'extra': [('124.5', 'inside the v5 gap between 124 and 125 mmol/L')]}),
    ('TRIG', 'H', 'N', 1.0, {}),
    ('TROPONI', 'H', 'N', 5, {}), ('TROPONT', 'H', 'N', 5, {'mini': True}),
    ('URATE', 'H', 'N', 300, {}),
    ('VTD2D3IT', 'L', 'N', 80, {}),
    ('APTT', 'H', 'N', 30, {}),
    ('FIBRINO', 'L', 'N', 3.0, {}), ('FIBRINO', 'L', 'Y', 1.6, {'extra': [('0.49', 'below the absolute 0.5 g/L bound while the decrease is above -75%')]}),
    ('FIBRINO', 'L', 'M', None, {}), ('FIBRINO', 'L', 'HI', 5.0, {}),
    ('INR', 'H', 'N', 1.0, {}),
    ('CD4', 'L', 'N', 1.0, {}),
    ('EOS', 'H', 'N', 0.3, {}), ('EOS', 'H', 'Y', 0.9, {}), ('EOS', 'H', 'M', None, {}),
    ('HGB', 'L', 'N', 140, {}), ('HGB', 'H', 'N', 140, {}), ('HGB', 'H', 'Y', 170, {}), ('HGB', 'H', 'M', None, {}),
    ('LYM', 'L', 'N', 2.0, {}), ('LYM', 'H', 'N', 2.0, {}),
    ('HGBMHGB', 'H', 'N', 0.5, {}),
    ('NEUT', 'L', 'N', 4.0, {}), ('NEUT', 'H', 'N', 4.0, {}),
    ('PLAT', 'L', 'N', 250, {}),
    ('WBC', 'L', 'N', 7.0, {}), ('WBC', 'H', 'N', 7.0, {}),
    ('PROTEXR', 'H', 'N', 80, {}),
]
ARM_MODULE = {'N': 'CORE', 'Y': 'BASELINE', 'M': 'BASELINE', 'LO': 'BASELINE', 'HI': 'BASELINE'}

def build_subject(test, d, arm, base, opts):
    a = AN[test]
    unit, dec = a['UNIT_SI'], int(a['DECIMALS_SI'])
    lo = float(a['LLN_SI']) if a['LLN_SI'] else None
    hi = float(a['ULN_SI']) if a['ULN_SI'] else None
    step = 10 ** (-dec)
    subj = f'{test}-{d}-{arm}'
    module = ARM_MODULE[arm]
    recs = []
    if base is not None:
        recs.append(Rec(subject=subj, scenario=f'{subj}-BL', module=module, test=test, spec=spec_of(test), val=rnd(base, dec),
                        unit=unit, lo=lo, hi=hi, date=REF_DATE - dt.timedelta(7), desc='baseline record', dec=dec))
    vals = {}
    def add(v, label, dec_v=dec):
        v = rnd(v, dec_v)
        if v is None or v < 0: return
        key = fmt(v, max(dec, dec_v))
        if key in vals: return
        vals[key] = (v, label, dec_v)
    if lo is not None and hi is not None: add((lo + hi) / 2, 'mid-normal value')
    elif lo is not None: add(lo * 1.2, 'above LLN, inside the normal range')
    blo, bhi = (lo, hi) if base is not None else (None, None)
    for label, p in points(test, DIRNAME[d], lo, hi, base, blo, bhi):
        pv = rnd(p, dec)
        if opts.get('mini'):
            add(pv + step if d == 'H' else pv - step, f'1 step {"above" if d == "H" else "below"} {label} ({fmt(pv, dec)})')
        else:
            add(pv - step, f'1 step below {label} ({fmt(pv, dec)})')
            add(pv, f'exactly {label} ({fmt(pv, dec)})')
            add(pv + step, f'1 step above {label} ({fmt(pv, dec)})')
    for v, label in opts.get('extra', []):
        add(float(v), label, max(dec, len(v.split('.')[1]) if '.' in v else 0))
    day = 2
    for i, key in enumerate(sorted(vals, key=lambda k: float(k)), 1):
        v, label, dec_v = vals[key]
        recs.append(Rec(subject=subj, scenario=f'{subj}-{i:02d}', module=module, test=test, spec=spec_of(test), val=v, unit=unit,
                        lo=lo, hi=hi, date=REF_DATE + dt.timedelta(day), desc=label, dec=dec_v))
        day += 1
    return recs

def edge_subjects():
    R = []
    def rec(subj, module, test, val, lo, hi, day, scen, desc, unit=None, dec=None, status='', spec=None, dur=None):
        a = AN[test]
        R.append(Rec(subject=subj, scenario=scen, module=module, test=test, spec=spec or spec_of(test), dur=dur,
                     val=rnd(val, dec if dec is not None else int(a['DECIMALS_SI'])), unit=a['UNIT_SI'] if unit is None else unit,
                     lo=lo, hi=hi, date=REF_DATE + dt.timedelta(day), status=status, desc=desc,
                     dec=dec if dec is not None else int(a['DECIMALS_SI'])))
    # ---- MISSING: missing result or limit
    s = 'ALT-E-MISSVAL'
    rec(s, 'MISSING', 'ALT', 25, 10, 40, -7, s + '-BL', 'baseline record')
    rec(s, 'MISSING', 'ALT', None, 10, 40, 2, s + '-01', 'post-baseline result missing: grades missing, terms populated')
    rec(s, 'MISSING', 'ALT', 121, 10, 40, 3, s + '-02', '1 step above 3 x ULN (120)')
    s = 'K-E-NOULN'
    rec(s, 'MISSING', 'K', 4.0, 3.5, None, -7, s + '-BL', 'baseline record, ULN missing')
    for i, (v, lab) in enumerate([(5.2, 'above the usual ULN but ULN missing: high grade unevaluable'),
                                  (5.6, '1 step above 5.5 mmol/L, ULN missing: absolute threshold still grades'),
                                  (6.5, 'between 6.0 and 7.0 mmol/L, ULN missing'), (7.5, 'above 7.0 mmol/L, ULN missing')], 1):
        rec(s, 'MISSING', 'K', v, 3.5, None, 1 + i, s + f'-{i:02d}', lab)
    s = 'K-E-NOLLN'
    rec(s, 'MISSING', 'K', 4.0, None, 5.0, -7, s + '-BL', 'baseline record, LLN missing')
    for i, (v, lab) in enumerate([(3.2, 'below the usual LLN but LLN missing: low grade unevaluable'),
                                  (2.9, '1 step below 3.0 mmol/L, LLN missing'), (2.4, '1 step below 2.5 mmol/L, LLN missing')], 1):
        rec(s, 'MISSING', 'K', v, None, 5.0, 1 + i, s + f'-{i:02d}', lab)
    s = 'ALT-E-NOULN'
    rec(s, 'MISSING', 'ALT', 30, 10, None, -7, s + '-BL', 'baseline record, ULN missing')
    rec(s, 'MISSING', 'ALT', 500, 10, None, 2, s + '-01', 'high value but ULN missing on a ULN-multiple test: grade missing')
    s = 'TRIG-E-NORANGE'
    rec(s, 'MISSING', 'TRIG', 1.0, None, None, -7, s + '-BL', 'baseline record, no normal range')
    rec(s, 'MISSING', 'TRIG', 1.71, None, None, 2, s + '-01', 'exactly 1.71 mmol/L with no range: grade 1 (absolute, inclusive)')
    rec(s, 'MISSING', 'TRIG', 3.43, None, None, 3, s + '-02', '1 step above 3.42 mmol/L with no range')
    # ---- NOTDONE
    s = 'ALT-E-NOTDONE'
    rec(s, 'NOTDONE', 'ALT', 30, 10, 40, -10, s + '-BL', 'true baseline record (day -10)')
    rec(s, 'NOTDONE', 'ALT', 500, 10, 40, -3, s + '-01', 'NOT DONE with a stray value before REF_DATE: ignored, never the baseline', status=NOT_DONE)
    rec(s, 'NOTDONE', 'ALT', None, 10, 40, 3, s + '-02', 'NOT DONE without a value: every expectation blank', status=NOT_DONE)
    rec(s, 'NOTDONE', 'ALT', 121, 10, 40, 8, s + '-03', '1 step above 3 x ULN, graded against the true baseline 30')
    # ---- CORE: test without a CTCAE term
    s = 'UREA-E-NOTERM'
    rec(s, 'CORE', 'UREA', 5.0, 2.9, 7.1, -7, s + '-BL', 'baseline record, test without a CTCAE term')
    rec(s, 'CORE', 'UREA', 12.0, 2.9, 7.1, 2, s + '-01', 'abnormal value, no CTCAE term: every expectation blank')
    # ---- BASELINE: baseline record without a range, baseline selection
    s = 'ALT-E-BLNORANGE'
    rec(s, 'BASELINE', 'ALT', 80, None, None, -7, s + '-BL', 'baseline record without its own normal range: grade missing')
    rec(s, 'BASELINE', 'ALT', 120, 10, 40, 2, s + '-01', 'exactly 1.5 x baseline (120): baseline abnormal per the current ULN 40')
    rec(s, 'BASELINE', 'ALT', 121, 10, 40, 3, s + '-02', '1 step above 1.5 x baseline: baseline abnormal per the current ULN 40')
    s = 'ALT-E-LASTPRE'
    rec(s, 'BASELINE', 'ALT', 25, 10, 40, -10, s + '-00', 'earlier pre-treatment record (not the baseline)')
    rec(s, 'BASELINE', 'ALT', 80, 10, 40, -3, s + '-BL', 'last pre-treatment record = baseline (abnormal)')
    rec(s, 'BASELINE', 'ALT', 121, 10, 40, 2, s + '-01', '1 step above 1.5 x baseline: uses the day -3 baseline (80), not day -10 (25)')
    s = 'ALT-E-ONTRTSDT'
    rec(s, 'BASELINE', 'ALT', 25, 10, 40, -7, s + '-00', 'earlier pre-treatment record (not the baseline)')
    rec(s, 'BASELINE', 'ALT', 80, 10, 40, 0, s + '-BL', 'record dated on REF_DATE = baseline (DATE <= REF_DATE)')
    rec(s, 'BASELINE', 'ALT', 121, 10, 40, 2, s + '-01', '1 step above 1.5 x baseline: must use the REF_DATE baseline (80)')
    # ---- UNITS: values in the record's own unit; expected grades after conversion to UNIT_SI
    def usub(s, test, unit, lo, hi, base, posts, dec):
        rec(s, 'UNITS', test, base, lo, hi, -7, s + '-BL', f'baseline record in {unit or "blank unit"}', unit=unit, dec=dec)
        for i, p in enumerate(posts, 1):
            v, lab = p[0], p[1]
            u2 = p[2] if len(p) > 2 else unit
            lo2, hi2 = (p[3], p[4]) if len(p) > 3 else (lo, hi)
            rec(s, 'UNITS', test, v, lo2, hi2, 1 + i, s + f'-{i:02d}', lab, unit=u2, dec=dec)
    usub('HGB-U-GDL', 'HGB', 'g/dL', 12.0, 16.0, 14.0, [(9.9, '9.9 g/dL x 10 = 99 g/L: low grade 2'), (7.9, '7.9 g/dL = 79 g/L: low grade 3'),
         (11.9, '11.9 g/dL = 119 g/L, below LLN 120: low grade 1'), (16.5, '16.5 g/dL = 165 g/L, 5 above ULN: high grade 1'),
         (18.1, '18.1 g/dL = 181 g/L, 21 above ULN: high grade 2')], 1)
    usub('HGB-U-MMOL', 'HGB', 'mmol/L', 7.45, 9.93, 8.70, [(6.14, '6.14 mmol/L x 16.114 = 98.9 g/L: low grade 2'),
         (4.90, '4.90 mmol/L = 79.0 g/L: low grade 3')], 2)
    usub('HGB-U-MIXED', 'HGB', 'g/dL', 12.0, 16.0, 14.0, [(95, 'post-baseline record already in g/L (95) while the baseline is in g/dL: grade 2', 'g/L', 120, 160),
         (9.5, '9.5 g/dL = 95 g/L: grade 2')], 1)
    usub('HGB-U-UNK', 'HGB', 'g/L', 120, 160, 140, [(85, 'unit mg/L has no units.csv conversion for an absolute-threshold test: not gradable', 'mg/L', 120, 160),
         (85, 'same value in g/L: grade 2')], 0)
    usub('HGB-U-BLANK', 'HGB', 'g/L', 120, 160, 140, [(85, 'blank unit: not gradable', '', 120, 160)], 0)
    usub('K-U-MEQ', 'K', 'mEq/L', 3.5, 5.0, 4.2, [(5.6, 'mEq/L = mmol/L (factor 1): high grade 2'), (2.4, '2.4 mEq/L: low grade 4'), (7.1, '7.1 mEq/L: high grade 4')], 1)
    usub('K-U-SPELL', 'K', 'MMOL/L', 3.5, 5.0, 4.2, [(5.6, 'unit spelled MMOL/L (upper case): accepted, high grade 2')], 1)
    usub('GLUC-U-MGDL', 'GLUC', 'mg/dL', 70, 99, 90, [(300, '300 mg/dL x 0.0555 = 16.65 mmol/L: v6 grade 3, v5 grade 1'),
         (35, '35 mg/dL = 1.94 mmol/L: low grade 3'), (25, '25 mg/dL = 1.39 mmol/L: low grade 4'),
         (161, '161 mg/dL = 8.94 mmol/L: v6 grade 2, v5 grade 1')], 0)
    usub('CD4-U-CELLS', 'CD4', 'cells/uL', 530, 1570, 1000, [(150, '150 cells/uL x 0.001 = 0.15 x 10^9/L: grade 3'), (40, '40 cells/uL = 0.04: grade 4'),
         (450, '450 cells/uL = 0.45: grade 2'), (520, '520 cells/uL = 0.52, below LLN 0.53: grade 1')], 0)
    usub('PLAT-U-KUL', 'PLAT', '10^3/uL', 150, 450, 250, [(20, '10^3/uL = 10^9/L (factor 1): 20 is v5 grade 4, v6 grade 3'), (74, '74 x 10^3/uL: grade 2')], 0)
    usub('PLAT-U-PERUL', 'PLAT', '/uL', 150000, 450000, 250000, [(20000, '20000 /uL x 0.001 = 20 x 10^9/L: v5 grade 4, v6 grade 3'), (9000, '9000 /uL = 9: grade 4')], 0)
    usub('PLAT-U-SPELL', 'PLAT', '10*3/uL', 150, 450, 250, [(20, 'spelled 10*3/uL = 10^3/uL: v5 grade 4, v6 grade 3')], 0)
    usub('WBC-U-GL', 'WBC', 'G/L', 4.0, 11.0, 7.0, [(120, 'G/L = giga per litre for counts: 120 is leukocytosis grade 3'), (2.5, '2.5 G/L: low grade 2')], 1)
    usub('NEUT-U-MM3', 'NEUT', '/mm3', 2000, 8250, 4000, [(80, '80 /mm3 = 0.08 x 10^9/L: grade 4 (v5 <0.5, v6 <0.1)'), (1600, '1600 /mm3 = 1.6: v5 grade 1, v6 grade 0')], 0)
    usub('NEUT-U-SPELL', 'NEUT', 'x10^9/L', 2.00, 8.25, 4.00, [(0.30, 'x10^9/L accepted: 0.30 is v5 grade 4, v6 grade 3')], 2)
    usub('CACR-U-MGDL', 'CACR', 'mg/dL', 8.6, 10.2, 9.4, [(12.0, '12.0 mg/dL x 0.2495 = 2.99 mmol/L: high grade 2'), (7.5, '7.5 mg/dL = 1.87 mmol/L: low grade 2'),
         (13.7, '13.7 mg/dL = 3.42 mmol/L: high grade 4')], 1)
    usub('PROTEXR-U-G', 'PROTEXR', 'g/24h', 0.00, 0.10, 0.08, [(4.00, '4.0 g/24h x 1000 = 4000 mg/day: grade 3'), (1.20, '1.2 g/24h = 1200 mg/day: grade 2'),
         (0.50, '0.5 g/24h = 500 mg/day, at or above ULN 100: grade 1')], 2)
    usub('FIBRINO-U-MGDL', 'FIBRINO', 'mg/dL', 200, 400, 300, [(40, '40 mg/dL x 0.01 = 0.40 g/L: grade 4'), (120, '120 mg/dL = 1.20 g/L: grade 2'), (190, '190 mg/dL = 1.90 g/L: grade 1')], 0)
    usub('ALB-U-GDL', 'ALB', 'g/dL', 3.5, 5.5, 4.2, [(2.8, '2.8 g/dL x 10 = 28 g/L: grade 2'), (1.9, '1.9 g/dL = 19 g/L: grade 3')], 1)
    usub('TRIG-U-MGDL', 'TRIG', 'mg/dL', 0, 150, 100, [(200, '200 mg/dL x 0.01129 = 2.26 mmol/L: grade 1'), (320, '320 mg/dL = 3.61 mmol/L: grade 2'), (1100, '1100 mg/dL = 12.4 mmol/L: grade 4')], 0)
    usub('MG-U-MGDL', 'MG', 'mg/dL', 1.6, 2.6, 2.0, [(3.1, '3.1 mg/dL x 0.4114 = 1.28 mmol/L: high grade 3'), (1.0, '1.0 mg/dL = 0.41 mmol/L: low grade 2'), (0.6, '0.6 mg/dL = 0.25 mmol/L: low grade 4')], 1)
    usub('CHOL-U-MGDL', 'CHOL', 'mg/dL', 0, 200, 180, [(310, '310 mg/dL x 0.02586 = 8.02 mmol/L: grade 2'), (520, '520 mg/dL = 13.4 mmol/L: grade 4')], 0)
    usub('SODIUM-U-MEQ', 'SODIUM', 'mEq/L', 136, 145, 140, [(124, '124 mEq/L: low grade 3'), (151, '151 mEq/L: high grade 2')], 0)
    usub('ALT-U-IUL', 'ALT', 'IU/L', 10, 40, 25, [(121, 'IU/L normalised to U/L: 1 step above 3 x ULN, grade 2')], 0)
    usub('ALT-U-UKAT', 'ALT', 'ukat/L', 0.17, 0.67, 0.40, [(2.02, 'ukat/L on a ULN-multiple test: the factor cancels, 3.01 x ULN is grade 2')], 2)
    usub('ALT-U-BLANK', 'ALT', 'U/L', 10, 40, 25, [(121, 'blank unit: not gradable even on a ULN-multiple test', '', 10, 40)], 0)
    usub('INR-U-BLANK', 'INR', '', 0.8, 1.1, 1.0, [(1.6, 'INR is unitless: blank unit accepted, grade 2')], 1)
    usub('BILI-U-MGDL', 'BILI', 'mg/dL', 0.3, 1.0, 0.6, [(2.5, 'mg/dL on a ULN-multiple test: 2.5 x ULN is grade 2 before and after conversion')], 1)
    usub('GFRBSCRT-U-MLS', 'GFRBSCRT', 'mL/s/1.73m2', 1.50, None, 1.67, [(0.45, '0.45 mL/s/1.73m2 x 60 = 27 mL/min/1.73 m2: grade 3')], 2)
    # ---- CATEGORY: the same test code under another specimen has no criterion
    rec('CREAT-C-URINE', 'CATEGORY', 'CREAT', 10.0, 4.4, 17.7, -7, 'CREAT-C-URINE-BL', 'urine creatinine (mmol/24h, 24-hour collection)', unit='mmol/24h', dec=1, spec='URINE', dur='PT24H')
    rec('CREAT-C-URINE', 'CATEGORY', 'CREAT', 40.0, 4.4, 17.7, 2, 'CREAT-C-URINE-01', '2.3 x ULN but urine specimen: no serum criterion, every expectation blank', unit='mmol/24h', dec=1, spec='URINE', dur='PT24H')
    rec('GLUC-C-URINE', 'CATEGORY', 'GLUC', 0.2, None, None, -7, 'GLUC-C-URINE-BL', 'urine glucose (mmol/L, urinalysis, no published normal range)', spec='URINE')
    rec('GLUC-C-URINE', 'CATEGORY', 'GLUC', 30.0, None, None, 2, 'GLUC-C-URINE-01', '30 mmol/L urine glucose would be v6 grade 4 if graded as serum: blank', spec='URINE')
    rec('K-C-URINE', 'CATEGORY', 'K', 60.0, 25.0, 125.0, -7, 'K-C-URINE-BL', 'urine potassium (mmol/24h, 24-hour collection)', unit='mmol/24h', spec='URINE', dur='PT24H')
    rec('K-C-URINE', 'CATEGORY', 'K', 200.0, 25.0, 125.0, 2, 'K-C-URINE-01', '200 mmol/24h: no serum criterion for a urine specimen, blank', unit='mmol/24h', spec='URINE', dur='PT24H')
    rec('WBC-C-URINE', 'CATEGORY', 'WBC', 2.0, None, None, -7, 'WBC-C-URINE-BL', 'urinalysis leukocytes per high-power field (no published normal range)', unit='/HPF', spec='URINE')
    rec('WBC-C-URINE', 'CATEGORY', 'WBC', 150.0, None, None, 2, 'WBC-C-URINE-01', '150 /HPF: urine specimen, blank, no unit warning expected', unit='/HPF', spec='URINE')
    s = 'CREAT-C-MIXED'
    rec(s, 'CATEGORY', 'CREAT', 80, 44, 97, -7, s + '-BL', 'serum creatinine baseline (umol/L)')
    rec(s, 'CATEGORY', 'CREAT', 10.0, 4.4, 17.7, -3, s + '-01', 'urine creatinine day -3: other specimen, blank, not the serum baseline', unit='mmol/24h', dec=1, spec='URINE', dur='PT24H')
    rec(s, 'CATEGORY', 'CREAT', 160, 44, 97, 2, s + '-02', 'serum 160 vs serum baseline 80: grade 2 (3 if the urine record were taken as baseline)')
    rec(s, 'CATEGORY', 'CREAT', 12.0, 4.4, 17.7, 3, s + '-03', 'urine creatinine post-baseline: blank', unit='mmol/24h', dec=1, spec='URINE', dur='PT24H')
    return R

# ============================================================================= assembly
def select_baselines(recs):
    """BASELINE_SELECTION: last record with a result, not NOT DONE, dated on or before REF_DATE, per subject x test x specimen"""
    groups = defaultdict(list)
    for r in recs: groups[(r.subject, r.test, r.spec)].append(r)
    for g in groups.values():
        cands = [r for r in g if r.date <= REF_DATE and r.status != NOT_DONE and r.val is not None]
        bl = max(cands, key=lambda r: r.date) if cands else None
        for r in g:
            r.baseline_flag = 'Y' if r is bl else ''
            r.base = None if r.status == NOT_DONE else bl

def grading_values(r):
    """as-received -> UNIT_SI for grading; returns (status, factor, val, lo, hi)"""
    if not analyte_spec(r.test, r.spec): return 'NA', None, None, None, None
    status, f = convert(r.test, r.unit)
    if status in ('OK', 'CONV'):
        ff = float(f)
        sc = lambda x: None if x is None else x * ff
        return status, f, sc(r.val), sc(r.lo), sc(r.hi)
    if status == 'ACCEPTED': return status, None, r.val, r.lo, r.hi
    return status, None, None, r.lo, r.hi

def ctx_for(r, N=float):
    """grading context of a record; N = float (published) or Fraction (exact self-check)"""
    def conv(x, f): return None if x is None else N(str(x)) * N(f)
    st, f, _, _, _ = grading_values(r)
    if st in ('OK', 'CONV'): val, lo, hi = conv(r.val, f), conv(r.lo, f), conv(r.hi, f)
    elif st == 'ACCEPTED': val, lo, hi = (None if r.val is None else N(str(r.val))), (None if r.lo is None else N(str(r.lo))), (None if r.hi is None else N(str(r.hi)))
    else: val, lo, hi = None, (None if r.lo is None else N(str(r.lo))), (None if r.hi is None else N(str(r.hi)))
    base = blo = bhi = None
    b = r.base
    if b is not None:
        bst, bf, _, _, _ = grading_values(b)
        if bst in ('OK', 'CONV'): base, blo, bhi = conv(b.val, bf), conv(b.lo, bf), conv(b.hi, bf)
        elif bst == 'ACCEPTED': base, blo, bhi = N(str(b.val)), (None if b.lo is None else N(str(b.lo))), (None if b.hi is None else N(str(b.hi)))
    return Ctx(val, lo, hi, base, blo, bhi, unit_status=st, N=N)

def grade_record(r, profile, N=float):
    """-> {ver: {'L': Result, 'H': Result}} for one profile"""
    out = {}
    nd = r.status == NOT_DONE
    c = None if nd else ctx_for(r, N)
    for ver in VERSIONS:
        out[ver] = {}
        for d in ('L', 'H'):
            if nd or not r.graded_spec: out[ver][d] = Result()
            else: out[ver][d] = grade_direction(ver, r.test, r.spec, DIRNAME[d], c, profile, tag=(profile == 'DEFAULT' and N is float))
    return out

def data_conventions(r, recs_by_subject):
    """DATA conventions the record state relies on"""
    s = set()
    a = AN[r.test]
    if r.status == NOT_DONE: s.add('NOT_DONE_NULL'); return s
    if not r.graded_spec:
        s.add('SPECIMEN_MATCH' if r.spec != a['LBSPEC'] else 'NO_TERM_NULL')
        return s
    if r.baseline_flag == 'Y': s.add('BASELINE_SELF')
    if r.val is None: s.add('MISSING_RESULT')
    si = unorm(a['UNIT_SI'])
    if unorm(r.unit) != si: s.add('UNIT_GUARD')
    if r.base is not None and (unorm(r.base.unit) != si or unorm(r.base.unit) != unorm(r.unit)): s.add('BASELINE_OWN_UNIT')
    subj = recs_by_subject[r.subject]
    if len({x.spec for x in subj}) > 1: s.add('SPECIMEN_MATCH')
    if sum(1 for x in subj if x.date <= REF_DATE and x.test == r.test and x.spec == r.spec) > 1: s.add('BASELINE_SELECTION')
    for d in ('HIGH', 'LOW'):
        if (a['TERM_V5_' + d] == '') != (a['TERM_V6_' + d] == ''): s.add('VERSION_SPECIFIC_TERM')
    return s

def main():
    recs = []
    for test, d, arm, base, opts in SUBJECTS: recs += build_subject(test, d, arm, base, opts)
    recs += edge_subjects()
    for i, r in enumerate(recs, 1): r.id = i
    select_baselines(recs)
    by_subject = defaultdict(list)
    for r in recs: by_subject[r.subject].append(r)
    for r in recs:
        r.ustatus, r.factor, r.gval, r.glo, r.ghi = grading_values(r)
        for p in PROFILES: r.res[p] = grade_record(r, p)
        r.convs = data_conventions(r, by_subject)
        for ver in VERSIONS:
            for d in ('L', 'H'): r.convs |= r.res['DEFAULT'][ver][d].convs

    # ---- per record expectation rows (grade, term, base grade) per profile and version
    def base_grade(r, p, ver, d):
        if r.status == NOT_DONE or r.base is None or not r.graded_spec: return None
        return r.base.res[p][ver][d].grade
    def expectation(r, p, ver):
        rl, rh = r.res[p][ver]['L'], r.res[p][ver]['H']
        wg, wt = worst_of(rl, rh)
        bl, bh = base_grade(r, p, ver, 'L'), base_grade(r, p, ver, 'H')
        bw = None if bl is None and bh is None else max(x for x in (bl, bh) if x is not None)
        return {'LOW': (rl.grade, rl.term, bl), 'HIGH': (rh.grade, rh.term, bh), 'WORST': (wg, wt, bw)}

    # ---- self-checks (design.md section 8)
    problems = []
    # (1) monotone grades within a subject: HIGH non-decreasing, LOW non-increasing with the graded value
    for subj, rs in by_subject.items():
        post = [r for r in rs if r.baseline_flag != 'Y' and r.status != NOT_DONE and r.graded_spec and r.gval is not None and r.date > REF_DATE]
        post.sort(key=lambda r: r.gval)
        for p in PROFILES:
            for ver in VERSIONS:
                for d, sign in (('H', 1), ('L', -1)):
                    seq = [(r.scenario, r.res[p][ver][d].grade) for r in post if r.res[p][ver][d].grade is not None]
                    for (s1, g1), (s2, g2) in zip(seq, seq[1:]):
                        if sign * (g2 - g1) < 0: problems.append(f'non-monotone {d} v{ver} {p}: {s1}={g1} then {s2}={g2}'); break
    # (2) floating-point safety: every DEFAULT grade is identical in IEEE double and in exact rational arithmetic
    for r in recs:
        if r.status == NOT_DONE or not r.graded_spec: continue
        exact = grade_record(r, 'DEFAULT', N=Fraction)
        for ver in VERSIONS:
            for d in ('L', 'H'):
                if exact[ver][d].grade != r.res['DEFAULT'][ver][d].grade:
                    problems.append(f'floating-point ambiguity {r.scenario} v{ver} {d}: float {r.res["DEFAULT"][ver][d].grade} exact {exact[ver][d].grade}')
    # (3) text hygiene for the SAS loaders: no ';' or '|' and no macro trigger in free text
    for r in recs:
        for txt in (r.desc, r.subject, r.scenario, r.unit):
            if re.search(r';|\||[%&][A-Za-z_]', txt): problems.append(f'{r.scenario}: forbidden character in {txt!r}')
        if len(r.desc) > 110: problems.append(f'{r.scenario}: description longer than 110 characters')
    # (4) rule coverage: every coverable clause fires for at least one record under a published profile
    fired = set()
    for r in recs:
        if r.status == NOT_DONE or not r.graded_spec: continue
        for p in PROFILES:
            c = ctx_for(r)
            for ver in VERSIONS:
                for d in ('L', 'H'):
                    res = grade_direction(ver, r.test, r.spec, DIRNAME[d], c, p, tag=True)
                    fired |= {cl.key for cl in res.fired}
    missing_rules = sorted({cl.rule_id for cl in ALL_CLAUSES if coverable(cl)} - {k[0] for k in fired})
    missing_clauses = sorted(cl.key for cl in ALL_CLAUSES if coverable(cl) and cl.key not in fired)
    not_coverable = sorted({cl.rule_id for cl in ALL_CLAUSES} - {cl.rule_id for cl in ALL_CLAUSES if coverable(cl)})
    if missing_rules: problems.append('lab-derivable rules never fired: ' + ' '.join(missing_rules))
    # (5) a worst grade never comes from both directions
    for r in recs:
        for ver in VERSIONS:
            rl, rh = r.res['DEFAULT'][ver]['L'], r.res['DEFAULT'][ver]['H']
            if rl.grade and rh.grade: problems.append(f'{r.scenario} v{ver}: both LOW and HIGH grades positive')
    if problems:
        print('SELF-CHECK PROBLEMS:')
        for p in problems: print('  ', p)
        sys.exit(1)

    # ---- records.csv
    with open(os.path.join(DATA, 'schema', 'records.schema.json'), encoding='utf-8') as f:
        cols = [fd['name'] for fd in json.load(f)['fields']]
    rows = []
    for r in recs:
        a = AN[r.test]
        e = {ver: expectation(r, 'DEFAULT', ver) for ver in VERSIONS}
        gradable = any(e[ver][d][0] is not None for ver in VERSIONS for d in ('LOW', 'HIGH'))
        delta = e[5] != e[6]
        rules = sorted(set().union(*(r.res['DEFAULT'][ver][d].rules for ver in VERSIONS for d in ('L', 'H'))))
        convs = sorted(r.convs)
        dep = 'Y' if any(c in DEP_Y for c in convs) else 'N'
        # unit views
        si_unit = conv_unit = ''
        val_si = lo_si = hi_si = val_cv = lo_cv = hi_cv = ''
        if analyte_spec(r.test, r.spec):
            si_unit, conv_unit = a['UNIT_SI'], a['UNIT_CONV']
            fcs = float(a['FACTOR_CONV_TO_SI'])
            if r.ustatus in ('OK', 'CONV'):
                ff = float(r.factor)
                def si(x): return '' if x is None else (fmt(x, r.dec) if ff == 1 else fnum(x * ff))
                def cv(x):
                    if x is None: return ''
                    if unorm(r.unit) == unorm(conv_unit) or ff / fcs == 1: return fmt(x, r.dec)
                    return fnum(x * ff / fcs)
                val_si, lo_si, hi_si = si(r.val), si(r.lo), si(r.hi)
                val_cv, lo_cv, hi_cv = cv(r.val), cv(r.lo), cv(r.hi)
        b = r.base
        bvals = [''] * 10
        if b is not None:
            bvals[0:4] = [fmt(b.val, b.dec), b.unit, fmt(b.lo, b.dec), fmt(b.hi, b.dec)]
            if b.ustatus in ('OK', 'CONV'):
                bf = float(b.factor); fcs = float(a['FACTOR_CONV_TO_SI'])
                def bsi(x): return '' if x is None else (fmt(x, b.dec) if bf == 1 else fnum(x * bf))
                def bcv(x):
                    if x is None: return ''
                    if unorm(b.unit) == unorm(a['UNIT_CONV']) or bf / fcs == 1: return fmt(x, b.dec)
                    return fnum(x * bf / fcs)
                bvals[4:10] = [bsi(b.val), bsi(b.lo), bsi(b.hi), bcv(b.val), bcv(b.lo), bcv(b.hi)]
        def g(x): return '' if x is None else str(x)
        row = {
            'RECORD_ID': r.id, 'SUBJECT_ID': r.subject, 'SCENARIO_ID': r.scenario, 'MODULE': r.module, 'RULE_IDS': ' '.join(rules),
            'LBTESTCD': r.test, 'LBTEST': a['LBTEST'], 'LBSPEC': r.spec, 'LBDUR': r.dur,
            'VAL': fmt(r.val, r.dec), 'UNIT': r.unit, 'LLN': fmt(r.lo, r.dec), 'ULN': fmt(r.hi, r.dec),
            'VAL_SI': val_si, 'UNIT_SI': si_unit, 'LLN_SI': lo_si, 'ULN_SI': hi_si,
            'VAL_CONV': val_cv, 'UNIT_CONV': conv_unit, 'LLN_CONV': lo_cv, 'ULN_CONV': hi_cv,
            'DATE': r.date.isoformat(), 'STUDY_DAY': r.day, 'REF_DATE': REF_DATE.isoformat(), 'BASELINE_FLAG': r.baseline_flag,
            'BASE_VAL': bvals[0], 'BASE_UNIT': bvals[1], 'BASE_LLN': bvals[2], 'BASE_ULN': bvals[3],
            'BASE_VAL_SI': bvals[4], 'BASE_LLN_SI': bvals[5], 'BASE_ULN_SI': bvals[6],
            'BASE_VAL_CONV': bvals[7], 'BASE_LLN_CONV': bvals[8], 'BASE_ULN_CONV': bvals[9],
            'STATUS': r.status, 'GRADABLE': 'Y' if gradable else 'N',
            'VERSION_DELTA': 'Y' if delta else 'N', 'CONVENTIONS': ' '.join(convs), 'CONVENTION_DEP': dep, 'DESCRIPTION': r.desc,
        }
        for ver in VERSIONS:
            row[f'EXP_GRADE_LOW_V{ver}'] = g(e[ver]['LOW'][0]); row[f'EXP_GRADE_HIGH_V{ver}'] = g(e[ver]['HIGH'][0])
            row[f'EXP_TERM_LOW_V{ver}'] = e[ver]['LOW'][1]; row[f'EXP_TERM_HIGH_V{ver}'] = e[ver]['HIGH'][1]
            row[f'EXP_BASE_GRADE_LOW_V{ver}'] = g(e[ver]['LOW'][2]); row[f'EXP_BASE_GRADE_HIGH_V{ver}'] = g(e[ver]['HIGH'][2])
            row[f'EXP_GRADE_V{ver}'] = g(e[ver]['WORST'][0]); row[f'EXP_TERM_V{ver}'] = e[ver]['WORST'][1]
        rows.append([row[c] for c in cols])
    with open(os.path.join(DATA, 'records.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(cols); w.writerows(rows)

    # ---- expectations.csv (DEFAULT for every record; alternatives only where they change the record x version)
    erows = []
    changed = Counter()
    for r in recs:
        for ver in VERSIONS:
            base_e = expectation(r, 'DEFAULT', ver)
            for p in PROFILES:
                e = expectation(r, p, ver)
                if p != 'DEFAULT':
                    if e == base_e: continue
                    changed[(p, ver)] += 1
                for d in ('LOW', 'HIGH', 'WORST'):
                    gr, term, bg = e[d]
                    erows.append([r.id, ver, p, d, '' if gr is None else gr, term, '' if bg is None else bg])
    with open(os.path.join(DATA, 'expectations.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(['RECORD_ID', 'VERSION', 'PROFILE', 'DIRECTION', 'GRADE', 'TERM', 'BASE_GRADE']); w.writerows(erows)

    # ---- summary
    nsubj = len(by_subject)
    print(f'records: {len(recs)}   subjects: {nsubj}   tests: {len({r.test for r in recs})}   expectations rows: {len(erows)}')
    print('modules: ' + ', '.join(f'{m}:{n}' for m, n in sorted(Counter(r.module for r in recs).items())))
    for ver in VERSIONS:
        ch = Counter(r.res['DEFAULT'][ver]['H'].grade for r in recs); cl = Counter(r.res['DEFAULT'][ver]['L'].grade for r in recs)
        print(f'v{ver} expected HIGH grades: ' + ', '.join(f'{k}:{ch[k]}' for k in [None, 0, 1, 2, 3, 4]) +
              '   LOW grades: ' + ', '.join(f'{k}:{cl[k]}' for k in [None, 0, 1, 2, 3, 4]))
    print('alternative profiles (record x version pairs changed): ' + ', '.join(f'{p} v{v}:{n}' for (p, v), n in sorted(changed.items())))
    print('convention tags: ' + ', '.join(f'{c}:{n}' for c, n in sorted(Counter(c for r in recs for c in r.convs).items())))
    print(f'CONVENTION_DEP = Y on {sum(1 for row in rows if row[cols.index("CONVENTION_DEP")] == "Y")} records')
    cov_rules = {cl.rule_id for cl in ALL_CLAUSES if coverable(cl)}
    print(f'rule coverage: {len(cov_rules) - len(missing_rules)} of {len(cov_rules)} coverable lab-derivable RULE_IDs fired; '
          f'{len([cl for cl in ALL_CLAUSES if coverable(cl)]) - len(missing_clauses)} of {len([cl for cl in ALL_CLAUSES if coverable(cl)])} clauses')
    if missing_clauses: print('  coverable clauses never fired: ' + ' '.join(f'{r}#{s}' for r, s in missing_clauses))
    print('  rules with no clause applied under any published profile (qualifier SYMPTOMATIC / ON_ANTICOAGULATION only): ' + ' '.join(not_coverable))
    print('PASS: records.csv and expectations.csv written, self-checks passed')

if __name__ == '__main__':
    main()
