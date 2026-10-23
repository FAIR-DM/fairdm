# Cross-references

This page gives the syntax for linking within the documentation. When to link is set by the
[documentation standard](../standards/documentation.md): a page links rather than repeats, and may
link to the maintainers' material, such as a decision record.

## Link to another page

Use a relative path to the file, with its `.md` extension:

```markdown
[Settings](../developers/reference/settings.md)
```

A link to a file that does not exist fails the build, so a misspelt path is caught when you build.

## Link to a heading

Add the heading's anchor after the path. MyST makes an anchor from each heading down to level 3 by
lowercasing it, replacing spaces with hyphens and dropping other punctuation:

| Heading | Anchor |
|---|---|
| `## Build the documentation` | `#build-the-documentation` |
| `### Shared reference` | `#shared-reference` |

```markdown
[Build the documentation](index.md#build-the-documentation)
```

To link to a heading deeper than level 3, or to one that may be renamed, give it a label above it:

```markdown
(glossary)=

# Glossary
```

and link with the `ref` role: ``{ref}`glossary` ``.

## Link to a decision record

A decision record in `docs/adr/` is a page like any other. Link to its file, using the exact name
the file has:

```markdown
[Portals run on PostGIS](../adr/0031-portals-run-on-postgis.md)
```

## Link to a file outside `docs/`

A file outside `docs/`, such as `CONSTITUTION.md` or `GOALS.md`, cannot be resolved by the build.
Link to it by its full address on GitHub:

```markdown
[Constitution](https://github.com/FAIR-DM/fairdm/blob/main/CONSTITUTION.md)
```

## Link to a term in the glossary

The glossary is a Sphinx glossary, so the `term` role links to an entry:

```markdown
{term}`contribution level`
```

## Related

- [Documentation standard](../standards/documentation.md)
- [Validation rules](validation-rules.md)
