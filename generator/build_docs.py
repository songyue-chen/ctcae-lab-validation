#!/usr/bin/env python3
"""
build_docs.py - regenerates the documentation that mirrors the published tables:

  docs/data_dictionary.md   every column of records.csv and expectations.csv (from data/schema/*.schema.json)
                            and the columns of the four reference tables
  docs/conventions.md       every reading convention (from data/conventions.csv) and the alternative profiles
  docs/coverage.md          record and rule coverage of the current records.csv

Usage:  python3 generator/build_docs.py [--data data] [--docs docs]      deterministic; CI checks the files are current
"""
import csv, json, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else os.path.join(ROOT, 'data')
DOCS = sys.argv[sys.argv.index('--docs') + 1] if '--docs' in sys.argv else os.path.join(ROOT, 'docs')
PROFILES = ['DEFAULT', 'BESTCASE_ENZYMES', 'HYPERGLY_NUMERIC_V5', 'PRESENT_NOT_LAB', 'UNGRADABLE_ZERO', 'BASELINE_STRICT']
RULE_RX = re.compile(r'^V([56])\.([A-Z0-9]+)\.([HL])\.(ANY|NRM|ABN|BLL)\.G([1-5])$')

def read(name):
    with open(os.path.join(DATA, name + '.csv'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def schema(name):
    with open(os.path.join(DATA, 'schema', name + '.schema.json'), encoding='utf-8') as f:
        return json.load(f)

def md(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')

def write(name, text):
    with open(os.path.join(DOCS, name), 'w', encoding='utf-8') as f:
        f.write(text.rstrip('\n') + '\n')

# ----------------------------------------------------------------------------- data dictionary
def data_dictionary():
    out = ['# Data dictionary', '',
           'Generated from `data/schema/*.schema.json` (Frictionless Table Schema) by `generator/build_docs.py`; the schema files are the',
           'authoritative definition and `generator/qc.py` validates every table against them.', '']
    for name, intro in (('records', 'One row per laboratory record. Feed the as-received columns to the implementation under test, merge its output back on RECORD_ID and compare with the EXP_* columns of the version being validated.'),
                        ('expectations', 'Long form of the expected values: the DEFAULT profile repeats the EXP_* columns of records.csv; alternative profiles are published only for the record and version pairs they change.')):
        sc = schema(name)
        out += [f'## data/{name}.csv', '', intro, '', f'{md(sc["description"])}', '', '| Column | Type | Constraints | Description |', '|---|---|---|---|']
        for fd in sc['fields']:
            c = fd.get('constraints', {})
            cons = []
            if c.get('required'): cons.append('required')
            if c.get('unique'): cons.append('unique')
            if 'enum' in c: cons.append('one of ' + ', '.join(str(x) for x in c['enum']))
            if 'minimum' in c or 'maximum' in c: cons.append(f'{c.get("minimum", "")}-{c.get("maximum", "")}')
            if 'pattern' in c: cons.append(f'pattern `{c["pattern"]}`')
            out.append(f'| {fd["name"]} | {fd["type"]} | {md("; ".join(cons))} | {md(fd.get("description", ""))} |')
        pk = sc.get('primaryKey')
        if pk: out += ['', f'Primary key: {", ".join(pk) if isinstance(pk, list) else pk}']
        out.append('')
    for name in ('analytes', 'criteria', 'conventions', 'units'):
        sc = schema(name)
        out += [f'## data/{name}.csv', '', md(sc['description']), '', '| Column | Type | Description |', '|---|---|---|']
        for fd in sc['fields']:
            out.append(f'| {fd["name"]} | {fd["type"]} | {md(fd.get("description", ""))} |')
        out.append('')
    out += ['## Naming aliases applied by the loaders', '',
            '| records.csv | ADaM (`naming=ADAM`) | SDTM (`naming=SDTM`) |', '|---|---|---|',
            '| SUBJECT_ID | USUBJID | USUBJID |', '| LBTESTCD | PARAMCD | LBTESTCD |', '| LBTEST | PARAM | LBTEST |',
            '| VAL | AVAL | LBSTRESN |', '| UNIT | AVALU | LBSTRESU |', '| LLN | ANRLO | LBSTNRLO |', '| ULN | ANRHI | LBSTNRHI |',
            '| DATE | ADT | LBDTC (ISO 8601 character) |', '| STUDY_DAY | ADY | LBDY |', '| REF_DATE | TRTSDT | RFSTDTC (ISO 8601 character) |',
            '| BASELINE_FLAG | ABLFL | LBBLFL |', '| BASE_VAL, BASE_LLN, BASE_ULN | BASE, BNRLO, BNRHI | unchanged |',
            '| STATUS | STATUS | LBSTAT |', '',
            'Every other column, including LBSPEC, LBDUR, the SI and conventional views and the EXP_* expectations, keeps its name.', '']
    write('data_dictionary.md', '\n'.join(out))

# ----------------------------------------------------------------------------- conventions
def conventions():
    cv = read('conventions')
    exp = read('expectations')
    changed = Counter((r['PROFILE'], r['VERSION']) for r in exp if r['PROFILE'] != 'DEFAULT' and r['DIRECTION'] == 'LOW')
    out = ['# Conventions behind the expected values', '',
           'Generated from `data/conventions.csv` by `generator/build_docs.py`. A convention is a reading the CTCAE wording does not',
           'settle. The DEFAULT profile applies the default choice of every convention; where a defensible alternative exists it is',
           'published as an alternative profile in `data/expectations.csv`, for the records it changes. Records whose expectation',
           'depends on a convention marked CONVENTION_DEP = Y carry CONVENTION_DEP = Y in `data/records.csv`, so an adopter can',
           'validate against the undisputed criteria alone by excluding them.', '',
           '## Alternative profiles', '', '| Profile | Flips | Record x version pairs changed |', '|---|---|---|']
    for p in PROFILES[1:]:
        flips = [r['CONVENTION'] for r in cv if r['ALTERNATIVE_PROFILE'] == p]
        pairs = ', '.join(f'v{v}: {changed[(p, v)]}' for v in ('5', '6') if changed[(p, v)]) or 'none'
        out.append(f'| {p} | {", ".join(flips)} | {pairs} |')
    out += ['', '## Conventions', '']
    for scope, title in (('GRADING', 'How a CTCAE criterion is read'), ('DATA', 'How record states are handled')):
        out += [f'### {title} (SCOPE = {scope})', '']
        for r in cv:
            if r['SCOPE'] != scope: continue
            out += [f'#### {r["CONVENTION"]}: {r["TITLE"]}', '',
                    f'- Versions: {r["VERSIONS"]}; tests: {r["LBTESTCD"]}; CONVENTION_DEP = {r["CONVENTION_DEP"]}' +
                    (f'; alternative profile: {r["ALTERNATIVE_PROFILE"]}' if r['ALTERNATIVE_PROFILE'] else '')]
            if r['CTCAE_WORDING']: out.append(f'- CTCAE wording: {md(r["CTCAE_WORDING"])}')
            out.append(f'- Default choice: {md(r["DEFAULT_CHOICE"])}')
            if r['ALTERNATIVE_CHOICE']: out.append(f'- Alternative choice: {md(r["ALTERNATIVE_CHOICE"])}')
            if r['NOTE']: out.append(f'- Note: {md(r["NOTE"])}')
            out.append('')
    write('conventions.md', '\n'.join(out))

# ----------------------------------------------------------------------------- coverage
def coverage():
    rec, cr, an, exp = read('records'), read('criteria'), read('analytes'), read('expectations')
    A = {r['LBTESTCD']: r for r in an}
    fired = set()
    for r in rec:
        for rid in r['RULE_IDS'].split():
            m = RULE_RX.match(rid)
            if m and r[f'EXP_GRADE_{ {"H": "HIGH", "L": "LOW"}[m.group(3)] }_V{m.group(1)}'] == m.group(5): fired.add(rid)
    rules = defaultdict(list)
    for r in cr: rules[r['RULE_ID']].append(r)
    def applied_default(r):
        q, enzyme = r['QUALIFIER'], 'ENZYME_SYMPTOM_WORST' in r['CONVENTION'].split()
        if q == 'ON_ANTICOAGULATION': return False
        if q == 'SYMPTOMATIC': return enzyme
        if q == 'ASYMPTOMATIC': return not enzyme
        return True
    def coverable(r): return applied_default(r) or (r['QUALIFIER'] == 'ASYMPTOMATIC' and 'ENZYME_SYMPTOM_WORST' in r['CONVENTION'].split())
    lab = {rid for rid, rows in rules.items() if any(x['LAB_DERIVABLE'] == 'Y' for x in rows)}
    cov = {rid for rid in lab if any(coverable(x) for x in rules[rid] if x['LAB_DERIVABLE'] == 'Y')}
    out = ['# Coverage', '', 'Generated from `data/records.csv`, `data/criteria.csv` and `data/expectations.csv` by `generator/build_docs.py`.',
           'A criteria rule is *exercised* when at least one record lists it in RULE_IDS and carries that grade for the version and',
           'direction; it is *coverable* when at least one of its clauses is applied under a published profile (clauses qualified',
           '"symptomatic" or "if on anticoagulation" of terms that are not amylase or lipase are never applied, see conventions.md).', '',
           '## Records', '', f'- Records: {len(rec)}; subjects: {len({r["SUBJECT_ID"] for r in rec})}; tests: {len({r["LBTESTCD"] for r in rec})}',
           f'- Gradable records (a grade expected in at least one version and direction): {sum(r["GRADABLE"] == "Y" for r in rec)}',
           f'- Records flagged CONVENTION_DEP = Y: {sum(r["CONVENTION_DEP"] == "Y" for r in rec)}',
           f'- Records whose v5 and v6 expectations differ (VERSION_DELTA = Y): {sum(r["VERSION_DELTA"] == "Y" for r in rec)}', '',
           '| Module | Records | Subjects | Gradable |', '|---|---|---|---|']
    for mname in ('CORE', 'BASELINE', 'MISSING', 'NOTDONE', 'UNITS', 'CATEGORY'):
        rs = [r for r in rec if r['MODULE'] == mname]
        out.append(f'| {mname} | {len(rs)} | {len({r["SUBJECT_ID"] for r in rs})} | {sum(r["GRADABLE"] == "Y" for r in rs)} |')
    out += ['', '## Rules by version', '', '| Version | Rules in criteria.csv | Lab-derivable | Coverable | Exercised |', '|---|---|---|---|---|']
    for v in ('5', '6'):
        allv = {rid for rid in rules if rid.startswith(f'V{v}.')}
        out.append(f'| {v} | {len(allv)} | {len(lab & allv)} | {len(cov & allv)} | {len(fired & cov & allv)} |')
    nc = sorted(lab - cov)
    out += ['', 'Lab-derivable rules with no clause applied under any published profile: ' + ', '.join(nc) + '.', '']
    miss = sorted(cov - fired)
    out += ['Coverable rules not exercised: ' + (', '.join(miss) if miss else 'none') + '.', '']
    out += ['## Records and exercised rules by test', '', '| LBTESTCD | LBTEST | Records | Subjects | v5 rules exercised / coverable | v6 rules exercised / coverable |', '|---|---|---|---|---|---|']
    for t in sorted(A):
        rs = [r for r in rec if r['LBTESTCD'] == t]
        if not rs: continue
        cells = []
        for v in ('5', '6'):
            c = {rid for rid in cov if rid.startswith(f'V{v}.{t}.')}
            cells.append(f'{len(c & fired)} / {len(c)}' if c else '-')
        out.append(f'| {t} | {A[t]["LBTEST"]} | {len(rs)} | {len({r["SUBJECT_ID"] for r in rs})} | {cells[0]} | {cells[1]} |')
    out += ['', '## Alternative profiles', '', '| Profile | Version | Records changed |', '|---|---|---|']
    changed = Counter((r['PROFILE'], r['VERSION']) for r in exp if r['PROFILE'] != 'DEFAULT' and r['DIRECTION'] == 'LOW')
    for (p, v), n in sorted(changed.items()): out.append(f'| {p} | {v} | {n} |')
    out += ['', '## Subjects', '', '| Subject | Module | Test | Records | Description of the subject |', '|---|---|---|---|---|']
    seen = []
    for r in rec:
        if r['SUBJECT_ID'] not in seen: seen.append(r['SUBJECT_ID'])
    for s in seen:
        rs = [r for r in rec if r['SUBJECT_ID'] == s]
        arm = s.split('-', 2)[2] if s.count('-') >= 2 else ''
        kind = {'N': 'normal baseline', 'Y': 'abnormal baseline', 'M': 'no baseline', 'LO': 'baseline below LLN', 'HI': 'baseline above ULN'}.get(arm)
        if kind is None:
            post = [r for r in rs if r['BASELINE_FLAG'] != 'Y']
            kind = post[0]['DESCRIPTION'] if post else rs[0]['DESCRIPTION']
        out.append(f'| {s} | {rs[0]["MODULE"]} | {rs[0]["LBTESTCD"]} | {len(rs)} | {md(kind)} |')
    write('coverage.md', '\n'.join(out))

if __name__ == '__main__':
    os.makedirs(DOCS, exist_ok=True)
    data_dictionary(); conventions(); coverage()
    print('docs written: data_dictionary.md conventions.md coverage.md')
