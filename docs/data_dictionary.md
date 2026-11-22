# Data dictionary

Generated from `data/schema/*.schema.json` (Frictionless Table Schema) by `generator/build_docs.py`; the schema files are the
authoritative definition and `generator/qc.py` validates every table against them.

## data/records.csv

One row per laboratory record. Feed the as-received columns to the implementation under test, merge its output back on RECORD_ID and compare with the EXP_* columns of the version being validated.

Feed the as-received columns (VAL, UNIT, LLN, ULN, DATE, REF_DATE, BASELINE_FLAG or BASE_*) to the implementation under test, merge its output back on RECORD_ID and compare with the EXP_* columns of the version being validated. Missing expected grade = not gradable, never 0. Terms compare case- and whitespace-insensitively.

| Column | Type | Constraints | Description |
|---|---|---|---|
| RECORD_ID | integer | required; unique; 1- | Stable integer key; adopters carry it through their pipeline and merge their output back on it |
| SUBJECT_ID | string | required | Synthetic subject, e.g. ALT-H-Y (<LBTESTCD>-<H\|L>-<arm>); one subject per test x direction x baseline arm |
| SCENARIO_ID | string | required; unique | Record scenario, e.g. ALT-H-Y-06 (<SUBJECT_ID>-BL for the baseline record) |
| MODULE | string | required; one of CORE, BASELINE, MISSING, NOTDONE, UNITS, CATEGORY | CORE = boundary records every implementation must pass; BASELINE = baseline selection and abnormal-baseline arms; MISSING = missing result or limit; NOTDONE = NOT DONE records; UNITS = foreign, alias or blank units; CATEGORY = same test code under another specimen |
| RULE_IDS | string |  | Space-separated criteria.csv RULE_IDs the record exercises in both versions: the rules that give a grade of 1 or more, the lowest applicable rule whose bound the value does not cross (grade 0), or the rules that are unevaluable (grade missing) |
| LBTESTCD | string | required | CDISC laboratory test code (analytes.csv; CD4 is sponsor-defined) |
| LBTEST | string | required | CDISC test name |
| LBSPEC | string | required; one of SERUM, PLASMA, BLOOD, URINE | Specimen type (CDISC SPECTYPE submission value) |
| LBDUR | string | one of PT24H | Collection duration (ISO 8601): PT24H marks a 24-hour collection |
| VAL | number |  | Result as an adopter's pipeline receives it, in UNIT (blank = missing result) |
| UNIT | string |  | Unit of VAL, LLN and ULN as received (foreign spellings and blanks in the UNITS module) |
| LLN | number |  | Lower limit of normal as received, in UNIT |
| ULN | number |  | Upper limit of normal as received, in UNIT |
| VAL_SI | number |  | VAL converted to UNIT_SI with the units.csv factor (blank when VAL is missing or UNIT is not convertible); a converted value is rounded to 6 decimals, so a boundary record is exact only in its as-received UNIT |
| UNIT_SI | string |  | Analyte SI unit (analytes.csv UNIT_SI) |
| LLN_SI | number |  | LLN in UNIT_SI |
| ULN_SI | number |  | ULN in UNIT_SI |
| VAL_CONV | number |  | VAL converted to UNIT_CONV (rounded to 6 decimals; informational: CTCAE prints its conventional and SI thresholds as rounded pairs, so grade a converted view only with the thresholds of the unit it is in) |
| UNIT_CONV | string |  | Analyte conventional unit (analytes.csv UNIT_CONV) |
| LLN_CONV | number |  | LLN in UNIT_CONV |
| ULN_CONV | number |  | ULN in UNIT_CONV |
| DATE | date | required | Collection date (ISO 8601) |
| STUDY_DAY | integer | required | Study day relative to REF_DATE: day 1 on REF_DATE, no day 0 (ADaM ADY convention) |
| REF_DATE | date | required | Reference date (first dose); records dated on or before it are pre-treatment |
| BASELINE_FLAG | string | one of Y | Y on the baseline record of the subject's test and specimen (last pre-treatment record with a result, see convention BASELINE_SELECTION) |
| BASE_VAL | number |  | Baseline value as received, in BASE_UNIT (blank when the subject has no baseline or the record is NOT DONE) |
| BASE_UNIT | string |  | Unit of the baseline record as received |
| BASE_LLN | number |  | Baseline record's LLN as received, in BASE_UNIT |
| BASE_ULN | number |  | Baseline record's ULN as received, in BASE_UNIT |
| BASE_VAL_SI | number |  | Baseline value in UNIT_SI |
| BASE_LLN_SI | number |  | Baseline record's LLN in UNIT_SI |
| BASE_ULN_SI | number |  | Baseline record's ULN in UNIT_SI |
| BASE_VAL_CONV | number |  | Baseline value in UNIT_CONV |
| BASE_LLN_CONV | number |  | Baseline record's LLN in UNIT_CONV |
| BASE_ULN_CONV | number |  | Baseline record's ULN in UNIT_CONV |
| STATUS | string | one of NOT DONE | NOT DONE marker (CDISC LBSTAT); blank otherwise |
| GRADABLE | string | required; one of Y, N | Y = a grade is expected in at least one direction and version; N = no grade is expected at all (missing result or needed limit, unknown or blank unit on an absolute-threshold test, no criterion for the test and specimen, NOT DONE) |
| EXP_GRADE_LOW_V5 | integer | 0-4 | Expected CTCAE v5 grade on the LOW scale under the DEFAULT profile; 0 = normal; blank = not gradable or no LOW term |
| EXP_GRADE_HIGH_V5 | integer | 0-4 | Expected CTCAE v5 grade on the HIGH scale under the DEFAULT profile; blank = not gradable or no HIGH term |
| EXP_TERM_LOW_V5 | string |  | Expected CTCAE v5 term of the LOW scale whenever the scale applies to the test (also at grade 0 and for a missing result); blank when no term applies or the record is NOT DONE |
| EXP_TERM_HIGH_V5 | string |  | Expected CTCAE v5 term of the HIGH scale whenever the scale applies |
| EXP_BASE_GRADE_LOW_V5 | integer | 0-4 | Expected v5 LOW grade of the subject's baseline record (blank without baseline or on NOT DONE records) |
| EXP_BASE_GRADE_HIGH_V5 | integer | 0-4 | Expected v5 HIGH grade of the subject's baseline record |
| EXP_GRADE_V5 | integer | 0-4 | Single worst v5 grade for single-scale designs: the maximum of the non-missing LOW and HIGH grades; blank when both are missing |
| EXP_TERM_V5 | string |  | Term of the direction that gives EXP_GRADE_V5; when the grade is 0 and both directions have a term, blank |
| EXP_GRADE_LOW_V6 | integer | 0-4 | Expected CTCAE v6 grade on the LOW scale under the DEFAULT profile; 0 = normal; blank = not gradable or no LOW term |
| EXP_GRADE_HIGH_V6 | integer | 0-4 | Expected CTCAE v6 grade on the HIGH scale under the DEFAULT profile; blank = not gradable or no HIGH term |
| EXP_TERM_LOW_V6 | string |  | Expected CTCAE v6 term of the LOW scale whenever the scale applies to the test (also at grade 0 and for a missing result); blank when no term applies or the record is NOT DONE |
| EXP_TERM_HIGH_V6 | string |  | Expected CTCAE v6 term of the HIGH scale whenever the scale applies |
| EXP_BASE_GRADE_LOW_V6 | integer | 0-4 | Expected v6 LOW grade of the subject's baseline record (blank without baseline or on NOT DONE records) |
| EXP_BASE_GRADE_HIGH_V6 | integer | 0-4 | Expected v6 HIGH grade of the subject's baseline record |
| EXP_GRADE_V6 | integer | 0-4 | Single worst v6 grade for single-scale designs: the maximum of the non-missing LOW and HIGH grades; blank when both are missing |
| EXP_TERM_V6 | string |  | Term of the direction that gives EXP_GRADE_V6; when the grade is 0 and both directions have a term, blank |
| VERSION_DELTA | string | required; one of Y, N | Y when any v5 expectation differs from the v6 expectation of the record |
| CONVENTIONS | string |  | Space-separated conventions.csv codes whose reading the record's expectations rely on |
| CONVENTION_DEP | string | required; one of Y, N | Y when a documented alternative reading of one of the record's conventions would change an expectation (conventions.csv CONVENTION_DEP = Y); exclude these records to validate against undisputed criteria only |
| DESCRIPTION | string | required | What the record proves, in plain words |

Primary key: RECORD_ID

## data/expectations.csv

Long form of the expected values: the DEFAULT profile repeats the EXP_* columns of records.csv; alternative profiles are published only for the record and version pairs they change.

The DEFAULT profile repeats the EXP_* columns of records.csv. Alternative profiles are published only for the records they change; a record absent under a profile keeps its DEFAULT expectation.

| Column | Type | Constraints | Description |
|---|---|---|---|
| RECORD_ID | integer | required | records.csv key |
| VERSION | integer | required; one of 5, 6 | CTCAE version |
| PROFILE | string | required; one of DEFAULT, BESTCASE_ENZYMES, HYPERGLY_NUMERIC_V5, PRESENT_NOT_LAB, UNGRADABLE_ZERO, BASELINE_STRICT | Convention profile (conventions.csv) |
| DIRECTION | string | required; one of LOW, HIGH, WORST | LOW and HIGH scales, or WORST = single worst grade across directions |
| GRADE | integer | 0-4 | Expected grade; blank = not gradable |
| TERM | string |  | Expected CTCAE term; blank when no term applies |
| BASE_GRADE | integer | 0-4 | Expected grade of the subject's baseline record in this direction; blank when there is no baseline or the record is NOT DONE |

Primary key: RECORD_ID, VERSION, PROFILE, DIRECTION

## data/analytes.csv

One row per laboratory test the dataset grades. Test codes and names are CDISC SDTM controlled terminology (codelists LBTESTCD C65047, LBTEST C67154, SPECTYPE C78734, UNIT C71620) except where CDISC_CT = N.

| Column | Type | Description |
|---|---|---|
| LBTESTCD | string | Test code used on records.csv and criteria.csv |
| LBTEST | string | CDISC test name (LBTEST submission value) |
| LBSPEC | string | Specimen type of the dataset records (CDISC SPECTYPE) |
| LBSPEC_ALT | string | Equivalent specimen graded identically |
| LBDUR | string | Collection duration (ISO 8601) when the test is a timed collection |
| NCI_CODE | string | NCI Thesaurus concept code of the LBTESTCD term |
| CDISC_CT | string | Y = LBTESTCD is a CDISC submission value; N = sponsor-defined code documented in NOTE |
| ALIAS_LBTESTCD | string | Space-separated CDISC test codes graded with the same criteria |
| LOINC | string | Optional LOINC cross-reference (one representative code) |
| UNIT_SI | string | Unit in which VAL_SI, the SI normal range and numeric criteria thresholds are expressed (CDISC UNIT submission value) |
| UNIT_CONV | string | Conventional unit of the VAL_CONV view (CDISC UNIT submission value) |
| FACTOR_CONV_TO_SI | number | Multiply a value in UNIT_CONV by this factor to obtain UNIT_SI (equals the units.csv row UNIT_CONV -> UNIT_SI) |
| DECIMALS_SI | integer | Reporting precision in UNIT_SI; one reporting step = 10^-DECIMALS_SI |
| LLN_SI | number | Default lower limit of normal (UNIT_SI): ABIM Laboratory Test Reference Ranges, January 2026, converted to SI (MedlinePlus for INR, KDIGO G1 for GFR); 0 when only an upper limit is published; blank when the test has no LLN |
| ULN_SI | number | Default upper limit of normal (UNIT_SI): ABIM Laboratory Test Reference Ranges, January 2026, converted to SI (MedlinePlus for INR); blank when the test has no ULN |
| DIRECTIONS | string | Directions with a CTCAE term in at least one version; blank = no term |
| TERM_V5_HIGH | string | CTCAE v5.0 term for the HIGH direction |
| TERM_V5_LOW | string | CTCAE v5.0 term for the LOW direction |
| TERM_V6_HIGH | string | CTCAE v6.0 term for the HIGH direction |
| TERM_V6_LOW | string | CTCAE v6.0 term for the LOW direction |
| NOTE | string | Mapping and scope notes |

## data/criteria.csv

One row per CTCAE version x test x direction x baseline arm x grade x clause. Every row quotes the grade cell verbatim (WORDING) and the fragment it transcribes (CLAUSE). Rows with LAB_DERIVABLE = N document grade cells or clauses that cannot be derived from laboratory data and are never used to grade. A grade is reached when any of its lab-derivable clauses holds under the active profile; clauses with a QUALIFIER are switched on or off by the conventions and profile (see conventions.csv).

| Column | Type | Description |
|---|---|---|
| RULE_ID | string | Identifier referenced by records.csv RULE_IDS: V<version>.<LBTESTCD>.<H\|L>.<ANY\|NRM\|ABN\|BLL>.G<grade>; several clauses of one grade share the RULE_ID and differ in CLAUSE_SEQ |
| CLAUSE_SEQ | integer | Sequence of the clause within the RULE_ID |
| VERSION | integer | CTCAE major version |
| LBTESTCD | string | CDISC laboratory test code (analytes.csv) |
| LBSPEC | string | Specimen type of the graded test (CDISC SPECTYPE submission value) |
| CTCAE_TERM | string | Official CTCAE term of this version, as printed |
| SOC | string | MedDRA System Organ Class under which CTCAE lists the term |
| DIRECTION | string | Direction of the abnormality graded |
| BASELINE_ARM | string | Baseline condition under which the clause applies: ANY = unconditional; NORMAL = baseline not abnormal in the graded direction; ABNORMAL = baseline >ULN (HIGH) or <LLN (LOW); BELOW_LLN = baseline below LLN (v6 creatinine) |
| GRADE | integer | CTCAE grade of the cell |
| LAB_DERIVABLE | string | Y = the clause can be evaluated from a laboratory value, its normal range and baseline; N = documentation only |
| WORDING | string | Verbatim text of the grade cell (whitespace normalised) |
| CLAUSE | string | Verbatim fragment of WORDING that this row transcribes; several non-contiguous fragments are joined with '; ' |
| COMPARATOR | string | Comparison of OPERAND against THRESHOLD (blank for LAB_DERIVABLE = N) |
| OPERAND | string | VALUE = result in UNIT_SI; PCHG = (value - baseline) / baseline x 100; EXCESS_ULN = value - ULN; EXCESS_BASE_OR_ULN = value minus the baseline when the baseline is >ULN, otherwise value minus ULN |
| THRESHOLD | string | Number in THRESHOLD_UNIT, or a multiple of ULN, LLN or BASE (e.g. 3*ULN, 1.5*BASE, 0.25*LLN) |
| THRESHOLD_UNIT | string | Unit of a numeric THRESHOLD: the analyte UNIT_SI, or % for PCHG |
| THRESHOLD_CONV | string | The same bound as CTCAE prints it in conventional units (number in THRESHOLD_CONV_UNIT, or ULN/LLN); blank when CTCAE gives no conventional figure |
| THRESHOLD_CONV_UNIT | string | Unit of THRESHOLD_CONV (analyte UNIT_CONV) |
| CONDITION | string | Additional laboratory condition that must hold (AND): VALUE>BASE = the result exceeds the baseline |
| QUALIFIER | string | Clinical qualifier attached to the clause; conventions.csv states which qualifiers the default and alternative profiles assume |
| CONVENTION | string | Space-separated convention codes (conventions.csv) that govern how the clause is read |
| SOURCE_DOC | string | Document the wording was transcribed from |
| SOURCE_PAGE | integer | Printed page number of the term in SOURCE_DOC |
| NOTE | string | Transcription note |

## data/conventions.csv

Every choice the expected values depend on that CTCAE wording does not settle, with the default reading and, where one is published, the alternative profile that holds the other reading. Profiles: DEFAULT, BESTCASE_ENZYMES, HYPERGLY_NUMERIC_V5, PRESENT_NOT_LAB, UNGRADABLE_ZERO, BASELINE_STRICT.

| Column | Type | Description |
|---|---|---|
| CONVENTION | string | Code referenced by criteria.csv CONVENTION and records.csv CONVENTIONS |
| SCOPE | string | GRADING = how a CTCAE criterion is read; DATA = how record states are handled (baseline, missing data, units, specimen) |
| TITLE | string | Short title |
| CTCAE_WORDING | string | Quoted CTCAE text that leaves the choice open (blank for DATA conventions) |
| DEFAULT_CHOICE | string | Reading used by the DEFAULT profile |
| ALTERNATIVE_CHOICE | string | Other defensible reading |
| ALTERNATIVE_PROFILE | string | Profile in expectations.csv that publishes the alternative, when one exists |
| VERSIONS | string | CTCAE versions concerned |
| LBTESTCD | string | Space-separated test codes concerned, or ALL |
| CONVENTION_DEP | string | Y = a record whose expectation depends on this convention is flagged CONVENTION_DEP = Y in records.csv |
| NOTE | string | Further notes |

## data/units.csv

value in FROM_UNIT x FACTOR = value in TO_UNIT. TO_UNIT is always the analyte's UNIT_SI; the reverse conversion is 1 / FACTOR. Factors are test-specific (the same unit string converts differently for different analytes, and G/L means giga per litre for counts but grams per litre for proteins). Unit spellings are matched after normalisation by the loaders.

| Column | Type | Description |
|---|---|---|
| LBTESTCD | string | Test code (analytes.csv) |
| FROM_UNIT | string | Unit as it may arrive on a record |
| TO_UNIT | string | Analyte UNIT_SI |
| FACTOR | number | Multiplier FROM_UNIT -> TO_UNIT |
| BASIS | string | Physical basis of the factor (molar mass, valence, prefix) |
| NOTE | string | Where CTCAE prints the pair of values this factor reproduces |

## Naming aliases applied by the loaders

| records.csv | ADaM (`naming=ADAM`) | SDTM (`naming=SDTM`) |
|---|---|---|
| SUBJECT_ID | USUBJID | USUBJID |
| LBTESTCD | PARAMCD | LBTESTCD |
| LBTEST | PARAM | LBTEST |
| VAL | AVAL | LBSTRESN |
| UNIT | AVALU | LBSTRESU |
| LLN | ANRLO | LBSTNRLO |
| ULN | ANRHI | LBSTNRHI |
| DATE | ADT | LBDTC (ISO 8601 character) |
| STUDY_DAY | ADY | LBDY |
| REF_DATE | TRTSDT | RFSTDTC (ISO 8601 character) |
| BASELINE_FLAG | ABLFL | LBBLFL |
| BASE_VAL, BASE_LLN, BASE_ULN | BASE, BNRLO, BNRHI | unchanged |
| STATUS | STATUS | LBSTAT |

Every other column, including LBSPEC, LBDUR, the SI and conventional views and the EXP_* expectations, keeps its name.
