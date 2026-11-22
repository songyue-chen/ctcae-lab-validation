# ctcae-lab-validation

A test dataset for CTCAE laboratory grading code, versions 5.0 and 6.0. One dataset, 1,057 laboratory records, each
with the grade and term a correct implementation must produce under both versions. Run your macro or function on
it, merge the output back on `RECORD_ID`, compare with the expected columns. Where the two differ, the record says
which CTCAE criterion and which reading of the wording is at stake.

This branch (`full`) is the complete package: the dataset, the SAS and R reference loaders and comparators, the
generator that derives the expected values, and the contributor documents. Branch `main` holds the dataset alone.

| File | Content |
|---|---|
| `data/records.csv` | the dataset, one row per laboratory record, 57 columns |
| `data/records.xpt` | the same rows as a SAS transport file (version 5, 8-character variable names) |
| `dictionary.md` | every column of the dataset, the convention codes, the modules and the tests covered |
| `data/criteria.csv` | the CTCAE laboratory criteria of both versions, one row per clause, with the verbatim wording and the comparator and threshold read from it |
| `data/conventions.csv` | every reading of the wording that the expectations rely on, with its default and alternative |
| `data/expectations.csv` | the expected values in long form, including the alternative profiles for the records they change |
| `data/analytes.csv`, `data/units.csv`, `data/schema/` | test master, unit conversion factors, column definitions of every table |
| `docs/` | data dictionary of every table, the conventions explained, record and rule coverage, the design |
| `reference/sas/`, `reference/r/` | loaders, comparators, self-checks and mapping templates for SAS and R |
| `reference/results_template.csv` | the minimum output to produce when comparing outside SAS or R |
| `generator/` | regenerates `records.csv`, `expectations.csv` and the generated documents from the tables; `qc.py` is the quality gate |
| `CONTRIBUTING.md`, `CHANGELOG.md`, `CITATION.cff` | how expectations change, release history, how to cite |
| `LICENSE`, `LICENSE-CODE` | CC BY 4.0 for data and documentation, MIT for code |

## What is in a record

Each record is one laboratory result of a synthetic subject: test code, specimen and unit (CDISC controlled
terminology), the value, the normal range, the collection date, the reference date (first dose), the subject's
baseline, and the expected outcome:

| Columns | Meaning |
|---|---|
| `VAL`, `UNIT`, `LLN`, `ULN` | the result as a pipeline receives it; the UNITS module sends conventional units, alias spellings, unknown and blank units |
| `VAL_SI`, `VAL_CONV` and their ranges | the same in the SI and the conventional unit, for information |
| `BASELINE_FLAG`, `BASE_VAL`, `BASE_LLN`, `BASE_ULN` | the baseline, both as a flagged record and as columns on every record of the subject |
| `EXP_GRADE_LOW_V5`, `EXP_GRADE_HIGH_V5`, `EXP_TERM_LOW_V5`, `EXP_TERM_HIGH_V5` | expected v5 grade and CTCAE term on the LOW and the HIGH scale; same with `_V6` |
| `EXP_GRADE_V5`, `EXP_TERM_V5` | the single worst grade and its term, for single-scale designs; same with `_V6` |
| `EXP_BASE_GRADE_*` | the expected grades of the subject's baseline record |
| `MODULE` | CORE (mandatory), BASELINE, MISSING, NOTDONE, UNITS, CATEGORY |
| `RULE_IDS`, `CONVENTIONS`, `CONVENTION_DEP`, `DESCRIPTION` | which criteria the record exercises, which readings of the wording it relies on, and what it proves |

The records sit at the boundaries: for every laboratory threshold of both versions there is a record exactly at
the threshold, one reporting step above and one below, with the subject's own normal range and baseline. Three
rules for reading the expected columns:

1. A blank expected grade means *not gradable*. The implementation must return a missing grade, never 0.
2. A term is expected whenever the scale applies, also at grade 0 and when the result is missing. Compare terms
   case- and whitespace-insensitively.
3. `CONVENTION_DEP = Y` marks the records whose expectation depends on a reading of the CTCAE wording that has a
   documented alternative (dictionary, appendix B). If your rules follow the other reading, exclude these records
   and say so in your validation report.

## Reference comparators

The reference code does the merge-and-compare of the next section for you and reports by module, by record and by
criteria rule. `reference/sas/selfcheck.sas` and `reference/r/selfcheck.R` prove loader and comparator in your session
before any grading code is plugged in (look for SELFCHECK PASSED); the mapping templates show where to recode your
test codes, categories, variable names and term names.

### SAS (SAS 9.4 or later)

```sas
%include "/path/to/ctcae-lab-validation/reference/sas/load_records.sas";
%include "/path/to/ctcae-lab-validation/reference/sas/compare_results.sas";
%ctcval_load(dir=/path/to/ctcae-lab-validation, naming=ADAM);   /* WORK.CTCVAL_RECORDS with ADaM names */

/* run your grading macro on CTCVAL_RECORDS for CTCAE v5 -> MY_RESULTS (keeps RECORD_ID), then */
%ctcval_compare(results=my_results, version=5, profile=DEFAULT,
                gradelow=ATOXGRL, gradehigh=ATOXGRH, termlow=ATOXDSCL, termhigh=ATOXDSCH);
```

### R (base R, no packages)

```r
source("reference/r/load_records.R"); source("reference/r/compare_results.R")
d <- ctcval_load("path/to/ctcae-lab-validation", naming = "adam")
# run your grading function on d$records for CTCAE v5 -> my_results (keeps RECORD_ID), then
cmp <- ctcval_compare(my_results, version = 5, profile = "DEFAULT",
                      cols = list(grade_low = "ATOXGRL", grade_high = "ATOXGRH", term_low = "ATOXDSCL", term_high = "ATOXDSCH"),
                      data = d)
```

### Anything else

Produce a CSV with the columns of `reference/results_template.csv` (`RECORD_ID` plus `GRADE_LOW`, `GRADE_HIGH`,
`TERM_LOW`, `TERM_HIGH` for bidirectional designs, or `GRADE` and `TERM` for a single worst grade) and compare it with
`data/expectations.csv` for the version and profile you validate against.

Both comparators report the status by `MODULE`, a mismatch listing (expected vs obtained with `RULE_IDS`, conventions
and the record description), the coverage and status by criteria `RULE_ID`, and a PASS/FAIL note. `convdep=N`
(`convdep = FALSE` in R) drops the records whose expectation depends on a documented alternative reading;
`profile=` compares against one of the alternative profiles instead.

## Test-driven development of a grading macro or function

The dataset is written to be the test suite you develop against, not only a final check.

**Step 1: write the comparison before the grader.** Read `records.csv`, run your (still empty) grader, merge the
output back on `RECORD_ID`, compare grade and term per scale and version, count disagreements by `MODULE` and by
`LBTESTCD`. The run must report every gradable record as failing. That is the test harness working.

```sas
proc import datafile="data/records.csv" out=records dbms=csv replace; guessingrows=max; run;
/* ... your grader turns RECORDS into GRADED with RECORD_ID, ATOXGRL, ATOXGRH, ATOXDSCL, ATOXDSCH ... */
proc sort data=graded; by RECORD_ID; run;
data compare;
  merge records(in=a keep=RECORD_ID MODULE LBTESTCD RULE_IDS CONVENTIONS CONVENTION_DEP DESCRIPTION
                        EXP_GRADE_LOW_V5 EXP_GRADE_HIGH_V5 EXP_TERM_LOW_V5 EXP_TERM_HIGH_V5)
        graded(keep=RECORD_ID ATOXGRL ATOXGRH ATOXDSCL ATOXDSCH);
  by RECORD_ID;
  if a;
  ok_low  = (missing(EXP_GRADE_LOW_V5) and missing(ATOXGRL)) or (EXP_GRADE_LOW_V5 = ATOXGRL and not missing(ATOXGRL));
  ok_high = (missing(EXP_GRADE_HIGH_V5) and missing(ATOXGRH)) or (EXP_GRADE_HIGH_V5 = ATOXGRH and not missing(ATOXGRH));
  ok_term = compress(upcase(EXP_TERM_LOW_V5)) = compress(upcase(ATOXDSCL)) and compress(upcase(EXP_TERM_HIGH_V5)) = compress(upcase(ATOXDSCH));
  ok = ok_low and ok_high and ok_term;
run;
proc freq data=compare; tables MODULE*ok LBTESTCD*ok / nocol nopercent; run;
proc print data=compare(where=(not ok)); var RECORD_ID LBTESTCD EXP_GRADE_LOW_V5 ATOXGRL EXP_GRADE_HIGH_V5 ATOXGRH RULE_IDS CONVENTIONS DESCRIPTION; run;
```

```r
rec <- read.csv("data/records.csv", na.strings = "")
# ... your grader turns rec into graded with RECORD_ID, grade_low, grade_high, term_low, term_high ...
cmp <- merge(rec, graded, by = "RECORD_ID", all.x = TRUE)
same <- function(e, g) (is.na(e) & is.na(g)) | (!is.na(e) & !is.na(g) & e == g)
norm <- function(x) gsub("\\s", "", toupper(ifelse(is.na(x), "", x)))
cmp$ok <- same(cmp$EXP_GRADE_LOW_V5, cmp$grade_low) & same(cmp$EXP_GRADE_HIGH_V5, cmp$grade_high) &
          norm(cmp$EXP_TERM_LOW_V5) == norm(cmp$term_low) & norm(cmp$EXP_TERM_HIGH_V5) == norm(cmp$term_high)
table(cmp$MODULE, cmp$ok)
cmp[!cmp$ok, c("RECORD_ID", "LBTESTCD", "EXP_GRADE_LOW_V5", "grade_low", "EXP_GRADE_HIGH_V5", "grade_high", "RULE_IDS", "CONVENTIONS", "DESCRIPTION")]
```

**Step 2: make CORE pass, one test at a time.** Filter on `MODULE = "CORE"` and one `LBTESTCD`. Implement the
criterion, rerun, read the failing records: `DESCRIPTION` says where the value sits ("exactly 3 x ULN", "1 step
above 1.71 mmol/L"), `RULE_IDS` says which grade cell decides it, and the direction of the error says whether a
bound is inclusive or exclusive. Move to the next test when the subject passes. CORE covers every laboratory
threshold of both versions with a normal baseline and SI units.

**Step 3: add the behaviours, module by module.** BASELINE (abnormal-baseline arms, no baseline, which record is the
baseline), MISSING (missing result, limit or range), NOTDONE, UNITS (conversion and unit normalisation),
CATEGORY (the same test code under another specimen has no criterion). Each module is a decision your SOP has
taken; the records make the decision testable.

**Step 4: settle the conventions.** When a failing record carries `CONVENTION_DEP = Y`, look up its `CONVENTIONS`
codes in the dictionary. Either your rules follow the default reading and the grader is wrong, or they follow the
alternative and the record is excluded with a written reason. Nothing else is acceptable: a convention is never an
excuse for a record-by-record exception.

**Step 5: run both versions, keep the evidence.** Run the comparison for v5 and v6, keep the program, the output
and the dataset version with your validation documents, and rerun it on every change of the grader or its
dictionary. A change that makes a previously passing record fail is a regression until the quoted CTCAE wording
says otherwise.

## How the expected values were produced

The expected values are generated, not typed. The CTCAE grade cells of both versions were transcribed clause by
clause into `data/criteria.csv`, which quotes the wording of each clause, the comparator read from it, the
threshold, the baseline arm and the clinical qualifier. A rule engine applies these rows to every record: clauses are chosen
by baseline arm and qualifier (the patient is assumed asymptomatic and without intervention; amylase and lipase
take the worst case), grades are read from 4 down, the highest satisfied clause wins, and the grade is missing when
only a clause that needs a missing limit remains. Every reading the wording does not settle is a named convention
with its default and its alternative (`data/conventions.csv`, explained in `docs/conventions.md`); where both
readings are defensible, `data/expectations.csv` publishes the alternative profile for the records it changes.
An independent re-simulation checks every expected grade on every regeneration; `docs/coverage.md` lists which
records exercise which rules. Disputes: open an issue quoting the CTCAE wording and naming the `RULE_IDS` of the
record.

## Sources, versions, licence

CTCAE v5.0 (NCI, published 27-Nov-2017) and CTCAE v6.0 (NCI, published 22-Jul-2025; PDF dated 20-Jan-2026).
CTCAE is a work of the US National Cancer Institute in the public domain. Test codes, names, specimens and units
are CDISC SDTM controlled terminology (NCI EVS codelists C65047, C67154, C78734, C71620).
Default normal ranges (`analytes.csv` LLN_SI, ULN_SI) are the adult reference ranges of the ABIM Laboratory
Test Reference Ranges (American Board of Internal Medicine, January 2026), converted to SI with the factors of
`units.csv` and rounded to the reporting precision; the female range where ABIM gives two, 0 as LLN where ABIM gives
an upper limit only. INR 0.8 - 1.1 and the 24-hour urine creatinine and potassium ranges are from the MedlinePlus
Medical Encyclopedia (US National Library of Medicine); GFR and eGFR >= 90 mL/min/1.73 m2 is the KDIGO normal
category G1. Every record carries its own range, so an adopter's ranges can replace them. Dataset release 1.0.0.
Licence CC BY 4.0 (`LICENSE`).

## Regenerating the data

Python 3.11 or later, no packages:

```bash
python3 generator/gen_records.py && python3 generator/qc.py && python3 generator/build_docs.py
```

`gen_records.py` rewrites `data/records.csv` and `data/expectations.csv` from the four tables (deterministic, no
CTCAE threshold is coded in it), `qc.py` validates every table and re-simulates every expected grade, `build_docs.py`
rewrites the generated documents. CI runs the three scripts, `Rscript reference/r/selfcheck.R`, and checks that the
committed files equal the regenerated ones and that the committed tree equals `generator/release.py --full`.

## Licence and citation

Data and documentation: CC BY 4.0 (`LICENSE`). Code: MIT (`LICENSE-CODE`). Cite as described in `CITATION.cff`.
Disputes and corrections: open an issue with the "Dispute an expectation" template, quoting the CTCAE wording.
