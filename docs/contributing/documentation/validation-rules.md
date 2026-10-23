# Validation rules

This page covers the two checks run on the documentation and how to fix what they report. The
[documentation standard](../standards/documentation.md) requires the build to treat warnings as
errors, so a page left out of the contents or a broken cross-reference fails it.

## The build

```bash
uv run sphinx-build -W --keep-going -b html docs docs/_build/html
```

`-W` turns each warning into an error and `--keep-going` reports all of them in one run. The build
passes when its exit code is 0.

| Report | Cause | Fix |
|---|---|---|
| `document isn't included in any toctree` | A page no toctree lists | Add the page to a toctree, or delete it |
| `image file not readable` | The image path is wrong or the file is missing | Correct the path or add the file |
| `Problems with "include" directive` | The included file does not exist | Correct the path |
| `cross-reference target not found` or `local id not found` | A link names a file or heading that does not exist | Correct the path or the anchor |
| A MyST warning | A directive is malformed | Check the colons or backticks, the indentation and the closing fence |

## The link check

The link check follows every link, including external addresses, and writes its report to
`docs/_build/linkcheck`, apart from the HTML build:

```bash
uv run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

The report is in `docs/_build/linkcheck/output.txt`. Fix every `[broken]` entry for a page in this
repository. A failure on an external address is often temporary, such as a rate limit or a
timeout. Retry it, and update the link when the page has moved. Addresses the check should skip are
listed in `linkcheck_ignore` in [`docs/conf.py`](https://github.com/FAIR-DM/fairdm/blob/main/docs/conf.py).

## Related

- [Documentation standard](../standards/documentation.md)
- [Cross-references](cross-references.md)
