# Review guide

This dataset gives the CTCAE grade a correct program should assign to each of 1,057 synthetic lab results, under
CTCAE v5.0 and v6.0. Most expected grades follow directly from the CTCAE thresholds. Some do not: where the CTCAE
wording leaves room, or needs information a lab result does not carry (symptoms, treatment, fasting), the dataset
has to choose a reading. Those choices are what we ask you to review. You do not need to run any code.

Each question below names the convention it belongs to. The full wording, the default reading and the alternative
are in [conventions.md](conventions.md) under that name. Please answer in your own words: agree, disagree, or "it
depends on", and why.

## For oncologists and drug safety physicians

1. **Symptoms and interventions are unknown** (CLINICAL_QUALIFIERS). A lab result does not say whether the patient
   had symptoms, received treatment or was on anticoagulation. The dataset assumes no symptoms, no intervention and
   no anticoagulation. Example: sodium 127 mmol/L is v5 grade 2 ("125-129 mmol/L and asymptomatic"), never grade 3;
   potassium below LLN down to 3.0 mmol/L is grade 1, not the symptomatic grade 2. Is assuming the patient is
   asymptomatic the right default for a lab-only grade?

2. **Amylase and lipase** (ENZYME_SYMPTOM_WORST). Here the grade also depends on symptoms, but the dataset takes the
   opposite default: worst case. Amylase above 5 x ULN is grade 4, above 2 x ULN is grade 3. The alternative (no
   symptoms) gives grade 3 above 5 x ULN and never grade 4. Should enzymes be treated differently from question 1,
   and which default would you expect in a safety table?

3. **"Present" in v6 lymphopenia and neutrophil count increased** (PRESENT_AS_LIMIT). v6 grade 1 says only
   "Present". The dataset reads it as lymphocytes below LLN and neutrophils above ULN. The alternative is that
   "Present" is a clinical judgement and no lab-only grade can be given. Which reading do you use?

4. **v5 hyperglycemia** (HYPERGLY_V5_LABONLY). v5 grades hyperglycemia by treatment, not by glucose value. The
   dataset gives grade 1 when glucose is above ULN and above baseline, and never a higher grade from lab data. The
   alternative applies the numeric thresholds of v4.03 and v6 under v5 as well. Is grade 1 as the ceiling sensible?

5. **v6 fasting glucose** (FASTING_NOT_EVALUATED). v6 grades 1 and 2 refer to fasting glucose. The dataset has no
   fasting flag and grades every glucose result as if fasting. Would you restrict grades 1 and 2 to fasting samples?

6. **What counts as an abnormal baseline** (BASELINE_ABNORMAL_DEF). Liver tests, creatinine and fibrinogen grade
   differently when the baseline was abnormal. The dataset calls a baseline abnormal when it is outside its own
   normal range in the direction being graded (above ULN for ALT, below LLN for fibrinogen). Does that match your
   understanding of "if baseline was abnormal"?

7. **v5 creatinine and baseline** (CREAT_BASELINE_ARM). v5 lists "1.5 - 3.0 x baseline" next to "1.5 - 3.0 x ULN"
   without saying when the baseline clause applies. The dataset applies it whatever the baseline, so creatinine that
   doubles from a low baseline can be grade 2 while still inside the normal range. v6 limits the baseline clause to
   a baseline below LLN. Should v5 be read the same way?

8. **Fibrinogen with an abnormal baseline** (FIBRINOGEN_ARMS). With a baseline below LLN, the percent-decrease
   clauses apply: any decrease is grade 1, 25% grade 2, 50% grade 3, 75% grade 4, and below 0.5 g/L is always grade
   4. Is that how you read the "if abnormal" clauses?

9. **Hemoglobin increased** (HGB_INCREASE_REF). v5 says "Increase in >0 - 2 g/dL" without saying increase above
   what. The dataset measures it above ULN, or above the baseline when the baseline was already above ULN. v6 says
   "above ULN" outright. Do you agree for v5?

10. **Kidney function** (CRCL_V6_BELOW_RANGE, CREATCLR_TERM_BY_VERSION). v6 creatinine clearance decreased stops
    at grade 3 ("10 - 25 ml/min") and sends grades 4 and 5 to acute or chronic kidney disease. The dataset grades
    values below 10 mL/min as grade 3. Under v5, creatinine clearance is graded with chronic kidney disease. Are both
    acceptable for a lab-only grade?

11. **Phosphate** (PHOS_LABONLY). Grade 1 is "laboratory finding only"; higher grades are clinical. The dataset gives
    grade 1 when phosphate is outside the normal range and never more. Agree?

## For laboratory medicine and clinical chemistry

12. **Normal ranges** (`data/analytes.csv`, columns LLN_SI and ULN_SI). The default ranges are the adult ranges of
    the ABIM Laboratory Test Reference Ranges (January 2026), converted to SI: the female range where ABIM gives two,
    0 as the lower limit where only an upper limit is given. INR is from MedlinePlus, GFR from the KDIGO G1 category.
    Do any look wrong for an adult reference population?

13. **Unit conversions** (`data/units.csv`). Each row is a factor from a reported unit to the SI unit used for
    grading. Are the factors right, and are common reported units missing?

14. **Units the dataset refuses to grade** (UNIT_GUARD). An unknown or blank unit makes a result not gradable when
    the criterion is an absolute value (for example potassium in mmol/L), but is accepted when the criterion is a
    multiple of ULN (for example ALT). Is that the right line to draw?

## For statistical programmers

Run your grading program against the dataset as the README describes, and tell us which records disagree with it
and why. A disagreement is either a bug in the program, a different reading of the wording (then it belongs to one
of the questions above), or an error in the dataset.

## How to respond

Open an issue on the repository, one per question or per finding, quoting the question number or convention name.
To dispute a specific expected grade, use the "Dispute an expectation" issue template, which asks for the record
and the CTCAE wording. Replies by message to the person who invited you are welcome too.

Reviewers who agree to be named are listed in the Acknowledgements of the README, with the area they reviewed.
Nobody is named without their consent.
