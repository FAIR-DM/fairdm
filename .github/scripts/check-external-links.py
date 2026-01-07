#!/usr/bin/env python3
"""
Check external links from Sphinx linkcheck output.

This script parses the linkcheck output and reports external link failures as warnings.
External links are those pointing to other domains. Failures do not block the build.

Usage:
    python .github/scripts/check-external-links.py

Exit codes:
    0 - Always (warnings only, never blocks)
"""

import sys
from pathlib import Path


def main():
    """Check external links from linkcheck output."""
    linkcheck_output = Path("docs/_build/linkcheck/output.txt")

    if not linkcheck_output.exists():
        print("⚠️  WARNING: Linkcheck output not found at docs/_build/linkcheck/output.txt")
        print("Run: poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck")
        sys.exit(0)  # Don't fail on missing output

    content = linkcheck_output.read_text(encoding="utf-8")
    lines = content.split("\n")

    broken_external_links = []
    total_external = 0

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Check for broken links
        if "[broken]" in line.lower() or "broken" in line.lower():
            # External links start with http:// or https://
            is_external = line.strip().startswith(("http://", "https://"))

            if is_external:
                broken_external_links.append(line.strip())

        # Count external links checked
        if line.strip().startswith(("http://", "https://")):
            total_external += 1

    # Print results
    print("\n" + "=" * 60)
    print("External Link Check Results")
    print("=" * 60)
    print(f"✅ {total_external} external links checked")

    if broken_external_links:
        print(f"⚠️  {len(broken_external_links)} external link warnings:\n")
        for link in broken_external_links:
            print(f"   - {link}")
        print("\nNote: External link failures are logged but do not block build.")
        print("Manual review recommended for broken external links.")
        print("\nResult: PASS (with warnings)")
    else:
        print("✅ 0 external link warnings")
        print("\nResult: PASS")

    print("=" * 60 + "\n")
    sys.exit(0)  # Always exit 0 for external links


if __name__ == "__main__":
    main()
