#!/usr/bin/env python3
"""
qc.py - consistency checks of the published tables (run by CI on every change).

Tables: schema validation of analytes.csv, criteria.csv, conventions.csv and units.csv, cross-table
integrity, and the criteria audit (comparator implied by the quoted CTCAE clause vs the transcribed
comparator, SI vs conventional thresholds, grade monotonicity).
Records (design.md section 8, when records.csv and expectations.csv are present): schema validation,
baseline selection and BASE_* columns, SI and conventional views against units.csv, worst grade and term,
VERSION_DELTA, GRADABLE, CONVENTION_DEP, monotone grades within a subject, coverage of every
lab-derivable RULE_ID, expectations.csv against the wide columns, and an independent re-simulation of
every DEFAULT grade from criteria.csv.

Usage:  python3 generator/qc.py [--data data]        exit code 0 = all checks passed
"""
import csv, datetime as dt, json, os, re, sys
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else os.path.join(ROOT, 'data')
SCHEMA = os.path.join(DATA, 'schema')
PROBLEMS = []
def bad(msg): PROBLEMS.append(msg)

def read(name):
    p = os.path.join(DATA, name + '.csv')
    if not os.path.exists(p): return None
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def schema(name):
    with open(os.path.join(SCHEMA, name + '.schema.json'), encoding='utf-8') as f:
        return json.load(f)

# ----------------------------------------------------------------------------- schema validation
def is_int(s): return re.fullmatch(r'-?\d+', s) is not None
def is_num(s): return re.fullmatch(r'-?\d+(\.\d+)?([eE][-+]?\d+)?', s) is not None
def is_date(s): return re.fullmatch(r'\d{4}-\d{2}-\d{2}', s) is not None

def validate(name, rows):
    sc = schema(name)
    fields = sc['fields']
    names = [f['name'] for f in fields]
    with open(os.path.join(DATA, name + '.csv'), newline='', encoding='utf-8') as f:
        header = next(csv.reader(f))
    if header != names:
        bad(f'{name}.csv: columns differ from schema\n      csv:    {header}\n      schema: {names}')
        return
    for i, r in enumerate(rows, start=2):
        for fd in fields:
            v = r[fd['name']]
            c = fd.get('constraints', {})
            if v == '':
                if c.get('required'): bad(f'{name}.csv row {i}: {fd["name"]} is required')
                continue
            t = fd['type']
            if t == 'integer' and not is_int(v): bad(f'{name}.csv row {i}: {fd["name"]}={v!r} is not an integer')
            elif t == 'number' and not is_num(v): bad(f'{name}.csv row {i}: {fd["name"]}={v!r} is not a number')
            elif t == 'date' and not is_date(v): bad(f'{name}.csv row {i}: {fd["name"]}={v!r} is not an ISO date')
            if 'enum' in c and (int(v) if t == 'integer' and is_int(v) else v) not in c['enum']:
                bad(f'{name}.csv row {i}: {fd["name"]}={v!r} not in {c["enum"]}')
            if 'pattern' in c and not re.fullmatch(c['pattern'], v): bad(f'{name}.csv row {i}: {fd["name"]}={v!r} does not match {c["pattern"]}')
            if 'minimum' in c and is_num(v) and float(v) < c['minimum']: bad(f'{name}.csv row {i}: {fd["name"]}={v} below minimum {c["minimum"]}')
            if 'maximum' in c and is_num(v) and float(v) > c['maximum']: bad(f'{name}.csv row {i}: {fd["name"]}={v} above maximum {c["maximum"]}')
    pk = sc.get('primaryKey')
    if pk:
        pk = [pk] if isinstance(pk, str) else pk
        seen = {}
        for i, r in enumerate(rows, start=2):
            k = tuple(r[c] for c in pk)
            if k in seen: bad(f'{name}.csv row {i}: duplicate primary key {k} (first at row {seen[k]})')
            seen[k] = i
    for fd in fields:
        if fd.get('constraints', {}).get('unique'):
            vals = [r[fd['name']] for r in rows if r[fd['name']] != '']
            dup = sorted({v for v in vals if vals.count(v) > 1})
            if dup: bad(f'{name}.csv: {fd["name"]} not unique: {dup}')

# ----------------------------------------------------------------------------- criteria audit
CMP_RX = re.compile(r'(>=|≥|<=|≤|>|<)')
def implied_comparator(clause, direction, operand, convention):
    """comparator the CTCAE wording implies, following the published reading rules (conventions.csv)"""
    s = clause.strip()
    if s.startswith('Present'): return '>' if direction == 'HIGH' else '<'
    if s.startswith('Laboratory finding only'): return '>' if direction == 'HIGH' else '<'
    if s.startswith('Abnormal glucose above baseline'): return '>'
    if s.startswith('Levels above the upper limit of normal'): return '>'
    if operand == 'PCHG':
        m = re.search(r'(<?)\s*(\d+)\s*(- <\d+)?% decrease', s)
        if m: return '<' if m.group(1) == '<' else '<='
    if s.startswith('Increase in'): return '>'
    body = re.sub(r'^(Corrected serum calcium of|Ionized calcium|Vitamin D decreased|urinary protein|Urinary protein|eGFR or CrCl|eGFR \(estimated Glomerular Filtration Rate\) or CrCl \(creatinine clearance\)|Fasting glucose value|Symptomatic with|absolute value|Hemoglobin \(Hgb\)|Hgb)\s*', '', s)
    m = CMP_RX.match(body)
    if m:
        c = m.group(1).replace('≥', '>=').replace('≤', '<=')
        return c
    if re.match(r'\d', body):                      # range without a leading sign
        if direction == 'HIGH': return '>='        # inclusive lower bound (INCLUSIVE_START)
        if 'SODIUM_V5_GAP' in convention and body.startswith('120-124'): return '<='
        return '<'                                  # integer range on a LOW scale -> strict bound (INTEGER_RANGE)
    return None

THR_RX = re.compile(r'^(-?\d+(?:\.\d+)?)$|^(?:(\d+(?:\.\d+)?)\*)?(ULN|LLN|BASE)$')
def thr_value(t):
    m = THR_RX.match(t)
    if not m: return None
    if m.group(1) is not None: return ('NUM', float(m.group(1)))
    return ('REL', m.group(3), float(m.group(2)) if m.group(2) else 1.0)

# ----------------------------------------------------------------------------- records and expectations (design section 8)
def unorm(u):
    """unit spelling normalisation of the loaders (conventions.csv UNIT_GUARD note)"""
    u = (u or '').strip().replace('µ', 'u').replace('μ', 'u').upper().replace(' ', '')
    u = u.replace('*', '^').replace('^^', '^').replace('X10^', '10^').replace('10E', '10^')
    u = u.replace('IU/L', 'U/L').replace('CELLS/', '/').replace('M^2', 'M2')
    u = u.replace('/24HRS', '/DAY').replace('/24HR', '/DAY').replace('/24H', '/DAY')
    if u.endswith('/D'): u = u[:-2] + '/DAY'
    if u in ('S', 'SEC', 'SECS', 'SECOND', 'SECONDS'): u = 'S'
    return u

def fnum(s): return None if s == '' else float(s)
def close(a, b, rel=1e-5): return abs(a - b) <= rel * max(1.0, abs(a), abs(b))
RULE_RX = re.compile(r'^V([56])\.([A-Z0-9]+)\.([HL])\.(ANY|NRM|ABN|BLL)\.G([1-5])$')

def applied_default(r):
    """clause applied under the DEFAULT profile (CLINICAL_QUALIFIERS, ENZYME_SYMPTOM_WORST)"""
    q, enzyme = r['QUALIFIER'], 'ENZYME_SYMPTOM_WORST' in r['CONVENTION'].split()
    if q == 'ON_ANTICOAGULATION': return False
    if q == 'SYMPTOMATIC': return enzyme
    if q == 'ASYMPTOMATIC': return not enzyme
    return True

def coverable(r):
    """clause applied under at least one published profile (DEFAULT or BESTCASE_ENZYMES)"""
    return applied_default(r) or (r['QUALIFIER'] == 'ASYMPTOMATIC' and 'ENZYME_SYMPTOM_WORST' in r['CONVENTION'].split())

def resimulate(ver, test, d, g, base, CL):
    """independent re-simulation of one version x direction from the criteria rows: g / base = dicts val, lo, hi in UNIT_SI
    (base None when the subject has no usable baseline). Returns the grade (None = missing)."""
    rows = CL.get((ver, test, d), [])
    if not rows or g['val'] is None: return None
    hi_ref = base['hi'] if base and base['hi'] is not None else g['hi']
    lo_ref = base['lo'] if base and base['lo'] is not None else g['lo']
    bval = base['val'] if base else None
    base_high = bval is not None and hi_ref is not None and bval > hi_ref
    base_low = bval is not None and lo_ref is not None and bval < lo_ref
    abn = base_high if d == 'HIGH' else base_low
    truths = defaultdict(list)
    for r in rows:
        if not applied_default(r): continue
        arm = r['BASELINE_ARM']
        if (arm == 'NORMAL' and abn) or (arm == 'ABNORMAL' and not abn) or (arm == 'BELOW_LLN' and not base_low): continue
        tv = thr_value(r['THRESHOLD'])
        if bval is None and ((tv[0] == 'REL' and tv[1] == 'BASE') or r['OPERAND'] == 'PCHG'): continue
        op = r['OPERAND']
        if op == 'VALUE': x = g['val']
        elif op == 'PCHG': x = None if bval in (None, 0) else (g['val'] - bval) / abs(bval) * 100
        elif op == 'EXCESS_ULN': x = None if g['hi'] is None else g['val'] - g['hi']
        else:
            ref = bval if base_high else g['hi']
            x = None if ref is None else g['val'] - ref
        if tv[0] == 'NUM': t = tv[1]
        else:
            ref = {'ULN': g['hi'], 'LLN': g['lo'], 'BASE': bval}[tv[1]]
            t = None if ref is None else tv[2] * ref
        if x is None or t is None: truth = None
        else: truth = {'>': x > t, '>=': x >= t, '<': x < t, '<=': x <= t}[r['COMPARATOR']]
        if r['CONDITION'] == 'VALUE>BASE' and bval is not None:
            cc = g['val'] > bval
            truth = False if (truth is False or cc is False) else (None if truth is None else True)
        truths[int(r['GRADE'])].append(truth)
    indet = False
    for grade in sorted(truths, reverse=True):
        if any(t is True for t in truths[grade]): return grade
        if any(t is None for t in truths[grade]): indet = True
    return None if indet else 0

def check_records(an, cr, cv, un, rec, exp):
    A = {r['LBTESTCD']: r for r in an}
    C = {r['CONVENTION']: r for r in cv}
    U = {(r['LBTESTCD'], unorm(r['FROM_UNIT'])): float(r['FACTOR']) for r in un}
    CL = defaultdict(list); rules = {}
    for r in cr:
        if r['LAB_DERIVABLE'] == 'Y':
            CL[(int(r['VERSION']), r['LBTESTCD'], r['DIRECTION'])].append(r)
            rules.setdefault(r['RULE_ID'], []).append(r)
    numeric = {t for (v, t, d), rows in CL.items() if any(thr_value(r['THRESHOLD'])[0] == 'NUM' and r['OPERAND'] != 'PCHG' for r in rows)}
    by_id = {r['RECORD_ID']: r for r in rec}
    def analyte_spec(r): return r['LBSPEC'] in (A[r['LBTESTCD']]['LBSPEC'], A[r['LBTESTCD']]['LBSPEC_ALT'])
    def graded(r): return analyte_spec(r) and A[r['LBTESTCD']]['DIRECTIONS'] != '' and r['STATUS'] == ''
    def factor(r):
        """as-received -> UNIT_SI factor from the unit alone (None = not convertible)"""
        a = A[r['LBTESTCD']]
        if a['UNIT_SI'] == 'RATIO': return 1.0
        u = unorm(r['UNIT'])
        if u == '': return None
        if u == unorm(a['UNIT_SI']): return 1.0
        if (r['LBTESTCD'], u) in U: return U[(r['LBTESTCD'], u)]
        return None if r['LBTESTCD'] in numeric else 1.0
    def inputs(r):
        f = factor(r)
        sc = lambda s: None if s == '' or f is None else float(s) * f
        return {'val': sc(r['VAL']), 'lo': sc(r['LLN']) if f is not None else fnum(r['LLN']), 'hi': sc(r['ULN']) if f is not None else fnum(r['ULN'])}
    # ---- baseline selection (BASELINE_SELECTION) and BASE_* columns
    groups = defaultdict(list)
    for r in rec: groups[(r['SUBJECT_ID'], r['LBTESTCD'], r['LBSPEC'])].append(r)
    baseline_of = {}
    for key, rs in groups.items():
        cands = [r for r in rs if r['DATE'] <= r['REF_DATE'] and r['STATUS'] == '' and r['VAL'] != '']
        bl = max(cands, key=lambda r: r['DATE']) if cands else None
        flagged = [r for r in rs if r['BASELINE_FLAG'] == 'Y']
        if (bl is None and flagged) or (bl is not None and flagged != [bl]):
            bad(f'records {key}: BASELINE_FLAG is not on the last pre-treatment record with a result')
        for r in rs:
            baseline_of[r['RECORD_ID']] = None if r['STATUS'] != '' else bl
            b = baseline_of[r['RECORD_ID']]
            want = (b['VAL'], b['UNIT'], b['LLN'], b['ULN']) if b else ('', '', '', '')
            if (r['BASE_VAL'], r['BASE_UNIT'], r['BASE_LLN'], r['BASE_ULN']) != want:
                bad(f'records {r["SCENARIO_ID"]}: BASE_* columns do not repeat the baseline record')
    # ---- per record
    resim_ok = resim_n = 0
    for r in rec:
        sid, t = r['SCENARIO_ID'], r['LBTESTCD']
        if t not in A: bad(f'records {sid}: unknown LBTESTCD'); continue
        a = A[t]
        if r['LBTEST'] != a['LBTEST']: bad(f'records {sid}: LBTEST differs from analytes')
        if analyte_spec(r) and r['LBDUR'] != a['LBDUR']: bad(f'records {sid}: LBDUR differs from analytes')
        exp_cols = [c for c in r if c.startswith('EXP_')]
        day = (dt.date.fromisoformat(r['DATE']) - dt.date.fromisoformat(r['REF_DATE'])).days
        if int(r['STUDY_DAY']) != (day + 1 if day >= 0 else day): bad(f'records {sid}: STUDY_DAY does not match DATE and REF_DATE')
        for code in r['CONVENTIONS'].split():
            if code not in C: bad(f'records {sid}: unknown convention {code}')
        dep = 'Y' if any(C.get(c, {}).get('CONVENTION_DEP') == 'Y' for c in r['CONVENTIONS'].split()) else 'N'
        if r['CONVENTION_DEP'] != dep: bad(f'records {sid}: CONVENTION_DEP should be {dep}')
        grades = [r[c] for c in exp_cols if c.startswith('EXP_GRADE_LOW') or c.startswith('EXP_GRADE_HIGH')]
        if r['GRADABLE'] != ('Y' if any(g != '' for g in grades) else 'N'): bad(f'records {sid}: GRADABLE inconsistent with the expected grades')
        if r['GRADABLE'] == 'Y' and r['RULE_IDS'] == '': bad(f'records {sid}: gradable record without RULE_IDS')
        for rid in r['RULE_IDS'].split():
            m = RULE_RX.match(rid)
            if rid not in rules: bad(f'records {sid}: RULE_ID {rid} is not a lab-derivable criteria rule')
            elif m.group(2) != t: bad(f'records {sid}: RULE_ID {rid} is for another test')
        if not graded(r) or not analyte_spec(r):
            if any(r[c] != '' for c in exp_cols) and (r['STATUS'] != '' or not analyte_spec(r)):
                bad(f'records {sid}: NOT DONE or other-specimen record with expectations')
            if r['STATUS'] != '' and (r['BASE_VAL'] != '' or r['BASELINE_FLAG'] != ''): bad(f'records {sid}: NOT DONE record with baseline columns')
        if not analyte_spec(r):
            if r['UNIT_SI'] != '' or r['VAL_SI'] != '' or r['UNIT_CONV'] != '': bad(f'records {sid}: other-specimen record with unit views')
        else:
            if r['UNIT_SI'] != a['UNIT_SI'] or r['UNIT_CONV'] != a['UNIT_CONV']: bad(f'records {sid}: UNIT_SI / UNIT_CONV differ from analytes')
            f = factor(r); fcs = float(a['FACTOR_CONV_TO_SI'])
            for col, si_col, cv_col in (('VAL', 'VAL_SI', 'VAL_CONV'), ('LLN', 'LLN_SI', 'LLN_CONV'), ('ULN', 'ULN_SI', 'ULN_CONV')):
                if f is None or r[col] == '':
                    if r[si_col] != '' or r[cv_col] != '': bad(f'records {sid}: {si_col} present although not convertible')
                    continue
                if r[si_col] == '' or not close(float(r[si_col]), float(r[col]) * f): bad(f'records {sid}: {si_col} is not {col} x {f}')
                if r[cv_col] == '' or not close(float(r[cv_col]) * fcs, float(r[si_col])): bad(f'records {sid}: {cv_col} is not {si_col} / FACTOR_CONV_TO_SI')
            b = baseline_of[r['RECORD_ID']]
            if b is not None:
                bf = factor(b)
                for col, si_col, cv_col in (('VAL', 'BASE_VAL_SI', 'BASE_VAL_CONV'), ('LLN', 'BASE_LLN_SI', 'BASE_LLN_CONV'), ('ULN', 'BASE_ULN_SI', 'BASE_ULN_CONV')):
                    if bf is None or b[col] == '':
                        if r[si_col] != '': bad(f'records {sid}: {si_col} present although the baseline is not convertible')
                        continue
                    if r[si_col] == '' or not close(float(r[si_col]), float(b[col]) * bf): bad(f'records {sid}: {si_col} is not the converted baseline')
                    if r[cv_col] == '' or not close(float(r[cv_col]) * fcs, float(r[si_col])): bad(f'records {sid}: {cv_col} is not {si_col} / FACTOR_CONV_TO_SI')
        # expected columns: terms, worst grade and term, version delta, baseline grades, re-simulation
        tuples = {}
        for v in (5, 6):
            gl, gh = r[f'EXP_GRADE_LOW_V{v}'], r[f'EXP_GRADE_HIGH_V{v}']
            tl, th = r[f'EXP_TERM_LOW_V{v}'], r[f'EXP_TERM_HIGH_V{v}']
            tuples[v] = (gl, gh, tl, th, r[f'EXP_BASE_GRADE_LOW_V{v}'], r[f'EXP_BASE_GRADE_HIGH_V{v}'], r[f'EXP_GRADE_V{v}'], r[f'EXP_TERM_V{v}'])
            if graded(r):
                for d, term, g in (('LOW', tl, gl), ('HIGH', th, gh)):
                    want = a[f'TERM_V{v}_{d}']
                    if term != want: bad(f'records {sid}: EXP_TERM_{d}_V{v} {term!r} should be {want!r}')
                    if want == '' and g != '': bad(f'records {sid}: grade without a term for v{v} {d}')
                    if want != '' and r['VAL'] == '' and g != '': bad(f'records {sid}: missing result with a grade')
            nums = [int(x) for x in (gl, gh) if x != '']
            worst = '' if not nums else str(max(nums))
            if r[f'EXP_GRADE_V{v}'] != worst: bad(f'records {sid}: EXP_GRADE_V{v} should be {worst!r}')
            if worst != '':
                if int(worst) == 0 and tl and th: wt = ''
                elif gh != '' and (gl == '' or int(gh) >= int(gl)): wt = th
                else: wt = tl
                if r[f'EXP_TERM_V{v}'] != wt: bad(f'records {sid}: EXP_TERM_V{v} should be {wt!r}')
            elif r[f'EXP_TERM_V{v}'] != '': bad(f'records {sid}: EXP_TERM_V{v} without a grade')
            b = baseline_of[r['RECORD_ID']]
            for d in ('LOW', 'HIGH'):
                want = b[f'EXP_GRADE_{d}_V{v}'] if (b is not None and graded(r)) else ''
                if r[f'EXP_BASE_GRADE_{d}_V{v}'] != want: bad(f'records {sid}: EXP_BASE_GRADE_{d}_V{v} should be {want!r}')
            if graded(r):
                g = inputs(r)
                base = inputs(b) if b is not None else None
                if base is not None and base['val'] is None: base = None
                for d, col in (('LOW', gl), ('HIGH', gh)):
                    if a[f'TERM_V{v}_{d}'] == '': continue
                    sim = resimulate(v, t, d, g, base, CL)
                    resim_n += 1
                    if ('' if sim is None else str(sim)) == col: resim_ok += 1
                    else: bad(f'records {sid}: re-simulated v{v} {d} grade {sim} differs from EXP_GRADE_{d}_V{v}={col!r}')
        if r['VERSION_DELTA'] != ('Y' if tuples[5] != tuples[6] else 'N'): bad(f'records {sid}: VERSION_DELTA inconsistent')
    # ---- monotone grades within a subject (fixed baseline): HIGH never decreases, LOW never increases with the value
    for key, rs in groups.items():
        post = [r for r in rs if graded(r) and r['BASELINE_FLAG'] != 'Y' and r['DATE'] > r['REF_DATE'] and r['VAL_SI'] != '']
        post.sort(key=lambda r: float(r['VAL_SI']))
        for v in (5, 6):
            for d, sign in (('HIGH', 1), ('LOW', -1)):
                seq = [(r['SCENARIO_ID'], int(r[f'EXP_GRADE_{d}_V{v}'])) for r in post if r[f'EXP_GRADE_{d}_V{v}'] != '']
                for (s1, g1), (s2, g2) in zip(seq, seq[1:]):
                    if sign * (g2 - g1) < 0: bad(f'records {key}: v{v} {d} grade not monotone ({s1}={g1}, {s2}={g2})'); break
    # ---- rule coverage: every coverable lab-derivable RULE_ID gives the grade of at least one record
    fired = set()
    for r in rec:
        for rid in r['RULE_IDS'].split():
            m = RULE_RX.match(rid)
            if m and r[f'EXP_GRADE_{ {"H": "HIGH", "L": "LOW"}[m.group(3)] }_V{m.group(1)}'] == m.group(5): fired.add(rid)
    cov = {rid for rid, rows in rules.items() if any(coverable(x) for x in rows)}
    missing = sorted(cov - fired)
    if missing: bad('rule coverage: coverable RULE_IDs never giving a grade: ' + ' '.join(missing))
    # ---- expectations.csv against the wide columns
    E = defaultdict(dict)
    for e in exp:
        if e['RECORD_ID'] not in by_id: bad(f'expectations: RECORD_ID {e["RECORD_ID"]} not in records.csv'); continue
        E[(e['RECORD_ID'], e['VERSION'], e['PROFILE'])][e['DIRECTION']] = (e['GRADE'], e['TERM'], e['BASE_GRADE'])
    for r in rec:
        for v in ('5', '6'):
            want = {'LOW': (r[f'EXP_GRADE_LOW_V{v}'], r[f'EXP_TERM_LOW_V{v}'], r[f'EXP_BASE_GRADE_LOW_V{v}']),
                    'HIGH': (r[f'EXP_GRADE_HIGH_V{v}'], r[f'EXP_TERM_HIGH_V{v}'], r[f'EXP_BASE_GRADE_HIGH_V{v}'])}
            bl = [int(x) for x in (want['LOW'][2], want['HIGH'][2]) if x != '']
            want['WORST'] = (r[f'EXP_GRADE_V{v}'], r[f'EXP_TERM_V{v}'], '' if not bl else str(max(bl)))
            got = E.get((r['RECORD_ID'], v, 'DEFAULT'))
            if got != want: bad(f'expectations {r["SCENARIO_ID"]} v{v}: DEFAULT rows differ from records.csv')
    for (rid, v, p), dirs in E.items():
        if set(dirs) != {'LOW', 'HIGH', 'WORST'}: bad(f'expectations {rid} v{v} {p}: LOW, HIGH and WORST rows expected')
        if p != 'DEFAULT' and dirs == E.get((rid, v, 'DEFAULT')): bad(f'expectations {rid} v{v} {p}: alternative profile identical to DEFAULT')
    # ---- the reference loaders must know every column of records.csv and expectations.csv
    for loader in ('reference/sas/load_records.sas', 'reference/r/load_records.R'):
        path = os.path.join(ROOT, loader)
        if not os.path.exists(path): continue
        with open(path, encoding='utf-8') as f: src = f.read()
        for name in ('records', 'expectations'):
            for fd in schema(name)['fields']:
                if not re.search(r'\b' + re.escape(fd['name']) + r'\b', src): bad(f'{loader}: column {fd["name"]} of {name}.csv is not declared')
        for m in re.finditer(r'\b([A-Z0-9_]+) \$(\d+)\b', src):
            col, n = m.group(1), int(m.group(2))
            if col in rec[0]:
                longest = max(len(r[col]) for r in rec)
                if longest > n: bad(f'{loader}: length ${n} of {col} is shorter than the longest value ({longest})')
    n_alt = sum(1 for k in E if k[2] != 'DEFAULT')
    print(f'records {len(rec)} rows, expectations {len(exp)} rows ({n_alt} record x version pairs under an alternative profile); '
          f'subjects {len({r["SUBJECT_ID"] for r in rec})}; modules ' + ', '.join(f'{m}:{n}' for m, n in sorted(Counter(r['MODULE'] for r in rec).items())))
    print(f'records audit: {resim_ok} of {resim_n} expected grades re-simulated from criteria.csv agree; '
          f'rule coverage {len(cov) - len(missing)} of {len(cov)} coverable lab-derivable RULE_IDs ({len(rules) - len(cov)} rules have no clause applied under any profile)')

def main():
    an, cr, cv, un = read('analytes'), read('criteria'), read('conventions'), read('units')
    for name, rows in (('analytes', an), ('criteria', cr), ('conventions', cv), ('units', un)):
        validate(name, rows)
    rec, exp = read('records'), read('expectations')
    for name, rows in (('records', rec), ('expectations', exp)):
        if rows is not None: validate(name, rows)
    A = {r['LBTESTCD']: r for r in an}
    C = {r['CONVENTION']: r for r in cv}
    U = {(r['LBTESTCD'], r['FROM_UNIT']): r for r in un}

    # ---- analytes
    for r in an:
        if r['UNIT_SI'] != r['UNIT_CONV']:
            k = (r['LBTESTCD'], r['UNIT_CONV'])
            if k not in U: bad(f'analytes {r["LBTESTCD"]}: no units.csv row {r["UNIT_CONV"]} -> {r["UNIT_SI"]}')
            elif abs(float(U[k]['FACTOR']) - float(r['FACTOR_CONV_TO_SI'])) > 1e-12:
                bad(f'analytes {r["LBTESTCD"]}: FACTOR_CONV_TO_SI {r["FACTOR_CONV_TO_SI"]} differs from units.csv {U[k]["FACTOR"]}')
        elif float(r['FACTOR_CONV_TO_SI']) != 1: bad(f'analytes {r["LBTESTCD"]}: same unit but factor {r["FACTOR_CONV_TO_SI"]}')
        for a in r['ALIAS_LBTESTCD'].split():
            if a in A: bad(f'analytes {r["LBTESTCD"]}: alias {a} is itself an analyte row')
        if r['LLN_SI'] and r['ULN_SI'] and float(r['LLN_SI']) >= float(r['ULN_SI']): bad(f'analytes {r["LBTESTCD"]}: LLN >= ULN')
        dirs = set()
        for col in ('TERM_V5_HIGH', 'TERM_V6_HIGH'):
            if r[col]: dirs.add('H')
        for col in ('TERM_V5_LOW', 'TERM_V6_LOW'):
            if r[col]: dirs.add('L')
        want = ('H' if 'H' in dirs else '') + ('L' if 'L' in dirs else '')
        if want != r['DIRECTIONS']: bad(f'analytes {r["LBTESTCD"]}: DIRECTIONS {r["DIRECTIONS"]!r} but terms imply {want!r}')
    # ---- units
    for r in un:
        if r['LBTESTCD'] not in A: bad(f'units {r["LBTESTCD"]} {r["FROM_UNIT"]}: unknown LBTESTCD')
        elif r['TO_UNIT'] != A[r['LBTESTCD']]['UNIT_SI']: bad(f'units {r["LBTESTCD"]} {r["FROM_UNIT"]}: TO_UNIT {r["TO_UNIT"]} is not the analyte UNIT_SI {A[r["LBTESTCD"]]["UNIT_SI"]}')
        if r['FROM_UNIT'] == r['TO_UNIT']: bad(f'units {r["LBTESTCD"]}: FROM_UNIT equals TO_UNIT')
    # ---- conventions
    used = defaultdict(int)
    for r in cr:
        for code in r['CONVENTION'].split():
            used[code] += 1
            if code not in C: bad(f'criteria {r["RULE_ID"]}: unknown convention {code}')
    for r in cv:
        for t in r['LBTESTCD'].split():
            if t != 'ALL' and t not in A: bad(f'conventions {r["CONVENTION"]}: unknown LBTESTCD {t}')
        if r['SCOPE'] == 'GRADING' and used[r['CONVENTION']] == 0: bad(f'conventions {r["CONVENTION"]}: GRADING convention not referenced by any criteria row')
        if r['ALTERNATIVE_PROFILE'] and not r['ALTERNATIVE_CHOICE']: bad(f'conventions {r["CONVENTION"]}: profile without alternative text')
    # ---- criteria
    terms = defaultdict(set); audit_ok = audit_bad = 0; max_dev = [0.0]
    by_group = defaultdict(list)
    for r in cr:
        t = r['LBTESTCD']
        if t not in A: bad(f'criteria {r["RULE_ID"]}: unknown LBTESTCD'); continue
        a = A[t]
        if r['LBSPEC'] != a['LBSPEC']: bad(f'criteria {r["RULE_ID"]}: LBSPEC {r["LBSPEC"]} differs from analytes {a["LBSPEC"]}')
        exp_id = f'V{r["VERSION"]}.{t}.{r["DIRECTION"][0]}.{ {"ANY":"ANY","NORMAL":"NRM","ABNORMAL":"ABN","BELOW_LLN":"BLL"}[r["BASELINE_ARM"]] }.G{r["GRADE"]}'
        if r['RULE_ID'] != exp_id: bad(f'criteria {r["RULE_ID"]}: RULE_ID should be {exp_id}')
        terms[(r['VERSION'], t, r['DIRECTION'])].add(r['CTCAE_TERM'])
        frags = [re.sub(r'\s+', ' ', x).strip() for x in r['CLAUSE'].split('; ')]
        w = re.sub(r'\s+', ' ', r['WORDING'])
        # a clause of several fragments is checked fragment by fragment; a single fragment may itself contain '; '
        if r['CLAUSE'] not in w and not all(fr in w for fr in frags):
            bad(f'criteria {r["RULE_ID"]}#{r["CLAUSE_SEQ"]}: CLAUSE is not a fragment of WORDING')
        col = a['TERM_V%s_%s' % (r['VERSION'], r['DIRECTION'])]
        if col != r['CTCAE_TERM']: bad(f'criteria {r["RULE_ID"]}: term {r["CTCAE_TERM"]!r} differs from analytes {col!r}')
        if r['LAB_DERIVABLE'] == 'N':
            if r['COMPARATOR'] or r['THRESHOLD'] or r['OPERAND']: bad(f'criteria {r["RULE_ID"]}#{r["CLAUSE_SEQ"]}: LAB_DERIVABLE = N but comparator/threshold present')
            continue
        if not (r['COMPARATOR'] and r['THRESHOLD'] and r['OPERAND']): bad(f'criteria {r["RULE_ID"]}#{r["CLAUSE_SEQ"]}: lab-derivable row without comparator, operand or threshold'); continue
        tv = thr_value(r['THRESHOLD'])
        if tv is None: bad(f'criteria {r["RULE_ID"]}: bad THRESHOLD {r["THRESHOLD"]!r}'); continue
        if tv[0] == 'NUM':
            want_u = '%' if r['OPERAND'] == 'PCHG' else a['UNIT_SI']
            if r['THRESHOLD_UNIT'] != want_u: bad(f'criteria {r["RULE_ID"]}: THRESHOLD_UNIT {r["THRESHOLD_UNIT"]!r} should be {want_u!r}')
            if r['THRESHOLD_CONV'] and r['OPERAND'] != 'PCHG':
                if r['THRESHOLD_CONV_UNIT'] != a['UNIT_CONV']: bad(f'criteria {r["RULE_ID"]}: THRESHOLD_CONV_UNIT {r["THRESHOLD_CONV_UNIT"]!r} should be {a["UNIT_CONV"]!r}')
                if is_num(r['THRESHOLD_CONV']) and a['UNIT_SI'] != a['UNIT_CONV']:
                    si_from_conv = float(r['THRESHOLD_CONV']) * float(a['FACTOR_CONV_TO_SI'])
                    # CTCAE prints rounded pairs (0.9 mg/dL ~ 0.4 mmol/L magnesium is 7.5% off); 10% still catches transposed digits
                    dev = abs(si_from_conv - tv[1]) / abs(tv[1]) if tv[1] != 0 else (0 if si_from_conv == 0 else 1)
                    max_dev[0] = max(max_dev[0], dev)
                    if dev > 0.10:
                        bad(f'criteria {r["RULE_ID"]}: THRESHOLD {tv[1]} {a["UNIT_SI"]} vs THRESHOLD_CONV {r["THRESHOLD_CONV"]} {a["UNIT_CONV"]} (= {si_from_conv:g} {a["UNIT_SI"]}) differ by {dev:.1%}')
        else:
            if r['THRESHOLD_UNIT']: bad(f'criteria {r["RULE_ID"]}: relative threshold with THRESHOLD_UNIT')
            if tv[1] == 'BASE' and r['BASELINE_ARM'] == 'ANY' and 'CREAT_BASELINE_ARM' not in r['CONVENTION'] and r['QUALIFIER'] != 'ON_ANTICOAGULATION':
                bad(f'criteria {r["RULE_ID"]}: baseline multiple under arm ANY without CREAT_BASELINE_ARM')
        imp = implied_comparator(r['CLAUSE'], r['DIRECTION'], r['OPERAND'], r['CONVENTION'])
        if imp is None: bad(f'criteria {r["RULE_ID"]}#{r["CLAUSE_SEQ"]}: audit cannot read a comparator from {r["CLAUSE"]!r}')
        elif imp != r['COMPARATOR']: audit_bad += 1; bad(f'criteria {r["RULE_ID"]}#{r["CLAUSE_SEQ"]}: wording {r["CLAUSE"]!r} implies {imp}, row has {r["COMPARATOR"]}')
        else: audit_ok += 1
        if r['DIRECTION'] == 'HIGH' and r['COMPARATOR'] not in ('>', '>='): bad(f'criteria {r["RULE_ID"]}: HIGH scale with comparator {r["COMPARATOR"]}')
        if r['DIRECTION'] == 'LOW' and r['COMPARATOR'] not in ('<', '<='): bad(f'criteria {r["RULE_ID"]}: LOW scale with comparator {r["COMPARATOR"]}')
        by_group[(r['VERSION'], t, r['DIRECTION'], r['BASELINE_ARM'], r['OPERAND'], r['QUALIFIER'] in ('SYMPTOMATIC', 'ON_ANTICOAGULATION'))].append((int(r['GRADE']), tv, r['RULE_ID']))
    for k, v in terms.items():
        if len(v) > 1: bad(f'criteria: several terms for {k}: {sorted(v)}')
    # monotonicity: within a group of comparable thresholds, higher grades have stricter bounds
    for k, items in by_group.items():
        nums = sorted((g, tv[1]) for g, tv, _ in items if tv[0] == 'NUM')
        rels = defaultdict(list)
        for g, tv, _ in items:
            if tv[0] == 'REL': rels[tv[1]].append((g, tv[2]))
        for seq in [nums] + [sorted(v) for v in rels.values()]:
            for (g1, x1), (g2, x2) in zip(seq, seq[1:]):
                if g1 == g2: continue
                ok = x2 > x1 if k[2] == 'HIGH' else x2 < x1
                if k[4] == 'PCHG': ok = x2 < x1
                if not ok: bad(f'criteria {k}: grade {g2} threshold {x2} not stricter than grade {g1} threshold {x1}')
    # every analyte with a term has criteria in that version, and vice versa
    for a in an:
        for v in (5, 6):
            for d in ('HIGH', 'LOW'):
                has_term = a[f'TERM_V{v}_{d}'] != ''
                has_rows = (str(v), a['LBTESTCD'], d) in terms
                if has_term != has_rows: bad(f'analytes {a["LBTESTCD"]} v{v} {d}: term {"present" if has_term else "absent"} but criteria rows {"present" if has_rows else "absent"}')
    if rec is not None and exp is not None: check_records(an, cr, cv, un, rec, exp)
    n_lab = sum(r['LAB_DERIVABLE'] == 'Y' for r in cr)
    print(f'analytes {len(an)} rows, criteria {len(cr)} rows ({n_lab} lab-derivable, {len({r["RULE_ID"] for r in cr})} rule ids), conventions {len(cv)}, units {len(un)}')
    print(f'criteria audit: {audit_ok} comparators agree with the wording, {audit_bad} disagree; largest SI vs conventional threshold deviation {max_dev[0]:.1%}')
    if PROBLEMS:
        print(f'\nFAIL: {len(PROBLEMS)} problem(s)')
        for p in PROBLEMS: print(' -', p)
        sys.exit(1)
    print('PASS: all table checks passed')

if __name__ == '__main__':
    main()
