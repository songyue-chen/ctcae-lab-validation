"""Writes data/analytes.csv, data/units.csv and data/conventions.csv (phase 1)."""
import csv, sys, os
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------------------- analytes
A_COLS = ['LBTESTCD','LBTEST','LBSPEC','LBSPEC_ALT','LBDUR','NCI_CODE','CDISC_CT','ALIAS_LBTESTCD','LOINC',
          'UNIT_SI','UNIT_CONV','FACTOR_CONV_TO_SI','DECIMALS_SI','LLN_SI','ULN_SI','DIRECTIONS',
          'TERM_V5_HIGH','TERM_V5_LOW','TERM_V6_HIGH','TERM_V6_LOW','NOTE']
S, P, B, U = 'SERUM', 'PLASMA', 'BLOOD', 'URINE'
A = [
 # code, LBTEST, spec, alt, dur, nci, ct, alias, loinc, usi, uconv, factor, dec, lln, uln, dirs, t5h, t5l, t6h, t6l, note
 ('ALB','Albumin',S,P,'','C64431','Y','','1751-7','g/L','g/dL','10',0,'35','55','L','','Hypoalbuminemia','','Hypoalbuminemia',''),
 ('ALP','Alkaline Phosphatase',S,P,'','C64432','Y','','6768-6','U/L','U/L','1',0,'30','120','H','Alkaline phosphatase increased','','Alkaline phosphatase increased','',''),
 ('ALT','Alanine Aminotransferase',S,P,'','C64433','Y','','1742-6','U/L','U/L','1',0,'10','40','H','Alanine aminotransferase increased','','Alanine aminotransferase increased','',''),
 ('AMYLASE','Amylase',S,P,'','C64434','Y','','1798-8','U/L','U/L','1',0,'25','125','H','Serum amylase increased','','Serum amylase increased','',''),
 ('APTT','Activated Partial Thromboplastin Time',P,'','','C38462','Y','','14979-9','s','s','1',1,'25','35','H','Activated partial thromboplastin time prolonged','','Activated partial thromboplastin time prolonged','',''),
 ('AST','Aspartate Aminotransferase',S,P,'','C64467','Y','','1920-8','U/L','U/L','1',0,'10','40','H','Aspartate aminotransferase increased','','Aspartate aminotransferase increased','',''),
 ('BICARB','Bicarbonate',S,P,'','C74667','Y','','1963-8','mmol/L','mEq/L','1',0,'23','28','L','','Blood bicarbonate decreased','','Blood bicarbonate decreased',''),
 ('BILI','Bilirubin',S,P,'','C38037','Y','','1975-2','umol/L','mg/dL','17.1',0,'5','17','H','Blood bilirubin increased','','Blood bilirubin increased','','Total bilirubin'),
 ('CACR','Calcium Corrected',S,P,'','C119272','Y','CACRALB','46099-8','mmol/L','mg/dL','0.2495',2,'2.15','2.54','HL','Hypercalcemia','Hypocalcemia','Hypercalcemia','Hypocalcemia','CTCAE grades "Corrected serum calcium"; CACRALB (corrected for albumin) is graded identically'),
 ('CAION','Calcium, Ionized',B,'','','C81948','Y','','1994-3','mmol/L','mg/dL','0.2495',2,'1.16','1.31','HL','Hypercalcemia','Hypocalcemia','Hypercalcemia','Hypocalcemia','CTCAE "Ionized calcium" clauses (mmol/L only)'),
 ('CD4','CD4 Lymphocytes',B,'','','','N','','24467-3','10^9/L','10^6/L','0.001',2,'0.53','1.57','L','','CD4 lymphocytes decreased','','CD4 lymphocytes decreased','Sponsor-defined code: the SDTM LBTESTCD codelist (C65047) has no absolute CD4 count; CDISC models lymphocyte subsets in the Cell Phenotyping domain'),
 ('CHOL','Cholesterol',S,P,'','C105586','Y','','2093-3','mmol/L','mg/dL','0.02586',2,'0','5.17','H','Cholesterol high','','Cholesterol high','','Total cholesterol'),
 ('CK','Creatine Kinase',S,P,'','C64489','Y','','2157-6','U/L','U/L','1',0,'30','135','H','CPK increased','','','','CPK is a CDISC synonym of CK; no v6 term'),
 ('CREAT','Creatinine',S,P,'','C64547','Y','','2160-0','umol/L','mg/dL','88.4',0,'44','97','H','Creatinine increased','','Creatinine increased','',''),
 ('CREATCLR','Creatinine Clearance',U,'','PT24H','C25747','Y','CRTCLRE','2164-2','mL/min','mL/min','1',0,'90','140','L','','Chronic kidney disease','','Creatinine clearance decreased','24-hour collection (LBDUR PT24H); CRTCLRE (estimated, e.g. Cockcroft-Gault) graded identically; term differs by version (convention CREATCLR_TERM_BY_VERSION)'),
 ('EOS','Eosinophils',B,'','','C64550','Y','','711-2','10^9/L','10^6/L','0.001',2,'0','0.33','H','Eosinophilia','','Eosinophilia','',''),
 ('FIBRINO','Fibrinogen',P,'','','C64606','Y','','3255-7','g/L','mg/dL','0.01',2,'2.0','4.0','L','','Fibrinogen decreased','','Fibrinogen decreased',''),
 ('GFR','Glomerular Filtration Rate',S,'','','C90505','Y','GFRBSA','','mL/min/1.73 m2','mL/min/1.73 m2','1',0,'90','','L','','Chronic kidney disease','','Chronic kidney disease','Measured GFR. CTCAE thresholds are stated per 1.73 m2: use GFRBSA when the value is indexed to body surface area; both codes are graded identically. No marker-independent LOINC code exists for measured GFR (iohexol 101921-5, inulin 72159-7, iothalamate 90995-2, isotopic 78006-4)'),
 ('GFRBSCRT','GFR from Creatinine Adjusted for BSA',S,P,'','C98735','Y','GFRBSCYC','98979-8','mL/min/1.73 m2','mL/min/1.73 m2','1',0,'90','','L','','Chronic kidney disease','','Chronic kidney disease','Estimated GFR (eGFR). Do not use EGFR, which is Epidermal Growth Factor Receptor in codelist C65047'),
 ('GGT','Gamma Glutamyl Transferase',S,P,'','C64847','Y','','2324-2','U/L','U/L','1',0,'8','40','H','GGT increased','','GGT increased','',''),
 ('GLUC','Glucose',S,P,'','C105585','Y','','2345-7','mmol/L','mg/dL','0.0555',1,'3.9','5.5','HL','Hyperglycemia','Hypoglycemia','Hyperglycemia','Hypoglycemia','v6 hyperglycemia grades 1-2 are written for fasting glucose (convention FASTING_NOT_EVALUATED)'),
 ('HAPTOG','Haptoglobin',S,P,'','C74740','Y','','4542-7','g/L','mg/dL','0.01',2,'0.83','2.67','L','','Haptoglobin decreased','','Haptoglobin decreased',''),
 ('HDL','HDL Cholesterol',S,P,'','C105587','Y','','2085-9','mmol/L','mg/dL','0.02586',2,'1.29','','L','','','','HDL decreased','v6 only'),
 ('HGB','Hemoglobin',B,'','','C64848','Y','','718-7','g/L','g/dL','10',0,'120','160','HL','Hemoglobin increased','Anemia','Hemoglobin increased','Anemia',''),
 ('HGBMHGB','Methemoglobin/Total Hemoglobin',B,'','','C147367','Y','HGBMET','2614-6','%','%','1',1,'0.5','3.0','H','Methemoglobinemia','','Methemoglobinemia','','The percentage fraction CTCAE grades (>ULN); HGBMET (methemoglobin concentration) is graded identically against its own ULN'),
 ('INR','Prothrombin Intl. Normalized Ratio',P,'','','C64805','Y','','6301-6','RATIO','RATIO','1',1,'0.8','1.1','H','INR increased','','INR increased','','Unitless'),
 ('K','Potassium',S,P,'','C64853','Y','','2823-3','mmol/L','mEq/L','1',1,'3.5','5.0','HL','Hyperkalemia','Hypokalemia','Hyperkalemia','Hypokalemia',''),
 ('LDH','Lactate Dehydrogenase',S,P,'','C64855','Y','','2532-0','U/L','U/L','1',0,'80','225','H','Blood lactate dehydrogenase increased','','Blood lactate dehydrogenase increased','',''),
 ('LDL','LDL Cholesterol',S,P,'','C105588','Y','','13457-7','mmol/L','mg/dL','0.02586',2,'0','2.59','H','','','LDL increased','','v6 only'),
 ('LIPASET','Lipase',S,P,'','C117748','Y','LIPASEP','3040-3','U/L','U/L','1',0,'10','140','H','Lipase increased','','Lipase increased','','LIPASEP (pancreatic lipase) graded identically'),
 ('LYM','Lymphocytes',B,'','','C51949','Y','','731-0','10^9/L','10^6/L','0.001',2,'1.20','4.95','HL','Lymphocyte count increased','Lymphocyte count decreased','Lymphocyte count increased','Lymphopenia','Absolute count, not the percentage (LYMLE)'),
 ('MG','Magnesium',S,P,'','C64840','Y','','19123-9','mmol/L','mg/dL','0.4114',2,'0.66','1.07','HL','Hypermagnesemia','Hypomagnesemia','Hypermagnesemia','Hypomagnesemia',''),
 ('NEUT','Neutrophils',B,'','','C63321','Y','','751-8','10^9/L','10^6/L','0.001',2,'2.00','8.25','HL','','Neutrophil count decreased','Neutrophil count increased','Neutrophil count decreased','Absolute count (ANC), not the percentage (NEUTLE); the HIGH term exists in v6 only'),
 ('PHOS','Phosphate',S,P,'','C64857','Y','','2777-1','mmol/L','mg/dL','0.3229',2,'0.97','1.45','HL','Hyperphosphatemia','Hypophosphatemia','Hyperphosphatemia','Hypophosphatemia','Inorganic phosphate'),
 ('PLAT','Platelets',B,'','','C51951','Y','','777-3','10^9/L','10^6/L','0.001',0,'150','450','L','','Platelet count decreased','','Thrombocytopenia',''),
 ('PROTEXR','Protein Excretion Rate',U,'','PT24H','C150822','Y','','2889-4','mg/day','g/day','1000',0,'0','100','H','Proteinuria','','Urinary protein increased','','24-hour urine protein (LBDUR PT24H); mg/day = mg/24 h'),
 ('SODIUM','Sodium',S,P,'','C64809','Y','','2951-2','mmol/L','mEq/L','1',0,'136','145','HL','Hypernatremia','Hyponatremia','Hypernatremia','Hyponatremia',''),
 ('TRIG','Triglycerides',S,P,'','C64812','Y','','2571-8','mmol/L','mg/dL','0.01129',2,'0','1.69','H','Hypertriglyceridemia','','Hypertriglyceridemia','',''),
 ('TROPONI','Troponin I',S,P,'','C74749','Y','TROPONI3','10839-9','ng/L','ug/L','1000',0,'0','15','H','Cardiac troponin I increased','','','','No v6 term. High-sensitivity assays are a method (LBMETHOD), not a separate test code; ug/L = ng/mL'),
 ('TROPONT','Troponin T',S,P,'','C74750','Y','','6598-7','ng/L','ug/L','1000',0,'0','10','H','Cardiac troponin T increased','','','','No v6 term; ug/L = ng/mL'),
 ('URATE','Urate',S,P,'','C64814','Y','','3084-1','umol/L','mg/dL','59.48',0,'178','416','H','Hyperuricemia','','Hyperuricemia','','Uric acid is a CDISC synonym of URATE'),
 ('UREA','Urea',S,P,'','C64815','Y','','22664-7','mmol/L','mg/dL','0.1665',1,'2.9','7.1','','','','','','No CTCAE term in either version (used by the no-criterion scenario). Factor is for urea, not for urea nitrogen (BUN, 0.357)'),
 ('VTD2D3IT','25-Hydroxyvit D2 + 25-Hydroxyvit D3',S,P,'','C147446','Y','V25HD3','62292-8','nmol/L','ug/L','2.496',0,'75','150','L','','','','Vitamin D decreased','v6 only; V25HD3 (25-hydroxyvitamin D3) graded identically; ug/L = ng/mL'),
 ('WBC','Leukocytes',B,'','','C51948','Y','','6690-2','10^9/L','10^6/L','0.001',1,'4.0','11.0','HL','Leukocytosis','White blood cell decreased','Leukocytosis','White blood cell decreased',''),
]
with open(os.path.join(OUT, 'analytes.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f, lineterminator='\n'); w.writerow(A_COLS)
    for r in A: w.writerow(r)

# ----------------------------------------------------------------------------------------- units
U_COLS = ['LBTESTCD','FROM_UNIT','TO_UNIT','FACTOR','BASIS','NOTE']
MW = 'molar mass {} g/mol'
UN = []
def u(code, frm, to, fac, basis, note=''): UN.append((code, frm, to, fac, basis, note))
u('ALB','g/dL','g/L','10','1 g/dL = 10 g/L')
u('ALB','mg/dL','g/L','0.01','1 mg/dL = 0.01 g/L')
u('BICARB','mEq/L','mmol/L','1','monovalent ion: 1 mEq = 1 mmol')
u('BILI','mg/dL','umol/L','17.1','molar mass 584.7 g/mol; 1 mg/dL = 17.1 umol/L','CTCAE quotes ULN multiples only')
for c in ('CACR','CAION'):
    u(c,'mg/dL','mmol/L','0.2495','molar mass 40.08 g/mol; 1 mg/dL = 0.2495 mmol/L','CTCAE pairs 11.5 mg/dL with 2.9 mmol/L')
    u(c,'mEq/L','mmol/L','0.5','divalent ion: 1 mEq = 0.5 mmol')
for c in ('CHOL','HDL','LDL'):
    u(c,'mg/dL','mmol/L','0.02586','molar mass 386.65 g/mol; 1 mg/dL = 0.02586 mmol/L','CTCAE pairs 300 mg/dL with 7.75 mmol/L')
u('CREAT','mg/dL','umol/L','88.4','molar mass 113.12 g/mol; 1 mg/dL = 88.4 umol/L','CTCAE quotes ULN and baseline multiples only')
u('CREATCLR','mL/s','mL/min','60','1 mL/s = 60 mL/min')
u('GFR','mL/s/1.73 m2','mL/min/1.73 m2','60','1 mL/s = 60 mL/min')
u('GFRBSCRT','mL/s/1.73 m2','mL/min/1.73 m2','60','1 mL/s = 60 mL/min')
u('FIBRINO','mg/dL','g/L','0.01','1 mg/dL = 0.01 g/L','CTCAE absolute clause <50 mg/dL = <0.5 g/L')
u('FIBRINO','umol/L','g/L','0.34','molar mass 340 kDa; 1 umol/L = 0.34 g/L')
u('GLUC','mg/dL','mmol/L','0.0555','molar mass 180.16 g/mol; 1 mg/dL = 0.0555 mmol/L','CTCAE pairs 160 mg/dL with 8.9 mmol/L')
u('HAPTOG','mg/dL','g/L','0.01','1 mg/dL = 0.01 g/L')
u('HGB','g/dL','g/L','10','1 g/dL = 10 g/L','CTCAE pairs 10.0 g/dL with 100 g/L')
u('HGB','mmol/L','g/L','16.114','iron-based (monomer) 1 mmol/L = 1.6114 g/dL','CTCAE pairs 6.2 mmol/L with 100 g/L')
u('K','mEq/L','mmol/L','1','monovalent ion: 1 mEq = 1 mmol')
u('MG','mg/dL','mmol/L','0.4114','molar mass 24.305 g/mol; 1 mg/dL = 0.4114 mmol/L','CTCAE pairs 3.0 mg/dL with 1.23 mmol/L')
u('MG','mEq/L','mmol/L','0.5','divalent ion: 1 mEq = 0.5 mmol')
u('PHOS','mg/dL','mmol/L','0.3229','phosphorus molar mass 30.97 g/mol; 1 mg/dL = 0.3229 mmol/L','CTCAE phosphate grades are not numeric')
u('PROTEXR','g/day','mg/day','1000','1 g = 1000 mg','CTCAE quotes g/24 hrs; g/24h is the CDISC synonym of g/day')
u('SODIUM','mEq/L','mmol/L','1','monovalent ion: 1 mEq = 1 mmol')
u('TRIG','mg/dL','mmol/L','0.01129','molar mass 885.4 g/mol (triolein); 1 mg/dL = 0.01129 mmol/L','CTCAE pairs 150 mg/dL with 1.71 mmol/L')
for c in ('TROPONI','TROPONT'):
    u(c,'ug/L','ng/L','1000','1 ug/L = 1 ng/mL = 1000 ng/L','CTCAE quotes ULN only')
u('URATE','mg/dL','umol/L','59.48','molar mass 168.11 g/mol; 1 mg/dL = 59.48 umol/L','CTCAE quotes ULN only')
u('UREA','mg/dL','mmol/L','0.1665','molar mass 60.06 g/mol; 1 mg/dL urea = 0.1665 mmol/L','not for urea nitrogen (BUN): 1 mg/dL BUN = 0.357 mmol/L urea')
u('VTD2D3IT','ug/L','nmol/L','2.496','molar mass 400.6 g/mol; 1 ng/mL = 2.496 nmol/L')
for c in ('ALT','AST','ALP','GGT','LDH','CK','AMYLASE','LIPASET'):
    u(c,'ukat/L','U/L','60','1 ukat/L = 60 U/L','CTCAE quotes ULN multiples only; the unit cancels')
for c in ('WBC','NEUT','LYM','EOS','PLAT','CD4'):
    u(c,'10^6/L','10^9/L','0.001','1 x 10^6/L = 0.001 x 10^9/L','CDISC 10^6/L = /uL = /mm3')
    u(c,'/uL','10^9/L','0.001','1 /uL = 1 x 10^6/L = 0.001 x 10^9/L','CTCAE quotes /mm3')
    u(c,'/mm3','10^9/L','0.001','1 /mm3 = 1 /uL')
    u(c,'10^3/uL','10^9/L','1','1 x 10^3/uL = 1 x 10^9/L','CDISC synonym of 10^9/L (K/uL, 10^3/mm3)')
    u(c,'10^3/mm3','10^9/L','1','1 x 10^3/mm3 = 1 x 10^9/L')
    u(c,'K/uL','10^9/L','1','1 K/uL = 1 x 10^9/L')
    u(c,'G/L','10^9/L','1','giga per litre = 10^9/L','test-specific: G/L means grams per litre for ALB, HGB, FIBRINO and HAPTOG')
with open(os.path.join(OUT, 'units.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f, lineterminator='\n'); w.writerow(U_COLS)
    for r in UN: w.writerow(r)

# ----------------------------------------------------------------------------------------- conventions
C_COLS = ['CONVENTION','SCOPE','TITLE','CTCAE_WORDING','DEFAULT_CHOICE','ALTERNATIVE_CHOICE','ALTERNATIVE_PROFILE','VERSIONS','LBTESTCD','CONVENTION_DEP','NOTE']
CV = []
def c(*r): CV.append(r)
c('BASELINE_SELECTION','DATA','Which record is the baseline','',
  'The baseline is the last record of the same test and specimen with a result, not marked NOT DONE, dated on or before REF_DATE (first dose). The dataset marks it with BASELINE_FLAG = Y and repeats its value and normal range in the BASE_* columns of every record of the subject, so an implementation may derive the baseline or take it as input.',
  '', '', '5 6', 'ALL', 'N', 'Records dated after REF_DATE, NOT DONE records, records without a result and records of another specimen are never the baseline.')
c('BASELINE_SELF','DATA','Baseline record graded against itself','',
  'The baseline record is graded with its own value as the baseline: abnormal-baseline arms apply to it and a ">baseline" clause is false for it (the value equals the baseline).',
  'Grade baseline records with the normal-baseline arm only, or do not grade them', '', '5 6', 'ALL', 'Y', '')
c('BASELINE_ABNORMAL_DEF','GRADING','Definition of an abnormal baseline',
  'v5: "if baseline was normal" / "if baseline was abnormal"; v6: "if baseline was normal or less than normal" / "if baseline was >ULN"; v6 creatinine: "if baseline is below LLN"; fibrinogen: "if abnormal"',
  'The baseline is abnormal in the graded direction when the baseline value is >ULN (HIGH terms) or <LLN (LOW terms) of the baseline record''s own normal range; otherwise the normal-baseline arm applies. A baseline outside the range in the opposite direction counts as normal for that term.',
  '', '', '5 6', 'ALP ALT AST BILI GGT CREAT FIBRINO', 'Y', '')
c('BASELINE_RANGE_FALLBACK','DATA','Baseline record without a normal range','',
  'When the baseline record carries no normal range, its abnormality is judged against the normal range of the record being graded.',
  'Treat the baseline arm as unevaluable (grade missing)', '', '5 6', 'ALL', 'Y', '')
c('INCLUSIVE_START','GRADING','Range written without a leading ">" starts inclusive',
  '"1.5 - 3.0 x baseline if baseline was abnormal" (v5 ALT, AST), "2.0 - 2.5 x baseline if baseline was abnormal" (v5 ALP, GGT), "1.0 - 1.5 x baseline if baseline was >ULN" (v6 ALT, AST, GGT, bilirubin), "150 mg/dL - 300 mg/dL; 1.71 mmol/L - 3.42 mmol/L" (hypertriglyceridemia grade 1)',
  'A range written "a - b" or ">=a" includes its lower bound (comparator >=); a range written ">a - b" or ">a" excludes it (comparator >). LOW-direction ranges "<a - b" use <.',
  'Read every lower bound as exclusive (>)', '', '5 6', 'ALP ALT AST BILI GGT TRIG', 'Y', 'v5 bilirubin writes "> 1.0 - 1.5 x baseline" and therefore stays exclusive.')
c('INTEGER_RANGE','GRADING','Integer ranges read up to the neighbouring bound',
  '"eGFR or CrCl 59 - 30 ml/min/1.73 m2" and "29 - 15 ml/min/1.73 m2" (v5 chronic kidney disease), "26 - 49 ml/min" and "10 - 25 ml/min" (v6 creatinine clearance decreased), "125-129 mmol/L" (v5 hyponatremia)',
  'An integer range is read as the real interval reaching the neighbouring grade bound: 59 - 30 => <60 and >=30; 29 - 15 => <30 and >=15; 26 - 49 => <50 and >=26; 10 - 25 => <26 and >=10; 125-129 => <130 and >=125.',
  'Read integer ranges literally (a non-integer value between two ranges is ungraded)', '', '5 6', 'GFRBSCRT GFR CREATCLR SODIUM', 'Y', 'v6 rewrites the kidney ranges as "<60 - 30" and "<30 - 15", confirming the reading.')
c('SODIUM_V5_GAP','GRADING','v5 hyponatremia gap between 124 and 125 mmol/L',
  '"125-129 mmol/L and asymptomatic" (grade 2); "120-124 mmol/L regardless of symptoms" (grade 3)',
  'Grade 3 is <=124 (literal upper bound of the integer range) and grade 2 is <130, so a value such as 124.5 mmol/L is grade 2.',
  'Grade 3 as <125 (as v6 writes it)', '', '5', 'SODIUM', 'Y', '')
c('CRCL_V6_BELOW_RANGE','GRADING','v6 creatinine clearance below 10 mL/min',
  '"10 - 25 ml/min" (grade 3); grades 4 and 5: "Report Grade 4 and 5 as Renal and urinary disorders: Acute kidney injury or Chronic kidney disease"',
  'Values below 10 mL/min are graded 3, the highest laboratory-defined grade of the term.',
  'Grade missing below 10 mL/min', '', '6', 'CREATCLR', 'Y', '')
c('CREATCLR_TERM_BY_VERSION','GRADING','Which term grades creatinine clearance',
  'v5 chronic kidney disease: "eGFR or CrCl 59 - 30 ml/min/1.73 m2"; v6 creatinine clearance decreased: "26 - 49 ml/min", "10 - 25 ml/min"',
  'Creatinine clearance (CREATCLR) is graded with Chronic kidney disease in v5, whose thresholds are stated per 1.73 m2 and applied to mL/min as reported, and with Creatinine clearance decreased in v6. Measured and estimated GFR are graded with Chronic kidney disease in both versions.',
  'v6: Chronic kidney disease for creatinine clearance as well', '', '5 6', 'CREATCLR', 'Y', '')
c('CKD_EGFR_ONLY','GRADING','Chronic kidney disease graded from eGFR/CrCl only',
  '"or proteinuria 2+ present; urine protein/creatinine >0.5" (grade 1); "dialysis or renal transplant indicated" (grade 4)',
  'Only the eGFR/CrCl clauses are evaluated; the proteinuria, protein/creatinine and dialysis clauses need other data.',
  '', '', '5 6', 'GFRBSCRT GFR CREATCLR', 'N', '')
c('ENZYME_SYMPTOM_WORST','GRADING','Amylase and lipase symptom-qualified ranges',
  '">1.5 - 2.0 x ULN; >2.0 - 5.0 x ULN and asymptomatic" (grade 2), ">2.0 - 5.0 x ULN with signs or symptoms; >5.0 x ULN and asymptomatic" (grade 3), ">5.0 x ULN and with signs or symptoms" (grade 4); v6 lipase uses 3.0 in place of 2.0',
  'Worst case: the clauses qualified "with signs or symptoms" are applied and the "asymptomatic" clauses are not, so >5 x ULN is grade 4 and >2 x ULN (v5; v6 lipase >3 x ULN) is grade 3.',
  'Best case: the "asymptomatic" clauses are applied and the symptomatic ones are not, so >5 x ULN is grade 3, >1.5 x ULN is grade 2 and grade 4 is never assigned', 'BESTCASE_ENZYMES', '5 6', 'AMYLASE LIPASET', 'Y', '')
c('CLINICAL_QUALIFIERS','GRADING','Clinical qualifiers not derivable from laboratory data',
  '"125-129 mmol/L and asymptomatic" / "symptomatic" (hyponatremia), "Symptomatic with <LLN - 3.0 mmol/L" (hypokalemia grade 2), ">ULN without physiologic consequences" / "with physiologic consequences" (hyperuricemia), "if on anticoagulation" (INR), "<LLN and no intervention initiated" (bicarbonate), "with no medical intervention" (v5 hyperglycemia), "below the level of myocardial infarction as defined by the manufacturer" (troponin), "; bleeding", "; transfusion indicated", "; hospitalization indicated", "; life-threatening consequences", "Steroids initiated"',
  'Laboratory-only reading: the patient is assumed asymptomatic, without intervention and not on anticoagulation, so clauses qualified "asymptomatic", "without physiologic consequences" or "no intervention" apply, clauses qualified "symptomatic", "with physiologic consequences" or "if on anticoagulation" do not, and grades defined only by clinical findings are never assigned. A clinical alternative separated by a semicolon never changes the grade of the laboratory clause. Amylase and lipase follow ENZYME_SYMPTOM_WORST instead.',
  'Assume symptoms present (worst case): hyponatremia 125-<130 mmol/L grade 3, hypokalemia <LLN - 3.0 mmol/L grade 2, hyperuricemia >ULN grade 3', '', '5 6', 'SODIUM K URATE INR BICARB GLUC TROPONI TROPONT PHOS', 'Y', 'Rows affected carry QUALIFIER = ASYMPTOMATIC, SYMPTOMATIC, NO_INTERVENTION or ON_ANTICOAGULATION in criteria.csv.')
c('HYPERGLY_V5_LABONLY','GRADING','v5 hyperglycemia without numeric thresholds',
  '"Abnormal glucose above baseline with no medical intervention" (grade 1); grades 2-4 are clinical',
  'Grade 1 when the value is >ULN and >baseline; never higher from laboratory data.',
  'Grade with the numeric fasting-glucose thresholds that v4.03 used and v6 restored (>ULN - 8.9, >8.9 - 13.9, >13.9 - 27.8, >27.8 mmol/L), i.e. apply rules V6.GLUC.H.ANY.G1 to G4 under version 5', 'HYPERGLY_NUMERIC_V5', '5', 'GLUC', 'Y', '')
c('FASTING_NOT_EVALUATED','GRADING','v6 hyperglycemia fasting qualifier',
  '"Fasting glucose value >ULN - 8.9 mmol/L" (grade 1), "Fasting glucose value >8.9 - 13.9 mmol/L" (grade 2)',
  'Every glucose result is graded as if fasting; the dataset carries no fasting flag.',
  'Grades 1-2 only for results flagged fasting', '', '6', 'GLUC', 'N', '')
c('ABOVE_BASELINE_WAIVED','GRADING','">baseline" clause when the subject has no baseline',
  '">ULN and >Baseline" (eosinophilia), ">Baseline and ULN" (v6 alkaline phosphatase), "Abnormal glucose above baseline" (v5 hyperglycemia)',
  'Without a baseline the ">baseline" requirement is waived and the >ULN clause alone grades.',
  'The clause fails without a baseline: grade 0', 'BASELINE_STRICT', '5 6', 'EOS ALP GLUC', 'Y', '')
c('PRESENT_AS_LIMIT','GRADING','"Present" read as outside the normal range',
  '"Present" (v6 lymphopenia grade 1; v6 neutrophil count increased grade 1)',
  'Lymphopenia is present when the lymphocyte count is <LLN; neutrophil count increased when the neutrophil count is >ULN.',
  '"Present" is not a laboratory criterion: no grade and no term from laboratory data', 'PRESENT_NOT_LAB', '6', 'LYM NEUT', 'Y', '')
c('PHOS_LABONLY','GRADING','Phosphate grade 1 "laboratory finding only"',
  '"Laboratory finding only and intervention not indicated" (grade 1 of hyperphosphatemia and hypophosphatemia)',
  'Grade 1 when the value is >ULN (hyperphosphatemia) or <LLN (hypophosphatemia); higher grades are clinical and never assigned.',
  'No laboratory grade for phosphate', '', '5 6', 'PHOS', 'Y', '')
c('ALT_V6_G3_CAP','GRADING','v6 transaminase grade 3 qualifier "up to 5 x ULN"',
  '">2.0 - 4.0 x baseline if baseline was >ULN up to 5 x ULN" (v6 ALT and AST grade 3)',
  'The qualifier "up to 5 x ULN" is not applied: >2.0 - 4.0 x baseline is grade 3 whatever the baseline. No record of the dataset has a baseline above 5 x ULN.',
  'Apply the qualifier: the clause holds only when the baseline is <=5 x ULN', '', '6', 'ALT AST', 'N', '')
c('CREAT_BASELINE_ARM','GRADING','Creatinine baseline clauses',
  'v5: ">1.5 - 3.0 x baseline; >1.5 - 3.0 x ULN" (grade 2), ">3.0 x baseline; >3.0 - 6.0 x ULN" (grade 3); v6: ">1.5 - 3.0 x baseline if baseline is below LLN; >1.5 - 3.0 x ULN", ">3.0 x baseline if baseline is below LLN; >3.0 - 6.0 x ULN"',
  'v5: the baseline clause applies whatever the baseline, the grade being the worse of the ULN clause and the baseline clause, so a value inside the normal range can be grade 2 or 3; v6: the baseline clause applies only when the baseline is below LLN.',
  'v5: baseline clause only when the baseline is abnormal', '', '5 6', 'CREAT', 'Y', '')
c('FIBRINOGEN_ARMS','GRADING','Fibrinogen normal- and abnormal-baseline clauses',
  '"<1.0 - 0.75 x LLN; if abnormal, <25% decrease from baseline" (grade 1), "<0.75 - 0.5 x LLN; if abnormal, 25 - <50% decrease from baseline" (grade 2), "<0.5 - 0.25 x LLN; if abnormal, 50 - <75% decrease from baseline" (grade 3), "<0.25 x LLN; if abnormal, 75% decrease from baseline; absolute value <50 mg/dL" (grade 4)',
  'With a normal baseline (>=LLN) the LLN-multiple clauses apply. With an abnormal baseline (<LLN) the percent-decrease clauses apply: grade 1 needs any decrease (percent change <0; a value equal to the baseline is grade 0), grade 2 <=-25%, grade 3 <=-50%, grade 4 <=-75%. The absolute clause <0.5 g/L is grade 4 in both arms.',
  'Apply the LLN-multiple clauses in both arms and take the worse grade', '', '5 6', 'FIBRINO', 'Y', 'Percent change = (value - baseline) / baseline x 100, computed in double precision.')
c('HGB_INCREASE_REF','GRADING','Reference for "Increase in >x g/dL"',
  'v5: "Increase in >0 - 2 g/dL", "Increase in >2 - 4 g/dL", "Increase in >4 g/dL"; v6: the same followed by "above ULN"',
  'v5: the increase is measured above the baseline when the baseline is >ULN and above ULN otherwise; v6: always above ULN.',
  'v5: always above ULN', '', '5 6', 'HGB', 'Y', '')
c('MISSING_LIMIT','DATA','Normal-range limit missing','',
  'Clauses are evaluated from grade 4 downwards and the highest satisfied clause gives the grade. A clause that needs a missing limit or a missing baseline is unevaluable. If no clause is satisfied and at least one clause was unevaluable, the grade is missing (not gradable); absolute thresholds still grade when they are satisfied. The expected term is populated.',
  'Grade 0 instead of missing', 'UNGRADABLE_ZERO', '5 6', 'ALL', 'Y', '')
c('MISSING_RESULT','DATA','Result missing','',
  'Grades are missing; the expected term is still populated because the scale applies to the test.',
  '', '', '5 6', 'ALL', 'N', '')
c('NOT_DONE_NULL','DATA','NOT DONE records','',
  'Every grading variable is null, including the term. A value present on a NOT DONE record is ignored and is never the baseline.',
  '', '', '5 6', 'ALL', 'N', '')
c('NO_TERM_NULL','DATA','Test without a CTCAE term','',
  'Every grading variable is null in both versions.',
  '', '', '5 6', 'UREA', 'N', '')
c('VERSION_SPECIFIC_TERM','DATA','Term in one CTCAE version only','',
  'Under the version that has no term for the test and direction, grade and term are null.',
  '', '', '5 6', 'CK TROPONI TROPONT HDL LDL VTD2D3IT NEUT', 'N', 'v5 only: CPK increased, cardiac troponin I/T increased; v6 only: HDL decreased, LDL increased, vitamin D decreased, neutrophil count increased.')
c('UNIT_GUARD','DATA','Unit handling before grading','',
  'The result and its normal range are converted to UNIT_SI of analytes.csv with the units.csv factor before grading. An unknown or blank unit on a test with absolute thresholds makes the record not gradable (grades missing, term populated). Tests graded only on ULN, LLN or baseline multiples accept any non-blank unit because the unit cancels; a blank unit is not gradable. INR is unitless: the unit is ignored.',
  'Unknown or blank unit: grade 0', 'UNGRADABLE_ZERO', '5 6', 'ALL', 'Y', 'Unit spellings are compared after normalisation (case, blanks, x10^9 / 10*9 / 10E9, IU/L = U/L, cells/uL = /uL, s = sec).')
c('BASELINE_OWN_UNIT','DATA','Unit of the as-received baseline columns','',
  'BASE_VAL, BASE_LLN and BASE_ULN are in the baseline record''s own unit (BASE_UNIT); the BASE_*_SI and BASE_*_CONV columns are converted.',
  '', '', '5 6', 'ALL', 'N', '')
c('SPECIMEN_MATCH','DATA','Criteria keyed on test code and specimen','',
  'A record matches criteria on LBTESTCD and LBSPEC. The same code with another specimen (urine creatinine, glucose, potassium, leukocytes) has no criterion: every grading variable is null, and such a record is never the baseline of the serum or blood record.',
  '', '', '5 6', 'CREAT GLUC K WBC', 'N', '')
c('PROTEINURIA_24H','GRADING','Urinary protein graded from the 24-hour excretion only',
  '"urinary protein >=ULN - <1.0 g/24 hrs" (grade 1), "urinary protein 1.0 - <3.5 g/24 hrs" (grade 2), "Urinary protein >=3.5 g/24 hrs" (grade 3); "1+ proteinuria", "P/C <1" and the pediatric ratios are not laboratory excretion values',
  'Graded from the 24-hour protein excretion (LBDUR PT24H) with inclusive bounds: >=ULN, >=1.0 g/24 h, >=3.5 g/24 h. Dipstick and protein/creatinine-ratio clauses are not evaluated.',
  'Exclusive lower bounds (>ULN, >1.0, >3.5 g/24 h)', '', '5 6', 'PROTEXR', 'Y', 'The navigational note says that the 24-hour collection takes precedence over dipstick.')
with open(os.path.join(OUT, 'conventions.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f, lineterminator='\n'); w.writerow(C_COLS)
    for r in CV: w.writerow(r)
print('analytes', len(A), 'units', len(UN), 'conventions', len(CV))
