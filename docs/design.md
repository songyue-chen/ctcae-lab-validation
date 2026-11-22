# CTCAE Lab Grading Validation Set — open-source design

**Status:** approved design, 2026-10-15, implemented in release 1.0.0 · **Decisions taken:** v5.0 + v6.0 first (v4.03 on the roadmap) · convention profiles with alternative expected values · first release = data + criteria table + analyte mapping + docs + SAS/R comparators (no MedDRA codes, no grading implementation) · **CDISC controlled terminology only**: the test key is `LBTESTCD` + `LBSPEC` (SDTM submission values, no sponsor codes); LOINC kept as an optional cross-reference column.

## 1. Purpose and scope

A vendor-neutral dataset that lets any organisation verify its CTCAE laboratory grading implementation (SAS macro, R function, SQL, Python) by a plain merge-and-compare: feed the records in, merge the output back by `RECORD_ID`, compare against the expected columns, report by module and by CTCAE criterion.

Out of scope for release 1.0: v4.03 criteria, non-laboratory CTCAE terms, vital-sign or ECG grading, MedDRA-coded output beyond the codes CTCAE itself publishes.

## 2. Design choices

| Area | Choice |
|---|---|
| Column names | Neutral names in `records.csv`; ADaM and SDTM aliases applied by the loaders |
| Test codes | CDISC `LBTESTCD` + `LBSPEC` submission values on every record (section 4a); `analytes.csv` lists the CDISC name, accepted alias codes and LOINC; adopters add one column with their own code |
| Units | Every record carries the value as received, in SI, and in conventional units; unit-guard records are a separate module |
| Conventions | Default profile wide on the record + `expectations.csv` (long) with alternative profiles; `CONVENTION_DEP` flag to exclude all convention-dependent records at once |
| Scope of a test | `MODULE` column: CORE (grading logic) is mandatory, BASELINE / MISSING / NOTDONE / UNITS / CATEGORY (data-management behaviour) optional |
| Grade layout | Bidirectional ADaMIG grades (LOW and HIGH) and a single worst grade + term per version for single-scale designs |
| Coverage | Term text + `RULE_IDS` for criterion-level coverage (MedDRA codes deliberately not shipped in 1.0) |
| Source of the expectations | `criteria.csv`: the machine-readable transcription (wording, comparator, threshold) that generates the expectations and can be reviewed line by line |
| Implementation | Dataset package is implementation-free: no grading implementation is shipped (decision 2026-10-15) |

## 3. Repository layout

```
ctcae-lab-validation/
  README.md                      what it is, 5-minute quick start (SAS and R)
  dictionary.md                  columns of records.csv and records.xpt, modules, conventions, tests
  LICENSE  (CC BY 4.0, data and documentation)      LICENSE-CODE (MIT, code)
  CHANGELOG.md  CITATION.cff  CONTRIBUTING.md
  .github/ISSUE_TEMPLATE/dispute-expectation.md   .github/workflows/ci.yml
  data/
    records.csv                  one row per lab record (section 4)
    records.xpt                  the same rows as a SAS transport file (version 5)
    expectations.csv             long: RECORD_ID x VERSION x PROFILE x DIRECTION (section 5)
    analytes.csv                 LBTESTCD, LBTEST, LBSPEC, NCI_CODE, ALIAS_LBTESTCD, LOINC, UNIT_SI, UNIT_CONV, FACTOR
    criteria.csv                 machine-readable CTCAE lab criteria, both versions (section 6)
    conventions.csv              code, text, default choice, alternative profile
    units.csv                    conversion factors (LBTESTCD, FROM_UNIT, TO_UNIT, FACTOR)
    schema/*.schema.json         column types, allowed values of every table
  docs/
    data_dictionary.md  conventions.md  coverage.md  (generated)   design.md (this file)   review-guide.md
  reference/
    sas/  load_records.sas  compare_results.sas  selfcheck.sas  mapping_template.sas
    r/    load_records.R    compare_results.R    selfcheck.R    mapping_template.R
    results_template.csv
  generator/
    gen_records.py  qc.py  build_docs.py  release.py  tools/   (CI runs the first three on every push)
```

Two branches of one repository, both assembled from the maintainers' build folder by `generator/release.py`:
`main` holds the dataset package for users (data/, docs/, dictionary.md, README.md, LICENSE); `full` adds
reference/, generator/, release/, .github/, CONTRIBUTING.md, CHANGELOG.md, CITATION.cff and LICENSE-CODE
(`release.py --full`). The dataset files are identical on both branches.

## 4. `records.csv`

| Column | Content |
|---|---|
| RECORD_ID | stable integer key; adopters carry it through their pipeline |
| SUBJECT_ID, SCENARIO_ID | synthetic subject (`ALT-H-Y`) and record scenario (`ALT-H-Y-06`) |
| MODULE | CORE, BASELINE, MISSING, NOTDONE, UNITS, CATEGORY |
| RULE_IDS | CTCAE criteria the record exercises, e.g. `V5.ALT.H.ABN.G1 V6.ALT.H.ABN.G2` |
| LBTESTCD, LBTEST, LBSPEC, LBDUR | CDISC submission values (codelists LBTESTCD C65047, LBTEST C67154, SPECTYPE C78734); LBDUR `PT24H` marks a 24-hour collection; no sponsor categories |
| VAL, UNIT, LLN, ULN | the record as an adopter's pipeline receives it (foreign units in the UNITS module) |
| VAL_SI, UNIT_SI, LLN_SI, ULN_SI | standardised SI view (blank when not convertible) |
| VAL_CONV, UNIT_CONV, LLN_CONV, ULN_CONV | conventional-unit view (mg/dL, /µL, g/dL …) |
| DATE, STUDY_DAY, REF_DATE | ISO dates; REF_DATE = first dose |
| BASELINE_FLAG, BASE_VAL_SI, BASE_LLN_SI, BASE_ULN_SI, BASE_VAL_CONV … | baseline supplied so CORE needs no derivation |
| STATUS | NOT DONE marker |
| GRADABLE | Y/N: whether a grade is expected at all (N = missing result/limit, unknown unit, no criterion, NOT DONE) |
| EXP_GRADE_LOW_V5, EXP_GRADE_HIGH_V5, EXP_TERM_LOW_V5, EXP_TERM_HIGH_V5, EXP_BASE_GRADE_LOW_V5, EXP_BASE_GRADE_HIGH_V5, EXP_GRADE_V5, EXP_TERM_V5 | default-profile expectations, v5; same set with `_V6` |
| VERSION_DELTA | Y when v5 and v6 expectations differ |
| CONVENTIONS, CONVENTION_DEP | convention codes applied; Y when any expectation depends on a convention |
| DESCRIPTION | what the record proves |

Loaders rename to ADaM (USUBJID, PARAMCD, AVAL, AVALU, ANRLO, ANRHI, ADT, ADY, TRTSDT, ABLFL, BASE, ATOXGRL …) or SDTM (LBTESTCD, LBSTRESN, LBSTRESU, LBSTNRLO, LBSTNRHI, LBDT) on request; the mapping template is where an adopter enters their own analyte codes and variable names.

## 4a. CDISC test codes (verified against the current NCI EVS SDTM terminology release, codelist C65047)

| LBTESTCD | LBTEST | LBSPEC | Note |
|---|---|---|---|
| ALB, ALP, ALT, AMYLASE, AST, BICARB, BILI, CHOL, CREAT, GGT, GLUC, HDL, K, LDH, LDL, MG, PHOS, SODIUM, TRIG, APTT, INR, FIBRINO, EOS, HGB, LYM, NEUT, PLAT, WBC | per codelist | SERUM / PLASMA / BLOOD | |
| CACR | Calcium Corrected | SERUM | alias CACRALB (Calcium Corrected for Albumin) graded identically |
| CAION | Calcium, Ionized | BLOOD | |
| CK | Creatine Kinase | SERUM | CPK is a synonym, not a submission value |
| URATE | Urate | SERUM | |
| HAPTOG | Haptoglobin | SERUM | |
| LIPASET | Lipase | SERUM | alias LIPASEP (pancreatic lipase) |
| HGBMHGB | Methemoglobin/Total Hemoglobin | BLOOD | the % fraction CTCAE grades; alias HGBMET (concentration) |
| GFRBSCRT | GFR from Creatinine Adjusted for BSA | SERUM | the usual eGFR in mL/min/1.73 m²; aliases GFRBSCYC (cystatin C), GFRBSA |
| GFR | Glomerular Filtration Rate | SERUM | measured GFR |
| CREATCLR | Creatinine Clearance | URINE | 24-h collection; alias CRTCLRE (estimated, e.g. Cockcroft-Gault) |
| PROTEXR | Protein Excretion Rate | URINE | LBDUR = PT24H; mg/24 h |
| TROPONI, TROPONT | Troponin I / Troponin T | SERUM | alias TROPONI3 (cardiac troponin I); high sensitivity is a method (LBMETHOD), not a separate test |
| VTD2D3IT | 25-Hydroxyvit D2 + 25-Hydroxyvit D3 | SERUM | alias V25HD3 |
| CD4 | | BLOOD | **not in LBTESTCD**: CDISC models lymphocyte subsets in the Cell Phenotyping domain; the record keeps a documented sponsor-defined code (`CD4`) flagged `CDISC_CT = N` until a CP-domain code is adopted |
| UREA | Urea | SERUM | unmatched-code scenario |

Category scenarios use `LBSPEC` (URINE vs SERUM/BLOOD) instead of a sponsor `LBCAT`, so the urine creatinine, glucose, potassium and WBC records need no category vocabulary of their own.

## 4b. Normal ranges

Default normal ranges (`analytes.csv` LLN_SI, ULN_SI) are the adult reference ranges of the ABIM Laboratory
Test Reference Ranges (American Board of Internal Medicine, January 2026), converted to SI with the factors of
`units.csv` and rounded to the reporting precision; the female range where ABIM gives two, 0 as LLN where ABIM gives
an upper limit only. INR 0.8 - 1.1 and the 24-hour urine creatinine and potassium ranges are from the MedlinePlus
Medical Encyclopedia (US National Library of Medicine); GFR and eGFR >= 90 mL/min/1.73 m2 is the KDIGO normal
category G1. Every record carries its own range, so an adopter's ranges can replace them.

## 5. Convention profiles (`expectations.csv`)

Long table: RECORD_ID, VERSION, PROFILE, DIRECTION, GRADE, TERM, BASE_GRADE. `DEFAULT` repeats the wide columns; alternatives are published only for records they change:

| Profile | Alternative choice |
|---|---|
| BESTCASE_ENZYMES | amylase/lipase symptom-qualified ranges at the lower (asymptomatic) grade |
| HYPERGLY_NUMERIC_V5 | v5 hyperglycemia graded with the v4.03 numeric thresholds (8.9 / 13.9 / 27.8 mmol/L) |
| PRESENT_NOT_LAB | v6 lymphopenia and neutrophilia ("Present") not derivable from labs → no grade |
| UNGRADABLE_ZERO | missing limit or unknown unit → grade 0 instead of missing |
| BASELINE_STRICT | ">baseline" clauses fail (not waived) when no baseline exists |

`conventions.csv` documents each code, the default choice, the CTCAE wording behind it and which profile holds the alternative. An adopter either picks a profile or excludes `CONVENTION_DEP = Y`.

## 6. `criteria.csv`

One row per CTCAE version × test × direction × baseline arm × grade: VERSION, LBTESTCD, LBSPEC, CTCAE_TERM, DIRECTION, BASELINE_ARM (ANY/NORMAL/ABNORMAL/BELOW_LLN), GRADE, WORDING (verbatim from the PDF), COMPARATOR (`>`, `>=`, `<`, `<=`), THRESHOLD (`3*ULN`, `1.5*BASE`, `5.5`, `-25 %CHG`), THRESHOLD_CONV, CONVENTION, SOURCE_PAGE. The generator derives every expectation from this table, so a disputed expectation is traced to one row and one quoted sentence. It is also the artefact most likely to be reused on its own (rule engines, R packages).

## 7. Reference comparators

- SAS `compare_results.sas`: `%include` the loader, run the adopter's macro, then `%ctcval_compare(results=<their output>, version=5, profile=DEFAULT, gradelow=ATOXGRL, gradehigh=ATOXGRH, termlow=ATOXDSCL, termhigh=ATOXDSCH)` (or `grade=, term=` for single-scale designs); output = status by MODULE, mismatch listing, coverage by RULE_ID, PASS/FAIL note. `selfcheck.sas` proves loader and comparator in a SAS session without any grading macro.
- R `ctcval_compare(results, version, profile, cols = list(...))` with the same outputs as a list and a printed summary; `selfcheck.R` is the R self-check, run by CI.
- `results_template.csv`: the minimum an adopter must produce (RECORD_ID + grade/term columns) if they prefer to compare outside SAS/R.
- Term comparison is case- and whitespace-insensitive on the CTCAE term text.

## 8. Quality gates (CI on every change)

Generator self-checks (monotone grades, floating-point safety, data-line hygiene), criteria-table audit (every comparator vs wording), unit-metadata cross-check, schema validation, independent re-simulation of all expectations from `criteria.csv`, record and rule coverage report regenerated into `docs/coverage.md`.

## 9. Governance and legal

CC BY 4.0 for data, MIT for code. CTCAE is a US Government (NCI) work in the public domain; the dataset cites the exact CTCAE documents and build dates. MedDRA codes are not shipped in 1.0 (decision 2026-10-15); a later release may add CTCAE-published codes after a licensing check. Semantic versioning of the dataset (1.0.0), CHANGELOG, CITATION.cff with a Zenodo DOI, named maintainers, dispute template requiring the CTCAE wording to be quoted, and a policy that expectations change only through a documented criteria-table change.

## 10. Build plan

1. Schema, `analytes.csv` (CDISC codes per section 4a), `criteria.csv` (transcribed clause by clause from the CTCAE PDFs), `conventions.csv`, `units.csv`.
2. Generator: neutral schema, modules, dual units, profiles, `expectations.csv`; QC with an independent re-simulation of every expectation.
3. SAS and R loaders and comparators, results template; self-checks in both languages, rehearsal with an independent R grading stub.
4. README, data dictionary, conventions and coverage docs, licenses, CI, contribution guide, issue template.
5. End-to-end rehearsal as an outside adopter, fixes, tag 1.0.0.

Roadmap after 1.0: v4.03 transcription (1.1), additional profiles on request, non-lab terms out of scope unless a maintainer volunteers.

## 11. Resolved and open points

- Resolved 2026-10-15: no MedDRA code column in 1.0; no grading implementation is published.
- Open: final project name (working title `ctcae-lab-validation`); named maintainers and where disputes are adjudicated.
