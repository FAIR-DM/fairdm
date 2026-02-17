# Feature Specification Tracking

Automated tracking system for FairDM feature development that captures metrics, status, and progress for project management and reporting.

## Overview

The feature tracking system provides:
- **Automated metrics collection**: Test counts, coverage percentages, implementation dates
- **CI/CD integration**: Automatic updates on PR merge and branch pushes
- **Visual dashboards**: HTML dashboard with charts and metrics
- **Markdown reports**: Shareable reports for stakeholders
- **Git-based tracking**: Tracks development timeline and milestones

## Quick Start

### 1. Initial Sync

Discover and sync all existing features:

```bash
poetry run python scripts/feature_tracker.py --sync
```

This creates `feature-tracking.yaml` with metadata from all `specs/*/spec.md` files.

### 2. Update Feature Status

When starting work on a feature:

```bash
poetry run python scripts/feature_tracker.py --feature 008-plugin-system --status in-progress
```

When completing a feature:

```bash
poetry run python scripts/feature_tracker.py --feature 008-plugin-system --status complete
```

### 3. Generate Reports

Markdown report (for stakeholders):

```bash
poetry run python scripts/feature_tracker.py --report
```

JSON export (for programmatic access):

```bash
poetry run python scripts/feature_tracker.py --report --format json
```

### 4. Generate Dashboard

Create interactive HTML dashboard:

```bash
poetry run python scripts/generate_feature_dashboard.py
```

Open `feature-dashboard.html` in your browser to see visual metrics.

## Tracked Metrics

For each feature, the system tracks:

### Metadata (from spec.md)
- Feature ID (e.g., `008-plugin-system`)
- Title
- Feature branch name
- User story count
- Creation date

### Lifecycle Dates
- `started`: First tracked (ISO 8601 timestamp)
- `completed`: When status changed to "complete"
- `last_updated`: Most recent status change

### Test Metrics
- Total test count
- Test file paths
- Coverage percentage (per module)
- Last test run timestamp

### Status
- `draft`: Specification in progress
- `in-progress`: Active development
- `complete`: Implementation finished

## Automation

### GitHub Actions Integration

The `.github/workflows/feature-tracking.yml` workflow automatically:

1. **On feature branch push**: Updates test metrics and status to `in-progress`
2. **On PR merge to main**: Updates status to `complete` and captures completion date
3. **On main branch push**: Syncs all features and commits `feature-tracking.yaml`
4. **On every run**: Generates and uploads tracking report as artifact

### Manual Updates

You can also update tracking data manually:

```bash
# Just refresh metrics without changing status
poetry run python scripts/feature_tracker.py --feature 006-core-measurements

# Update status only
poetry run python scripts/feature_tracker.py --feature 006-core-measurements --status complete
```

## File Structure

```
fairdm/
├── feature-tracking.yaml          # Central tracking database (YAML)
├── feature-dashboard.html         # Generated HTML dashboard
├── FEATURE_TRACKING_REPORT.md     # Generated markdown report (CI artifact)
├── scripts/
│   ├── feature_tracker.py         # Core tracking CLI
│   └── generate_feature_dashboard.py  # Dashboard generator
└── specs/
    ├── 001-fairdm-setup/
    │   └── spec.md               # Metadata source
    ├── 002-fairdm-registry/
    │   └── spec.md
    └── ...
```

## Data Format

### feature-tracking.yaml

```yaml
features:
  008-plugin-system:
    id: "008-plugin-system"
    title: "Plugin System for Model Extensibility"
    branch: "008-plugin-system"
    status: "in-progress"
    user_stories_count: 5
    started: "2026-02-17T10:30:00"
    last_updated: "2026-02-17T14:20:00"
    completed: null
    metrics:
      tests_total: 42
      tests_passed: 42
      tests_failed: 0
      coverage_percent: 87.5
      test_paths:
        - "tests/test_contrib/test_plugins/"
      last_test_run: "2026-02-17T14:20:00"
```

## Reporting for Stakeholders

### Weekly Status Report

Generate a markdown report for your workgroup:

```bash
poetry run python scripts/feature_tracker.py --report > weekly-report.md
```

Share `weekly-report.md` via email or wiki.

### Dashboard for Management

Generate the dashboard before meetings:

```bash
poetry run python scripts/generate_feature_dashboard.py
```

Open `feature-dashboard.html` and present metrics visually.

### Metrics Included

Reports show:
- ✅ Features completed this week
- 🚧 Features in active development
- 📊 Total test coverage across all features
- 📈 Progress trends (tests added, coverage improvements)
- 📅 Timeline (started/completed dates)

## Custom Metrics

### Adding Feature-Specific Test Paths

Edit `feature_tracker.py` method `_get_test_paths()`:

```python
def _get_test_paths(self, feature_id: str) -> list[str]:
    mappings = {
        "008-plugin-system": ["tests/test_contrib/test_plugins/"],
        "009-your-feature": ["tests/test_your_feature/"],  # Add your mapping
        # ...
    }
    return mappings.get(feature_id, [])
```

### Adding Module Coverage Tracking

Edit `feature_tracker.py` method `_get_coverage()`:

```python
module_mappings = {
    "008-plugin-system": "fairdm.contrib.plugins",
    "009-your-feature": "fairdm.your_module",  # Add your mapping
    # ...
}
```

## CI/CD Workflow Details

The GitHub Actions workflow runs on:
- Push to `main`, `feature/**`, or `[0-9][0-9][0-9]-*` branches
- Pull request events (opened, synchronized, closed/merged)
- Manual `workflow_dispatch` trigger

**What it does**:
1. Extracts feature ID from branch name (e.g., `008-plugin-system`)
2. Runs pytest with coverage collection
3. Parses test results and coverage data
4. Updates `feature-tracking.yaml` with new metrics
5. Generates markdown report as artifact
6. Commits `feature-tracking.yaml` back to main (on main branch only)

## Best Practices

1. **Use conventional branch names**: `008-plugin-system` (matches feature ID)
2. **Update status manually** when starting/completing features
3. **Sync regularly**: Run `--sync` weekly to catch metadata changes
4. **Review dashboards before standups**: Generate fresh dashboards for team meetings
5. **Archive tracking data**: Commit `feature-tracking.yaml` to version control
6. **Document in spec.md**: Keep spec metadata current (branch name, status, created date)

## Troubleshooting

### Coverage shows 0%

- Ensure `.coverage` file exists (run tests with `--cov` first)
- Check module name mappings in `_get_coverage()`
- Verify coverage.py is installed: `poetry run pip show coverage`

### Test count is 0

- Verify test path mappings in `_get_test_paths()`
- Ensure tests are discoverable by pytest
- Check test file naming (`test_*.py` or `*_test.py`)

### Feature not discovered

- Ensure `specs/###-feature-name/spec.md` exists
- Run `--sync` to force rediscovery
- Check spec.md has proper frontmatter (see existing specs)

## Future Enhancements

Potential additions:
- 📊 Grafana/Prometheus integration for live dashboards
- 🔔 Slack/email notifications on status changes
- 📈 Trend analysis (velocity, burndown charts)
- 🏷️ Tagging and filtering (by priority, team, milestone)
- 🔍 Diff highlighting (what changed since last report)
- 📦 Release note generation from completed features
