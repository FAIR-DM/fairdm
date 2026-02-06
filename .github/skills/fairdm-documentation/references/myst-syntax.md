# MyST Syntax Reference for FairDM Docs

Extended reference for MyST Markdown patterns used across FairDM documentation. Consult this when writing docs that require advanced MyST features beyond basic admonitions and code blocks.

## Enabled Extensions

### Core (always available)

- `colon_fence` — `:::` fence style for directives
- `deflist` — definition lists
- `html_image` — `<img>` tags in Markdown
- `replacements` — `(c)` → ©, `(tm)` → ™, etc.
- `smartquotes` — curly quotes
- `substitution` — `{{variable}}` replacements
- `tasklist` — `- [x]` checkbox lists

### From fairdm-docs base config

- `amsmath` — LaTeX math environments
- `attrs_inline` — inline attributes `{.class #id}`
- `dollarmath` — `$inline$` and `$$block$$` math
- `fieldlist` — `:field: value` lists
- `html_admonition` — `<div class="admonition">` parsing
- `strikethrough` — `~~deleted~~`

## Directive Nesting

Nest directives by increasing the number of colons:

```markdown
::::{note}
Outer note.

:::{warning}
Inner warning.
:::

::::
```

For deeper nesting, continue adding colons (5, 6, etc.).

## Substitutions

Define in `conf.py` via `myst_substitutions`:

```python
myst_substitutions = {
    "project_name": "FairDM",
    "version": "0.5.0",
}
```

Use in docs: `{{project_name}} version {{version}}`

## Field Lists

Useful for parameter documentation:

```markdown
:param name: The name of the sample.
:type name: str
:returns: The created sample instance.
:rtype: Sample
```

## Math

Inline: `$E = mc^2$`

Block:

```markdown
$$
\int_0^\infty f(x)\,dx = 1
$$
```

## Images

```markdown
```{figure} _static/screenshot.png
:alt: Description of the image
:width: 80%
:align: center

Caption text for the figure.
```

```

Or HTML-style (enabled via `html_image`):

```html
<img src="_static/icon.png" alt="icon" width="32">
```

## Tables

Standard Markdown tables work:

```markdown
| Column A | Column B |
|----------|----------|
| Value 1  | Value 2  |
```

For complex tables, use `list-table`:

```markdown
```{list-table} Title
:header-rows: 1
:widths: 30 70

* - Header A
  - Header B
* - Cell 1
  - Cell 2
```

```

## Mermaid Diagrams

Available for flowcharts and decision trees:

```markdown
```{mermaid}
graph TD
    A[Start] --> B{Decision?}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
```

```

## Roles

```markdown
{ref}`label-name`           — cross-reference to a label
{doc}`path/to/document`     — cross-reference to a document
{cite}`BibTexKey`           — citation reference
{octicon}`icon-name;size`   — GitHub Octicon icon (in sphinx-design)
{fas}`icon-name`            — Font Awesome solid icon
```

## Auto-generated Heading Anchors

`myst_heading_anchors = 3` generates anchors for H1–H3. Rules:

1. Lowercase
2. Spaces → hyphens
3. Special characters removed
4. Leading/trailing hyphens stripped

| Heading | Anchor |
|---------|--------|
| `# Getting Started` | `#getting-started` |
| `## API: CreateSample()` | `#api-createsample` |

## Orphan Pages

Pages not in any toctree must be marked:

```markdown
:orphan:

# Standalone Page
```

## Include Other Files

```markdown
```{include} ../README.md
:start-after: <!-- docs-start -->
:end-before: <!-- docs-end -->
```

```

## sphinxcontrib-bibtex Details

### Configuration (in conf.py)

The portal-administration sub-docs use their own conf.py with:

```python
bibtex_bibfiles = ["refs.bib"]
bibtex_reference_style = "author_year"
bibtex_default_style = "unsrt"
```

The main docs inherit bibtex config from the `fairdm-docs` base package when `sphinxcontrib-bibtex` is in the extensions list.

### Multiple Bibliography Files

If a subdirectory has its own `refs.bib`, it can be configured in that subdirectory's `conf.py`.

### Citation Styles

- `author_year` — (Author, Year) in-text style
- `label` — [1], [2] numeric labels
- `super` — superscript numbers

### Footnote-style Citations

```markdown
The FAIR principles {footcite}`Wilkinson2016` are foundational.

```{footbibliography}
```

```

Renders citations as footnotes at page bottom instead of a separate bibliography section.
