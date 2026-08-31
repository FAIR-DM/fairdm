# Documentation Validation Rules

```{contents}
:depth: 2
:local:
```

## Overview

FairDM documentation is validated by building it with Sphinx and checking its links. This guide documents both checks, how to run them locally, and how to fix common failures.

```{important}
There is currently no CI job that runs these checks automatically on pull requests. Run them locally before you submit documentation changes.
```

## Validation Categories

Documentation validation consists of two checks:

1. **Build Validation** — Ensures documentation compiles without errors or warnings
2. **Link Validation** — Verifies all cross-references and links resolve correctly

---

## Build Validation

### Purpose

Build validation ensures that all documentation can be successfully compiled by Sphinx without errors or warnings.

### Rules

#### Rule: Build Must Complete Without Errors

**Severity**: Error (blocking)

**Command**:

```bash
poetry run sphinx-build -W -b html docs docs/_build/html
```

**What it checks**:

- All MyST/Markdown syntax is valid
- All included files exist
- All toctree references resolve
- No orphaned documents (documents not in any toctree)
- Images referenced in documentation exist

**Validation criteria**:

- Exit code must be 0
- No ERROR messages in output
- No WARNING messages in output (warnings treated as errors with `-W` flag)

**Common failures**:

| Issue | Error Message | Fix |
|-------|--------------|-----|
| Missing file | `WARNING: ... could not be found` | Add the missing file or remove the reference |
| Invalid MyST | `WARNING: ... MyST...` | Fix the MyST syntax (check colons, backticks, indentation) |
| Orphaned doc | `WARNING: document isn't included in any toctree` | Add document to a toctree or mark as orphan with `:orphan:` |
| Missing image | `WARNING: image file not readable` | Add the image file or remove the reference |
| Broken include | `WARNING: Problems with "include" directive` | Check the included file path and existence |

**Example failure**:

```
WARNING: docs/contributing/new-guide.md:12: document isn't included in any toctree
```

**How to fix**:

1. Add `new-guide` to the toctree in `docs/contributing/index.md`:

   ```markdown
   ```{toctree}
   :maxdepth: 2

   existing-guide
   new-guide
   ```

   ```

2. Or, if the document is intentionally standalone, add `:orphan:` at the top:

   ```markdown
   :orphan:

   # Standalone Guide
   ```

---

## Link Validation

### Purpose

Link validation ensures all cross-references, specification links, constitution links, and external URLs are valid and accessible.

### Rules

#### Rule: All Internal Links Must Resolve

**Severity**: Error (blocking)

**Command**:

```bash
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

**What it checks**:

- Relative links to other documentation pages
- Specification cross-references (`../../specs/###-spec-name/spec.md`)
- Constitution cross-references (`../../CONSTITUTION.md`)
- Anchors within documents (`#section-heading`)
- Image paths and file references

**Validation criteria**:

- All internal links return `[working]` or `[redirected]` status
- No `[broken]` status for non-HTTP links
- All anchors exist in target documents

**Common failures**:

| Issue | Error Message | Fix |
|-------|--------------|-----|
| Wrong path | `[broken] ../../wrong/path.md` | Correct the relative path |
| Missing anchor | `[broken] file.md#missing-anchor` | Add the anchor or fix the heading |
| Typo in filename | `[broken] ../../specs/001-documenation-strategy/spec.md` | Fix typo: `documentation` |
| Wrong spec ID | `[broken] ../../specs/1-spec/spec.md` | Use 3-digit ID: `001-spec` |

**Example failure**:

```
docs/contributing/documentation/cross-references.md:45: [broken] ../../specs/042-plugin-system/spec.md
```

**How to fix**:

1. Check if the spec exists: `ls specs/042-plugin-system/spec.md`
2. If missing, create it or use correct spec ID
3. If path is wrong, fix the relative path (count `../../` correctly)
4. Re-run linkcheck to verify

#### Rule: External Links Checked (Warning Only)

**Severity**: Warning (non-blocking)

**What it checks**:

- HTTP/HTTPS URLs to external websites
- API documentation links
- GitHub repository links
- Third-party documentation

**Validation criteria**:

- External link failures generate warnings only
- Do not block PR merge
- Should be manually reviewed and fixed when possible

**Common warnings**:

| Issue | Warning Message | Action |
|-------|----------------|--------|
| Rate limiting | `429 Too Many Requests` | Ignore or retry later |
| Temporary outage | `Connection timeout` | Retry or ignore if transient |
| Moved permanently | `[redirected] ... to ...` | Update link to new URL |
| 404 Not Found | `404 Client Error` | Remove or update link |

**Example warning**:

```
docs/overview/background.md:15: [broken] https://example.com/old-page - 404 Client Error
```

**How to handle**:

- **Rate limits**: Ignore (temporary)
- **Redirects**: Update to new URL for cleaner links
- **404 errors**: Find new URL or remove if resource no longer exists
- **Timeouts**: Retry or ignore if site is known to be unreliable

---

## Continuous Integration

There is no CI workflow that builds or link-checks the documentation on pull requests today. A previous workflow (`docs-validation.yml`) was removed because it had been failing on an unrelated Sphinx theme error for months and never published anything. ReadTheDocs builds the documentation independently of this repository's CI.

Until a replacement workflow exists, treat the commands below as a manual pre-submission step rather than a merge gate.

---

## Running Validation Locally

### Before Committing

Run both checks locally before pushing, to catch issues early:

```bash
# 1. Build documentation
poetry run sphinx-build -W -b html docs docs/_build/html

# 2. Check links
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

### Quick Validation Script

Create a local script `validate-docs.sh`:

```bash
#!/bin/bash
set -e

echo "Building documentation..."
poetry run sphinx-build -W -b html docs docs/_build/html

echo "Checking links..."
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck

echo "All validation checks passed."
```

Make it executable and run:

```bash
chmod +x validate-docs.sh
./validate-docs.sh
```

---

## Troubleshooting Validation Failures

### Build Failures

**Issue**: `WARNING: document isn't included in any toctree`

**Solution**:

1. Add document to parent toctree
2. Or mark as orphan with `:orphan:` directive at top

**Issue**: `WARNING: image file not readable: _static/image.png`

**Solution**:

1. Add image file to `docs/_static/`
2. Or use correct relative path from current document
3. Or remove image reference if not needed

**Issue**: `WARNING: MyST syntax error`

**Solution**:

1. Check MyST directive syntax (```:directive```, not just `::directive`)
2. Verify proper indentation (3 spaces for content)
3. Close all directives with ``` on its own line

### Link Check Failures

**Issue**: `[broken] ../../specs/042-plugin-system/spec.md`

**Solution**:

1. Verify spec directory exists: `ls specs/042-plugin-system/`
2. Check filename: must be `spec.md` exactly
3. Fix relative path: count `../../` correctly from source file

**Issue**: `[broken] #missing-anchor`

**Solution**:

1. Check target document for heading
2. Verify anchor format: lowercase, hyphens, no special chars
3. Use `#actual-heading-text` format

**Issue**: External link `404` or timeout

**Solution**:

- Non-blocking warning only
- Update or remove link if resource no longer exists
- Ignore if transient (CI will retry)

---

## Validation Configuration

### Sphinx Configuration

Link check configuration in `docs/conf.py`:

```python
# Link check configuration
linkcheck_ignore = [
    r'http://localhost:\d+',      # Local development
    r'https://example\.com',       # Placeholder URLs
    r'.*\.local',                  # Local network
]

linkcheck_retries = 2              # Retry failed links
linkcheck_timeout = 10             # Seconds per link
linkcheck_workers = 5              # Parallel workers
```

---

## Related Documentation

- [Information Architecture](./information-architecture.md) — Where documentation belongs
- [Cross-Reference Patterns](./cross-references.md) — Linking to specs and constitution

---

## Summary

FairDM's documentation validation ensures:

- **Quality**: Documentation builds without errors or warnings
- **Correctness**: All links and cross-references resolve properly
- **Traceability**: Specifications and constitution references are valid

Run both checks locally before opening a pull request.

**Quick validation command**:

```bash
poetry run sphinx-build -W -b html docs docs/_build/html && \
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

If both succeed, your documentation is ready for review.
