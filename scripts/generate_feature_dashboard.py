"""
Generate an HTML dashboard for feature tracking.

Usage:
    poetry run python scripts/generate_feature_dashboard.py
    poetry run python scripts/generate_feature_dashboard.py --output docs/feature-dashboard.html
"""

import argparse
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
TRACKING_FILE = ROOT / "feature-tracking.yaml"


def load_tracking_data() -> dict:
    """Load feature tracking data."""
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE) as f:
            return yaml.safe_load(f) or {"features": {}}
    return {"features": {}}


def generate_html_dashboard(tracking_data: dict) -> str:
    """Generate HTML dashboard."""
    features = tracking_data.get("features", {})

    # Calculate statistics
    total_features = len(features)
    completed = sum(1 for f in features.values() if f.get("status") == "complete")
    in_progress = sum(1 for f in features.values() if f.get("status") == "in-progress")
    total_tests = sum(f.get("metrics", {}).get("tests_total", 0) for f in features.values())
    avg_coverage = (
        sum(f.get("metrics", {}).get("coverage_percent", 0) for f in features.values()) / total_features
        if total_features > 0
        else 0
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FairDM Feature Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .feature-card {{
            border-left: 4px solid #dee2e6;
            transition: transform 0.2s;
        }}
        .feature-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .status-draft {{ border-left-color: #6c757d; }}
        .status-in-progress {{ border-left-color: #0d6efd; }}
        .status-complete {{ border-left-color: #28a745; }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .progress-ring {{
            transform: rotate(-90deg);
        }}
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">FairDM Feature Dashboard</span>
            <span class="text-light">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>
        </div>
    </nav>

    <div class="container-fluid p-4">
        <!-- Summary Cards -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h2 class="display-4">{total_features}</h2>
                        <p class="mb-0">Total Features</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h2 class="display-4">{completed}</h2>
                        <p class="mb-0">Completed</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h2 class="display-4">{total_tests}</h2>
                        <p class="mb-0">Total Tests</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h2 class="display-4">{avg_coverage:.1f}%</h2>
                        <p class="mb-0">Avg Coverage</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Progress Overview -->
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">Feature Status Distribution</h5>
            </div>
            <div class="card-body">
                <div class="progress" style="height: 30px;">
                    <div class="progress-bar bg-success" role="progressbar" 
                         style="width: {(completed/total_features*100) if total_features > 0 else 0}%">
                        Complete ({completed})
                    </div>
                    <div class="progress-bar bg-primary" role="progressbar" 
                         style="width: {(in_progress/total_features*100) if total_features > 0 else 0}%">
                        In Progress ({in_progress})
                    </div>
                    <div class="progress-bar bg-secondary" role="progressbar" 
                         style="width: {((total_features-completed-in_progress)/total_features*100) if total_features > 0 else 0}%">
                        Draft ({total_features - completed - in_progress})
                    </div>
                </div>
            </div>
        </div>

        <!-- Feature Cards -->
        <div class="row g-3">
"""

    for feature_id, data in sorted(features.items()):
        title = data.get("title", "Unknown Feature")
        status = data.get("status", "draft")
        branch = data.get("branch", "N/A")
        metrics = data.get("metrics", {})
        tests = metrics.get("tests_total", 0)
        coverage = metrics.get("coverage_percent", 0)
        started = data.get("started", "N/A")[:10] if data.get("started") else "N/A"
        completed_date = data.get("completed", "-")[:10] if data.get("completed") else "-"

        status_badge_color = {
            "complete": "success",
            "in-progress": "primary",
            "draft": "secondary",
        }.get(status.lower(), "secondary")

        html += f"""
            <div class="col-md-6 col-lg-4">
                <div class="card feature-card status-{status.lower()}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">{feature_id}</h6>
                            <span class="badge bg-{status_badge_color}">{status}</span>
                        </div>
                        <p class="card-text text-muted small">{title}</p>
                        
                        <div class="row g-2 mb-2">
                            <div class="col-6">
                                <small class="text-muted">Tests:</small>
                                <div class="fw-bold">{tests}</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Coverage:</small>
                                <div class="fw-bold">{coverage:.1f}%</div>
                            </div>
                        </div>
                        
                        <div class="progress mb-2" style="height: 6px;">
                            <div class="progress-bar bg-success" style="width: {coverage}%"></div>
                        </div>
                        
                        <div class="row g-2 small text-muted">
                            <div class="col-6">
                                <strong>Started:</strong> {started}
                            </div>
                            <div class="col-6">
                                <strong>Completed:</strong> {completed_date}
                            </div>
                        </div>
                        
                        <div class="mt-2">
                            <code class="small">{branch}</code>
                        </div>
                    </div>
                </div>
            </div>
"""

    html += """
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

    return html


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate Feature Dashboard")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "feature-dashboard.html",
        help="Output HTML file path",
    )

    args = parser.parse_args()

    tracking_data = load_tracking_data()
    html = generate_html_dashboard(tracking_data)

    args.output.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard generated: {args.output}")
    print(f"   Open in browser: file://{args.output.absolute()}")


if __name__ == "__main__":
    main()
