#!/usr/bin/env python3
"""
Check internal links from Sphinx linkcheck output.

This script parses the linkcheck output and fails if any internal links are broken.
Internal links are those pointing to the same domain/repository.

Usage:
    python .github/scripts/check-internal-links.py

Exit codes:
    0 - All internal links passed
    1 - One or more internal links failed
"""

import sys
from pathlib import Path


def main():
    """Check internal links from linkcheck output."""
    linkcheck_output = Path("docs/_build/linkcheck/output.txt")

    if not linkcheck_output.exists():
        print("❌ ERROR: Linkcheck output not found at docs/_build/linkcheck/output.txt")
        print("Run: poetry run sphinx-build -b linkcheck docs docs/_build/linkcheck")
        sys.exit(1)

    content = linkcheck_output.read_text(encoding="utf-8")
    lines = content.split("\n")

    broken_internal_links = []
    total_internal = 0

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Check for broken links
        if "[broken]" in line.lower() or "broken" in line.lower():
            # Determine if it's internal (relative path or same domain)
            # Internal links typically start with ../ or / or are in the same repo
            is_internal = (
                "../" in line
                or line.strip().startswith("/")
                or "specs/" in line
                or ".specify/" in line
                or "docs/" in line
                or "#" in line  # Anchors are internal
            )

            if is_internal:
                broken_internal_links.append(line.strip())

        # Count internal links checked
        if any(marker in line for marker in ["../", "specs/", ".specify/", "docs/"]):
            total_internal += 1

    # Print results
    print("\n" + "=" * 60)
    print("Internal Link Check Results")
    print("=" * 60)
    print(f"✅ {total_internal} internal links checked")

    if broken_internal_links:
        print(f"❌ {len(broken_internal_links)} broken internal links found:\n")
        for link in broken_internal_links:
            print(f"   - {link}")
        print("\nResult: FAIL")
        print("=" * 60 + "\n")
        sys.exit(1)
    else:
        print("✅ 0 broken internal links")
        print("\nResult: PASS")
        print("=" * 60 + "\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
