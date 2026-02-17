"""
Feature Specification Tracker

Automatically tracks and reports on feature development progress including:
- Start/completion dates
- Test counts and coverage
- Implementation status
- CI/CD integration

Usage:
    poetry run python scripts/feature_tracker.py --feature 008-plugin-system --status in-progress
    poetry run python scripts/feature_tracker.py --report
    poetry run python scripts/feature_tracker.py --dashboard
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Project root
ROOT = Path(__file__).parent.parent
SPECS_DIR = ROOT / "specs"
TRACKING_FILE = ROOT / "feature-tracking.yaml"


class FeatureTracker:
    """Manages feature specification tracking and metrics."""

    def __init__(self) -> None:
        self.tracking_data = self._load_tracking_data()

    def _load_tracking_data(self) -> dict[str, Any]:
        """Load existing tracking data or create new structure."""
        if TRACKING_FILE.exists():
            with open(TRACKING_FILE) as f:
                return yaml.safe_load(f) or {"features": {}}
        return {"features": {}}

    def _save_tracking_data(self) -> None:
        """Save tracking data to YAML file."""
        with open(TRACKING_FILE, "w") as f:
            yaml.dump(
                self.tracking_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def discover_features(self) -> list[str]:
        """Discover all feature specs in the specs/ directory."""
        features = []
        for spec_dir in sorted(SPECS_DIR.glob("*-*")):
            if spec_dir.is_dir() and (spec_dir / "spec.md").exists():
                features.append(spec_dir.name)
        return features

    def extract_spec_metadata(self, feature_id: str) -> dict[str, Any]:
        """Extract metadata from spec.md file."""
        spec_file = SPECS_DIR / feature_id / "spec.md"
        if not spec_file.exists():
            return {}

        metadata = {}
        content = spec_file.read_text(encoding="utf-8")

        # Extract frontmatter-style metadata
        patterns = {
            "branch": r"\*\*Feature Branch\*\*:\s*`?([^`\n]+)`?",
            "created": r"\*\*Created\*\*:\s*([^\n]+)",
            "status": r"\*\*Status\*\*:\s*([^\n]+)",
            "title": r"^#\s+Feature Specification:\s*(.+)$",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()

        # Count user stories
        user_stories = re.findall(r"###\s+User Story\s+\d+", content)
        metadata["user_stories_count"] = len(user_stories)

        return metadata

    def get_test_metrics(self, feature_id: str) -> dict[str, Any]:
        """Run pytest and extract test metrics for the feature."""
        # Map feature ID to test paths
        test_paths = self._get_test_paths(feature_id)

        if not test_paths:
            return {
                "tests_total": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "coverage_percent": 0.0,
                "last_test_run": None,
            }

        try:
            # Run pytest with JSON reporter
            result = subprocess.run(
                [
                    "poetry",
                    "run",
                    "pytest",
                    *test_paths,
                    "--tb=no",
                    "-q",
                    "--co",  # Just collect, don't run
                ],
                capture_output=True,
                text=True,
                cwd=ROOT,
                timeout=60,  # Increased timeout
            )

            # Parse test count from collection
            test_count_match = re.search(r"(\d+) tests? collected", result.stdout)
            test_count = int(test_count_match.group(1)) if test_count_match else 0

            # Get coverage if available
            coverage_percent = self._get_coverage(feature_id)

            return {
                "tests_total": test_count,
                "tests_passed": 0,  # Would need actual run for this
                "tests_failed": 0,
                "coverage_percent": coverage_percent,
                "test_paths": test_paths,
                "last_test_run": datetime.now().isoformat(),
            }

        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Test collection timed out for {feature_id}")
            return {
                "tests_total": 0,
                "error": "Test collection timed out",
                "test_paths": test_paths,
                "last_test_run": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"  ⚠️  Error collecting tests for {feature_id}: {e}")
            return {
                "tests_total": 0,
                "error": str(e),
                "test_paths": test_paths,
                "last_test_run": datetime.now().isoformat(),
            }

    def _get_test_paths(self, feature_id: str) -> list[str]:
        """Map feature ID to test file paths."""
        # Feature-specific mapping
        mappings = {
            "008-plugin-system": ["tests/test_contrib/test_plugins/"],
            "006-core-measurements": ["tests/test_core/test_measurement.py"],
            "005-core-samples": ["tests/test_core/test_sample.py"],
            "004-core-datasets": ["tests/test_core/test_dataset.py"],
            "003-core-projects": ["tests/test_core/test_project.py"],
            "002-fairdm-registry": ["tests/test_core/test_registry.py"],
        }

        return mappings.get(feature_id, [])

    def _get_coverage(self, feature_id: str) -> float:
        """Extract coverage percentage from coverage report."""
        # This would need actual coverage run - placeholder for now
        coverage_file = ROOT / ".coverage"
        if not coverage_file.exists():
            return 0.0

        # Parse coverage data (requires coverage.py)
        try:
            import coverage

            cov = coverage.Coverage(data_file=str(coverage_file))
            cov.load()

            # Get coverage for specific module
            module_mappings = {
                "008-plugin-system": "fairdm.contrib.plugins",
                "006-core-measurements": "fairdm.measurement",
                "005-core-samples": "fairdm.sample",
                "004-core-datasets": "fairdm.dataset",
                "003-core-projects": "fairdm.project",
                "002-fairdm-registry": "fairdm.registry",
            }

            module_name = module_mappings.get(feature_id)
            if module_name:
                analysis = cov.analysis2(module_name)
                if analysis:
                    executed, missing = analysis[1], analysis[2]
                    total = len(executed) + len(missing)
                    if total > 0:
                        return (len(executed) / total) * 100

        except Exception:
            pass

        return 0.0

    def update_feature(
        self,
        feature_id: str,
        status: str | None = None,
        refresh_metrics: bool = True,
    ) -> None:
        """Update tracking data for a feature."""
        if "features" not in self.tracking_data:
            self.tracking_data["features"] = {}

        # Initialize feature entry if needed
        if feature_id not in self.tracking_data["features"]:
            self.tracking_data["features"][feature_id] = {
                "id": feature_id,
                "started": datetime.now().isoformat(),
            }

        feature = self.tracking_data["features"][feature_id]

        # Update status
        if status:
            old_status = feature.get("status")
            feature["status"] = status
            feature["last_updated"] = datetime.now().isoformat()

            # Track completion
            if status == "complete" and old_status != "complete":
                feature["completed"] = datetime.now().isoformat()

        # Extract metadata from spec
        spec_metadata = self.extract_spec_metadata(feature_id)
        feature.update(spec_metadata)

        # Refresh metrics
        if refresh_metrics:
            metrics = self.get_test_metrics(feature_id)
            feature["metrics"] = metrics

        self._save_tracking_data()
        print(f"✅ Updated tracking data for {feature_id}")

    def generate_report(self, format_type: str = "markdown") -> str:
        """Generate a report of all features."""
        features = self.tracking_data.get("features", {})

        if format_type == "markdown":
            return self._generate_markdown_report(features)
        elif format_type == "json":
            return json.dumps(features, indent=2)
        else:
            return str(features)

    def _generate_markdown_report(self, features: dict) -> str:
        """Generate markdown format report."""
        lines = [
            "# FairDM Feature Tracking Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Features**: {len(features)}",
            "",
            "## Feature Summary",
            "",
            "| Feature ID | Title | Status | Tests | Coverage | Started | Completed |",
            "|------------|-------|--------|-------|----------|---------|-----------|",
        ]

        for feature_id, data in sorted(features.items()):
            title = data.get("title", "N/A")
            status = data.get("status", "unknown")
            metrics = data.get("metrics", {})
            tests = metrics.get("tests_total", 0)
            coverage = metrics.get("coverage_percent", 0)
            started = data.get("started", "N/A")[:10]
            completed = data.get("completed", "-")[:10] if data.get("completed") else "-"

            # Truncate title if too long
            if len(title) > 40:
                title = title[:37] + "..."

            status_emoji = {"complete": "✅", "in-progress": "🚧", "draft": "📝"}.get(
                status.lower(), "❓"
            )

            lines.append(
                f"| {feature_id} | {title} | {status_emoji} {status} | "
                f"{tests} | {coverage:.1f}% | {started} | {completed} |"
            )

        lines.extend(
            [
                "",
                "## Feature Details",
                "",
            ]
        )

        for feature_id, data in sorted(features.items()):
            title = data.get("title", "Unknown Feature")
            status = data.get("status", "unknown")
            branch = data.get("branch", "N/A")
            user_stories = data.get("user_stories_count", 0)
            metrics = data.get("metrics", {})

            lines.extend(
                [
                    f"### {feature_id}: {title}",
                    "",
                    f"- **Status**: {status}",
                    f"- **Branch**: `{branch}`",
                    f"- **User Stories**: {user_stories}",
                    f"- **Started**: {data.get('started', 'N/A')}",
                ]
            )

            if data.get("completed"):
                lines.append(f"- **Completed**: {data['completed']}")

            if metrics:
                lines.extend(
                    [
                        f"- **Tests**: {metrics.get('tests_total', 0)}",
                        f"- **Coverage**: {metrics.get('coverage_percent', 0):.1f}%",
                    ]
                )
                if metrics.get("test_paths"):
                    lines.append(f"  - Test paths: {', '.join(metrics['test_paths'])}")

            lines.append("")

        return "\n".join(lines)

    def sync_all_features(self) -> None:
        """Discover and update all features."""
        discovered = self.discover_features()
        print(f"📊 Discovered {len(discovered)} features")

        for feature_id in discovered:
            print(f"  Syncing {feature_id}...", end=" ")
            try:
                self.update_feature(feature_id, refresh_metrics=True)
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

        print(f"\n✅ Synced {len(discovered)} features")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="FairDM Feature Tracker")
    parser.add_argument(
        "--feature", help="Feature ID (e.g., 008-plugin-system)", type=str
    )
    parser.add_argument(
        "--status",
        help="Update feature status",
        choices=["draft", "in-progress", "complete"],
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate tracking report",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Sync all features from specs directory",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Report format",
    )

    args = parser.parse_args()

    tracker = FeatureTracker()

    if args.sync:
        tracker.sync_all_features()
    elif args.feature:
        tracker.update_feature(args.feature, status=args.status)
    elif args.report:
        report = tracker.generate_report(format_type=args.format)
        print(report)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
