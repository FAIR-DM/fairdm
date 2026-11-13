# Research: download a record's citation as BibTeX or RIS

## Assumptions checked

Run against `main` at `2267f6e0` while the specification was written.

| What the specification assumes | Result |
|---|---|
| Each of the four overview pages writes the record's text citation, with a note when it points at the permalink | Holds. `get_citation_details` on the project, dataset, sample and measurement overview plugins, with `get_citation` in `fairdm/core/plugins.py`. The 32 existing citation tests under `tests/test_core` and `tests/test_templates` pass |
| The parts of the text citation (people, year, title, publisher, link) can be had apart from the text, so the formats need not parse it | Holds. Each `get_citation_details` gathers them before calling `get_citation`. The build exposes them rather than the text alone |
| A record with no DOI or IGSN is cited by its permalink | Holds. Every plugin calls `get_permalink` from `fairdm/views/permalink.py` (specification 034) |
| A dataset with a data publication is cited as that publication | Holds. `Dataset.reference`, a one-to-one link to a literature item, and the dataset plugin uses `str(reference)` as the text. The publication's own people and type are on the literature item, which the build reads for D2 |
| The Cite panel with its format switch exists in `main` | Does not hold yet. It arrives with the first pull request for #672, which the issue names as its dependency |
| A package already installed writes BibTeX or RIS | Not as a runtime dependency. `pybtex` is in the lock file for the documentation build only, and neither `citeproc-py` nor `rispy` is installed. The search before new code is the build's (planning note N6) |
