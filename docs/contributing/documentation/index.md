# Working on the documentation

The [documentation standard](../standards/documentation.md) sets the rules for every page under
`docs/`: the readers, the four page types, where a page lives and how it is written. This section
covers only how to work on this repository's documentation: building it, checking it and linking
within it.

## Build the documentation

Build the HTML once, treating warnings as errors:

```bash
uv run sphinx-build -W --keep-going -b html docs docs/_build/html
```

Serve it and rebuild on every save:

```bash
uv run sphinx-autobuild docs docs/_build/html
```

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
