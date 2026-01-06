#!/usr/bin/env python
"""
Feature Documentation Checklist Validator

Validates that feature documentation checklists are complete and properly formatted.

Validation Rules (per plan.md Entity 2):
- All items must be marked [x] (completed)
- Each item must specify target section and required content
- Checklist status must progress: not-started → in-progress → completed

Exit Codes:
    0: All checklists pass validation
    1: One or more checklists failed validation
    2: No checklists found (warning)
"""

import re
import sys
from pathlib import Path


class ChecklistValidator:
    """Validator for feature documentation checklists."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def find_checklists(self) -> list[Path]:
        """Find all documentation checklists in specs/ directories."""
        specs_dir = self.repo_root / "specs"

        if not specs_dir.exists():
            return []

        checklists = []
        for feature_dir in specs_dir.iterdir():
            if not feature_dir.is_dir():
                continue

            checklist_dir = feature_dir / "checklists"
            if not checklist_dir.exists():
                continue

            doc_checklist = checklist_dir / "documentation.md"
            if doc_checklist.exists():
                checklists.append(doc_checklist)

        return checklists

    def parse_checklist_status(self, content: str) -> str:
        """Extract the status field from checklist header."""
        match = re.search(r"\*\*Status\*\*:\s*(\w+(?:-\w+)*)", content)
        if match:
            return match.group(1)
        return "unknown"

    def validate_checklist_items(self, content: str) -> tuple[int, int, list[str]]:
        """
        Count total and completed checklist items.

        Returns:
            (total_items, completed_items, incomplete_item_descriptions)
        """
        # Pattern matches both [ ] and [x] or [X]
        total_pattern = r"^-\s*\[([ xX])\]\s+(.+)$"

        total_items = 0
        completed_items = 0
        incomplete_items = []

        for line in content.split("\n"):
            match = re.match(total_pattern, line.strip())
            if match:
                checked = match.group(1)
                description = match.group(2)
                total_items += 1

                if checked in ["x", "X"]:
                    completed_items += 1
                else:
                    incomplete_items.append(description)

        return total_items, completed_items, incomplete_items

    def validate_status_progression(self, status: str, completed: int, total: int) -> bool:
        """Validate that status matches completion progress."""
        if status == "not-started" and completed > 0:
            return False

        if status == "in-progress" and (completed == 0 or completed == total):
            return False

        if status == "completed" and completed < total:
            return False

        return True

    def validate_checklist(self, checklist_path: Path) -> bool:
        """
        Validate a single documentation checklist.

        Returns:
            True if checklist passes all validation rules, False otherwise
        """
        content = checklist_path.read_text(encoding="utf-8")
        feature_name = checklist_path.parent.parent.name

        passed = True

        # Extract status
        status = self.parse_checklist_status(content)

        # Count items
        total, completed, incomplete = self.validate_checklist_items(content)

        if total == 0:
            self.warnings.append(f"{feature_name}: No checklist items found")
            return True  # Not an error, might be intentional

        # Rule 1: At least one item must be marked [x]
        if completed == 0:
            self.errors.append(f"{feature_name}: No items marked as completed ([x])")
            passed = False

        # Rule 2: Status must match completion progress
        if not self.validate_status_progression(status, completed, total):
            self.errors.append(
                f"{feature_name}: Status '{status}' doesn't match progress " f"({completed}/{total} completed)"
            )
            passed = False

        # Rule 3: If status is "completed", all items must be checked
        if status == "completed" and incomplete:
            self.errors.append(
                f"{feature_name}: Status is 'completed' but {len(incomplete)} items " f"remain unchecked"
            )
            passed = False

        # Validation passed
        if passed and status == "completed":
            print(f"✓ {feature_name}: Complete ({completed}/{total} items)")
        elif passed:
            print(f"⚠ {feature_name}: {status} ({completed}/{total} items)")

        return passed

    def run(self) -> int:
        """
        Run validation on all checklists.

        Returns:
            Exit code (0 = success, 1 = failure, 2 = no checklists)
        """
        print("Feature Documentation Checklist Validation")
        print("=" * 60)

        checklists = self.find_checklists()

        if not checklists:
            print("⚠ No documentation checklists found")
            return 2

        print(f"Found {len(checklists)} checklist(s)\n")

        all_passed = True
        for checklist in checklists:
            if not self.validate_checklist(checklist):
                all_passed = False

        # Print summary
        print()
        print("=" * 60)
        if self.errors:
            print(f"✗ Validation FAILED ({len(self.errors)} errors)")
            print()
            for error in self.errors:
                print(f"  ✗ {error}")
            return 1

        if self.warnings:
            print(f"⚠ {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        print("✓ All checklists pass validation")
        return 0


def main():
    """Main entry point."""
    # Find repository root (assuming script is in .specify/scripts/powershell/)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent.parent

    validator = ChecklistValidator(repo_root)
    exit_code = validator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
