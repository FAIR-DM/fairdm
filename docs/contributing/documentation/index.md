# Working on the documentation

The [documentation standard](../standards/documentation.md) sets the rules for every page under
`docs/`: the readers, the four page types, where a page lives and how it is written. This section
covers only how to work on this repository's documentation: building it, checking it and linking
within it.

## Build the documentation

Install the documentation dependencies, then build the HTML once, treating warnings as errors:

```bash
uv sync --group docs
uv run sphinx-build -W --keep-going -b html docs docs/_build/html
```

Serve it and rebuild on every save:

```bash
uv run sphinx-autobuild docs docs/_build/html
```

## Publishing

Every push to `main` builds the documentation with the commands above and publishes it to
<https://docs.fairdm.org/>. The site shows `main` as it stands, with no older versions. A build
that fails on a warning publishes nothing, so the site stays at the last build that passed.

## In this section

- [Cross-references](cross-references.md) covers the syntax for linking between pages, to decision
  records and to the maintainers' material.
- [Validation rules](validation-rules.md) covers what the build and the link check report and how
  to fix it.

```{toctree}
:hidden:

cross-references
validation-rules
```
