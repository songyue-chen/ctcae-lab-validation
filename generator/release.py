#!/usr/bin/env python3
"""
release.py - assembles the user-facing package from the build folder into the release repository.

The release repository holds the data and the documents, no code: data/ (records.csv, records.xpt as SAS
transport version 5 with 8-character names, the five source tables and schema/), docs/ (the generated
documentation and the design), dictionary.md, README.md and LICENSE. The generator, QC and reference code
stay in the build folder.

Usage:  python3 generator/release.py [--out ../ctcae-lab-validation] [--full]
        run after gen_records.py and qc.py; the output is deterministic
        --full writes the complete package (branch full): the dataset package plus reference/, generator/, release/,
        .github/, CONTRIBUTING.md, CHANGELOG.md, CITATION.cff, LICENSE-CODE, the full README and the .gitignore
"""
import csv, datetime as dt, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xpt import write_xpt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(os.path.dirname(ROOT), 'ctcae-lab-validation')
VERSION = '1.0.0'
FULL = '--full' in sys.argv
FULL_DIRS = ('reference', 'generator', 'release', '.github')
FULL_FILES = ('CONTRIBUTING.md', 'CHANGELOG.md', 'CITATION.cff', 'LICENSE-CODE')
GITIGNORE_FULL = '''.DS_Store
__pycache__/
*.pyc
# local working notes, not part of the package
AGENTS.md
# SAS and R session files
*.log
*.lst
.Rhistory
.RData
'''
RELEASE_DATE = dt.datetime(2026, 10, 15, 12, 0, 0)        # written into the transport file header; keeps the file byte-identical

# records.csv column -> transport variable (8 characters); the csv name is the variable label
XPT_NAMES = {
    'RECORD_ID': 'RECID', 'SUBJECT_ID': 'SUBJID', 'SCENARIO_ID': 'SCENID', 'MODULE': 'MODULE', 'RULE_IDS': 'RULEIDS',
    'LBTESTCD': 'LBTESTCD', 'LBTEST': 'LBTEST', 'LBSPEC': 'LBSPEC', 'LBDUR': 'LBDUR',
    'VAL': 'VAL', 'UNIT': 'UNIT', 'LLN': 'LLN', 'ULN': 'ULN',
    'VAL_SI': 'VALSI', 'UNIT_SI': 'UNITSI', 'LLN_SI': 'LLNSI', 'ULN_SI': 'ULNSI',
    'VAL_CONV': 'VALCONV', 'UNIT_CONV': 'UNITCONV', 'LLN_CONV': 'LLNCONV', 'ULN_CONV': 'ULNCONV',
    'DATE': 'DATE', 'STUDY_DAY': 'STUDYDAY', 'REF_DATE': 'REFDATE', 'BASELINE_FLAG': 'BLFL',
    'BASE_VAL': 'BASEVAL', 'BASE_UNIT': 'BASEUNIT', 'BASE_LLN': 'BASELLN', 'BASE_ULN': 'BASEULN',
    'BASE_VAL_SI': 'BVALSI', 'BASE_LLN_SI': 'BLLNSI', 'BASE_ULN_SI': 'BULNSI',
    'BASE_VAL_CONV': 'BVALCONV', 'BASE_LLN_CONV': 'BLLNCONV', 'BASE_ULN_CONV': 'BULNCONV',
    'STATUS': 'STATUS', 'GRADABLE': 'GRADABLE',
    'EXP_GRADE_LOW_V5': 'EXPGRL5', 'EXP_GRADE_HIGH_V5': 'EXPGRH5', 'EXP_TERM_LOW_V5': 'EXPTRL5', 'EXP_TERM_HIGH_V5': 'EXPTRH5',
    'EXP_BASE_GRADE_LOW_V5': 'EXPBGL5', 'EXP_BASE_GRADE_HIGH_V5': 'EXPBGH5', 'EXP_GRADE_V5': 'EXPGR5', 'EXP_TERM_V5': 'EXPTR5',
    'EXP_GRADE_LOW_V6': 'EXPGRL6', 'EXP_GRADE_HIGH_V6': 'EXPGRH6', 'EXP_TERM_LOW_V6': 'EXPTRL6', 'EXP_TERM_HIGH_V6': 'EXPTRH6',
    'EXP_BASE_GRADE_LOW_V6': 'EXPBGL6', 'EXP_BASE_GRADE_HIGH_V6': 'EXPBGH6', 'EXP_GRADE_V6': 'EXPGR6', 'EXP_TERM_V6': 'EXPTR6',
    'VERSION_DELTA': 'VERDELTA', 'CONVENTIONS': 'CONVS', 'CONVENTION_DEP': 'CONVDEP', 'DESCRIPTION': 'DESCR',
}

def read(name):
    with open(os.path.join(DATA, name + '.csv'), newline='', encoding='utf-8') as f: return list(csv.DictReader(f))

def schema(name):
    with open(os.path.join(DATA, 'schema', name + '.schema.json'), encoding='utf-8') as f: return json.load(f)

def md(s): return str(s).replace('|', '\\|').replace('\n', ' ')

def build_xpt(rows, fields, path):
    variables, cols = [], []
    for fd in fields:
        name = fd['name']
        if XPT_NAMES[name] in {v['name'] for v in variables}: raise ValueError(f'duplicate transport name for {name}')
        if fd['type'] in ('integer', 'number'):
            variables.append({'name': XPT_NAMES[name], 'label': name, 'type': 'num'})
        elif fd['type'] == 'date':
            variables.append({'name': XPT_NAMES[name], 'label': name, 'type': 'num', 'format': 'DATE9.'})
        else:
            variables.append({'name': XPT_NAMES[name], 'label': name, 'type': 'char', 'length': max(1, max(len(r[name]) for r in rows))})
        cols.append((name, fd['type']))
    def cell(r, name, t):
        v = r[name]
        if t in ('integer', 'number'): return None if v == '' else float(v)
        if t == 'date': return None if v == '' else dt.date.fromisoformat(v)
        return v
    data = ([cell(r, n, t) for n, t in cols] for r in rows)
    return write_xpt(path, variables, data, dsname='RECORDS', dslabel=f'CTCAE lab grading validation {VERSION}', created=RELEASE_DATE), variables

def build_dictionary(rows, fields, variables, path):
    an, cv = read('analytes'), read('conventions')
    out = [f'# Data dictionary: records.csv and records.xpt (release {VERSION})', '',
           'One row per laboratory record. The two files hold the same rows: data/records.csv with the column names of this',
           'dictionary, data/records.xpt (SAS transport version 5) with the 8-character variable names of the second column and',
           'the csv column name as variable label. DATE and REF_DATE are ISO 8601 text in the csv and SAS dates (format',
           'DATE9.) in the transport file. Blank cells in the csv are missing values in the transport file.', '',
           '## Reading the files', '',
           '- SAS: `proc import datafile="data/records.csv" out=records dbms=csv replace; guessingrows=max; run;` or',
           '  `libname xpt xport "data/records.xpt"; proc copy in=xpt out=work; run;`',
           '- R: `read.csv("data/records.csv", na.strings = "")` or `haven::read_xpt("data/records.xpt")`',
           '- Python: `pandas.read_csv("data/records.csv")` or `pandas.read_sas("data/records.xpt")`', '',
           'The other tables of data/ (criteria.csv, conventions.csv, expectations.csv, analytes.csv, units.csv) and their',
           'columns are described in docs/data_dictionary.md.', '',
           '## Reading the expected values', '',
           '- A blank expected grade means *not gradable*: the implementation must return a missing grade, never 0.',
           '- A term is given whenever the scale applies to the test, also at grade 0 and for a missing result; compare terms',
           '  case- and whitespace-insensitively. Terms are the official CTCAE terms of the version, as printed.',
           '- EXP_GRADE_V5 / EXP_GRADE_V6 and the matching terms are for single-scale designs: the worst of the LOW and HIGH',
           '  grades; the term is blank when the grade is 0 and both scales have a term.',
           '- The baseline is given twice: as the record flagged BASELINE_FLAG = Y and as the BASE_* columns of every record',
           '  of the subject, so an implementation may derive it or take it as input.',
           '- RULE_IDS name the CTCAE criteria a record exercises, as V<version>.<LBTESTCD>.<H|L>.<arm>.G<grade>; CONVENTIONS',
           '  name the readings of the CTCAE wording the expectation relies on (appendix B); CONVENTION_DEP = Y marks records',
           '  for which a documented alternative reading would change the expectation.', '',
           '## Columns', '', '| csv column | xpt variable | type | allowed values | description |', '|---|---|---|---|---|']
    vt = {v['label']: v for v in variables}
    for fd in fields:
        c = fd.get('constraints', {})
        allowed = []
        if 'enum' in c: allowed.append(', '.join(str(x) for x in c['enum']))
        if 'minimum' in c or 'maximum' in c: allowed.append(f'{c.get("minimum", "")} to {c.get("maximum", "")}')
        if c.get('required'): allowed.append('never blank')
        v = vt[fd['name']]
        t = {'integer': 'integer', 'number': 'number', 'date': 'date', 'string': f'text ({v.get("length", "")})'}[fd['type']]
        out.append(f'| {fd["name"]} | {v["name"]} | {t} | {md("; ".join(allowed))} | {md(fd.get("description", ""))} |')
    out += ['', '## Appendix A: modules', '', '| MODULE | Records | What the records prove |', '|---|---|---|']
    mod_desc = {'CORE': 'every laboratory threshold of both versions at its boundary, with a normal baseline; mandatory',
                'BASELINE': 'abnormal-baseline arms, no baseline, baseline selection (last pre-treatment record, record on REF_DATE, baseline without a range)',
                'MISSING': 'missing result, missing limit, missing range', 'NOTDONE': 'NOT DONE records, one with a stray value before REF_DATE',
                'UNITS': 'results in conventional units, alias spellings, unknown and blank units',
                'CATEGORY': 'the same test code under another specimen (urine) has no criterion'}
    for m in ('CORE', 'BASELINE', 'MISSING', 'NOTDONE', 'UNITS', 'CATEGORY'):
        out.append(f'| {m} | {sum(r["MODULE"] == m for r in rows)} | {mod_desc[m]} |')
    out += ['', '## Appendix B: convention codes', '',
            'Each code names one reading of the CTCAE wording. The expectations follow the default reading; where an',
            'alternative reading is defensible, CONVENTION_DEP = Y and the alternative is stated.', '',
            '| Code | Title | Default reading | Alternative reading | Dependent |', '|---|---|---|---|---|']
    for r in cv:
        out.append(f'| {r["CONVENTION"]} | {md(r["TITLE"])} | {md(r["DEFAULT_CHOICE"])} | {md(r["ALTERNATIVE_CHOICE"])} | {r["CONVENTION_DEP"]} |')
    out += ['', '## Appendix C: tests', '', 'CDISC SDTM test codes (codelist C65047), specimens (C78734) and units (C71620); CD4 is sponsor-defined.', '',
            '| LBTESTCD | LBTEST | LBSPEC | UNIT_SI | UNIT_CONV | Records | v5 HIGH term | v5 LOW term | v6 HIGH term | v6 LOW term |', '|---|---|---|---|---|---|---|---|---|---|']
    for a in an:
        n = sum(r['LBTESTCD'] == a['LBTESTCD'] for r in rows)
        out.append(f'| {a["LBTESTCD"]} | {a["LBTEST"]} | {a["LBSPEC"]} | {a["UNIT_SI"]} | {a["UNIT_CONV"]} | {n} | {a["TERM_V5_HIGH"]} | {a["TERM_V5_LOW"]} | {a["TERM_V6_HIGH"]} | {a["TERM_V6_LOW"]} |')
    out += ['', 'Sources: CTCAE v5.0 (NCI, published 27-Nov-2017) and CTCAE v6.0 (NCI, published 22-Jul-2025; PDF dated 20-Jan-2026).']
    with open(path, 'w', encoding='utf-8') as f: f.write('\n'.join(out) + '\n')

def main():
    rows = read('records')
    fields = schema('records')['fields']
    os.makedirs(OUT, exist_ok=True)
    for r in rows:
        for k, v in r.items():
            if not v.isascii(): raise ValueError(f'non-ASCII value in {k}: {v!r}')
    out_data, out_docs = os.path.join(OUT, 'data'), os.path.join(OUT, 'docs')
    os.makedirs(os.path.join(out_data, 'schema'), exist_ok=True); os.makedirs(out_docs, exist_ok=True)
    tables = sorted(f for f in os.listdir(DATA) if f.endswith('.csv'))
    for f in tables: shutil.copyfile(os.path.join(DATA, f), os.path.join(out_data, f))
    schemas = sorted(f for f in os.listdir(os.path.join(DATA, 'schema')) if f.endswith('.schema.json'))
    for f in schemas: shutil.copyfile(os.path.join(DATA, 'schema', f), os.path.join(out_data, 'schema', f))
    docs = sorted(f for f in os.listdir(os.path.join(ROOT, 'docs')) if f.endswith('.md'))
    for f in docs: shutil.copyfile(os.path.join(ROOT, 'docs', f), os.path.join(out_docs, f))
    size, variables = build_xpt(rows, fields, os.path.join(out_data, 'records.xpt'))
    build_dictionary(rows, fields, variables, os.path.join(OUT, 'dictionary.md'))
    shutil.copyfile(os.path.join(ROOT, 'release', 'README-full.md' if FULL else 'README.md'), os.path.join(OUT, 'README.md'))
    shutil.copyfile(os.path.join(ROOT, 'release', 'LICENSE'), os.path.join(OUT, 'LICENSE'))
    extra = ''
    if FULL:
        for d in FULL_DIRS:
            dst = os.path.join(OUT, d)
            if os.path.isdir(dst): shutil.rmtree(dst)
            shutil.copytree(os.path.join(ROOT, d), dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
        for name in FULL_FILES:
            shutil.copyfile(os.path.join(ROOT, name), os.path.join(OUT, name))
        with open(os.path.join(OUT, '.gitignore'), 'w', encoding='utf-8') as f: f.write(GITIGNORE_FULL)
        extra = f'; full package: {", ".join(FULL_DIRS)}, {", ".join(FULL_FILES)}, .gitignore'
    print(f'release {VERSION} written to {OUT}: data/ ({len(tables)} tables incl. records.csv with {len(rows)} rows, '
          f'records.xpt {size} bytes with {len(variables)} variables, {len(schemas)} schemas), docs/ ({len(docs)} files), dictionary.md, README.md, LICENSE{extra}')

if __name__ == '__main__':
    main()
