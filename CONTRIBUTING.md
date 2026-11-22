# Contributing

## Reviewing the dataset

`docs/review-guide.md` lists the questions for clinical, laboratory and programming reviewers. Answer them in
issues, one per question or finding.

## Disputing an expected value

Open an issue with the "Dispute an expectation" template. It asks for the `RECORD_ID` or `SCENARIO_ID`, the
CTCAE version and profile, the grade or term you expect instead, the `RULE_ID` of the criteria row concerned and the
CTCAE wording quoted verbatim with its page. An expectation never changes on the strength of another
implementation's output: the quoted wording decides, and where the wording leaves a choice the dispute becomes a
convention (`data/conventions.csv`) with, when both readings are defensible, an alternative profile.

## Changing expected values

Expected values are never edited by hand. They change only through:

1. a row of `data/criteria.csv` (comparator, threshold, qualifier, condition, arm) or `data/conventions.csv`
   (default or alternative choice), with the CTCAE wording quoted in the row and the change described in
   `CHANGELOG.md`;
2. `python3 generator/gen_records.py`, which regenerates `data/records.csv` and `data/expectations.csv`;
3. `python3 generator/qc.py`, which must print PASS (schema validation, criteria audit, independent re-simulation
   of every expected grade, monotonicity, rule coverage);
4. `python3 generator/build_docs.py`, which regenerates `docs/data_dictionary.md`, `docs/conventions.md` and
   `docs/coverage.md`.

CI runs the same three scripts and fails when a committed file differs from the regenerated one, so commit the
regenerated outputs together with the table change.

5. `python3 generator/release.py --out <release repository>` assembles the user package (records.csv, records.xpt,
   dictionary.md, README.md, LICENSE) from `data/records.csv` and `release/`; `Rscript generator/check_xpt.R <release
   repository>` reads the transport file back and compares every value. Commit the package in the release repository:
   on branch `main` the dataset package, on branch `full` the complete package (`python3 generator/release.py --out
   <release repository> --full`, run with that branch checked out). The dataset files must stay identical on both.

## Adding records or scenarios

Boundary records are derived from the criteria: a new subject in `generator/gen_records.py` (`SUBJECTS`) receives
every threshold of its applicable rules automatically. Edge, unit and specimen scenarios are explicit records in
`edge_subjects()`. Keep descriptions free of `;`, `|` and macro triggers (`%name`, `&name`), the generator checks it.

## Conventions of the repository

- Test codes, names, specimens and units are CDISC SDTM submission values; a code outside the codelists is flagged
  `CDISC_CT = N` in `data/analytes.csv` with a note.
- Contributions are attributed through the version history. Reviewers are named in the README Acknowledgements
  (name, role, area reviewed) only with their written consent; no other document carries personal names.
- Python 3.11 or later with the standard library only; base R for the R reference code; SAS 9.4 for the SAS
  reference code. The SAS programs cannot be executed by CI: `reference/sas/selfcheck.sas` is the self-check to run
  in a SAS session after a change to the SAS files.
- Versioning: see `CHANGELOG.md`.
