# generator/tools - provenance of the published tables

`data/criteria.csv`, `data/analytes.csv`, `data/units.csv` and `data/conventions.csv` are the
artefacts; they are edited directly and checked by `generator/qc.py`. The scripts here record how
they were first produced from the CTCAE PDFs and the CDISC terminology, so the transcription can
be repeated or audited.

1. `pdftotext -tsv <CTCAE pdf> <version>.tsv` (poppler) gives one word per line with its bounding box.
2. `extract_ctcae_cells.py v5|v6 <version>.tsv ctcae_lab_terms.txt <version>_cells.json` assigns every
   word of a term block to its grade column by x coordinate (the v5 quick reference has the term in a
   first column and five grade columns; v6 prints a "Grade 1 ... Grade 5" header per term) and writes
   the verbatim cell text with the page number.
3. `build_tables.py <data dir>` writes analytes.csv, units.csv and conventions.csv.
4. `build_criteria.py <dir with the two *_cells.json> <data dir>` writes criteria.csv (the extracted cells are kept
   here as `v5_cells.json` and `v6_cells.json`, so `python3 generator/tools/build_criteria.py generator/tools data`
   regenerates the table without the PDFs); every CLAUSE must
   be a verbatim fragment of the extracted cell or the script stops. Two cells are transcribed by hand
   from the layout text because the word boxes overlapped (v5 White blood cell decreased, v6
   Thrombocytopenia grade 4); both are marked in the script.

Sources: CTCAE v5.0 Quick Reference (NCI, 27-Nov-2017, 155 pages) and CTCAE v6.0 (NCI, 22-Jul-2025,
PDF dated 20-Jan-2026, 312 pages); SDTM Terminology (NCI EVS, file dated 25-Sep-2026) for codelists
C65047 (LBTESTCD), C67154 (LBTEST), C78734 (SPECTYPE), C71620 (UNIT). LOINC cross-references were
checked against the NLM Clinical Table Search Service copy of the LOINC table.
Default normal ranges (`analytes.csv` LLN_SI, ULN_SI) are the adult reference ranges of the ABIM Laboratory
Test Reference Ranges (American Board of Internal Medicine, January 2026), converted to SI with the factors of
`units.csv` and rounded to the reporting precision; the female range where ABIM gives two, 0 as LLN where ABIM gives
an upper limit only. INR 0.8 - 1.1 and the 24-hour urine creatinine and potassium ranges are from the MedlinePlus
Medical Encyclopedia (US National Library of Medicine); GFR and eGFR >= 90 mL/min/1.73 m2 is the KDIGO normal
category G1. Every record carries its own range, so an adopter's ranges can replace them.
