import pytest
import pandas as pd

from src.monitoring.drift import build_drift_report, compute_current_drift, drift_summary
from src.monitoring.store import log_scan_features


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


def _log_fake_scans(count: int, pixel_mean: float) -> None:
    for i in range(count):
        log_scan_features(
            {
                "filename": f"scan-{i}.dcm",
                "metadata": {"sop_instance_uid": f"scan-{i}", "rows": 512, "columns": 512},
                "pixel_stats": {"mean": pixel_mean, "std": 0.1, "processed_shape": [224, 224]},
                "findings": [],
                "vision": {"probabilities": [0.1, 0.2, 0.1]},
                "status": "analyzed",
            }
        )


def test_compute_current_drift_raises_with_too_little_history():
    _log_fake_scans(3, pixel_mean=0.4)

    with pytest.raises(ValueError):
        compute_current_drift(min_samples=10)


def test_compute_current_drift_splits_logged_history():
    _log_fake_scans(10, pixel_mean=0.4)

    snapshot = compute_current_drift(min_samples=10)
    summary = drift_summary(snapshot)

    assert "metrics" in summary
