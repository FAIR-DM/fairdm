---
name: fairdm-documentation
description: >-
  Create and maintain documentation for the FairDM project. Use when asked to write, update,
  or review documentation pages, guides, tutorials, or reference material for any FairDM
  audience. Covers all four documentation sections: user-guide (portal users/data contributors),
  portal-development (portal builders), portal-administration (admins/staff), and contributing
  (framework contributors). Handles MyST Markdown syntax, sphinx-design components (grids, cards,
  tabs), sphinxcontrib-bibtex citations, admonitions, cross-references to specs/constitution,
  toctree management, and documentation validation. Also use when discussing FAIR data principles
  and needing to back up claims with genuine academic citations.
---

# FairDM Documentation

## Quick Reference

| Audience | Directory | Shorthand |
|----------|-----------|-----------|
| Portal users (data contributors) | `docs/user-guide/` | UG |
| Portal administrators | `docs/portal-administration/` | PA |
| Portal developers (building portals) | `docs/portal-development/` | PD |
| Framework contributors | `docs/contributing/` | FC |

These four sections are **immutable**. Never create a fifth top-level section.

Additional locations:

- `docs/overview/` — project vision, background, FAIR philosophy
- `docs/more/` — glossary, changelog, support
- `.specify/memory/constitution.md` — governance principles
- `specs/###-feature-name/` — feature specifications

## Audience Decision

1. Using the portal web interface? → `user-guide/`
2. Managing/configuring through Django admin? → `portal-administration/`
3. Building/customising a portal with FairDM? → `portal-development/`
4. Contributing to FairDM core? → `contributing/`

## Writing Standards

### Voice & Tone

- **UG**: Friendly, non-technical. Assume no Python/Django knowledge. Use "you" voice.
- **PA**: Professional, task-oriented. Assume Django admin familiarity but not development skills.
- **PD**: Technical but welcoming. Assume basic Python/Django skills. Provide complete code examples.
- **FC**: Peer-to-peer technical. Assume strong Python/Django knowledge.

### Structure Rules

- One `H1` per page (the page title)
- Never skip heading levels (H2 → H4 is invalid)
- Maximum heading depth: H4 (rarely H5)
- New page if content exceeds ~500 words of new material, has a distinct audience, or covers a standalone concept
- Every new page must be added to a `{toctree}` directive

### Prose Rules

- Present tense, active voice
- Second person ("you") for instructions
- Short paragraphs (3-5 sentences max)
- Lead with the action in task-based docs ("To create a sample, navigate to...")
- Wrap all user-facing strings in docs with clear labelling of what is UI text vs code

## MyST Markdown Syntax

All docs are `.md` files parsed by `myst_parser`. The following MyST extensions are enabled:

`colon_fence`, `deflist`, `html_image`, `replacements`, `smartquotes`, `substitution`, `tasklist`

The base `fairdm-docs` package additionally enables: `amsmath`, `attrs_inline`, `dollarmath`, `fieldlist`, `html_admonition`, `strikethrough`

### Admonitions

Use colon-fence style (3 colons minimum, nest with 4+):

```markdown
:::{note}
Brief informational note.
:::

:::{tip}
Helpful suggestion for the reader.
:::

:::{warning}
Something the reader should be careful about.
:::

:::{important}
Critical information the reader must not miss.
:::

:::{seealso}
Links to related documentation.
:::
```

### Code Blocks

````markdown
```python
from fairdm.registry import register
```

```bash
poetry run python manage.py migrate
```

```json
{"key": "value"}
```
````

### Definition Lists

```markdown
Term
: Definition text here.

Another Term
: Its definition.
```

### Task Lists

```markdown
- [x] Completed item
- [ ] Incomplete item
```

### Page-level Table of Contents

```markdown
```{contents}
:depth: 2
:local:
```

```

### Custom Anchors

```markdown
(my-custom-anchor)=
## Section Heading

Link elsewhere with: [text](#my-custom-anchor)
```

### YAML Frontmatter

Use for pydata-sphinx-theme page-level options:

```markdown
---
sd_hide_title: true
---
```

## Sphinx-Design Components

`sphinx-design` is available (via `fairdm-docs` dependency). Use for visually rich landing pages and index pages. Avoid overuse in tutorial/guide content.

### Grid Cards

```markdown
::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} {octicon}`book;1.5em` Card Title
:link: target-page
:link-type: doc

Card description text.
+++
[Link text →](target-page)
:::

:::{grid-item-card} {octicon}`gear;1.5em` Another Card
:link: another-page
:link-type: doc

Another description.
:::

::::
```

Grid spec `1 2 2 3` means: 1 col on xs, 2 on sm, 2 on md, 3 on lg.

### Tabs

```markdown
::::{tab-set}

:::{tab-item} Python
```python
print("hello")
```

:::

:::{tab-item} Bash

```bash
echo "hello"
```

:::

::::

```

### Dropdowns

```markdown
:::{dropdown} Click to expand
Hidden content here.
:::
```

## Citations & References

Citations use `sphinxcontrib-bibtex`. The BibTeX file is at `docs/refs.bib`.

### Adding a Citation

1. Add the BibTeX entry to `docs/refs.bib`:

```bibtex
@article{Wilkinson2016,
  author  = {Wilkinson, Mark D. and others},
  title   = {The FAIR Guiding Principles for scientific data management and stewardship},
  journal = {Scientific Data},
  volume  = {3},
  pages   = {160018},
  year    = {2016},
  doi     = {10.1038/sdata.2016.18}
}
```

1. Cite in-text using MyST role syntax:

```markdown
The FAIR principles {cite}`Wilkinson2016` define four foundational pillars.
```

1. Add a bibliography section at the bottom of the page:

```markdown
## References

```{bibliography}
:filter: docname in docnames
```

```

The `:filter: docname in docnames` directive renders only citations used on that page.

### Citation Guidelines

- **Always cite** when making claims about FAIR data principles, research data management standards, or scientific methodology
- Use the `citation-management` skill to find and validate citations when needed
- Prefer DOI-based entries for reproducibility
- Use the BibTeX key format: `AuthorYear` (e.g., `Wilkinson2016`)
- Portal-admin and user-guide pages rarely need citations; portal-development and overview pages often do

## Cross-References

### To Specifications

```markdown
[Spec: Feature Name](../../specs/###-spec-name/spec.md)
[specific requirement](../../specs/###-spec-name/spec.md#fr-008)
```

### To Constitution

```markdown
[FAIR-First](../../.specify/memory/constitution.md#i-fair-first-research-portals)
[Domain-Driven Modeling](../../.specify/memory/constitution.md#ii-domain-driven-declarative-modeling)
[Configuration Over Plumbing](../../.specify/memory/constitution.md#iii-configuration-over-custom-plumbing)
[Opinionated Defaults](../../.specify/memory/constitution.md#iv-opinionated-production-grade-defaults)
[Test-First Quality](../../.specify/memory/constitution.md#v-test-first-quality-sustainability)
[Documentation Critical](../../.specify/memory/constitution.md#vi-documentation-critical)
```

### Between Sections

Use relative paths: `../portal-development/getting_started.md`

### Cross-Reference Rules

- PD docs **must** link to relevant specs
- FC docs **should** link to constitution principles
- UG/PA docs **rarely** need spec or constitution links
- Never use "click here" as link text

## Toctree Management

Every index page uses `{toctree}` to define its children:

```markdown
```{toctree}
:maxdepth: 1
:caption: Section Title

page-one
page-two
subdirectory/index
```

```

- Use `:caption:` to group related pages
- Use `:maxdepth: 1` for flat lists, `:maxdepth: 2` for nested sections
- Every `.md` file must appear in exactly one toctree (or be marked `:orphan:`)

## Lifecycle Markers

```markdown
:::{deprecated} Since version X.Y
Use `new_function()` instead of `old_function()`.
:::

:::{warning} Experimental
This API may change in future releases.
:::

:::{note} Maintenance Mode
This feature receives bug fixes only. Prefer [newer alternative](path).
:::
```

## Page Templates

### Tutorial/Guide Page

```markdown
# Page Title

Brief intro paragraph explaining what the reader will accomplish.

:::{tip}
Prerequisites or helpful context.
:::

## Step 1: First Action

Explanation and code example.

## Step 2: Second Action

Explanation and code example.

## What You've Accomplished

- ✅ First outcome
- ✅ Second outcome

:::{seealso}
- [Next topic](next-page.md)
- [Related concept](related.md)
:::
```

### Reference Page

```markdown
# Feature Reference

```{contents}
:depth: 2
:local:
```

## Overview

Brief description of the feature.

## Configuration Options

### `option_name`

Type
: `str`

Default
: `"default_value"`

Description of what this option controls.

## Examples

### Basic Usage

\```python

# code example

\```

## References

\```{bibliography}
:filter: docname in docnames
\```

```

### Landing/Index Page

```markdown
# Section Title

Intro paragraph for the section.

:::{important}
Key information for the reader.
:::

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} {octicon}`book;1.5em` Sub-topic
:link: sub-topic
:link-type: doc

Brief description.
:::

::::

\```{toctree}
:maxdepth: 1
:caption: Guides

page-one
page-two
\```
```

## Validation

Before committing documentation changes, run:

```bash
# Build (warnings as errors)
poetry run sphinx-build -W -b html docs docs/_build/html

# Link check
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck

# Checklist validation (if feature spec exists)
poetry run pytest tests/integration/docs/test_documentation_validation.py -v
```

All three must pass for a PR to merge.

## Context7 Libraries

When writing documentation that references specific tools or libraries, fetch current docs:

- `pydata/pydata-sphinx-theme` — theme configuration and layout options
- `executablebooks/sphinx-design` — cards, grids, tabs, dropdowns
- `sphinx-doc/sphinx` — core Sphinx directives and configuration
- `FAIR-DM/fairdm-docs` — base Sphinx config shared across FairDM projects

For detailed guidance on specific topics, see:

- [references/myst-syntax.md](references/myst-syntax.md) — Extended MyST syntax reference and patterns
- [references/audience-guide.md](references/audience-guide.md) — Detailed audience profiling and content strategy
