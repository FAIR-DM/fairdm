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

The site at <https://docs.fairdm.org/> is served from the `gh-pages` branch, which holds one folder
per version:

| Folder | Built from | Published |
| --- | --- | --- |
| `latest/` | `main` | on every push to `main` |
| `0.4/` | the newest `v0.4.x` tag | when a release is published |

The address of the site redirects to `latest/`. Each build replaces its own folder and leaves the
others alone, and a patch release replaces the folder of its minor version. A release also adds its
version to `switcher.json`, the list behind the version switcher in the site's header.

To publish a release that is already out, run the **Documentation** workflow by hand and give it
the tag:

```bash
gh workflow run docs.yml -f tag=v0.4.0
```

A build that fails on a warning publishes nothing, so that version stays at the last build that
passed. Link to pages under `latest/`, so a link keeps working as releases come out.

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
