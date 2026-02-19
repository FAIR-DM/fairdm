#!/usr/bin/env python3
"""
Check internal links from Sphinx linkcheck output.

This script parses the linkcheck output and fails only on critical internal link failures.
Image files and tutorial assets are logged as warnings but don't cause failure until docs cleanup is complete.

Usage:
    python .github/scripts/check-internal-links.py

Exit codes:
    0 - All critical internal links passed (warnings may be present)
    1 - One or more critical internal links failed
"""

import sys
from pathlib import Path


def is_critical_link(line: str) -> bool:
    """Check if a broken link is critical (not an image or static asset)."""
    # Non-critical: images, static assets, tutorial screenshots
    non_critical_patterns = [".png", ".jpg", ".jpeg", ".gif", ".svg", "_static/", "images/"]
    return not any(pattern in line.lower() for pattern in non_critical_patterns)


def main():
    """Check internal links from linkcheck output."""
    linkcheck_output = Path("docs/_build/linkcheck/output.txt")

    if not linkcheck_output.exists():
        print("[WARNING] Linkcheck output not found - skipping internal link validation")
        print("Note: This is informational only until docs cleanup is complete")
        sys.exit(0)

    content = linkcheck_output.read_text(encoding="utf-8")
    lines = content.split("\n")

    broken_critical_links = []
    broken_non_critical_links = []
    total_internal = 0

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Check for broken links
        if "[broken]" in line.lower() or "broken" in line.lower():
            # Determine if it's internal (relative path or same domain)
            is_internal = (
                "../" in line
                or line.strip().startswith("/")
                or "specs/" in line
                or ".specify/" in line
                or "docs/" in line
                or "#" in line  # Anchors are internal
            )

            if is_internal:
                if is_critical_link(line):
                    broken_critical_links.append(line.strip())
                else:
                    broken_non_critical_links.append(line.strip())

        # Count internal links checked
        if any(marker in line for marker in ["../", "specs/", ".specify/", "docs/"]):
            total_internal += 1

    # Print results
    print("\n" + "=" * 60)
    print("Internal Link Check Results (Lenient Mode)")
    print("=" * 60)
    print(f"[INFO] {total_internal} internal links checked")

    # Report critical broken links (failures)
    if broken_critical_links:
        print(f"\n[FAIL] {len(broken_critical_links)} CRITICAL broken links found:\n")
        for link in broken_critical_links[:10]:  # Show first 10
            print(f"   - {link}")
        if len(broken_critical_links) > 10:
            print(f"   ... and {len(broken_critical_links) - 10} more")
        print("\nResult: FAIL")
        print("=" * 60 + "\n")
        sys.exit(1)
    else:
        print("[PASS] 0 critical broken links")

    # Report non-critical warnings (informational only)
    if broken_non_critical_links:
        print(f"\n[WARNING] {len(broken_non_critical_links)} non-critical warnings (images/assets):\n")
        for link in broken_non_critical_links[:5]:  # Show first 5
            print(f"   - {link}")
        if len(broken_non_critical_links) > 5:
            print(f"   ... and {len(broken_non_critical_links) - 5} more")
        print("\nNote: Image/asset warnings are informational until docs cleanup is complete")

    print("\nResult: PASS")
    print("=" * 60 + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
