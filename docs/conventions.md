# Conventions behind the expected values

Generated from `data/conventions.csv` by `generator/build_docs.py`. A convention is a reading the CTCAE wording does not
settle. The DEFAULT profile applies the default choice of every convention; where a defensible alternative exists it is
published as an alternative profile in `data/expectations.csv`, for the records it changes. Records whose expectation
depends on a convention marked CONVENTION_DEP = Y carry CONVENTION_DEP = Y in `data/records.csv`, so an adopter can
validate against the undisputed criteria alone by excluding them.

## Alternative profiles

| Profile | Flips | Record x version pairs changed |
|---|---|---|
| BESTCASE_ENZYMES | ENZYME_SYMPTOM_WORST | v5: 11, v6: 8 |
| HYPERGLY_NUMERIC_V5 | HYPERGLY_V5_LABONLY | v5: 33 |
| PRESENT_NOT_LAB | PRESENT_AS_LIMIT | v6: 49 |
| UNGRADABLE_ZERO | MISSING_LIMIT, UNIT_GUARD | v5: 17, v6: 17 |
| BASELINE_STRICT | ABOVE_BASELINE_WAIVED | v5: 11, v6: 11 |

## Conventions

### How a CTCAE criterion is read (SCOPE = GRADING)

#### BASELINE_ABNORMAL_DEF: Definition of an abnormal baseline

- Versions: 5 6; tests: ALP ALT AST BILI GGT CREAT FIBRINO; CONVENTION_DEP = Y
- CTCAE wording: v5: "if baseline was normal" / "if baseline was abnormal"; v6: "if baseline was normal or less than normal" / "if baseline was >ULN"; v6 creatinine: "if baseline is below LLN"; fibrinogen: "if abnormal"
- Default choice: The baseline is abnormal in the graded direction when the baseline value is >ULN (HIGH terms) or <LLN (LOW terms) of the baseline records own normal range; otherwise the normal-baseline arm applies. A baseline outside the range in the opposite direction counts as normal for that term.

#### INCLUSIVE_START: Range written without a leading ">" starts inclusive

- Versions: 5 6; tests: ALP ALT AST BILI GGT TRIG; CONVENTION_DEP = Y
- CTCAE wording: "1.5 - 3.0 x baseline if baseline was abnormal" (v5 ALT, AST), "2.0 - 2.5 x baseline if baseline was abnormal" (v5 ALP, GGT), "1.0 - 1.5 x baseline if baseline was >ULN" (v6 ALT, AST, GGT, bilirubin), "150 mg/dL - 300 mg/dL; 1.71 mmol/L - 3.42 mmol/L" (hypertriglyceridemia grade 1)
- Default choice: A range written "a - b" or ">=a" includes its lower bound (comparator >=); a range written ">a - b" or ">a" excludes it (comparator >). LOW-direction ranges "<a - b" use <.
- Alternative choice: Read every lower bound as exclusive (>)
- Note: v5 bilirubin writes "> 1.0 - 1.5 x baseline" and therefore stays exclusive.

#### INTEGER_RANGE: Integer ranges read up to the neighbouring bound

- Versions: 5 6; tests: GFRBSCRT GFR CREATCLR SODIUM; CONVENTION_DEP = Y
- CTCAE wording: "eGFR or CrCl 59 - 30 ml/min/1.73 m2" and "29 - 15 ml/min/1.73 m2" (v5 chronic kidney disease), "26 - 49 ml/min" and "10 - 25 ml/min" (v6 creatinine clearance decreased), "125-129 mmol/L" (v5 hyponatremia)
- Default choice: An integer range is read as the real interval reaching the neighbouring grade bound: 59 - 30 => <60 and >=30; 29 - 15 => <30 and >=15; 26 - 49 => <50 and >=26; 10 - 25 => <26 and >=10; 125-129 => <130 and >=125.
- Alternative choice: Read integer ranges literally (a non-integer value between two ranges is ungraded)
- Note: v6 rewrites the kidney ranges as "<60 - 30" and "<30 - 15", confirming the reading.

#### SODIUM_V5_GAP: v5 hyponatremia gap between 124 and 125 mmol/L

- Versions: 5; tests: SODIUM; CONVENTION_DEP = Y
- CTCAE wording: "125-129 mmol/L and asymptomatic" (grade 2); "120-124 mmol/L regardless of symptoms" (grade 3)
- Default choice: Grade 3 is <=124 (literal upper bound of the integer range) and grade 2 is <130, so a value such as 124.5 mmol/L is grade 2.
- Alternative choice: Grade 3 as <125 (as v6 writes it)

#### CRCL_V6_BELOW_RANGE: v6 creatinine clearance below 10 mL/min

- Versions: 6; tests: CREATCLR; CONVENTION_DEP = Y
- CTCAE wording: "10 - 25 ml/min" (grade 3); grades 4 and 5: "Report Grade 4 and 5 as Renal and urinary disorders: Acute kidney injury or Chronic kidney disease"
- Default choice: Values below 10 mL/min are graded 3, the highest laboratory-defined grade of the term.
- Alternative choice: Grade missing below 10 mL/min

#### CREATCLR_TERM_BY_VERSION: Which term grades creatinine clearance

- Versions: 5 6; tests: CREATCLR; CONVENTION_DEP = Y
- CTCAE wording: v5 chronic kidney disease: "eGFR or CrCl 59 - 30 ml/min/1.73 m2"; v6 creatinine clearance decreased: "26 - 49 ml/min", "10 - 25 ml/min"
- Default choice: Creatinine clearance (CREATCLR) is graded with Chronic kidney disease in v5, whose thresholds are stated per 1.73 m2 and applied to mL/min as reported, and with Creatinine clearance decreased in v6. Measured and estimated GFR are graded with Chronic kidney disease in both versions.
- Alternative choice: v6: Chronic kidney disease for creatinine clearance as well

#### CKD_EGFR_ONLY: Chronic kidney disease graded from eGFR/CrCl only

- Versions: 5 6; tests: GFRBSCRT GFR CREATCLR; CONVENTION_DEP = N
- CTCAE wording: "or proteinuria 2+ present; urine protein/creatinine >0.5" (grade 1); "dialysis or renal transplant indicated" (grade 4)
- Default choice: Only the eGFR/CrCl clauses are evaluated; the proteinuria, protein/creatinine and dialysis clauses need other data.

#### ENZYME_SYMPTOM_WORST: Amylase and lipase symptom-qualified ranges

- Versions: 5 6; tests: AMYLASE LIPASET; CONVENTION_DEP = Y; alternative profile: BESTCASE_ENZYMES
- CTCAE wording: ">1.5 - 2.0 x ULN; >2.0 - 5.0 x ULN and asymptomatic" (grade 2), ">2.0 - 5.0 x ULN with signs or symptoms; >5.0 x ULN and asymptomatic" (grade 3), ">5.0 x ULN and with signs or symptoms" (grade 4); v6 lipase uses 3.0 in place of 2.0
- Default choice: Worst case: the clauses qualified "with signs or symptoms" are applied and the "asymptomatic" clauses are not, so >5 x ULN is grade 4 and >2 x ULN (v5; v6 lipase >3 x ULN) is grade 3.
- Alternative choice: Best case: the "asymptomatic" clauses are applied and the symptomatic ones are not, so >5 x ULN is grade 3, >1.5 x ULN is grade 2 and grade 4 is never assigned

#### CLINICAL_QUALIFIERS: Clinical qualifiers not derivable from laboratory data

- Versions: 5 6; tests: SODIUM K URATE INR BICARB GLUC TROPONI TROPONT PHOS; CONVENTION_DEP = Y
- CTCAE wording: "125-129 mmol/L and asymptomatic" / "symptomatic" (hyponatremia), "Symptomatic with <LLN - 3.0 mmol/L" (hypokalemia grade 2), ">ULN without physiologic consequences" / "with physiologic consequences" (hyperuricemia), "if on anticoagulation" (INR), "<LLN and no intervention initiated" (bicarbonate), "with no medical intervention" (v5 hyperglycemia), "below the level of myocardial infarction as defined by the manufacturer" (troponin), "; bleeding", "; transfusion indicated", "; hospitalization indicated", "; life-threatening consequences", "Steroids initiated"
- Default choice: Laboratory-only reading: the patient is assumed asymptomatic, without intervention and not on anticoagulation, so clauses qualified "asymptomatic", "without physiologic consequences" or "no intervention" apply, clauses qualified "symptomatic", "with physiologic consequences" or "if on anticoagulation" do not, and grades defined only by clinical findings are never assigned. A clinical alternative separated by a semicolon never changes the grade of the laboratory clause. Amylase and lipase follow ENZYME_SYMPTOM_WORST instead.
- Alternative choice: Assume symptoms present (worst case): hyponatremia 125-<130 mmol/L grade 3, hypokalemia <LLN - 3.0 mmol/L grade 2, hyperuricemia >ULN grade 3
- Note: Rows affected carry QUALIFIER = ASYMPTOMATIC, SYMPTOMATIC, NO_INTERVENTION or ON_ANTICOAGULATION in criteria.csv.

#### HYPERGLY_V5_LABONLY: v5 hyperglycemia without numeric thresholds

- Versions: 5; tests: GLUC; CONVENTION_DEP = Y; alternative profile: HYPERGLY_NUMERIC_V5
- CTCAE wording: "Abnormal glucose above baseline with no medical intervention" (grade 1); grades 2-4 are clinical
- Default choice: Grade 1 when the value is >ULN and >baseline; never higher from laboratory data.
- Alternative choice: Grade with the numeric fasting-glucose thresholds that v4.03 used and v6 restored (>ULN - 8.9, >8.9 - 13.9, >13.9 - 27.8, >27.8 mmol/L), i.e. apply rules V6.GLUC.H.ANY.G1 to G4 under version 5

#### FASTING_NOT_EVALUATED: v6 hyperglycemia fasting qualifier

- Versions: 6; tests: GLUC; CONVENTION_DEP = N
- CTCAE wording: "Fasting glucose value >ULN - 8.9 mmol/L" (grade 1), "Fasting glucose value >8.9 - 13.9 mmol/L" (grade 2)
- Default choice: Every glucose result is graded as if fasting; the dataset carries no fasting flag.
- Alternative choice: Grades 1-2 only for results flagged fasting

#### ABOVE_BASELINE_WAIVED: ">baseline" clause when the subject has no baseline

- Versions: 5 6; tests: EOS ALP GLUC; CONVENTION_DEP = Y; alternative profile: BASELINE_STRICT
- CTCAE wording: ">ULN and >Baseline" (eosinophilia), ">Baseline and ULN" (v6 alkaline phosphatase), "Abnormal glucose above baseline" (v5 hyperglycemia)
- Default choice: Without a baseline the ">baseline" requirement is waived and the >ULN clause alone grades.
- Alternative choice: The clause fails without a baseline: grade 0

#### PRESENT_AS_LIMIT: "Present" read as outside the normal range

- Versions: 6; tests: LYM NEUT; CONVENTION_DEP = Y; alternative profile: PRESENT_NOT_LAB
- CTCAE wording: "Present" (v6 lymphopenia grade 1; v6 neutrophil count increased grade 1)
- Default choice: Lymphopenia is present when the lymphocyte count is <LLN; neutrophil count increased when the neutrophil count is >ULN.
- Alternative choice: "Present" is not a laboratory criterion: no grade and no term from laboratory data

#### PHOS_LABONLY: Phosphate grade 1 "laboratory finding only"

- Versions: 5 6; tests: PHOS; CONVENTION_DEP = Y
- CTCAE wording: "Laboratory finding only and intervention not indicated" (grade 1 of hyperphosphatemia and hypophosphatemia)
- Default choice: Grade 1 when the value is >ULN (hyperphosphatemia) or <LLN (hypophosphatemia); higher grades are clinical and never assigned.
- Alternative choice: No laboratory grade for phosphate

#### ALT_V6_G3_CAP: v6 transaminase grade 3 qualifier "up to 5 x ULN"

- Versions: 6; tests: ALT AST; CONVENTION_DEP = N
- CTCAE wording: ">2.0 - 4.0 x baseline if baseline was >ULN up to 5 x ULN" (v6 ALT and AST grade 3)
- Default choice: The qualifier "up to 5 x ULN" is not applied: >2.0 - 4.0 x baseline is grade 3 whatever the baseline. No record of the dataset has a baseline above 5 x ULN.
- Alternative choice: Apply the qualifier: the clause holds only when the baseline is <=5 x ULN

#### CREAT_BASELINE_ARM: Creatinine baseline clauses

- Versions: 5 6; tests: CREAT; CONVENTION_DEP = Y
- CTCAE wording: v5: ">1.5 - 3.0 x baseline; >1.5 - 3.0 x ULN" (grade 2), ">3.0 x baseline; >3.0 - 6.0 x ULN" (grade 3); v6: ">1.5 - 3.0 x baseline if baseline is below LLN; >1.5 - 3.0 x ULN", ">3.0 x baseline if baseline is below LLN; >3.0 - 6.0 x ULN"
- Default choice: v5: the baseline clause applies whatever the baseline, the grade being the worse of the ULN clause and the baseline clause, so a value inside the normal range can be grade 2 or 3; v6: the baseline clause applies only when the baseline is below LLN.
- Alternative choice: v5: baseline clause only when the baseline is abnormal

#### FIBRINOGEN_ARMS: Fibrinogen normal- and abnormal-baseline clauses

- Versions: 5 6; tests: FIBRINO; CONVENTION_DEP = Y
- CTCAE wording: "<1.0 - 0.75 x LLN; if abnormal, <25% decrease from baseline" (grade 1), "<0.75 - 0.5 x LLN; if abnormal, 25 - <50% decrease from baseline" (grade 2), "<0.5 - 0.25 x LLN; if abnormal, 50 - <75% decrease from baseline" (grade 3), "<0.25 x LLN; if abnormal, 75% decrease from baseline; absolute value <50 mg/dL" (grade 4)
- Default choice: With a normal baseline (>=LLN) the LLN-multiple clauses apply. With an abnormal baseline (<LLN) the percent-decrease clauses apply: grade 1 needs any decrease (percent change <0; a value equal to the baseline is grade 0), grade 2 <=-25%, grade 3 <=-50%, grade 4 <=-75%. The absolute clause <0.5 g/L is grade 4 in both arms.
- Alternative choice: Apply the LLN-multiple clauses in both arms and take the worse grade
- Note: Percent change = (value - baseline) / baseline x 100, computed in double precision.

#### HGB_INCREASE_REF: Reference for "Increase in >x g/dL"

- Versions: 5 6; tests: HGB; CONVENTION_DEP = Y
- CTCAE wording: v5: "Increase in >0 - 2 g/dL", "Increase in >2 - 4 g/dL", "Increase in >4 g/dL"; v6: the same followed by "above ULN"
- Default choice: v5: the increase is measured above the baseline when the baseline is >ULN and above ULN otherwise; v6: always above ULN.
- Alternative choice: v5: always above ULN

#### PROTEINURIA_24H: Urinary protein graded from the 24-hour excretion only

- Versions: 5 6; tests: PROTEXR; CONVENTION_DEP = Y
- CTCAE wording: "urinary protein >=ULN - <1.0 g/24 hrs" (grade 1), "urinary protein 1.0 - <3.5 g/24 hrs" (grade 2), "Urinary protein >=3.5 g/24 hrs" (grade 3); "1+ proteinuria", "P/C <1" and the pediatric ratios are not laboratory excretion values
- Default choice: Graded from the 24-hour protein excretion (LBDUR PT24H) with inclusive bounds: >=ULN, >=1.0 g/24 h, >=3.5 g/24 h. Dipstick and protein/creatinine-ratio clauses are not evaluated.
- Alternative choice: Exclusive lower bounds (>ULN, >1.0, >3.5 g/24 h)
- Note: The navigational note says that the 24-hour collection takes precedence over dipstick.

### How record states are handled (SCOPE = DATA)

#### BASELINE_SELECTION: Which record is the baseline

- Versions: 5 6; tests: ALL; CONVENTION_DEP = N
- Default choice: The baseline is the last record of the same test and specimen with a result, not marked NOT DONE, dated on or before REF_DATE (first dose). The dataset marks it with BASELINE_FLAG = Y (one per test and specimen of the subject) and repeats its value and normal range in the BASE_* columns of every record of the subject, so an implementation may derive the baseline or take it as input.
- Note: Records dated after REF_DATE, NOT DONE records, records without a result and records of another specimen are never the baseline.

#### BASELINE_SELF: Baseline record graded against itself

- Versions: 5 6; tests: ALL; CONVENTION_DEP = Y
- Default choice: The baseline record is graded with its own value as the baseline: abnormal-baseline arms apply to it and a ">baseline" clause is false for it (the value equals the baseline).
- Alternative choice: Grade baseline records with the normal-baseline arm only, or do not grade them

#### BASELINE_RANGE_FALLBACK: Baseline record without a normal range

- Versions: 5 6; tests: ALL; CONVENTION_DEP = Y
- Default choice: When the baseline record carries no normal range, its abnormality is judged against the normal range of the record being graded.
- Alternative choice: Treat the baseline arm as unevaluable (grade missing)

#### MISSING_LIMIT: Normal-range limit missing

- Versions: 5 6; tests: ALL; CONVENTION_DEP = Y; alternative profile: UNGRADABLE_ZERO
- Default choice: Clauses are evaluated from grade 4 downwards and the highest satisfied clause gives the grade. A clause that needs a missing limit is unevaluable; a clause compared with the baseline is not applied when the subject has no baseline (see ABOVE_BASELINE_WAIVED and CREAT_BASELINE_ARM). If no clause is satisfied and at least one clause was unevaluable, the grade is missing (not gradable); absolute thresholds still grade when they are satisfied. The expected term is populated.
- Alternative choice: Grade 0 instead of missing

#### MISSING_RESULT: Result missing

- Versions: 5 6; tests: ALL; CONVENTION_DEP = N
- Default choice: Grades are missing; the expected term is still populated because the scale applies to the test.

#### NOT_DONE_NULL: NOT DONE records

- Versions: 5 6; tests: ALL; CONVENTION_DEP = N
- Default choice: Every grading variable is null, including the term. A value present on a NOT DONE record is ignored and is never the baseline.

#### NO_TERM_NULL: Test without a CTCAE term

- Versions: 5 6; tests: UREA; CONVENTION_DEP = N
- Default choice: Every grading variable is null in both versions.

#### VERSION_SPECIFIC_TERM: Term in one CTCAE version only

- Versions: 5 6; tests: CK TROPONI TROPONT HDL LDL VTD2D3IT NEUT; CONVENTION_DEP = N
- Default choice: Under the version that has no term for the test and direction, grade and term are null.
- Note: v5 only: CPK increased, cardiac troponin I/T increased; v6 only: HDL decreased, LDL increased, vitamin D decreased, neutrophil count increased.

#### UNIT_GUARD: Unit handling before grading

- Versions: 5 6; tests: ALL; CONVENTION_DEP = Y; alternative profile: UNGRADABLE_ZERO
- Default choice: The result and its normal range are converted to UNIT_SI of analytes.csv with the units.csv factor before grading. An unknown or blank unit on a test with absolute thresholds makes the record not gradable (grades missing, term populated). Tests graded only on ULN, LLN or baseline multiples accept any non-blank unit because the unit cancels; a blank unit is not gradable. INR is unitless: the unit is ignored.
- Alternative choice: Unknown or blank unit: grade 0
- Note: Unit spellings are compared after normalisation (case, blanks, x10^9 / 10*9 / 10E9, IU/L = U/L, cells/uL = /uL, s = sec).

#### BASELINE_OWN_UNIT: Unit of the as-received baseline columns

- Versions: 5 6; tests: ALL; CONVENTION_DEP = N
- Default choice: BASE_VAL, BASE_LLN and BASE_ULN are in the baseline records own unit (BASE_UNIT); the BASE_*_SI and BASE_*_CONV columns are converted.

#### SPECIMEN_MATCH: Criteria keyed on test code and specimen

- Versions: 5 6; tests: CREAT GLUC K WBC; CONVENTION_DEP = N
- Default choice: A record matches criteria on LBTESTCD and LBSPEC. The same code with another specimen (urine creatinine, glucose, potassium, leukocytes) has no criterion: every grading variable is null, and such a record is never the baseline of the serum or blood record.
