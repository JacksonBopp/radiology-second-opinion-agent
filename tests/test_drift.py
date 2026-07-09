import pandas as pd

from src.monitoring.drift import build_drift_report, drift_summary


def test_build_drift_report_detects_shifted_feature():
    reference = pd.DataFrame({"pixel_mean": [0.4] * 50, "rows": [512] * 50})
    current = pd.DataFrame({"pixel_mean": [0.9] * 50, "rows": [512] * 50})

    snapshot = build_drift_report(reference, current)
    summary = drift_summary(snapshot)

    assert "metrics" in summary
    drifted_counts = [
        m for m in summary["metrics"] if m["metric_name"].startswith("DriftedColumnsCount")
    ]
    assert drifted_counts
    assert drifted_counts[0]["value"]["count"] >= 1
