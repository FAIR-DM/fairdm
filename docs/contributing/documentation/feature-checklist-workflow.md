# Feature Documentation Checklist Workflow

```{contents}
:depth: 2
:local:
```

## Overview

The Feature Documentation Checklist is a structured process that ensures every feature has complete, high-quality documentation before being marked as "done". This guide walks you through the 6-step workflow for using the checklist effectively.

```{important}
**When is the checklist required?**
- ✅ All features that modify user-facing behavior
- ✅ New functionality (models, UI components, APIs, CLI commands)
- ✅ Breaking changes or deprecations
- ⚠️ **Optional** for internal refactoring with no external interface changes
- ⚠️ **Optional** for bug fixes that don't introduce new concepts
```

---

## The 6-Step Workflow

### Step 1: Create the Checklist

**When**: After your feature spec is finalized, before starting implementation

**Action**: Copy the template to your feature directory

```bash
# Navigate to your feature directory
cd specs/###-feature-name/

# Create checklists directory if it doesn't exist
mkdir -p checklists

# Copy the template
cp ../../.specify/templates/feature-docs-checklist.md checklists/documentation.md
```

**Fill in the header**:

```markdown
**Feature**: Custom Rock Sample Fields
**Spec**: [Custom Sample Fields](../spec.md)
**Author**: Jane Developer
**Date Created**: 2026-01-07
**Status**: not-started
```

**What to include**:

- **Feature name**: Human-readable feature name
- **Spec link**: Relative link to `spec.md` (usually `../spec.md`)
- **Author**: Your name or team name
- **Date**: Today's date
- **Status**: Start with `not-started`

---

### Step 2: Classify Your Feature

**When**: Immediately after creating the checklist

**Action**: Identify which documentation sections your feature affects

Use the **Section Checklist** to mark relevant sections:

```markdown
### Section Checklist

- [x] **user-guide/** - My feature adds a new UI form
  - [x] Feature usage guide created/updated
  - [x] Screenshots or UI examples added
  - [ ] Common workflows documented

- [ ] **portal-administration/** - No admin changes

- [x] **portal-development/** - Developers need API docs
  - [x] Model configuration documented
  - [x] API usage examples provided

- [ ] **contributing/** - No framework dev workflow changes
```

**Decision tree**:

1. **Does it affect portal users?** → Mark user-guide/
2. **Does it add admin configuration?** → Mark portal-administration/
3. **Does it require developer integration?** → Mark portal-development/
4. **Does it change framework contributor workflow?** → Mark contributing/

```{tip}
Most features affect 1-3 sections. It's rare to affect all four.
```

---

### Step 3: Document As You Build

**When**: During feature implementation

**Action**: Write documentation alongside code changes

**Best Practice**: Write docs in small increments as you complete each sub-feature, rather than leaving all documentation until the end.

**For each marked section**:

1. **Navigate to the section** (e.g., `docs/user-guide/`)
2. **Determine file location** using the [Information Architecture Guide](./information-architecture.md)
3. **Create or update the file**
4. **Add the documentation page link to the checklist**:

```markdown
**Documentation Updated** (add links as you complete):
- [Feature Usage Guide](../../docs/user-guide/samples/custom-fields.md)
- [Model Configuration](../../docs/portal-development/models/custom-fields.md)
```

**What to write**:

- **Feature overview**: What does this feature do and why?
- **Usage examples**: Show, don't just tell
- **Configuration**: Any settings or options
- **Screenshots**: For UI features
- **Code snippets**: For developer-facing features

---

### Step 4: Add Content Requirements

**When**: As you write each documentation page

**Action**: Ensure each page has the required content types

Check off items in the **Content Requirements** section:

```markdown
### Content Requirements

- [x] **Feature overview** - Included in user-guide/samples/custom-fields.md
- [x] **Usage examples** - 3 examples provided
- [x] **Configuration options** - Model field configuration documented
- [ ] **Migration guide** - N/A (no breaking changes)
- [x] **Cross-references** - Linked to spec and related docs
- [x] **Code snippets** - All tested and validated
- [x] **Screenshots/diagrams** - 2 screenshots added
- [ ] **Lifecycle markers** - N/A (not deprecated or experimental)
```

**Cross-references** (always required):

Add at least one reference to your spec:

```markdown
For implementation details, see the [Custom Sample Fields Specification](../../specs/015-custom-sample-fields/spec.md).
```

If your feature aligns with constitution principles, reference them:

```markdown
This feature implements the [FAIR-First principle](../../.specify/memory/constitution.md#i-fair-first-research-portals) by ensuring all custom fields have proper metadata.
```

```{important}
**Cross-references are mandatory** for all portal-development/ and contributing/ documentation.
See [Cross-Reference Patterns](./cross-references.md) for complete guidelines on:
- Specification cross-reference syntax
- Constitution cross-reference patterns
- Anchor generation rules
- Validation requirements
```

---

### Step 5: Validate Your Documentation

**When**: After completing all documentation updates

**Action**: Run validation checks to ensure quality

#### Build Check

```bash
poetry run sphinx-build -b html docs docs/_build/html
```

**Expected**: Build succeeds (warnings are OK at this stage, errors are not)

#### Link Check

```bash
poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck
```

**Expected**: Internal links pass, external links may have warnings

#### Internal Link Validation

```bash
poetry run python .github/scripts/check-internal-links.py
```

**Expected**: Script reports 0 broken internal links

#### Mark Validation Checklist

```markdown
### Validation Checklist

- [x] **Spec link resolves** - ✅ Verified
- [x] **Documentation builds** - ✅ Succeeds with 12 warnings (expected)
- [x] **Internal links valid** - ✅ All pass
- [x] **External links checked** - ⚠️ 2 warnings (expected - GitHub API rate limits)
- [x] **Examples tested** - ✅ All code examples syntactically valid
- [x] **Screenshots current** - ✅ Reflect current UI
- [x] **Cross-references added** - ✅ Spec and constitution links present
```

---

### Step 6: Mark Complete and Merge

**When**: All sections complete, all validation passes

**Action**: Update checklist status and merge

```markdown
**Status**: completed

---

## Completion

**Date Completed**: 2026-01-07
**Completed By**: Jane Developer
**Final Status**: ✅ completed

**Notes**:
All documentation complete. User guide includes 2 screenshots, developer guide has 3 code examples, all links validated.
```

**Then**:

1. **Commit the completed checklist** to your feature branch
2. **Open a PR** (or update existing PR)
3. **Tag reviewers** — documentation reviewer and code reviewer
4. **CI/CD** will automatically validate your documentation
5. **Merge** when approved and all checks pass

---

## Common Questions

### Q: What if I don't know which section to update?

**A**: Use the [Information Architecture Guide](./information-architecture.md) decision tree. If still unsure, ask in the PR or discussions.

### Q: Can I skip sections that don't apply?

**A**: Yes! Leave unchecked sections blank. Most features don't affect all four sections.

### Q: What if my feature is experimental?

**A**: Still document it, but add lifecycle markers:

```markdown
:::{{warning}} Experimental
This feature is experimental and the API may change in future releases.
:::
```

### Q: My build has warnings. Is that OK?

**A**: Minor warnings are acceptable (missing images elsewhere, orphaned docs). **Errors are not** — errors must be fixed.

### Q: How do I handle breaking changes?

**A**: Breaking changes require:

1. **Migration guide** showing old → new pattern
2. **Deprecation markers** on old documentation
3. **Clear communication** in changelog

### Q: What about internal refactoring with no user impact?

**A**: Checklist is **optional** for pure internal refactoring. Use judgment — if it changes testing patterns or architecture, document it in contributing/.

### Q: Can I update the template?

**A**: Yes! If you find the template lacking, propose improvements via PR to `.specify/templates/feature-docs-checklist.md`.

---

## Examples

### Example 1: New User Feature (Batch Upload)

**Sections affected**: user-guide/, portal-administration/

**Documentation created**:

- `docs/user-guide/dataset/batch-upload.md` — Step-by-step guide with screenshots
- `docs/portal-administration/configuration.md` — Updated with file size limit setting

**Content requirements**:

- ✅ Feature overview
- ✅ 4 screenshots showing UI flow
- ✅ Configuration options
- ✅ Cross-reference to spec
- ❌ Migration guide (N/A)

**Time**: ~2 hours (1 hour writing, 1 hour screenshots and validation)

### Example 2: New Developer API (Custom Filters)

**Sections affected**: portal-development/, contributing/

**Documentation created**:

- `docs/portal-development/views/custom-filters.md` — FilterSet API guide
- `docs/contributing/testing/filter-tests.md` — Testing patterns

**Content requirements**:

- ✅ Feature overview
- ✅ 5 code examples (all tested)
- ✅ Configuration options
- ✅ Cross-reference to spec and architecture docs
- ❌ Screenshots (N/A)

**Time**: ~3 hours (2 hours API docs, 1 hour testing docs)

### Example 3: Breaking Change (Renamed Setting)

**Sections affected**: portal-development/, portal-administration/

**Documentation created**:

- `docs/portal-development/configuration.md` — Updated with new setting name
- `docs/portal-development/migration-guides/v2-settings.md` — Created migration guide
- `docs/portal-administration/configuration.md` — Updated admin config reference

**Content requirements**:

- ✅ Feature overview
- ✅ Migration guide (old → new pattern)
- ✅ Deprecation markers on old docs
- ✅ Cross-reference to spec
- ❌ Screenshots (N/A)

**Time**: ~1.5 hours (mostly migration guide)

---

## Integration with Speckit

The feature documentation checklist integrates with the Speckit workflow:

1. **After `/speckit.tasks`**: Create the checklist as part of setup
2. **During implementation**: Update checklist as documentation is written
3. **Before `/speckit.finalize`**: Complete all checklist items
4. **At finalize**: Checklist verification is part of finalization checks

```{tip}
Consider running `/speckit.validate-docs` (if available) to automatically check documentation completeness.
```

---

## Related Documentation

- [Information Architecture Guide](./information-architecture.md) — Where to put documentation
- [Documentation Standards](./documentation-standards.md) — Writing style and formatting (coming soon)
- [Documentation Validation](./validation.md) — Detailed validation guide (coming soon)
- [Constitution: Documentation Principles](../../.specify/memory/constitution.md#documentation-principles) — Governance principles

---

**Questions about the workflow? See [Contributing Guidelines](../getting_started.md) or open a discussion.**
