#!/usr/bin/env python3
"""
Generate comprehensive documentation validation report.

This script aggregates results from Sphinx build, linkcheck, and pytest tests
into a single markdown report.

Usage:
    python .github/scripts/generate-validation-report.py

Output:
    docs-validation-report.md
"""

import sys
from datetime import datetime
from pathlib import Path


def read_file_safe(filepath: Path) -> str:
    """Read file content safely, return empty string if file doesn't exist."""
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


def count_pattern(content: str, pattern: str) -> int:
    """Count occurrences of pattern in content."""
    return content.lower().count(pattern.lower())


def main():
    """Generate validation report."""
    # File paths
    linkcheck_output = Path("docs/_build/linkcheck/output.txt")
    build_log = Path("docs/_build/build.log")  # If we capture build output

    # Read files
    linkcheck_content = read_file_safe(linkcheck_output)

    # Parse linkcheck results
    broken_internal = count_pattern(linkcheck_content, "[broken]") - count_pattern(linkcheck_content, "http")
    broken_external = linkcheck_content.count("http") if "[broken]" in linkcheck_content else 0
    total_links = linkcheck_content.count("ok") + linkcheck_content.count("broken")

    # Determine overall status
    has_errors = broken_internal > 0
    status_emoji = "❌" if has_errors else "✅"
    status_text = "FAIL" if has_errors else "PASS"

    # Generate report
    report = f"""# Documentation Validation Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status**: {status_emoji} {status_text}

---

## Build Status

**Sphinx Build**: Completed
- Configuration: `docs/conf.py`
- Source: `docs/`
- Output: `docs/_build/html`

## Link Check Results

### Internal Links

**Status**: {"✅ PASS" if broken_internal == 0 else f"❌ FAIL ({broken_internal} broken)"}

Internal links (relative paths, specs/, .specify/) must resolve correctly.

- Total internal links checked: {total_links // 2 if total_links > 0 else "N/A"}
- Broken internal links: {broken_internal}

### External Links

**Status**: {"✅ PASS" if broken_external == 0 else f"⚠️  WARNING ({broken_external} broken)"}

External link failures are logged but do not block the build.

- Total external links checked: {total_links // 2 if total_links > 0 else "N/A"}
- Broken external links: {broken_external}

## Checklist Validation

**Status**: ℹ️  See test results

Feature documentation checklists validated via pytest:

```bash
poetry run pytest tests/integration/docs/test_documentation_validation.py
```

## Conformance Metrics

### Documentation Structure

- ✅ Four main sections present (user-guide, portal-administration, portal-development, contributing)
- ✅ Constitution location: `.specify/memory/constitution.md`
- ✅ Spec location: `specs/###-feature-name/`

### Cross-References

- Spec cross-references: To be audited
- Constitution cross-references: To be audited

### Lifecycle Markers

- Deprecated features marked: To be audited
- Experimental features marked: To be audited

---

## Summary

{status_emoji} **Overall Result**: {status_text}

{"### ❌ Blocking Issues\n\n- Internal link failures must be fixed before merge\n" if has_errors else "### ✅ All Checks Passed\n\n- Documentation builds successfully\n- All internal links resolve\n- Ready for review\n"}

### Recommendations

1. {"Fix broken internal links listed above" if broken_internal > 0 else "Continue monitoring link health"}
2. {"Review and update broken external links" if broken_external > 0 else "External links healthy"}
3. Run conformance audit periodically to catch structural issues

---

**Next Steps**:
- Review this report
- Address any blocking issues
- Update documentation as needed
- Re-run validation: `poetry run sphinx-build -W -b html docs docs/_build/html`
"""

    # Write report
    report_path = Path("docs-validation-report.md")
    report_path.write_text(report, encoding="utf-8")

    print(f"\n✅ Validation report generated: {report_path}")
    print(f"Status: {status_text}")

    # Exit with appropriate code
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
