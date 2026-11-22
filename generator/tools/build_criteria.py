"""Builds data/criteria.csv from the verbatim CTCAE cells extracted from the PDFs (v5_cells.json, v6_cells.json)."""
import csv, json, re, sys, os
S, OUT = sys.argv[1], sys.argv[2]
cells = {}
for v, fn in ((5, 'v5_cells.json'), (6, 'v6_cells.json')):
    for r in json.load(open(os.path.join(S, fn), encoding='utf-8')):
        cells[(v, r['term'])] = r
# --- two cells the word-box extraction could not reproduce; transcribed from the layout text, same pages
cells[(5, 'White blood cell decreased')] = {'term': 'White blood cell decreased', 'pdf_page': 90, 'grades': {
    '1': '<LLN - 3000/mm3; <LLN - 3.0 x 10e9 /L', '2': '<3000 - 2000/mm3; <3.0 - 2.0 x 10e9 /L',
    '3': '<2000 - 1000/mm3; <2.0 - 1.0 x 10e9 /L', '4': '<1000/mm3; <1.0 x 10e9 /L', '5': '-'}}
cells[(6, 'Thrombocytopenia')]['grades']['4'] = '<10,000/mm3; <10.0 x 10^9/L; life-threatening consequences; urgent intervention indicated'

an = {r['LBTESTCD']: r for r in csv.DictReader(open(os.path.join(OUT, 'analytes.csv'), encoding='utf-8'))}
SOC = {}
for t in ['Anemia', 'Eosinophilia', 'Leukocytosis', 'Lymphopenia', 'Methemoglobinemia', 'Thrombocytopenia']: SOC[t] = 'Blood and lymphatic system disorders'
for t in ['Chronic kidney disease', 'Proteinuria']: SOC[t] = 'Renal and urinary disorders'
for t in ['Hypercalcemia', 'Hyperglycemia', 'Hyperkalemia', 'Hypermagnesemia', 'Hypernatremia', 'Hyperphosphatemia', 'Hypertriglyceridemia', 'Hyperuricemia',
          'Hypoalbuminemia', 'Hypocalcemia', 'Hypoglycemia', 'Hypokalemia', 'Hypomagnesemia', 'Hyponatremia', 'Hypophosphatemia']: SOC[t] = 'Metabolism and nutrition disorders'
DOC = {5: 'CTCAE v5.0 (NCI, published 27-Nov-2017)', 6: 'CTCAE v6.0 (NCI, published 22-Jul-2025; PDF dated 20-Jan-2026)'}
ARM3 = {'ANY': 'ANY', 'NORMAL': 'NRM', 'ABNORMAL': 'ABN', 'BELOW_LLN': 'BLL'}
COLS = ['RULE_ID', 'CLAUSE_SEQ', 'VERSION', 'LBTESTCD', 'LBSPEC', 'CTCAE_TERM', 'SOC', 'DIRECTION', 'BASELINE_ARM', 'GRADE', 'LAB_DERIVABLE',
        'WORDING', 'CLAUSE', 'COMPARATOR', 'OPERAND', 'THRESHOLD', 'THRESHOLD_UNIT', 'THRESHOLD_CONV', 'THRESHOLD_CONV_UNIT', 'CONDITION',
        'QUALIFIER', 'CONVENTION', 'SOURCE_DOC', 'SOURCE_PAGE', 'NOTE']
rows, errors, seq = [], [], {}
def norm(s): return re.sub(r'\s+', ' ', s).strip()
def R(ver, test, d, grade, term, clause, cmp='', thr='', thr_conv='', arm='ANY', operand='VALUE', cond='', qual='', conv='', lab='Y', note=''):
    c = cells[(ver, term)]
    wording = norm(c['grades'][str(grade)])
    for frag in clause.split(' | '):
        if norm(frag) not in wording:
            errors.append(f'v{ver} {test} {term} G{grade}: clause not in cell\n   clause: {frag}\n   cell:   {wording}')
    rid = f"V{ver}.{test}.{d[0]}.{ARM3[arm]}.G{grade}"
    seq[rid] = seq.get(rid, 0) + 1
    a = an[test]
    if lab == 'Y' and thr != '' and re.fullmatch(r'-?\d+(\.\d+)?', thr):
        tu = '%' if operand == 'PCHG' else a['UNIT_SI']
    else:
        tu = ''
    tcu = a['UNIT_CONV'] if thr_conv != '' and not re.fullmatch(r'(ULN|LLN|BASE)', thr_conv) and thr_conv not in ('',) else ('' if thr_conv == '' else a['UNIT_CONV'])
    if thr_conv in ('ULN', 'LLN', 'BASE'): tcu = ''
    rows.append(dict(RULE_ID=rid, CLAUSE_SEQ=seq[rid], VERSION=ver, LBTESTCD=test, LBSPEC=a['LBSPEC'], CTCAE_TERM=term, SOC=SOC.get(term, 'Investigations'),
                     DIRECTION=d, BASELINE_ARM=arm, GRADE=grade, LAB_DERIVABLE=lab, WORDING=wording, CLAUSE=clause.replace(' | ', '; '),
                     COMPARATOR=cmp if lab == 'Y' else '', OPERAND=operand if lab == 'Y' else '', THRESHOLD=thr if lab == 'Y' else '',
                     THRESHOLD_UNIT=tu, THRESHOLD_CONV=thr_conv if lab == 'Y' else '', THRESHOLD_CONV_UNIT=tcu if lab == 'Y' else '',
                     CONDITION=cond, QUALIFIER=qual, CONVENTION=conv, SOURCE_DOC=DOC[ver], SOURCE_PAGE=c['pdf_page'], NOTE=note))
def N(ver, test, d, grade, term, clause=None, arm='ANY', conv='', note=''):
    """grade cell (or clause) that has no laboratory criterion"""
    if clause is None: clause = norm(cells[(ver, term)]['grades'][str(grade)])
    R(ver, test, d, grade, term, clause, arm=arm, conv=conv, lab='N', note=note)
B = (5, 6)
BAD = 'BASELINE_ABNORMAL_DEF'
# ============================================================================ liver enzymes and bilirubin
def liver(ver, test, term, nrm, abn, g1abn_cmp, g1abn_mult, cap_g3=False):
    """nrm = [(grade, clause, mult)], abn = [(grade, clause, mult)]"""
    for g, cl, m in nrm:
        R(ver, test, 'HIGH', g, term, cl, '>', 'ULN' if m == 1 else f'{m}*ULN', arm='NORMAL', conv=BAD)
    for g, cl, m in abn:
        cmp = g1abn_cmp if g == 1 else '>'
        conv = BAD + (' INCLUSIVE_START' if (g == 1 and cmp == '>=') else '') + (' ALT_V6_G3_CAP' if (g == 3 and cap_g3) else '')
        R(ver, test, 'HIGH', g, term, cl, cmp, 'BASE' if m == 1 else f'{m}*BASE', arm='ABNORMAL', conv=conv,
          note='Lower bound written without ">" read as inclusive' if (g == 1 and cmp == '>=') else ('"up to 5 x ULN" qualifier not applied (convention ALT_V6_G3_CAP)' if (g == 3 and cap_g3) else ''))
    N(ver, test, 'HIGH', 5, term) if cells[(ver, term)]['grades']['5'] != '-' else None
V5N = ' if baseline was normal'; V5A = ' if baseline was abnormal'
V6N = ' if baseline was normal or less than normal'; V6A = ' if baseline was >ULN'
for t, term in (('ALT', 'Alanine aminotransferase increased'), ('AST', 'Aspartate aminotransferase increased')):
    liver(5, t, term, [(1, '>ULN - 3.0 x ULN' + V5N, 1), (2, '>3.0 - 5.0 x ULN' + V5N, 3), (3, '>5.0 - 20.0 x ULN' + V5N, 5), (4, '>20.0 x ULN' + V5N, 20)],
          [(1, '1.5 - 3.0 x baseline' + V5A, 1.5), (2, '>3.0 - 5.0 x baseline' + V5A, 3), (3, '>5.0 - 20.0 x baseline' + V5A, 5), (4, '>20.0 x baseline' + V5A, 20)], '>=', 1.5)
    liver(6, t, term, [(1, '>ULN - 3.0 x ULN' + V6N, 1), (2, '>3.0 - 5.0 x ULN' + V6N, 3), (3, '>5.0 - 20.0 x ULN' + V6N, 5), (4, '>20.0 x ULN' + V6N, 20)],
          [(1, '1.0 - 1.5 x baseline' + V6A, 1), (2, '>1.5 - 2.0 x baseline' + V6A, 1.5), (3, '>2.0 - 4.0 x baseline' + V6A + ' up to 5 x ULN', 2), (4, '>4.0 x baseline' + V6A, 4)], '>=', 1, cap_g3=True)
for t, term in (('ALP', 'Alkaline phosphatase increased'), ('GGT', 'GGT increased')):
    liver(5, t, term, [(1, '>ULN - 2.5 x ULN' + V5N, 1), (2, '>2.5 - 5.0 x ULN' + V5N, 2.5), (3, '>5.0 - 20.0 x ULN' + V5N, 5), (4, '>20.0 x ULN' + V5N, 20)],
          [(1, '2.0 - 2.5 x baseline' + V5A, 2), (2, '>2.5 - 5.0 x baseline' + V5A, 2.5), (3, '>5.0 - 20.0 x baseline' + V5A, 5), (4, '>20.0 x baseline' + V5A, 20)], '>=', 2)
liver(6, 'GGT', 'GGT increased', [(1, '>ULN - 2.5 x ULN' + V6N, 1), (2, '>2.5 - 5.0 x ULN' + V6N, 2.5), (3, '>5.0 - 20.0 x ULN' + V6N, 5), (4, '>20.0 x ULN' + V6N, 20)],
      [(1, '1.0 - 1.5 x baseline' + V6A, 1), (2, '>1.5 - 3.0 x baseline' + V6A, 1.5), (3, '>3.0 - 10.0 x baseline' + V6A, 3), (4, '>10.0 x baseline' + V6A, 10)], '>=', 1)
R(6, 'ALP', 'HIGH', 1, 'Alkaline phosphatase increased', '>Baseline and ULN', '>', 'ULN', cond='VALUE>BASE', conv='ABOVE_BASELINE_WAIVED',
  note='Grade 1 only; the record must exceed both the ULN and the baseline')
liver(5, 'BILI', 'Blood bilirubin increased', [(1, '>ULN - 1.5 x ULN' + V5N, 1), (2, '>1.5 - 3.0 x ULN' + V5N, 1.5), (3, '>3.0 - 10.0 x ULN' + V5N, 3), (4, '>10.0 x ULN' + V5N, 10)],
      [(1, '> 1.0 - 1.5 x baseline' + V5A, 1), (2, '>1.5 - 3.0 x baseline' + V5A, 1.5), (3, '>3.0 - 10.0 x baseline' + V5A, 3), (4, '>10.0 x baseline' + V5A, 10)], '>', 1)
liver(6, 'BILI', 'Blood bilirubin increased', [(1, '>ULN - 1.5 x ULN' + V6N, 1), (2, '>1.5 - 3.0 x ULN' + V6N, 1.5), (3, '>3.0 - 10.0 x ULN' + V6N, 3), (4, '>10.0 x ULN' + V6N, 10)],
      [(1, '1.0 - 1.5 x baseline' + V6A, 1), (2, '>1.5 - 2.5 x baseline' + V6A, 1.5), (3, '>2.5 - 10.0 x baseline' + V6A, 2.5), (4, '>10.0 x baseline' + V6A, 10)], '>=', 1)
# ============================================================================ amylase, lipase (symptom-qualified)
def enzyme(ver, test, term, g2lo, g2hi, g3lo):
    E = 'ENZYME_SYMPTOM_WORST'
    R(ver, test, 'HIGH', 1, term, '>ULN - 1.5 x ULN', '>', 'ULN')
    R(ver, test, 'HIGH', 2, term, f'>1.5 - {g2lo} x ULN', '>', '1.5*ULN')
    R(ver, test, 'HIGH', 2, term, g2hi, '>', f'{float(g2lo):g}*ULN', qual='ASYMPTOMATIC', conv=E)
    R(ver, test, 'HIGH', 3, term, g3lo, '>', f'{float(g2lo):g}*ULN', qual='SYMPTOMATIC', conv=E)
    R(ver, test, 'HIGH', 3, term, '>5.0 x ULN and asymptomatic', '>', '5*ULN', qual='ASYMPTOMATIC', conv=E)
    R(ver, test, 'HIGH', 4, term, '>5.0 x ULN and with signs or symptoms', '>', '5*ULN', qual='SYMPTOMATIC', conv=E)
enzyme(5, 'AMYLASE', 'Serum amylase increased', '2.0', '>2.0 - 5.0 x ULN and asymptomatic', '>2.0 - 5.0 x ULN with signs or symptoms')
enzyme(6, 'AMYLASE', 'Serum amylase increased', '2.0', '>2.0 - 5.0 x ULN and asymptomatic or with mild signs or symptoms', '>2.0 - 5.0 x ULN with moderate or severe signs or symptoms')
enzyme(5, 'LIPASET', 'Lipase increased', '2.0', '>2.0 - 5.0 x ULN and asymptomatic', '>2.0 - 5.0 x ULN with signs or symptoms')
enzyme(6, 'LIPASET', 'Lipase increased', '3.0', '>3.0 - 5.0 x ULN and asymptomatic', '>3.0 - 5.0 x ULN with signs or symptoms')
# ============================================================================ single-grade terms
for v in B:
    R(v, 'BICARB', 'LOW', 1, 'Blood bicarbonate decreased', '<LLN and no intervention initiated', '<', 'LLN', qual='NO_INTERVENTION', conv='CLINICAL_QUALIFIERS')
    R(v, 'LDH', 'HIGH', 1, 'Blood lactate dehydrogenase increased', '>ULN', '>', 'ULN')
    R(v, 'HAPTOG', 'LOW', 1, 'Haptoglobin decreased', '<LLN', '<', 'LLN')
    R(v, 'URATE', 'HIGH', 1, 'Hyperuricemia', '>ULN without physiologic consequences', '>', 'ULN', qual='ASYMPTOMATIC', conv='CLINICAL_QUALIFIERS')
    R(v, 'URATE', 'HIGH', 3, 'Hyperuricemia', '>ULN with physiologic consequences', '>', 'ULN', qual='SYMPTOMATIC', conv='CLINICAL_QUALIFIERS')
    N(v, 'URATE', 'HIGH', 4, 'Hyperuricemia'); N(v, 'URATE', 'HIGH', 5, 'Hyperuricemia')
    R(v, 'PHOS', 'HIGH', 1, 'Hyperphosphatemia', 'Laboratory finding only and intervention not indicated', '>', 'ULN', qual='NO_INTERVENTION', conv='PHOS_LABONLY CLINICAL_QUALIFIERS',
      note='No numeric threshold: "laboratory finding" read as value >ULN')
    for g in (2, 3, 4, 5): N(v, 'PHOS', 'HIGH', g, 'Hyperphosphatemia', conv='PHOS_LABONLY')
    R(v, 'PHOS', 'LOW', 1, 'Hypophosphatemia', 'Laboratory finding only and intervention not indicated', '<', 'LLN', qual='NO_INTERVENTION', conv='PHOS_LABONLY CLINICAL_QUALIFIERS',
      note='No numeric threshold: "laboratory finding" read as value <LLN')
    for g in (2, 3, 4, 5): N(v, 'PHOS', 'LOW', g, 'Hypophosphatemia', conv='PHOS_LABONLY')
    R(v, 'EOS', 'HIGH', 1, 'Eosinophilia', '>ULN and >Baseline', '>', 'ULN', cond='VALUE>BASE', conv='ABOVE_BASELINE_WAIVED')
    N(v, 'EOS', 'HIGH', 3, 'Eosinophilia', conv='CLINICAL_QUALIFIERS')
    R(v, 'HGBMHGB', 'HIGH', 2, 'Methemoglobinemia', '>ULN', '>', 'ULN', note='No grade 1: the first laboratory grade is 2')
    for g in (3, 4, 5): N(v, 'HGBMHGB', 'HIGH', g, 'Methemoglobinemia', conv='CLINICAL_QUALIFIERS')
    R(v, 'WBC', 'HIGH', 3, 'Leukocytosis', '>100,000/mm3', '>', '100', '100000', note='No grade 1 or 2: the first laboratory grade is 3')
    for g in (4, 5): N(v, 'WBC', 'HIGH', g, 'Leukocytosis')
    R(v, 'LYM', 'HIGH', 2, 'Lymphocyte count increased', '>4000/mm3 - 20,000/mm3', '>', '4', '4000', note='No grade 1: the first laboratory grade is 2')
    R(v, 'LYM', 'HIGH', 3, 'Lymphocyte count increased', '>20,000/mm3', '>', '20', '20000')
R(6, 'HDL', 'LOW', 1, 'HDL decreased', '<LLN', '<', 'LLN', conv='VERSION_SPECIFIC_TERM')
R(6, 'LDL', 'HIGH', 1, 'LDL increased', '>ULN', '>', 'ULN', conv='VERSION_SPECIFIC_TERM')
R(6, 'VTD2D3IT', 'LOW', 1, 'Vitamin D decreased', 'Vitamin D decreased <LLN', '<', 'LLN', conv='VERSION_SPECIFIC_TERM')
R(6, 'LYM', 'LOW', 1, 'Lymphopenia', 'Present', '<', 'LLN', conv='PRESENT_AS_LIMIT', note='"Present" read as count <LLN')
R(6, 'NEUT', 'HIGH', 1, 'Neutrophil count increased', 'Present', '>', 'ULN', conv='PRESENT_AS_LIMIT VERSION_SPECIFIC_TERM', note='"Present" read as count >ULN')
# ============================================================================ v5-only terms
for t, term in (('TROPONI', 'Cardiac troponin I increased'), ('TROPONT', 'Cardiac troponin T increased')):
    R(5, t, 'HIGH', 1, term, 'Levels above the upper limit of normal and below the level of myocardial infarction as defined by the manufacturer', '>', 'ULN',
      conv='CLINICAL_QUALIFIERS VERSION_SPECIFIC_TERM', note='The upper bound (level of myocardial infarction) is assay-specific and not derivable: every value >ULN is grade 1')
    N(5, t, 'HIGH', 3, term, conv='CLINICAL_QUALIFIERS VERSION_SPECIFIC_TERM')
R(5, 'CK', 'HIGH', 1, 'CPK increased', '>ULN - 2.5 x ULN', '>', 'ULN', conv='VERSION_SPECIFIC_TERM')
R(5, 'CK', 'HIGH', 2, 'CPK increased', '>2.5 x ULN - 5 x ULN', '>', '2.5*ULN', conv='VERSION_SPECIFIC_TERM')
R(5, 'CK', 'HIGH', 3, 'CPK increased', '>5 x ULN - 10 x ULN', '>', '5*ULN', conv='VERSION_SPECIFIC_TERM')
R(5, 'CK', 'HIGH', 4, 'CPK increased', '>10 x ULN', '>', '10*ULN', conv='VERSION_SPECIFIC_TERM')
# ============================================================================ APTT, INR, fibrinogen
for v in B:
    R(v, 'APTT', 'HIGH', 1, 'Activated partial thromboplastin time prolonged', '>ULN - 1.5 x ULN', '>', 'ULN')
    R(v, 'APTT', 'HIGH', 2, 'Activated partial thromboplastin time prolonged', '>1.5 - 2.5 x ULN', '>', '1.5*ULN')
    R(v, 'APTT', 'HIGH', 3, 'Activated partial thromboplastin time prolonged', '>2.5 x ULN', '>', '2.5*ULN', note='"; bleeding" is a clinical alternative')
    Q = 'CLINICAL_QUALIFIERS'
    R(v, 'INR', 'HIGH', 1, 'INR increased', '>1.2 - 1.5', '>', '1.2')
    R(v, 'INR', 'HIGH', 1, 'INR increased', '>1 - 1.5 x baseline if on anticoagulation', '>', 'BASE', qual='ON_ANTICOAGULATION', conv=Q)
    R(v, 'INR', 'HIGH', 2, 'INR increased', '>1.5 - 2.5', '>', '1.5')
    R(v, 'INR', 'HIGH', 2, 'INR increased', '>1.5 - 2.5 x baseline if on anticoagulation', '>', '1.5*BASE', qual='ON_ANTICOAGULATION', conv=Q)
    R(v, 'INR', 'HIGH', 3, 'INR increased', '>2.5', '>', '2.5')
    R(v, 'INR', 'HIGH', 3, 'INR increased', '>2.5 x baseline if on anticoagulation', '>', '2.5*BASE', qual='ON_ANTICOAGULATION', conv=Q)
    F = 'FIBRINOGEN_ARMS ' + BAD
    R(v, 'FIBRINO', 'LOW', 1, 'Fibrinogen decreased', '<1.0 - 0.75 x LLN', '<', 'LLN', arm='NORMAL', conv=F)
    R(v, 'FIBRINO', 'LOW', 2, 'Fibrinogen decreased', '<0.75 - 0.5 x LLN', '<', '0.75*LLN', arm='NORMAL', conv=F)
    R(v, 'FIBRINO', 'LOW', 3, 'Fibrinogen decreased', '<0.5 - 0.25 x LLN', '<', '0.5*LLN', arm='NORMAL', conv=F)
    R(v, 'FIBRINO', 'LOW', 4, 'Fibrinogen decreased', '<0.25 x LLN', '<', '0.25*LLN', arm='NORMAL', conv=F)
    R(v, 'FIBRINO', 'LOW', 1, 'Fibrinogen decreased', 'if abnormal, <25% decrease from baseline', '<', '0', arm='ABNORMAL', operand='PCHG', conv=F, note='Any decrease (percent change <0) is grade 1; a value equal to the baseline is grade 0')
    R(v, 'FIBRINO', 'LOW', 2, 'Fibrinogen decreased', 'if abnormal, 25 - <50% decrease from baseline', '<=', '-25', arm='ABNORMAL', operand='PCHG', conv=F)
    R(v, 'FIBRINO', 'LOW', 3, 'Fibrinogen decreased', 'if abnormal, 50 - <75% decrease from baseline', '<=', '-50', arm='ABNORMAL', operand='PCHG', conv=F)
    R(v, 'FIBRINO', 'LOW', 4, 'Fibrinogen decreased', 'if abnormal, 75% decrease from baseline', '<=', '-75', arm='ABNORMAL', operand='PCHG', conv=F)
    R(v, 'FIBRINO', 'LOW', 4, 'Fibrinogen decreased', 'absolute value <50 mg/dL', '<', '0.5', '50', conv='FIBRINOGEN_ARMS', note='Applies in both baseline arms')
# ============================================================================ electrolytes and metabolites (identical in v5 and v6 unless stated)
for v in B:
    R(v, 'ALB', 'LOW', 1, 'Hypoalbuminemia', '<LLN - 30 g/L', '<', 'LLN', 'LLN')
    R(v, 'ALB', 'LOW', 2, 'Hypoalbuminemia', '<30 - 20 g/L', '<', '30', '3')
    R(v, 'ALB', 'LOW', 3, 'Hypoalbuminemia', '<20 g/L', '<', '20', '2')
    N(v, 'ALB', 'LOW', 4, 'Hypoalbuminemia'); N(v, 'ALB', 'LOW', 5, 'Hypoalbuminemia')
    R(v, 'CACR', 'HIGH', 1, 'Hypercalcemia', 'Corrected serum calcium of >ULN - 11.5 mg/dL; >ULN - 2.9 mmol/L', '>', 'ULN', 'ULN')
    R(v, 'CACR', 'HIGH', 2, 'Hypercalcemia', 'Corrected serum calcium of >11.5 - 12.5 mg/dL; >2.9 - 3.1 mmol/L', '>', '2.9', '11.5')
    R(v, 'CACR', 'HIGH', 3, 'Hypercalcemia', 'Corrected serum calcium of >12.5 - 13.5 mg/dL; >3.1 - 3.4 mmol/L', '>', '3.1', '12.5')
    R(v, 'CACR', 'HIGH', 4, 'Hypercalcemia', 'Corrected serum calcium of >13.5 mg/dL; >3.4 mmol/L', '>', '3.4', '13.5')
    N(v, 'CACR', 'HIGH', 5, 'Hypercalcemia')
    R(v, 'CAION', 'HIGH', 1, 'Hypercalcemia', 'Ionized calcium >ULN - 1.5 mmol/L', '>', 'ULN')
    R(v, 'CAION', 'HIGH', 2, 'Hypercalcemia', 'Ionized calcium >1.5 - 1.6 mmol/L', '>', '1.5')
    R(v, 'CAION', 'HIGH', 3, 'Hypercalcemia', 'Ionized calcium >1.6 - 1.8 mmol/L', '>', '1.6')
    R(v, 'CAION', 'HIGH', 4, 'Hypercalcemia', 'Ionized calcium >1.8 mmol/L', '>', '1.8')
    N(v, 'CAION', 'HIGH', 5, 'Hypercalcemia')
    R(v, 'CACR', 'LOW', 1, 'Hypocalcemia', 'Corrected serum calcium of <LLN - 8.0 mg/dL; <LLN - 2.0 mmol/L', '<', 'LLN', 'LLN')
    R(v, 'CACR', 'LOW', 2, 'Hypocalcemia', 'Corrected serum calcium of <8.0 - 7.0 mg/dL; <2.0 - 1.75 mmol/L', '<', '2.0', '8.0')
    R(v, 'CACR', 'LOW', 3, 'Hypocalcemia', 'Corrected serum calcium of <7.0 - 6.0 mg/dL; <1.75 - 1.5 mmol/L', '<', '1.75', '7.0')
    R(v, 'CACR', 'LOW', 4, 'Hypocalcemia', 'Corrected serum calcium of <6.0 mg/dL; <1.5 mmol/L', '<', '1.5', '6.0')
    N(v, 'CACR', 'LOW', 5, 'Hypocalcemia')
    R(v, 'CAION', 'LOW', 1, 'Hypocalcemia', 'Ionized calcium <LLN - 1.0 mmol/L', '<', 'LLN')
    R(v, 'CAION', 'LOW', 2, 'Hypocalcemia', 'Ionized calcium <1.0 - 0.9 mmol/L', '<', '1.0')
    R(v, 'CAION', 'LOW', 3, 'Hypocalcemia', 'Ionized calcium <0.9 - 0.8 mmol/L', '<', '0.9')
    R(v, 'CAION', 'LOW', 4, 'Hypocalcemia', 'Ionized calcium <0.8 mmol/L', '<', '0.8')
    N(v, 'CAION', 'LOW', 5, 'Hypocalcemia')
    R(v, 'CHOL', 'HIGH', 1, 'Cholesterol high', '>ULN - 300 mg/dL; >ULN - 7.75 mmol/L', '>', 'ULN', 'ULN')
    R(v, 'CHOL', 'HIGH', 2, 'Cholesterol high', '>300 - 400 mg/dL; >7.75 - 10.34 mmol/L', '>', '7.75', '300')
    R(v, 'CHOL', 'HIGH', 3, 'Cholesterol high', '>400 - 500 mg/dL; >10.34 - 12.92 mmol/L', '>', '10.34', '400')
    R(v, 'CHOL', 'HIGH', 4, 'Cholesterol high', '>500 mg/dL; >12.92 mmol/L', '>', '12.92', '500')
    R(v, 'GLUC', 'LOW', 1, 'Hypoglycemia', '<LLN - 55 mg/dL; <LLN - 3.0 mmol/L', '<', 'LLN', 'LLN')
    R(v, 'GLUC', 'LOW', 2, 'Hypoglycemia', '<55 - 40 mg/dL; <3.0 - 2.2 mmol/L', '<', '3.0', '55')
    R(v, 'GLUC', 'LOW', 3, 'Hypoglycemia', '<40 - 30 mg/dL; <2.2 - 1.7 mmol/L', '<', '2.2', '40')
    R(v, 'GLUC', 'LOW', 4, 'Hypoglycemia', '<30 mg/dL; <1.7 mmol/L', '<', '1.7', '30')
    N(v, 'GLUC', 'LOW', 5, 'Hypoglycemia')
    R(v, 'K', 'HIGH', 1, 'Hyperkalemia', '>ULN - 5.5 mmol/L', '>', 'ULN')
    R(v, 'K', 'HIGH', 2, 'Hyperkalemia', '>5.5 - 6.0 mmol/L', '>', '5.5')
    R(v, 'K', 'HIGH', 3, 'Hyperkalemia', '>6.0 - 7.0 mmol/L', '>', '6.0')
    R(v, 'K', 'HIGH', 4, 'Hyperkalemia', '>7.0 mmol/L', '>', '7.0')
    N(v, 'K', 'HIGH', 5, 'Hyperkalemia')
    R(v, 'K', 'LOW', 1, 'Hypokalemia', '<LLN - 3.0 mmol/L', '<', 'LLN')
    R(v, 'K', 'LOW', 2, 'Hypokalemia', 'Symptomatic with <LLN - 3.0 mmol/L', '<', 'LLN', qual='SYMPTOMATIC', conv='CLINICAL_QUALIFIERS', note='Same laboratory range as grade 1; grade 2 needs symptoms')
    R(v, 'K', 'LOW', 3, 'Hypokalemia', '<3.0 - 2.5 mmol/L', '<', '3.0')
    R(v, 'K', 'LOW', 4, 'Hypokalemia', '<2.5 mmol/L', '<', '2.5')
    N(v, 'K', 'LOW', 5, 'Hypokalemia')
    R(v, 'MG', 'HIGH', 1, 'Hypermagnesemia', '>ULN - 3.0 mg/dL; >ULN - 1.23 mmol/L', '>', 'ULN', 'ULN')
    R(v, 'MG', 'HIGH', 3, 'Hypermagnesemia', '>3.0 - 8.0 mg/dL; >1.23 - 3.30 mmol/L', '>', '1.23', '3.0', note='No grade 2 for hypermagnesemia')
    R(v, 'MG', 'HIGH', 4, 'Hypermagnesemia', '>8.0 mg/dL; >3.30 mmol/L', '>', '3.30', '8.0')
    N(v, 'MG', 'HIGH', 5, 'Hypermagnesemia')
    R(v, 'MG', 'LOW', 1, 'Hypomagnesemia', '<LLN - 1.2 mg/dL; <LLN - 0.5 mmol/L', '<', 'LLN', 'LLN')
    R(v, 'MG', 'LOW', 2, 'Hypomagnesemia', '<1.2 - 0.9 mg/dL; <0.5 - 0.4 mmol/L', '<', '0.5', '1.2')
    R(v, 'MG', 'LOW', 3, 'Hypomagnesemia', '<0.9 - 0.7 mg/dL; <0.4 - 0.3 mmol/L', '<', '0.4', '0.9', note='CTCAE pairs 0.9 mg/dL with 0.4 mmol/L although 0.9 mg/dL = 0.37 mmol/L; the SI figure is used as printed')
    R(v, 'MG', 'LOW', 4, 'Hypomagnesemia', '<0.7 mg/dL; <0.3 mmol/L', '<', '0.3', '0.7', note='CTCAE pairs 0.7 mg/dL with 0.3 mmol/L although 0.7 mg/dL = 0.29 mmol/L; the SI figure is used as printed')
    N(v, 'MG', 'LOW', 5, 'Hypomagnesemia')
    R(v, 'SODIUM', 'HIGH', 1, 'Hypernatremia', '>ULN - 150 mmol/L', '>', 'ULN')
    R(v, 'SODIUM', 'HIGH', 2, 'Hypernatremia', '>150 - 155 mmol/L', '>', '150')
    R(v, 'SODIUM', 'HIGH', 3, 'Hypernatremia', '>155 - 160 mmol/L', '>', '155')
    R(v, 'SODIUM', 'HIGH', 4, 'Hypernatremia', '>160 mmol/L', '>', '160')
    N(v, 'SODIUM', 'HIGH', 5, 'Hypernatremia')
    R(v, 'TRIG', 'HIGH', 1, 'Hypertriglyceridemia', '1.71 mmol/L - 3.42 mmol/L', '>=', '1.71', '150', conv='INCLUSIVE_START', note='"150 mg/dL - 300 mg/dL" has no leading ">": inclusive lower bound')
    R(v, 'TRIG', 'HIGH', 2, 'Hypertriglyceridemia', '>3.42 mmol/L - 5.7 mmol/L', '>', '3.42', '300')
    R(v, 'TRIG', 'HIGH', 3, 'Hypertriglyceridemia', '>5.7 mmol/L - 11.4 mmol/L', '>', '5.7', '500')
    R(v, 'TRIG', 'HIGH', 4, 'Hypertriglyceridemia', '>11.4 mmol/L', '>', '11.4', '1000')
    N(v, 'TRIG', 'HIGH', 5, 'Hypertriglyceridemia')
    # ----- sodium LOW differs by version
    if v == 5:
        R(5, 'SODIUM', 'LOW', 1, 'Hyponatremia', '<LLN - 130 mmol/L', '<', 'LLN')
        R(5, 'SODIUM', 'LOW', 2, 'Hyponatremia', '125-129 mmol/L and asymptomatic', '<', '130', qual='ASYMPTOMATIC', conv='INTEGER_RANGE SODIUM_V5_GAP CLINICAL_QUALIFIERS', note='Integer range read as >=125 and <130')
        R(5, 'SODIUM', 'LOW', 3, 'Hyponatremia', '125-129 mmol/L symptomatic', '<', '130', qual='SYMPTOMATIC', conv='INTEGER_RANGE CLINICAL_QUALIFIERS')
        R(5, 'SODIUM', 'LOW', 3, 'Hyponatremia', '120-124 mmol/L regardless of symptoms', '<=', '124', conv='INTEGER_RANGE SODIUM_V5_GAP', note='Literal upper bound 124: 124.5 mmol/L is grade 2 (convention SODIUM_V5_GAP)')
        R(5, 'SODIUM', 'LOW', 4, 'Hyponatremia', '<120 mmol/L', '<', '120')
        N(5, 'SODIUM', 'LOW', 5, 'Hyponatremia')
    else:
        R(6, 'SODIUM', 'LOW', 1, 'Hyponatremia', '<LLN - 130 mmol/L', '<', 'LLN')
        R(6, 'SODIUM', 'LOW', 2, 'Hyponatremia', '125 - <130 mmol/L and asymptomatic', '<', '130', qual='ASYMPTOMATIC', conv='CLINICAL_QUALIFIERS')
        R(6, 'SODIUM', 'LOW', 3, 'Hyponatremia', '125 - <130 mmol/L symptomatic', '<', '130', qual='SYMPTOMATIC', conv='CLINICAL_QUALIFIERS')
        R(6, 'SODIUM', 'LOW', 3, 'Hyponatremia', '120 - <125 mmol/L regardless of symptoms', '<', '125')
        R(6, 'SODIUM', 'LOW', 4, 'Hyponatremia', '<120 mmol/L', '<', '120')
        N(6, 'SODIUM', 'LOW', 5, 'Hyponatremia')
# ============================================================================ glucose HIGH
R(5, 'GLUC', 'HIGH', 1, 'Hyperglycemia', 'Abnormal glucose above baseline with no medical intervention', '>', 'ULN', cond='VALUE>BASE', qual='NO_INTERVENTION',
  conv='HYPERGLY_V5_LABONLY ABOVE_BASELINE_WAIVED CLINICAL_QUALIFIERS', note='v5 removed the numeric thresholds: "abnormal" read as >ULN, "above baseline" as >baseline')
for g in (2, 3, 4, 5): N(5, 'GLUC', 'HIGH', g, 'Hyperglycemia', conv='HYPERGLY_V5_LABONLY')
R(6, 'GLUC', 'HIGH', 1, 'Hyperglycemia', 'Fasting glucose value >ULN - 8.9 mmol/L', '>', 'ULN', 'ULN', conv='FASTING_NOT_EVALUATED')
R(6, 'GLUC', 'HIGH', 2, 'Hyperglycemia', 'Fasting glucose value >8.9 - 13.9 mmol/L', '>', '8.9', '160', conv='FASTING_NOT_EVALUATED')
R(6, 'GLUC', 'HIGH', 3, 'Hyperglycemia', '>250 - 500 mg/dL; >13.9 - 27.8 mmol/L', '>', '13.9', '250')
R(6, 'GLUC', 'HIGH', 4, 'Hyperglycemia', '>500 mg/dL; >27.8 mmol/L', '>', '27.8', '500')
# ============================================================================ creatinine
R(5, 'CREAT', 'HIGH', 1, 'Creatinine increased', '>ULN - 1.5 x ULN', '>', 'ULN')
R(5, 'CREAT', 'HIGH', 2, 'Creatinine increased', '>1.5 - 3.0 x baseline', '>', '1.5*BASE', conv='CREAT_BASELINE_ARM', note='Applies whatever the baseline (convention CREAT_BASELINE_ARM)')
R(5, 'CREAT', 'HIGH', 2, 'Creatinine increased', '>1.5 - 3.0 x ULN', '>', '1.5*ULN')
R(5, 'CREAT', 'HIGH', 3, 'Creatinine increased', '>3.0 x baseline', '>', '3*BASE', conv='CREAT_BASELINE_ARM')
R(5, 'CREAT', 'HIGH', 3, 'Creatinine increased', '>3.0 - 6.0 x ULN', '>', '3*ULN')
R(5, 'CREAT', 'HIGH', 4, 'Creatinine increased', '>6.0 x ULN', '>', '6*ULN')
R(6, 'CREAT', 'HIGH', 1, 'Creatinine increased', '>ULN - 1.5 x ULN', '>', 'ULN')
R(6, 'CREAT', 'HIGH', 2, 'Creatinine increased', '>1.5 - 3.0 x baseline if baseline is below LLN', '>', '1.5*BASE', arm='BELOW_LLN', conv='CREAT_BASELINE_ARM ' + BAD)
R(6, 'CREAT', 'HIGH', 2, 'Creatinine increased', '>1.5 - 3.0 x ULN', '>', '1.5*ULN')
R(6, 'CREAT', 'HIGH', 3, 'Creatinine increased', '>3.0 x baseline if baseline is below LLN', '>', '3*BASE', arm='BELOW_LLN', conv='CREAT_BASELINE_ARM ' + BAD)
R(6, 'CREAT', 'HIGH', 3, 'Creatinine increased', '>3.0 - 6.0 x ULN', '>', '3*ULN')
R(6, 'CREAT', 'HIGH', 4, 'Creatinine increased', '>6.0 x ULN', '>', '6*ULN')
# ============================================================================ kidney function
CKD = 'Chronic kidney disease'
for v, tests in ((5, ('GFRBSCRT', 'GFR', 'CREATCLR')), (6, ('GFRBSCRT', 'GFR'))):
    for t in tests:
        cv = 'CKD_EGFR_ONLY' + (' CREATCLR_TERM_BY_VERSION' if t == 'CREATCLR' else '')
        nt = 'Thresholds stated per 1.73 m2 applied to the reported clearance in mL/min (convention CREATCLR_TERM_BY_VERSION)' if t == 'CREATCLR' else ''
        R(v, t, 'LOW', 1, CKD, 'eGFR (estimated Glomerular Filtration Rate) or CrCl (creatinine clearance) <LLN - 60 ml/min/1.73 m2', '<', 'LLN', conv=cv, note=nt)
        N(v, t, 'LOW', 1, CKD, 'or proteinuria 2+ present; urine protein/creatinine >0.5', conv='CKD_EGFR_ONLY')
        if v == 5:
            R(5, t, 'LOW', 2, CKD, 'eGFR or CrCl 59 - 30 ml/min/1.73 m2', '<', '60', conv=cv + ' INTEGER_RANGE', note='Integer range read as <60 and >=30')
            R(5, t, 'LOW', 3, CKD, 'eGFR or CrCl 29 - 15 ml/min/1.73 m2', '<', '30', conv=cv + ' INTEGER_RANGE', note='Integer range read as <30 and >=15')
        else:
            R(6, t, 'LOW', 2, CKD, 'eGFR or CrCl <60 - 30 ml/min/1.73 m2', '<', '60', conv=cv)
            R(6, t, 'LOW', 3, CKD, 'eGFR or CrCl <30 - 15 ml/min/1.73 m2', '<', '30', conv=cv)
        R(v, t, 'LOW', 4, CKD, 'eGFR or CrCl <15 ml/min/1.73 m2', '<', '15', conv=cv, note='"; dialysis or renal transplant indicated" is a clinical alternative')
        N(v, t, 'LOW', 5, CKD)
CCD = 'Creatinine clearance decreased'
R(6, 'CREATCLR', 'LOW', 2, CCD, '26 - 49 ml/min', '<', '50', conv='INTEGER_RANGE CREATCLR_TERM_BY_VERSION', note='Integer range read as <50 and >=26; no grade 1')
R(6, 'CREATCLR', 'LOW', 3, CCD, '10 - 25 ml/min', '<', '26', conv='INTEGER_RANGE CRCL_V6_BELOW_RANGE CREATCLR_TERM_BY_VERSION', note='Integer range read as <26; values <10 mL/min stay grade 3 (grades 4-5 are reported as acute kidney injury or chronic kidney disease)')
# ============================================================================ haematology counts
def counts(ver, test, term, items):
    for g, cl, thr, conv_thr, extra in items:
        if cl == 'LLN':
            pass
        R(ver, test, 'LOW', g, term, cl, '<', thr, conv_thr, note=extra)
for v, e in ((5, 'e'), (6, '^')):
    x = '10e9 /L' if v == 5 else '10^9/L'
    anem = 'Anemia'
    R(v, 'HGB', 'LOW', 1, anem, '<LLN - 100 g/L', '<', 'LLN', 'LLN', note='Also written "<LLN - 10.0 g/dL; <LLN - 6.2 mmol/L"')
    R(v, 'HGB', 'LOW', 2, anem, '<100 - 80g/L' if v == 5 else '<100 - 80 g/L', '<', '100', '10.0', note='Also written "<10.0 - 8.0 g/dL; <6.2 - 4.9 mmol/L"')
    R(v, 'HGB', 'LOW', 3, anem, '<80 g/L', '<', '80', '8.0', note='Also written "<8.0 g/dL; <4.9 mmol/L"; "; transfusion indicated" is a clinical alternative')
    N(v, 'HGB', 'LOW', 4, anem); N(v, 'HGB', 'LOW', 5, anem)
    sfx = '' if v == 5 else ' above ULN'
    op = 'EXCESS_BASE_OR_ULN' if v == 5 else 'EXCESS_ULN'
    hn = 'Increase measured above the baseline when the baseline is >ULN, otherwise above ULN (convention HGB_INCREASE_REF)' if v == 5 else 'Increase measured above ULN'
    R(v, 'HGB', 'HIGH', 1, 'Hemoglobin increased', 'Increase in >0 - 2 g/dL' + sfx, '>', '0', '0', operand=op, conv='HGB_INCREASE_REF', note=hn)
    R(v, 'HGB', 'HIGH', 2, 'Hemoglobin increased', 'Increase in >2 - 4 g/dL' + sfx, '>', '20', '2', operand=op, conv='HGB_INCREASE_REF')
    R(v, 'HGB', 'HIGH', 3, 'Hemoglobin increased', 'Increase in >4 g/dL' + sfx, '>', '40', '4', operand=op, conv='HGB_INCREASE_REF')
    wbc = 'White blood cell decreased'
    R(v, 'WBC', 'LOW', 1, wbc, f'<LLN - 3.0 x {x}', '<', 'LLN', 'LLN')
    R(v, 'WBC', 'LOW', 2, wbc, f'<3.0 - 2.0 x {x}', '<', '3.0', '3000')
    R(v, 'WBC', 'LOW', 3, wbc, f'<2.0 - 1.0 x {x}', '<', '2.0', '2000')
    R(v, 'WBC', 'LOW', 4, wbc, f'<1.0 x {x}', '<', '1.0', '1000')
    cd4 = 'CD4 lymphocytes decreased'
    R(v, 'CD4', 'LOW', 1, cd4, f'<LLN - 0.5 x {x}', '<', 'LLN', 'LLN')
    R(v, 'CD4', 'LOW', 2, cd4, f'<0.5 - 0.2 x {x}', '<', '0.5', '500')
    R(v, 'CD4', 'LOW', 3, cd4, '<0.2 x 0.05 - 10e9 /L' if v == 5 else '<0.2 - 0.05 x 10^9/L', '<', '0.2', '200',
      note='Source PDF reads "<0.2 x 0.05 - 10e9 /L" (transposed symbols); read as <0.2 - 0.05 x 10^9/L, consistent with "<200 - 50/mm3"' if v == 5 else '')
    R(v, 'CD4', 'LOW', 4, cd4, f'<0.05 x {x}', '<', '0.05', '50')
    if v == 5:
        R(5, 'LYM', 'LOW', 1, 'Lymphocyte count decreased', '<LLN - 0.8 x 10e9/L', '<', 'LLN', 'LLN')
        R(5, 'LYM', 'LOW', 2, 'Lymphocyte count decreased', '<0.8 - 0.5 x 10e9 /L', '<', '0.8', '800')
        R(5, 'LYM', 'LOW', 3, 'Lymphocyte count decreased', '<0.5 - 0.2 x 10e9 /L', '<', '0.5', '500')
        R(5, 'LYM', 'LOW', 4, 'Lymphocyte count decreased', '<0.2 x 10e9 /L', '<', '0.2', '200')
        nd = 'Neutrophil count decreased'
        R(5, 'NEUT', 'LOW', 1, nd, '<LLN - 1.5 x 10e9 /L', '<', 'LLN', 'LLN')
        R(5, 'NEUT', 'LOW', 2, nd, '<1.5 - 1.0 x 10e9 /L', '<', '1.5', '1500')
        R(5, 'NEUT', 'LOW', 3, nd, '<1.0 - 0.5 x 10e9 /L', '<', '1.0', '1000')
        R(5, 'NEUT', 'LOW', 4, nd, '<0.5 x 10e9 /L', '<', '0.5', '500')
        pd_ = 'Platelet count decreased'
        R(5, 'PLAT', 'LOW', 1, pd_, '<LLN - 75.0 x 10e9 /L', '<', 'LLN', 'LLN')
        R(5, 'PLAT', 'LOW', 2, pd_, '<75.0 - 50.0 x 10e9 /L', '<', '75', '75000')
        R(5, 'PLAT', 'LOW', 3, pd_, '<50.0 - 25.0 x 10e9 /L', '<', '50', '50000')
        R(5, 'PLAT', 'LOW', 4, pd_, '<25.0 x 10e9 /L', '<', '25', '25000')
    else:
        nd = 'Neutrophil count decreased'
        R(6, 'NEUT', 'LOW', 1, nd, '<1.5 - 1.0 x 10^9/L', '<', '1.5', '1500', note='v6 grade 1 no longer refers to LLN')
        R(6, 'NEUT', 'LOW', 2, nd, '<1.0 - 0.5 x 10^9/L', '<', '1.0', '1000')
        R(6, 'NEUT', 'LOW', 3, nd, '<0.5 - 0.1 x 10^9/L', '<', '0.5', '500')
        R(6, 'NEUT', 'LOW', 4, nd, '<0.1 x 10^9/L', '<', '0.1', '100')
        th = 'Thrombocytopenia'
        R(6, 'PLAT', 'LOW', 1, th, '<LLN - 75.0 x 10^9/L', '<', 'LLN', 'LLN')
        R(6, 'PLAT', 'LOW', 2, th, '<75.0 - 50.0 x 10^9/L', '<', '75', '75000')
        R(6, 'PLAT', 'LOW', 3, th, '<50.0 - 10.0 x 10^9/L', '<', '50', '50000', note='"; transfusion indicated" is a clinical alternative')
        R(6, 'PLAT', 'LOW', 4, th, '<10.0 x 10^9/L', '<', '10', '10000')
        N(6, 'PLAT', 'LOW', 5, th)
# ============================================================================ urinary protein
PU = 'PROTEINURIA_24H'
R(5, 'PROTEXR', 'HIGH', 1, 'Proteinuria', 'urinary protein ≥ULN - <1.0 g/24 hrs', '>=', 'ULN', 'ULN', conv=PU)
N(5, 'PROTEXR', 'HIGH', 1, 'Proteinuria', '1+ proteinuria', conv=PU, note='Dipstick result, not the 24-hour excretion')
R(5, 'PROTEXR', 'HIGH', 2, 'Proteinuria', 'urinary protein 1.0 - <3.5 g/24 hrs', '>=', '1000', '1.0', conv=PU + ' INCLUSIVE_START')
N(5, 'PROTEXR', 'HIGH', 2, 'Proteinuria', 'Adult: 2+ and 3+ proteinuria | Pediatric: Urine P/C (Protein/Creatinine) ratio 0.5 - 1.9', conv=PU, note='Dipstick and protein/creatinine ratio, not the 24-hour excretion')
R(5, 'PROTEXR', 'HIGH', 3, 'Proteinuria', 'Urinary protein >=3.5 g/24 hrs', '>=', '3500', '3.5', conv=PU)
N(5, 'PROTEXR', 'HIGH', 3, 'Proteinuria', '4+ proteinuria | Pediatric: Urine P/C (Protein/Creatinine) ratio >1.9', conv=PU, note='Dipstick and protein/creatinine ratio, not the 24-hour excretion')
UP = 'Urinary protein increased'
R(6, 'PROTEXR', 'HIGH', 1, UP, 'urinary protein ≥ULN - <1.0 g/24 hrs', '>=', 'ULN', 'ULN', conv=PU)
N(6, 'PROTEXR', 'HIGH', 1, UP, 'Adult: 1+ proteinuria | P/C <1 | Pediatric: 1 + proteinuria', conv=PU, note='Dipstick and protein/creatinine ratio, not the 24-hour excretion')
R(6, 'PROTEXR', 'HIGH', 2, UP, 'urinary protein 1.0 - <3.5 g/24 hrs', '>=', '1000', '1.0', conv=PU + ' INCLUSIVE_START')
N(6, 'PROTEXR', 'HIGH', 2, UP, 'Adult: 2+ and 3+ proteinuria | P/C 1 - 3.5 | Pediatric: Urine P/C (Protein/Creatinine) ratio 0.5 - 1.9; 2 - 3+ proteinuria', conv=PU, note='Dipstick and protein/creatinine ratio, not the 24-hour excretion')
R(6, 'PROTEXR', 'HIGH', 3, UP, 'Urinary protein >=3.5 g/24 hrs', '>=', '3500', '3.5', conv=PU)
N(6, 'PROTEXR', 'HIGH', 3, UP, '4+ proteinuria | P/C >3.5 | Pediatric: Urine P/C (Protein/Creatinine) ratio >1.9, 4+ proteinuria', conv=PU, note='Dipstick and protein/creatinine ratio, not the 24-hour excretion')
# ============================================================================ write
order = {'HIGH': 0, 'LOW': 1}
arms = {'ANY': 0, 'NORMAL': 1, 'ABNORMAL': 2, 'BELOW_LLN': 3}
rows.sort(key=lambda r: (r['VERSION'], r['LBTESTCD'], order[r['DIRECTION']], arms[r['BASELINE_ARM']], r['GRADE'], r['CLAUSE_SEQ']))
with open(os.path.join(OUT, 'criteria.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=COLS, lineterminator='\n'); w.writeheader()
    for r in rows: w.writerow(r)
print(f'rows: {len(rows)}  lab-derivable: {sum(r["LAB_DERIVABLE"]=="Y" for r in rows)}  v5: {sum(r["VERSION"]==5 for r in rows)}  v6: {sum(r["VERSION"]==6 for r in rows)}')
print(f'distinct RULE_IDs: {len(seq)}  terms: {len(set((r["VERSION"], r["CTCAE_TERM"]) for r in rows))}')
if errors:
    print(f'\n{len(errors)} CLAUSE ERROR(S):'); [print(' -', e) for e in errors]; sys.exit(1)
print('all clauses are verbatim fragments of their cells')
