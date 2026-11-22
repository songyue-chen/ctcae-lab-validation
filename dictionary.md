# Data dictionary: records.csv and records.xpt (release 1.0.0)

One row per laboratory record. The two files hold the same rows: data/records.csv with the column names of this
dictionary, data/records.xpt (SAS transport version 5) with the 8-character variable names of the second column and
the csv column name as variable label. DATE and REF_DATE are ISO 8601 text in the csv and SAS dates (format
DATE9.) in the transport file. Blank cells in the csv are missing values in the transport file.

## Reading the files

- SAS: `proc import datafile="data/records.csv" out=records dbms=csv replace; guessingrows=max; run;` or
  `libname xpt xport "data/records.xpt"; proc copy in=xpt out=work; run;`
- R: `read.csv("data/records.csv", na.strings = "")` or `haven::read_xpt("data/records.xpt")`
- Python: `pandas.read_csv("data/records.csv")` or `pandas.read_sas("data/records.xpt")`

The other tables of data/ (criteria.csv, conventions.csv, expectations.csv, analytes.csv, units.csv) and their
columns are described in docs/data_dictionary.md.

## Reading the expected values

- A blank expected grade means *not gradable*: the implementation must return a missing grade, never 0.
- A term is given whenever the scale applies to the test, also at grade 0 and for a missing result; compare terms
  case- and whitespace-insensitively. Terms are the official CTCAE terms of the version, as printed.
- EXP_GRADE_V5 / EXP_GRADE_V6 and the matching terms are for single-scale designs: the worst of the LOW and HIGH
  grades; the term is blank when the grade is 0 and both scales have a term.
- The baseline is given twice: as the record flagged BASELINE_FLAG = Y and as the BASE_* columns of every record
  of the subject, so an implementation may derive it or take it as input.
- RULE_IDS name the CTCAE criteria a record exercises, as V<version>.<LBTESTCD>.<H|L>.<arm>.G<grade>; CONVENTIONS
  name the readings of the CTCAE wording the expectation relies on (appendix B); CONVENTION_DEP = Y marks records
  for which a documented alternative reading would change the expectation.

## Columns

| csv column | xpt variable | type | allowed values | description |
|---|---|---|---|---|
| RECORD_ID | RECID | integer | 1 to ; never blank | Stable integer key; adopters carry it through their pipeline and merge their output back on it |
| SUBJECT_ID | SUBJID | text (15) | never blank | Synthetic subject, e.g. ALT-H-Y (<LBTESTCD>-<H\|L>-<arm>); one subject per test x direction x baseline arm |
| SCENARIO_ID | SCENID | text (18) | never blank | Record scenario, e.g. ALT-H-Y-06 (<SUBJECT_ID>-BL for the baseline record) |
| MODULE | MODULE | text (8) | CORE, BASELINE, MISSING, NOTDONE, UNITS, CATEGORY; never blank | CORE = boundary records every implementation must pass; BASELINE = baseline selection and abnormal-baseline arms; MISSING = missing result or limit; NOTDONE = NOT DONE records; UNITS = foreign, alias or blank units; CATEGORY = same test code under another specimen |
| RULE_IDS | RULEIDS | text (127) |  | Space-separated criteria.csv RULE_IDs the record exercises in both versions: the rules that give a grade of 1 or more, the lowest applicable rule whose bound the value does not cross (grade 0), or the rules that are unevaluable (grade missing) |
| LBTESTCD | LBTESTCD | text (8) | never blank | CDISC laboratory test code (analytes.csv; CD4 is sponsor-defined) |
| LBTEST | LBTEST | text (37) | never blank | CDISC test name |
| LBSPEC | LBSPEC | text (6) | SERUM, PLASMA, BLOOD, URINE; never blank | Specimen type (CDISC SPECTYPE submission value) |
| LBDUR | LBDUR | text (5) | PT24H | Collection duration (ISO 8601): PT24H marks a 24-hour collection |
| VAL | VAL | number |  | Result as an adopter's pipeline receives it, in UNIT (blank = missing result) |
| UNIT | UNIT | text (14) |  | Unit of VAL, LLN and ULN as received (foreign spellings and blanks in the UNITS module) |
| LLN | LLN | number |  | Lower limit of normal as received, in UNIT |
| ULN | ULN | number |  | Upper limit of normal as received, in UNIT |
| VAL_SI | VALSI | number |  | VAL converted to UNIT_SI with the units.csv factor (blank when VAL is missing or UNIT is not convertible); a converted value is rounded to 6 decimals, so a boundary record is exact only in its as-received UNIT |
| UNIT_SI | UNITSI | text (14) |  | Analyte SI unit (analytes.csv UNIT_SI) |
| LLN_SI | LLNSI | number |  | LLN in UNIT_SI |
| ULN_SI | ULNSI | number |  | ULN in UNIT_SI |
| VAL_CONV | VALCONV | number |  | VAL converted to UNIT_CONV (rounded to 6 decimals; informational: CTCAE prints its conventional and SI thresholds as rounded pairs, so grade a converted view only with the thresholds of the unit it is in) |
| UNIT_CONV | UNITCONV | text (14) |  | Analyte conventional unit (analytes.csv UNIT_CONV) |
| LLN_CONV | LLNCONV | number |  | LLN in UNIT_CONV |
| ULN_CONV | ULNCONV | number |  | ULN in UNIT_CONV |
| DATE | DATE | date | never blank | Collection date (ISO 8601) |
| STUDY_DAY | STUDYDAY | integer | never blank | Study day relative to REF_DATE: day 1 on REF_DATE, no day 0 (ADaM ADY convention) |
| REF_DATE | REFDATE | date | never blank | Reference date (first dose); records dated on or before it are pre-treatment |
| BASELINE_FLAG | BLFL | text (1) | Y | Y on the baseline record of the subject's test and specimen (last pre-treatment record with a result, see convention BASELINE_SELECTION) |
| BASE_VAL | BASEVAL | number |  | Baseline value as received, in BASE_UNIT (blank when the subject has no baseline or the record is NOT DONE) |
| BASE_UNIT | BASEUNIT | text (14) |  | Unit of the baseline record as received |
| BASE_LLN | BASELLN | number |  | Baseline record's LLN as received, in BASE_UNIT |
| BASE_ULN | BASEULN | number |  | Baseline record's ULN as received, in BASE_UNIT |
| BASE_VAL_SI | BVALSI | number |  | Baseline value in UNIT_SI |
| BASE_LLN_SI | BLLNSI | number |  | Baseline record's LLN in UNIT_SI |
| BASE_ULN_SI | BULNSI | number |  | Baseline record's ULN in UNIT_SI |
| BASE_VAL_CONV | BVALCONV | number |  | Baseline value in UNIT_CONV |
| BASE_LLN_CONV | BLLNCONV | number |  | Baseline record's LLN in UNIT_CONV |
| BASE_ULN_CONV | BULNCONV | number |  | Baseline record's ULN in UNIT_CONV |
| STATUS | STATUS | text (8) | NOT DONE | NOT DONE marker (CDISC LBSTAT); blank otherwise |
| GRADABLE | GRADABLE | text (1) | Y, N; never blank | Y = a grade is expected in at least one direction and version; N = no grade is expected at all (missing result or needed limit, unknown or blank unit on an absolute-threshold test, no criterion for the test and specimen, NOT DONE) |
| EXP_GRADE_LOW_V5 | EXPGRL5 | integer | 0 to 4 | Expected CTCAE v5 grade on the LOW scale under the DEFAULT profile; 0 = normal; blank = not gradable or no LOW term |
| EXP_GRADE_HIGH_V5 | EXPGRH5 | integer | 0 to 4 | Expected CTCAE v5 grade on the HIGH scale under the DEFAULT profile; blank = not gradable or no HIGH term |
| EXP_TERM_LOW_V5 | EXPTRL5 | text (27) |  | Expected CTCAE v5 term of the LOW scale whenever the scale applies to the test (also at grade 0 and for a missing result); blank when no term applies or the record is NOT DONE |
| EXP_TERM_HIGH_V5 | EXPTRH5 | text (47) |  | Expected CTCAE v5 term of the HIGH scale whenever the scale applies |
| EXP_BASE_GRADE_LOW_V5 | EXPBGL5 | integer | 0 to 4 | Expected v5 LOW grade of the subject's baseline record (blank without baseline or on NOT DONE records) |
| EXP_BASE_GRADE_HIGH_V5 | EXPBGH5 | integer | 0 to 4 | Expected v5 HIGH grade of the subject's baseline record |
| EXP_GRADE_V5 | EXPGR5 | integer | 0 to 4 | Single worst v5 grade for single-scale designs: the maximum of the non-missing LOW and HIGH grades; blank when both are missing |
| EXP_TERM_V5 | EXPTR5 | text (47) |  | Term of the direction that gives EXP_GRADE_V5; when the grade is 0 and both directions have a term, blank |
| EXP_GRADE_LOW_V6 | EXPGRL6 | integer | 0 to 4 | Expected CTCAE v6 grade on the LOW scale under the DEFAULT profile; 0 = normal; blank = not gradable or no LOW term |
| EXP_GRADE_HIGH_V6 | EXPGRH6 | integer | 0 to 4 | Expected CTCAE v6 grade on the HIGH scale under the DEFAULT profile; blank = not gradable or no HIGH term |
| EXP_TERM_LOW_V6 | EXPTRL6 | text (30) |  | Expected CTCAE v6 term of the LOW scale whenever the scale applies to the test (also at grade 0 and for a missing result); blank when no term applies or the record is NOT DONE |
| EXP_TERM_HIGH_V6 | EXPTRH6 | text (47) |  | Expected CTCAE v6 term of the HIGH scale whenever the scale applies |
| EXP_BASE_GRADE_LOW_V6 | EXPBGL6 | integer | 0 to 4 | Expected v6 LOW grade of the subject's baseline record (blank without baseline or on NOT DONE records) |
| EXP_BASE_GRADE_HIGH_V6 | EXPBGH6 | integer | 0 to 4 | Expected v6 HIGH grade of the subject's baseline record |
| EXP_GRADE_V6 | EXPGR6 | integer | 0 to 4 | Single worst v6 grade for single-scale designs: the maximum of the non-missing LOW and HIGH grades; blank when both are missing |
| EXP_TERM_V6 | EXPTR6 | text (47) |  | Term of the direction that gives EXP_GRADE_V6; when the grade is 0 and both directions have a term, blank |
| VERSION_DELTA | VERDELTA | text (1) | Y, N; never blank | Y when any v5 expectation differs from the v6 expectation of the record |
| CONVENTIONS | CONVS | text (104) |  | Space-separated conventions.csv codes whose reading the record's expectations rely on |
| CONVENTION_DEP | CONVDEP | text (1) | Y, N; never blank | Y when a documented alternative reading of one of the record's conventions would change an expectation (conventions.csv CONVENTION_DEP = Y); exclude these records to validate against undisputed criteria only |
| DESCRIPTION | DESCR | text (86) | never blank | What the record proves, in plain words |

## Appendix A: modules

| MODULE | Records | What the records prove |
|---|---|---|
| CORE | 607 | every laboratory threshold of both versions at its boundary, with a normal baseline; mandatory |
| BASELINE | 327 | abnormal-baseline arms, no baseline, baseline selection (last pre-treatment record, record on REF_DATE, baseline without a range) |
| MISSING | 17 | missing result, missing limit, missing range |
| NOTDONE | 4 | NOT DONE records, one with a stray value before REF_DATE |
| UNITS | 90 | results in conventional units, alias spellings, unknown and blank units |
| CATEGORY | 12 | the same test code under another specimen (urine) has no criterion |

## Appendix B: convention codes

Each code names one reading of the CTCAE wording. The expectations follow the default reading; where an
alternative reading is defensible, CONVENTION_DEP = Y and the alternative is stated.

| Code | Title | Default reading | Alternative reading | Dependent |
|---|---|---|---|---|
| BASELINE_SELECTION | Which record is the baseline | The baseline is the last record of the same test and specimen with a result, not marked NOT DONE, dated on or before REF_DATE (first dose). The dataset marks it with BASELINE_FLAG = Y (one per test and specimen of the subject) and repeats its value and normal range in the BASE_* columns of every record of the subject, so an implementation may derive the baseline or take it as input. |  | N |
| BASELINE_SELF | Baseline record graded against itself | The baseline record is graded with its own value as the baseline: abnormal-baseline arms apply to it and a ">baseline" clause is false for it (the value equals the baseline). | Grade baseline records with the normal-baseline arm only, or do not grade them | Y |
| BASELINE_ABNORMAL_DEF | Definition of an abnormal baseline | The baseline is abnormal in the graded direction when the baseline value is >ULN (HIGH terms) or <LLN (LOW terms) of the baseline records own normal range; otherwise the normal-baseline arm applies. A baseline outside the range in the opposite direction counts as normal for that term. |  | Y |
| BASELINE_RANGE_FALLBACK | Baseline record without a normal range | When the baseline record carries no normal range, its abnormality is judged against the normal range of the record being graded. | Treat the baseline arm as unevaluable (grade missing) | Y |
| INCLUSIVE_START | Range written without a leading ">" starts inclusive | A range written "a - b" or ">=a" includes its lower bound (comparator >=); a range written ">a - b" or ">a" excludes it (comparator >). LOW-direction ranges "<a - b" use <. | Read every lower bound as exclusive (>) | Y |
| INTEGER_RANGE | Integer ranges read up to the neighbouring bound | An integer range is read as the real interval reaching the neighbouring grade bound: 59 - 30 => <60 and >=30; 29 - 15 => <30 and >=15; 26 - 49 => <50 and >=26; 10 - 25 => <26 and >=10; 125-129 => <130 and >=125. | Read integer ranges literally (a non-integer value between two ranges is ungraded) | Y |
| SODIUM_V5_GAP | v5 hyponatremia gap between 124 and 125 mmol/L | Grade 3 is <=124 (literal upper bound of the integer range) and grade 2 is <130, so a value such as 124.5 mmol/L is grade 2. | Grade 3 as <125 (as v6 writes it) | Y |
| CRCL_V6_BELOW_RANGE | v6 creatinine clearance below 10 mL/min | Values below 10 mL/min are graded 3, the highest laboratory-defined grade of the term. | Grade missing below 10 mL/min | Y |
| CREATCLR_TERM_BY_VERSION | Which term grades creatinine clearance | Creatinine clearance (CREATCLR) is graded with Chronic kidney disease in v5, whose thresholds are stated per 1.73 m2 and applied to mL/min as reported, and with Creatinine clearance decreased in v6. Measured and estimated GFR are graded with Chronic kidney disease in both versions. | v6: Chronic kidney disease for creatinine clearance as well | Y |
| CKD_EGFR_ONLY | Chronic kidney disease graded from eGFR/CrCl only | Only the eGFR/CrCl clauses are evaluated; the proteinuria, protein/creatinine and dialysis clauses need other data. |  | N |
| ENZYME_SYMPTOM_WORST | Amylase and lipase symptom-qualified ranges | Worst case: the clauses qualified "with signs or symptoms" are applied and the "asymptomatic" clauses are not, so >5 x ULN is grade 4 and >2 x ULN (v5; v6 lipase >3 x ULN) is grade 3. | Best case: the "asymptomatic" clauses are applied and the symptomatic ones are not, so >5 x ULN is grade 3, >1.5 x ULN is grade 2 and grade 4 is never assigned | Y |
| CLINICAL_QUALIFIERS | Clinical qualifiers not derivable from laboratory data | Laboratory-only reading: the patient is assumed asymptomatic, without intervention and not on anticoagulation, so clauses qualified "asymptomatic", "without physiologic consequences" or "no intervention" apply, clauses qualified "symptomatic", "with physiologic consequences" or "if on anticoagulation" do not, and grades defined only by clinical findings are never assigned. A clinical alternative separated by a semicolon never changes the grade of the laboratory clause. Amylase and lipase follow ENZYME_SYMPTOM_WORST instead. | Assume symptoms present (worst case): hyponatremia 125-<130 mmol/L grade 3, hypokalemia <LLN - 3.0 mmol/L grade 2, hyperuricemia >ULN grade 3 | Y |
| HYPERGLY_V5_LABONLY | v5 hyperglycemia without numeric thresholds | Grade 1 when the value is >ULN and >baseline; never higher from laboratory data. | Grade with the numeric fasting-glucose thresholds that v4.03 used and v6 restored (>ULN - 8.9, >8.9 - 13.9, >13.9 - 27.8, >27.8 mmol/L), i.e. apply rules V6.GLUC.H.ANY.G1 to G4 under version 5 | Y |
| FASTING_NOT_EVALUATED | v6 hyperglycemia fasting qualifier | Every glucose result is graded as if fasting; the dataset carries no fasting flag. | Grades 1-2 only for results flagged fasting | N |
| ABOVE_BASELINE_WAIVED | ">baseline" clause when the subject has no baseline | Without a baseline the ">baseline" requirement is waived and the >ULN clause alone grades. | The clause fails without a baseline: grade 0 | Y |
| PRESENT_AS_LIMIT | "Present" read as outside the normal range | Lymphopenia is present when the lymphocyte count is <LLN; neutrophil count increased when the neutrophil count is >ULN. | "Present" is not a laboratory criterion: no grade and no term from laboratory data | Y |
| PHOS_LABONLY | Phosphate grade 1 "laboratory finding only" | Grade 1 when the value is >ULN (hyperphosphatemia) or <LLN (hypophosphatemia); higher grades are clinical and never assigned. | No laboratory grade for phosphate | Y |
| ALT_V6_G3_CAP | v6 transaminase grade 3 qualifier "up to 5 x ULN" | The qualifier "up to 5 x ULN" is not applied: >2.0 - 4.0 x baseline is grade 3 whatever the baseline. No record of the dataset has a baseline above 5 x ULN. | Apply the qualifier: the clause holds only when the baseline is <=5 x ULN | N |
| CREAT_BASELINE_ARM | Creatinine baseline clauses | v5: the baseline clause applies whatever the baseline, the grade being the worse of the ULN clause and the baseline clause, so a value inside the normal range can be grade 2 or 3; v6: the baseline clause applies only when the baseline is below LLN. | v5: baseline clause only when the baseline is abnormal | Y |
| FIBRINOGEN_ARMS | Fibrinogen normal- and abnormal-baseline clauses | With a normal baseline (>=LLN) the LLN-multiple clauses apply. With an abnormal baseline (<LLN) the percent-decrease clauses apply: grade 1 needs any decrease (percent change <0; a value equal to the baseline is grade 0), grade 2 <=-25%, grade 3 <=-50%, grade 4 <=-75%. The absolute clause <0.5 g/L is grade 4 in both arms. | Apply the LLN-multiple clauses in both arms and take the worse grade | Y |
| HGB_INCREASE_REF | Reference for "Increase in >x g/dL" | v5: the increase is measured above the baseline when the baseline is >ULN and above ULN otherwise; v6: always above ULN. | v5: always above ULN | Y |
| MISSING_LIMIT | Normal-range limit missing | Clauses are evaluated from grade 4 downwards and the highest satisfied clause gives the grade. A clause that needs a missing limit is unevaluable; a clause compared with the baseline is not applied when the subject has no baseline (see ABOVE_BASELINE_WAIVED and CREAT_BASELINE_ARM). If no clause is satisfied and at least one clause was unevaluable, the grade is missing (not gradable); absolute thresholds still grade when they are satisfied. The expected term is populated. | Grade 0 instead of missing | Y |
| MISSING_RESULT | Result missing | Grades are missing; the expected term is still populated because the scale applies to the test. |  | N |
| NOT_DONE_NULL | NOT DONE records | Every grading variable is null, including the term. A value present on a NOT DONE record is ignored and is never the baseline. |  | N |
| NO_TERM_NULL | Test without a CTCAE term | Every grading variable is null in both versions. |  | N |
| VERSION_SPECIFIC_TERM | Term in one CTCAE version only | Under the version that has no term for the test and direction, grade and term are null. |  | N |
| UNIT_GUARD | Unit handling before grading | The result and its normal range are converted to UNIT_SI of analytes.csv with the units.csv factor before grading. An unknown or blank unit on a test with absolute thresholds makes the record not gradable (grades missing, term populated). Tests graded only on ULN, LLN or baseline multiples accept any non-blank unit because the unit cancels; a blank unit is not gradable. INR is unitless: the unit is ignored. | Unknown or blank unit: grade 0 | Y |
| BASELINE_OWN_UNIT | Unit of the as-received baseline columns | BASE_VAL, BASE_LLN and BASE_ULN are in the baseline records own unit (BASE_UNIT); the BASE_*_SI and BASE_*_CONV columns are converted. |  | N |
| SPECIMEN_MATCH | Criteria keyed on test code and specimen | A record matches criteria on LBTESTCD and LBSPEC. The same code with another specimen (urine creatinine, glucose, potassium, leukocytes) has no criterion: every grading variable is null, and such a record is never the baseline of the serum or blood record. |  | N |
| PROTEINURIA_24H | Urinary protein graded from the 24-hour excretion only | Graded from the 24-hour protein excretion (LBDUR PT24H) with inclusive bounds: >=ULN, >=1.0 g/24 h, >=3.5 g/24 h. Dipstick and protein/creatinine-ratio clauses are not evaluated. | Exclusive lower bounds (>ULN, >1.0, >3.5 g/24 h) | Y |

## Appendix C: tests

CDISC SDTM test codes (codelist C65047), specimens (C78734) and units (C71620); CD4 is sponsor-defined.

| LBTESTCD | LBTEST | LBSPEC | UNIT_SI | UNIT_CONV | Records | v5 HIGH term | v5 LOW term | v6 HIGH term | v6 LOW term |
|---|---|---|---|---|---|---|---|---|---|
| ALB | Albumin | SERUM | g/L | g/dL | 14 |  | Hypoalbuminemia |  | Hypoalbuminemia |
| ALP | Alkaline Phosphatase | SERUM | U/L | U/L | 47 | Alkaline phosphatase increased |  | Alkaline phosphatase increased |  |
| ALT | Alanine Aminotransferase | SERUM | U/L | U/L | 88 | Alanine aminotransferase increased |  | Alanine aminotransferase increased |  |
| AMYLASE | Amylase | SERUM | U/L | U/L | 14 | Serum amylase increased |  | Serum amylase increased |  |
| APTT | Activated Partial Thromboplastin Time | PLASMA | s | s | 11 | Activated partial thromboplastin time prolonged |  | Activated partial thromboplastin time prolonged |  |
| AST | Aspartate Aminotransferase | SERUM | U/L | U/L | 37 | Aspartate aminotransferase increased |  | Aspartate aminotransferase increased |  |
| BICARB | Bicarbonate | SERUM | mmol/L | mEq/L | 5 |  | Blood bicarbonate decreased |  | Blood bicarbonate decreased |
| BILI | Bilirubin | SERUM | umol/L | mg/dL | 33 | Blood bilirubin increased |  | Blood bilirubin increased |  |
| CACR | Calcium Corrected | SERUM | mmol/L | mg/dL | 32 | Hypercalcemia | Hypocalcemia | Hypercalcemia | Hypocalcemia |
| CAION | Calcium, Ionized | BLOOD | mmol/L | mg/dL | 28 | Hypercalcemia | Hypocalcemia | Hypercalcemia | Hypocalcemia |
| CD4 | CD4 Lymphocytes | BLOOD | 10^9/L | 10^6/L | 19 |  | CD4 lymphocytes decreased |  | CD4 lymphocytes decreased |
| CHOL | Cholesterol | SERUM | mmol/L | mg/dL | 17 | Cholesterol high |  | Cholesterol high |  |
| CK | Creatine Kinase | SERUM | U/L | U/L | 14 | CPK increased |  |  |  |
| CREAT | Creatinine | SERUM | umol/L | mg/dL | 79 | Creatinine increased |  | Creatinine increased |  |
| CREATCLR | Creatinine Clearance | URINE | mL/min | mL/min | 21 |  | Chronic kidney disease |  | Creatinine clearance decreased |
| EOS | Eosinophils | BLOOD | 10^9/L | 10^6/L | 17 | Eosinophilia |  | Eosinophilia |  |
| FIBRINO | Fibrinogen | PLASMA | g/L | mg/dL | 62 |  | Fibrinogen decreased |  | Fibrinogen decreased |
| GFR | Glomerular Filtration Rate | SERUM | mL/min/1.73 m2 | mL/min/1.73 m2 | 6 |  | Chronic kidney disease |  | Chronic kidney disease |
| GFRBSCRT | GFR from Creatinine Adjusted for BSA | SERUM | mL/min/1.73 m2 | mL/min/1.73 m2 | 16 |  | Chronic kidney disease |  | Chronic kidney disease |
| GGT | Gamma Glutamyl Transferase | SERUM | U/L | U/L | 40 | GGT increased |  | GGT increased |  |
| GLUC | Glucose | SERUM | mmol/L | mg/dL | 65 | Hyperglycemia | Hypoglycemia | Hyperglycemia | Hypoglycemia |
| HAPTOG | Haptoglobin | SERUM | g/L | mg/dL | 5 |  | Haptoglobin decreased |  | Haptoglobin decreased |
| HDL | HDL Cholesterol | SERUM | mmol/L | mg/dL | 5 |  |  |  | HDL decreased |
| HGB | Hemoglobin | BLOOD | g/L | g/dL | 69 | Hemoglobin increased | Anemia | Hemoglobin increased | Anemia |
| HGBMHGB | Methemoglobin/Total Hemoglobin | BLOOD | % | % | 5 | Methemoglobinemia |  | Methemoglobinemia |  |
| INR | Prothrombin Intl. Normalized Ratio | PLASMA | RATIO | RATIO | 13 | INR increased |  | INR increased |  |
| K | Potassium | SERUM | mmol/L | mEq/L | 42 | Hyperkalemia | Hypokalemia | Hyperkalemia | Hypokalemia |
| LDH | Lactate Dehydrogenase | SERUM | U/L | U/L | 5 | Blood lactate dehydrogenase increased |  | Blood lactate dehydrogenase increased |  |
| LDL | LDL Cholesterol | SERUM | mmol/L | mg/dL | 5 |  |  | LDL increased |  |
| LIPASET | Lipase | SERUM | U/L | U/L | 17 | Lipase increased |  | Lipase increased |  |
| LYM | Lymphocytes | BLOOD | 10^9/L | 10^6/L | 22 | Lymphocyte count increased | Lymphocyte count decreased | Lymphocyte count increased | Lymphopenia |
| MG | Magnesium | SERUM | mmol/L | mg/dL | 29 | Hypermagnesemia | Hypomagnesemia | Hypermagnesemia | Hypomagnesemia |
| NEUT | Neutrophils | BLOOD | 10^9/L | 10^6/L | 27 |  | Neutrophil count decreased | Neutrophil count increased | Neutrophil count decreased |
| PHOS | Phosphate | SERUM | mmol/L | mg/dL | 10 | Hyperphosphatemia | Hypophosphatemia | Hyperphosphatemia | Hypophosphatemia |
| PLAT | Platelets | BLOOD | 10^9/L | 10^6/L | 25 |  | Platelet count decreased |  | Thrombocytopenia |
| PROTEXR | Protein Excretion Rate | URINE | mg/day | g/day | 15 | Proteinuria |  | Urinary protein increased |  |
| SODIUM | Sodium | SERUM | mmol/L | mEq/L | 33 | Hypernatremia | Hyponatremia | Hypernatremia | Hyponatremia |
| TRIG | Triglycerides | SERUM | mmol/L | mg/dL | 21 | Hypertriglyceridemia |  | Hypertriglyceridemia |  |
| TROPONI | Troponin I | SERUM | ng/L | ug/L | 5 | Cardiac troponin I increased |  |  |  |
| TROPONT | Troponin T | SERUM | ng/L | ug/L | 3 | Cardiac troponin T increased |  |  |  |
| URATE | Urate | SERUM | umol/L | mg/dL | 5 | Hyperuricemia |  | Hyperuricemia |  |
| UREA | Urea | SERUM | mmol/L | mg/dL | 2 |  |  |  |  |
| VTD2D3IT | 25-Hydroxyvit D2 + 25-Hydroxyvit D3 | SERUM | nmol/L | ug/L | 5 |  |  |  | Vitamin D decreased |
| WBC | Leukocytes | BLOOD | 10^9/L | 10^6/L | 24 | Leukocytosis | White blood cell decreased | Leukocytosis | White blood cell decreased |

Sources: CTCAE v5.0 (NCI, published 27-Nov-2017) and CTCAE v6.0 (NCI, published 22-Jul-2025; PDF dated 20-Jan-2026).
