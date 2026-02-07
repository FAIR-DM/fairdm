# Documentation Validation Rules

```{contents}
:depth: 2
:local:
```

## Overview

FairDM enforces automated validation of all documentation to ensure quality, consistency, and correctness. This guide documents all validation rules, how to run them locally, and how to fix common failures.

```{important}
**All validation checks must pass before documentation can be merged.** The CI/CD pipeline automatically runs these validations on every pull request affecting documentation files.
```

## Validation Categories

Documentation validation consists of three main categories:

1. **Build Validation** — Ensures documentation compiles without errors or warnings
2. **Link Validation** — Verifies all cross-references and links resolve correctly
3. **Checklist Validation** — Confirms feature documentation checklists are complete and well-formed

---

## Build Validation

### Purpose

Build validation ensures that all documentation can be successfully compiled by Sphinx without errors or warnings.

### Rules

#### Rule: Build Must Complete Without Errors

**Severity**: ❌ Error (blocking)

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

**Severity**: ❌ Error (blocking)

**Command**:

```bash
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

**What it checks**:

- Relative links to other documentation pages
- Specification cross-references (`../../specs/###-spec-name/spec.md`)
- Constitution cross-references (`../../.specify/memory/constitution.md`)
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

**Severity**: ⚠️ Warning (non-blocking)

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

## Checklist Validation

### Purpose

Checklist validation ensures that feature documentation checklists exist, are well-formed, and contain all required sections.

### Rules

#### Rule: Feature Specs Must Have Checklists

**Severity**: ❌ Error (blocking)

**Command**:

```bash
poetry run pytest tests/integration/docs/test_documentation_validation.py::test_checklist_exists -v
```

**What it checks**:

- Every `specs/###-feature-name/` directory has at least one checklist
- Checklist files are in `specs/###-feature-name/checklists/` directory
- Checklist files have `.md` extension

**Validation criteria**:

- At least one `*.md` file exists in `specs/###-feature-name/checklists/`

**Exception**: `specs/000-*/` directories (spec 000 reserved for meta-specs)

**Example failure**:

```
The following specs are missing checklists:
  042-plugin-system
```

**How to fix**:

1. Create the checklists directory:

   ```bash
   mkdir -p specs/042-plugin-system/checklists
   ```

2. Copy the template:

   ```bash
   cp .specify/templates/feature-docs-checklist.md specs/042-plugin-system/checklists/documentation.md
   ```

3. Fill in the metadata and sections

#### Rule: Checklists Must Have Required Structure

**Severity**: ❌ Error (blocking)

**Command**:

```bash
poetry run pytest tests/integration/docs/test_documentation_validation.py::test_checklist_structure -v
```

**What it checks**:

- Checklist has metadata section with `**Feature**:`, `**Spec**:`, `**Author**:`, `**Date**:`
- Checklist has `## Documentation Updates` section
- Checklist has `### Section Checklist` section
- Checklist has `### Content Requirements` section

**Validation criteria**:

- All required metadata fields present
- All required section headings present
- Sections formatted correctly (Markdown heading syntax)

**Example failure**:

```
The following checklists have invalid structure:
  - 042-plugin-system/documentation.md: missing metadata (Feature, Spec, Author, Date)
```

**How to fix**:

1. Add missing metadata at the top of the checklist:

   ```markdown
   # Feature Documentation Checklist

   **Feature**: Plugin System
   **Spec**: [Plugin System](../spec.md)
   **Author**: Your Name
   **Date Created**: 2026-01-07
   **Status**: in-progress
   ```

2. Add missing sections:

   ```markdown
   ## Documentation Updates

   ### Section Checklist

   ### Content Requirements
   ```

#### Rule: Spec References Must Resolve

**Severity**: ❌ Error (blocking)

**Command**:

```bash
poetry run pytest tests/integration/docs/test_documentation_validation.py::test_spec_reference_resolves -v
```

**What it checks**:

- Checklist's `**Spec**:` field contains link to `../spec.md` or `./spec.md`
- Target `spec.md` file exists in parent directory

**Validation criteria**:

- `../spec.md` or `./spec.md` appears in content
- File `specs/###-feature-name/spec.md` exists

**Example failure**:

```
The following checklists have broken spec references:
  - 042-plugin-system/documentation.md: Spec field present but no link to spec.md
```

**How to fix**:

1. Ensure `**Spec**:` field has proper link:

   ```markdown
   **Spec**: [Plugin System](../spec.md)
   ```

2. Verify spec.md exists:

   ```bash
   ls specs/042-plugin-system/spec.md
   ```

#### Rule: At Least One Section Must Be Marked

**Severity**: ❌ Error (blocking)

**Command**:

```bash
poetry run pytest tests/integration/docs/test_documentation_validation.py::test_checklist_section_checkbox_marked -v
```

**What it checks**:

- At least one of the four documentation sections is checked: `[x]` or `[X]`
- Sections: user-guide/, portal-administration/, portal-development/, contributing/

**Validation criteria**:

- One or more section checkboxes marked as complete

**Example failure**:

```
The following checklists have no documentation sections marked:
  - 042-plugin-system/documentation.md

At least one of user-guide, portal-administration, portal-development, or contributing should be checked.
```

**How to fix**:

1. Mark applicable sections in the Section Checklist:

   ```markdown
   ### Section Checklist

   - [ ] **user-guide/** - Not applicable
   - [ ] **portal-administration/** - Not applicable
   - [x] **portal-development/** - Developers need API docs
     - [x] Plugin API documented
   - [x] **contributing/** - Framework contributors need guidelines
     - [x] Plugin development workflow documented
   ```

---

## CI/CD Integration

### Automated Validation Workflow

All validation checks run automatically on every pull request that modifies documentation files.

**Workflow file**: `.github/workflows/docs-validation.yml`

**Trigger paths**:

- `docs/**` — Any documentation file
- `specs/**` — Any specification file
- `**.md` — Any Markdown file anywhere
- `.specify/templates/feature-docs-checklist.md` — Template changes

**Workflow steps**:

1. **Build documentation** (warnings as errors)
   - Runs: `sphinx-build -W -b html docs docs/_build/html`
   - Blocks PR if: Build fails or warnings present

2. **Check links** (internal hard fail, external warn)
   - Runs: `sphinx-build -b linkcheck docs docs/_build/linkcheck`
   - Blocks PR if: Internal links broken
   - Warns if: External links broken (non-blocking)

3. **Validate checklists**
   - Runs: `pytest tests/integration/docs/test_documentation_validation.py`
   - Blocks PR if: Any test fails

4. **Generate validation report**
   - Runs: `python .github/scripts/generate-validation-report.py`
   - Non-blocking (informational only)

### PR Merge Requirements

For a PR to be mergeable, all of the following must pass:

- ✅ Build validation: `validate-docs / Build documentation` — PASS
- ✅ Link validation: `validate-docs / Check internal links` — PASS
- ✅ Checklist validation: `validate-docs / Validate feature documentation checklists` — PASS

External link warnings do **not** block merge but should be reviewed and fixed when reasonable.

---

## Running Validation Locally

### Before Committing

Run all validation checks locally before pushing to catch issues early:

```bash
# 1. Build documentation
poetry run sphinx-build -W -b html docs docs/_build/html

# 2. Check links
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck

# 3. Check internal links specifically
poetry run python .github/scripts/check-internal-links.py

# 4. Validate checklists
poetry run pytest tests/integration/docs/test_documentation_validation.py -v

# 5. Generate validation report (optional)
poetry run python .github/scripts/generate-validation-report.py
```

### Quick Validation Script

Create a local script `validate-docs.sh` (or `.ps1` for Windows):

```bash
#!/bin/bash
set -e

echo "🔨 Building documentation..."
poetry run sphinx-build -W -b html docs docs/_build/html

echo "🔗 Checking links..."
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck

echo "✅ Validating checklists..."
poetry run pytest tests/integration/docs/test_documentation_validation.py -v

echo "✨ All validation checks passed!"
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

### Checklist Failures

**Issue**: Spec missing checklists

**Solution**:

```bash
mkdir -p specs/###-feature-name/checklists
cp .specify/templates/feature-docs-checklist.md specs/###-feature-name/checklists/documentation.md
# Fill in metadata and sections
```

**Issue**: Invalid checklist structure

**Solution**:

1. Verify metadata block present:

   ```markdown
   **Feature**: Name
   **Spec**: [Link](../spec.md)
   **Author**: Name
   **Date Created**: YYYY-MM-DD
   ```

2. Verify required sections present:
   - `## Documentation Updates`
   - `### Section Checklist`
   - `### Content Requirements`

**Issue**: No sections marked in checklist

**Solution**:

1. Mark at least one applicable section:

   ```markdown
   - [x] **portal-development/** - Developers need this
   ```

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

### Pytest Configuration

Test configuration in `tests/integration/docs/test_documentation_validation.py`:

- **test_checklist_exists**: Verifies checklists exist
- **test_checklist_structure**: Validates required sections
- **test_spec_reference_resolves**: Checks spec links
- **test_checklist_has_checkboxes**: Ensures checkboxes present
- **test_checklist_section_checkbox_marked**: Verifies sections marked

---

## Related Documentation

- [Information Architecture](./information-architecture.md) — Where documentation belongs
- [Feature Checklist Workflow](./feature-checklist-workflow.md) — How to create and complete checklists
- [Cross-Reference Patterns](./cross-references.md) — Linking to specs and constitution

---

## Summary

FairDM's documentation validation ensures:

- ✅ **Quality**: Documentation builds without errors or warnings
- ✅ **Correctness**: All links and cross-references resolve properly
- ✅ **Completeness**: Feature documentation checklists are present and well-formed
- ✅ **Traceability**: Specifications and constitution references are valid

All validation checks must pass before documentation can be merged. Run validation locally before pushing to catch issues early and speed up the review process.

**Quick validation command**:

```bash
poetry run sphinx-build -W -b html docs docs/_build/html && \
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck && \
poetry run pytest tests/integration/docs/test_documentation_validation.py -v
```

If all three succeed, your documentation is ready for review! ✨
