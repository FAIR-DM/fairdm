# Documenting features

This page is for contributors who change FairDM and need to know what to document. Where a page
lives, which type it is and how it is written are set by the
[documentation standard](standards/documentation.md). This page covers only how a change maps onto
the pages.

## Document a change

1. Find the readers the change affects. Each reader is a section of `docs/`: `developers/`,
   `administrators/` or `users/`.
2. For each reader, pick the page whose type matches what the change needs, as the standard
   describes:
   - a new thing to do gets a how-to guide,
   - a new setting, component, template tag or command gets an entry on its reference page,
   - a new idea a reader must understand gets an explanation.
3. Link to the new or changed page from the pages that mention the subject. Do not repeat it
   there.
4. Describe the current release only. Record what changed, and the steps to upgrade, in the
   `CHANGELOG.md` entry for the release, not on the page.
5. Build the documentation and fix every warning, as [validation rules](documentation/validation-rules.md)
   describes:

   ```bash
   uv run sphinx-build -W --keep-going -b html docs docs/_build/html
   ```

6. Name the pages you changed in your pull request description, so a reviewer can check the
   coverage.

## Add a setting

Add its entry to the settings reference, `docs/developers/reference/settings.md`, and link to the
entry from any page that mentions it. A public setting with no entry is a defect.

## Related

- [Documentation standard](standards/documentation.md)
- [Cross-references](documentation/cross-references.md)
- [Validation rules](documentation/validation-rules.md)
