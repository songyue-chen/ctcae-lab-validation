# Changelog

The dataset follows semantic versioning. A change of an expected value is a minor release when it follows a
documented change of `data/criteria.csv` or `data/conventions.csv`, a major release when it changes the record keys
or the column layout. Added records are a minor release.

## Unreleased

- Documentation: `docs/review-guide.md` with the questions for clinical, laboratory and programming
  reviewers; README note for clinical reviewers and an Acknowledgements section. Reviewers are named only with their
  consent (CONTRIBUTING.md).
- Repository: branch `main` holds the dataset package, branch `full` the complete package with the reference code,
  the generator and the contributor documents; both are assembled by `generator/release.py` (`--full`).
- Reference code: the comparators no longer keep STATUS, which the SDTM naming renames (a comparison after an SDTM
  load failed); the SAS comparator and loader count observations with `if 0 then set ... nobs=` (the previous idiom
  left the count blank on an empty dataset and stopped the macro); self-check 7b added in SAS and R.

## 1.0.0 (2026-10-15)

First release.

- CTCAE v5.0 (27-Nov-2017) and v6.0 (22-Jul-2025) laboratory criteria transcribed clause by clause into
  `data/criteria.csv` (458 rows, 371 lab-derivable clauses, 429 rule identifiers), with the verbatim wording of
  every grade cell.
- 1,057 records in 118 subjects over 44 tests (`data/records.csv`), 6,813 expectation rows
  (`data/expectations.csv`): DEFAULT profile plus BESTCASE_ENZYMES, HYPERGLY_NUMERIC_V5, PRESENT_NOT_LAB,
  UNGRADABLE_ZERO and BASELINE_STRICT for the records they change.
- Modules CORE, BASELINE, MISSING, NOTDONE, UNITS, CATEGORY; every coverable lab-derivable rule exercised.
- CDISC SDTM controlled terminology for test codes, names, specimens and units; SI and conventional views on every
  record; ADaM and SDTM naming through the loaders.
- Reference loaders, comparators, self-checks and mapping templates for SAS and R; results template.
- Generator and quality gate in Python (schema validation, criteria audit, independent re-simulation of every
  expected grade, monotonicity, coverage).

Roadmap: CTCAE v4.03 transcription (1.1), further profiles on request.
