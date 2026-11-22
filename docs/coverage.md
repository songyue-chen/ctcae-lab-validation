# Coverage

Generated from `data/records.csv`, `data/criteria.csv` and `data/expectations.csv` by `generator/build_docs.py`.
A criteria rule is *exercised* when at least one record lists it in RULE_IDS and carries that grade for the version and
direction; it is *coverable* when at least one of its clauses is applied under a published profile (clauses qualified
"symptomatic" or "if on anticoagulation" of terms that are not amylase or lipase are never applied, see conventions.md).

## Records

- Records: 1057; subjects: 118; tests: 44
- Gradable records (a grade expected in at least one version and direction): 1036
- Records flagged CONVENTION_DEP = Y: 475
- Records whose v5 and v6 expectations differ (VERSION_DELTA = Y): 328

| Module | Records | Subjects | Gradable |
|---|---|---|---|
| CORE | 607 | 55 | 605 |
| BASELINE | 327 | 23 | 326 |
| MISSING | 17 | 5 | 14 |
| NOTDONE | 4 | 1 | 2 |
| UNITS | 90 | 29 | 87 |
| CATEGORY | 12 | 5 | 2 |

## Rules by version

| Version | Rules in criteria.csv | Lab-derivable | Coverable | Exercised |
|---|---|---|---|---|
| 5 | 222 | 181 | 179 | 179 |
| 6 | 207 | 172 | 170 | 170 |

Lab-derivable rules with no clause applied under any published profile: V5.K.L.ANY.G2, V5.URATE.H.ANY.G3, V6.K.L.ANY.G2, V6.URATE.H.ANY.G3.

Coverable rules not exercised: none.

## Records and exercised rules by test

| LBTESTCD | LBTEST | Records | Subjects | v5 rules exercised / coverable | v6 rules exercised / coverable |
|---|---|---|---|---|---|
| ALB | Albumin | 14 | 2 | 3 / 3 | 3 / 3 |
| ALP | Alkaline Phosphatase | 47 | 3 | 8 / 8 | 1 / 1 |
| ALT | Alanine Aminotransferase | 88 | 13 | 8 / 8 | 8 / 8 |
| AMYLASE | Amylase | 14 | 1 | 4 / 4 | 4 / 4 |
| APTT | Activated Partial Thromboplastin Time | 11 | 1 | 3 / 3 | 3 / 3 |
| AST | Aspartate Aminotransferase | 37 | 2 | 8 / 8 | 8 / 8 |
| BICARB | Bicarbonate | 5 | 1 | 1 / 1 | 1 / 1 |
| BILI | Bilirubin | 33 | 3 | 8 / 8 | 8 / 8 |
| CACR | Calcium Corrected | 32 | 3 | 8 / 8 | 8 / 8 |
| CAION | Calcium, Ionized | 28 | 2 | 8 / 8 | 8 / 8 |
| CD4 | CD4 Lymphocytes | 19 | 2 | 4 / 4 | 4 / 4 |
| CHOL | Cholesterol | 17 | 2 | 4 / 4 | 4 / 4 |
| CK | Creatine Kinase | 14 | 1 | 4 / 4 | - |
| CREAT | Creatinine | 79 | 6 | 4 / 4 | 6 / 6 |
| CREATCLR | Creatinine Clearance | 21 | 1 | 4 / 4 | 2 / 2 |
| EOS | Eosinophils | 17 | 3 | 1 / 1 | 1 / 1 |
| FIBRINO | Fibrinogen | 62 | 5 | 9 / 9 | 9 / 9 |
| GFR | Glomerular Filtration Rate | 6 | 1 | 4 / 4 | 4 / 4 |
| GFRBSCRT | GFR from Creatinine Adjusted for BSA | 16 | 2 | 4 / 4 | 4 / 4 |
| GGT | Gamma Glutamyl Transferase | 40 | 2 | 8 / 8 | 8 / 8 |
| GLUC | Glucose | 65 | 6 | 5 / 5 | 8 / 8 |
| HAPTOG | Haptoglobin | 5 | 1 | 1 / 1 | 1 / 1 |
| HDL | HDL Cholesterol | 5 | 1 | - | 1 / 1 |
| HGB | Hemoglobin | 69 | 9 | 6 / 6 | 6 / 6 |
| HGBMHGB | Methemoglobin/Total Hemoglobin | 5 | 1 | 1 / 1 | 1 / 1 |
| INR | Prothrombin Intl. Normalized Ratio | 13 | 2 | 3 / 3 | 3 / 3 |
| K | Potassium | 42 | 7 | 7 / 7 | 7 / 7 |
| LDH | Lactate Dehydrogenase | 5 | 1 | 1 / 1 | 1 / 1 |
| LDL | LDL Cholesterol | 5 | 1 | - | 1 / 1 |
| LIPASET | Lipase | 17 | 1 | 4 / 4 | 4 / 4 |
| LYM | Lymphocytes | 22 | 2 | 6 / 6 | 3 / 3 |
| MG | Magnesium | 29 | 3 | 7 / 7 | 7 / 7 |
| NEUT | Neutrophils | 27 | 4 | 4 / 4 | 5 / 5 |
| PHOS | Phosphate | 10 | 2 | 2 / 2 | 2 / 2 |
| PLAT | Platelets | 25 | 4 | 4 / 4 | 4 / 4 |
| PROTEXR | Protein Excretion Rate | 15 | 2 | 3 / 3 | 3 / 3 |
| SODIUM | Sodium | 33 | 3 | 8 / 8 | 8 / 8 |
| TRIG | Triglycerides | 21 | 3 | 4 / 4 | 4 / 4 |
| TROPONI | Troponin I | 5 | 1 | 1 / 1 | - |
| TROPONT | Troponin T | 3 | 1 | 1 / 1 | - |
| URATE | Urate | 5 | 1 | 1 / 1 | 1 / 1 |
| UREA | Urea | 2 | 1 | - | - |
| VTD2D3IT | 25-Hydroxyvit D2 + 25-Hydroxyvit D3 | 5 | 1 | - | 1 / 1 |
| WBC | Leukocytes | 24 | 4 | 5 / 5 | 5 / 5 |

## Alternative profiles

| Profile | Version | Records changed |
|---|---|---|
| BASELINE_STRICT | 5 | 11 |
| BASELINE_STRICT | 6 | 11 |
| BESTCASE_ENZYMES | 5 | 11 |
| BESTCASE_ENZYMES | 6 | 8 |
| HYPERGLY_NUMERIC_V5 | 5 | 33 |
| PRESENT_NOT_LAB | 6 | 49 |
| UNGRADABLE_ZERO | 5 | 17 |
| UNGRADABLE_ZERO | 6 | 17 |

## Subjects

| Subject | Module | Test | Records | Description of the subject |
|---|---|---|---|---|
| ALB-L-N | CORE | ALB | 11 | normal baseline |
| ALP-H-N | CORE | ALP | 14 | normal baseline |
| ALP-H-Y | BASELINE | ALP | 20 | abnormal baseline |
| ALP-H-M | BASELINE | ALP | 13 | no baseline |
| ALT-H-N | CORE | ALT | 14 | normal baseline |
| ALT-H-Y | BASELINE | ALT | 23 | abnormal baseline |
| ALT-H-M | BASELINE | ALT | 13 | no baseline |
| ALT-H-LO | BASELINE | ALT | 14 | baseline below LLN |
| AMYLASE-H-N | CORE | AMYLASE | 14 | normal baseline |
| AST-H-N | CORE | AST | 14 | normal baseline |
| AST-H-Y | BASELINE | AST | 23 | abnormal baseline |
| BICARB-L-N | CORE | BICARB | 5 | normal baseline |
| BILI-H-N | CORE | BILI | 14 | normal baseline |
| BILI-H-Y | BASELINE | BILI | 17 | abnormal baseline |
| CACR-H-N | CORE | CACR | 14 | normal baseline |
| CACR-L-N | CORE | CACR | 14 | normal baseline |
| CAION-H-N | CORE | CAION | 14 | normal baseline |
| CAION-L-N | CORE | CAION | 14 | normal baseline |
| CHOL-H-N | CORE | CHOL | 14 | normal baseline |
| CK-H-N | CORE | CK | 14 | normal baseline |
| CREAT-H-N | CORE | CREAT | 20 | normal baseline |
| CREAT-H-LO | BASELINE | CREAT | 20 | baseline below LLN |
| CREAT-H-HI | BASELINE | CREAT | 20 | baseline above ULN |
| CREAT-H-M | BASELINE | CREAT | 13 | no baseline |
| CREATCLR-L-N | CORE | CREATCLR | 21 | normal baseline |
| GFRBSCRT-L-N | CORE | GFRBSCRT | 14 | normal baseline |
| GFR-L-N | CORE | GFR | 6 | normal baseline |
| GGT-H-N | CORE | GGT | 14 | normal baseline |
| GGT-H-Y | BASELINE | GGT | 26 | abnormal baseline |
| GLUC-H-N | CORE | GLUC | 14 | normal baseline |
| GLUC-H-Y | BASELINE | GLUC | 17 | abnormal baseline |
| GLUC-H-M | BASELINE | GLUC | 13 | no baseline |
| GLUC-L-N | CORE | GLUC | 14 | normal baseline |
| HAPTOG-L-N | CORE | HAPTOG | 5 | normal baseline |
| HDL-L-N | CORE | HDL | 5 | normal baseline |
| K-H-N | CORE | K | 14 | normal baseline |
| K-L-N | CORE | K | 11 | normal baseline |
| LDH-H-N | CORE | LDH | 5 | normal baseline |
| LDL-H-N | CORE | LDL | 5 | normal baseline |
| LIPASET-H-N | CORE | LIPASET | 17 | normal baseline |
| MG-H-N | CORE | MG | 11 | normal baseline |
| MG-L-N | CORE | MG | 14 | normal baseline |
| PHOS-H-N | CORE | PHOS | 5 | normal baseline |
| PHOS-L-N | CORE | PHOS | 5 | normal baseline |
| SODIUM-H-N | CORE | SODIUM | 14 | normal baseline |
| SODIUM-L-N | CORE | SODIUM | 16 | normal baseline |
| TRIG-H-N | CORE | TRIG | 14 | normal baseline |
| TROPONI-H-N | CORE | TROPONI | 5 | normal baseline |
| TROPONT-H-N | CORE | TROPONT | 3 | normal baseline |
| URATE-H-N | CORE | URATE | 5 | normal baseline |
| VTD2D3IT-L-N | CORE | VTD2D3IT | 5 | normal baseline |
| APTT-H-N | CORE | APTT | 11 | normal baseline |
| FIBRINO-L-N | CORE | FIBRINO | 14 | normal baseline |
| FIBRINO-L-Y | BASELINE | FIBRINO | 17 | abnormal baseline |
| FIBRINO-L-M | BASELINE | FIBRINO | 13 | no baseline |
| FIBRINO-L-HI | BASELINE | FIBRINO | 14 | baseline above ULN |
| INR-H-N | CORE | INR | 11 | normal baseline |
| CD4-L-N | CORE | CD4 | 14 | normal baseline |
| EOS-H-N | CORE | EOS | 5 | normal baseline |
| EOS-H-Y | BASELINE | EOS | 8 | abnormal baseline |
| EOS-H-M | BASELINE | EOS | 4 | no baseline |
| HGB-L-N | CORE | HGB | 11 | normal baseline |
| HGB-H-N | CORE | HGB | 11 | normal baseline |
| HGB-H-Y | BASELINE | HGB | 20 | abnormal baseline |
| HGB-H-M | BASELINE | HGB | 10 | no baseline |
| LYM-L-N | CORE | LYM | 14 | normal baseline |
| LYM-H-N | CORE | LYM | 8 | normal baseline |
| HGBMHGB-H-N | CORE | HGBMHGB | 5 | normal baseline |
| NEUT-L-N | CORE | NEUT | 17 | normal baseline |
| NEUT-H-N | CORE | NEUT | 5 | normal baseline |
| PLAT-L-N | CORE | PLAT | 17 | normal baseline |
| WBC-L-N | CORE | WBC | 14 | normal baseline |
| WBC-H-N | CORE | WBC | 5 | normal baseline |
| PROTEXR-H-N | CORE | PROTEXR | 11 | normal baseline |
| ALT-E-MISSVAL | MISSING | ALT | 3 | post-baseline result missing: grades missing, terms populated |
| K-E-NOULN | MISSING | K | 5 | above the usual ULN but ULN missing: high grade unevaluable |
| K-E-NOLLN | MISSING | K | 4 | below the usual LLN but LLN missing: low grade unevaluable |
| ALT-E-NOULN | MISSING | ALT | 2 | high value but ULN missing on a ULN-multiple test: grade missing |
| TRIG-E-NORANGE | MISSING | TRIG | 3 | exactly 1.71 mmol/L with no range: grade 1 (absolute, inclusive) |
| ALT-E-NOTDONE | NOTDONE | ALT | 4 | NOT DONE with a stray value before REF_DATE: ignored, never the baseline |
| UREA-E-NOTERM | CORE | UREA | 2 | abnormal value, no CTCAE term: every expectation blank |
| ALT-E-BLNORANGE | BASELINE | ALT | 3 | exactly 1.5 x baseline (120): baseline abnormal per the current ULN 40 |
| ALT-E-LASTPRE | BASELINE | ALT | 3 | earlier pre-treatment record (not the baseline) |
| ALT-E-ONTRTSDT | BASELINE | ALT | 3 | earlier pre-treatment record (not the baseline) |
| HGB-U-GDL | UNITS | HGB | 6 | 9.9 g/dL x 10 = 99 g/L: low grade 2 |
| HGB-U-MMOL | UNITS | HGB | 3 | 6.14 mmol/L x 16.114 = 98.9 g/L: low grade 2 |
| HGB-U-MIXED | UNITS | HGB | 3 | post-baseline record already in g/L (95) while the baseline is in g/dL: grade 2 |
| HGB-U-UNK | UNITS | HGB | 3 | unit mg/L has no units.csv conversion for an absolute-threshold test: not gradable |
| HGB-U-BLANK | UNITS | HGB | 2 | blank unit: not gradable |
| K-U-MEQ | UNITS | K | 4 | mEq/L = mmol/L (factor 1): high grade 2 |
| K-U-SPELL | UNITS | K | 2 | unit spelled MMOL/L (upper case): accepted, high grade 2 |
| GLUC-U-MGDL | UNITS | GLUC | 5 | 300 mg/dL x 0.0555 = 16.65 mmol/L: v6 grade 3, v5 grade 1 |
| CD4-U-CELLS | UNITS | CD4 | 5 | 150 cells/uL x 0.001 = 0.15 x 10^9/L: grade 3 |
| PLAT-U-KUL | UNITS | PLAT | 3 | 10^3/uL = 10^9/L (factor 1): 20 is v5 grade 4, v6 grade 3 |
| PLAT-U-PERUL | UNITS | PLAT | 3 | 20000 /uL x 0.001 = 20 x 10^9/L: v5 grade 4, v6 grade 3 |
| PLAT-U-SPELL | UNITS | PLAT | 2 | spelled 10*3/uL = 10^3/uL: v5 grade 4, v6 grade 3 |
| WBC-U-GL | UNITS | WBC | 3 | G/L = giga per litre for counts: 120 is leukocytosis grade 3 |
| NEUT-U-MM3 | UNITS | NEUT | 3 | 80 /mm3 = 0.08 x 10^9/L: grade 4 (v5 <0.5, v6 <0.1) |
| NEUT-U-SPELL | UNITS | NEUT | 2 | x10^9/L accepted: 0.30 is v5 grade 4, v6 grade 3 |
| CACR-U-MGDL | UNITS | CACR | 4 | 12.0 mg/dL x 0.2495 = 2.99 mmol/L: high grade 2 |
| PROTEXR-U-G | UNITS | PROTEXR | 4 | 4.0 g/24h x 1000 = 4000 mg/day: grade 3 |
| FIBRINO-U-MGDL | UNITS | FIBRINO | 4 | 40 mg/dL x 0.01 = 0.40 g/L: grade 4 |
| ALB-U-GDL | UNITS | ALB | 3 | 2.8 g/dL x 10 = 28 g/L: grade 2 |
| TRIG-U-MGDL | UNITS | TRIG | 4 | 200 mg/dL x 0.01129 = 2.26 mmol/L: grade 1 |
| MG-U-MGDL | UNITS | MG | 4 | 3.1 mg/dL x 0.4114 = 1.28 mmol/L: high grade 3 |
| CHOL-U-MGDL | UNITS | CHOL | 3 | 310 mg/dL x 0.02586 = 8.02 mmol/L: grade 2 |
| SODIUM-U-MEQ | UNITS | SODIUM | 3 | 124 mEq/L: low grade 3 |
| ALT-U-IUL | UNITS | ALT | 2 | IU/L normalised to U/L: 1 step above 3 x ULN, grade 2 |
| ALT-U-UKAT | UNITS | ALT | 2 | ukat/L on a ULN-multiple test: the factor cancels, 3.01 x ULN is grade 2 |
| ALT-U-BLANK | UNITS | ALT | 2 | blank unit: not gradable even on a ULN-multiple test |
| INR-U-BLANK | UNITS | INR | 2 | INR is unitless: blank unit accepted, grade 2 |
| BILI-U-MGDL | UNITS | BILI | 2 | mg/dL on a ULN-multiple test: 2.5 x ULN is grade 2 before and after conversion |
| GFRBSCRT-U-MLS | UNITS | GFRBSCRT | 2 | 0.45 mL/s/1.73m2 x 60 = 27 mL/min/1.73 m2: grade 3 |
| CREAT-C-URINE | CATEGORY | CREAT | 2 | 2.3 x ULN but urine specimen: no serum criterion, every expectation blank |
| GLUC-C-URINE | CATEGORY | GLUC | 2 | 30 mmol/L urine glucose would be v6 grade 4 if graded as serum: blank |
| K-C-URINE | CATEGORY | K | 2 | 200 mmol/24h: no serum criterion for a urine specimen, blank |
| WBC-C-URINE | CATEGORY | WBC | 2 | 150 /HPF: urine specimen, blank, no unit warning expected |
| CREAT-C-MIXED | CATEGORY | CREAT | 4 | serum 160 vs serum baseline 80: grade 2 (3 if the urine record were taken as baseline) |
