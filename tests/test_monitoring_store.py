from src.monitoring.store import load_feature_history, log_scan_features


def _fake_scan_result(scan_id: str, pixel_mean: float) -> dict:
    return {
        "filename": f"{scan_id}.dcm",
        "metadata": {"sop_instance_uid": scan_id, "rows": 512, "columns": 512},
        "pixel_stats": {"mean": pixel_mean, "std": 0.1, "processed_shape": [224, 224]},
        "findings": [{"label": "Pneumonia", "confidence": 0.8}],
        "vision": {"probabilities": [0.1, 0.8, 0.05]},
        "status": "analyzed",
    }


def test_log_and_load_scan_features():
    log_scan_features(_fake_scan_result("scan-1", 0.4))
    log_scan_features(_fake_scan_result("scan-2", 0.5))

    history = load_feature_history()

    assert len(history) == 2
    assert history.iloc[0]["scan_id"] == "scan-1"
    assert history.iloc[1]["pixel_mean"] == 0.5
    assert history.iloc[0]["findings_count"] == 1


def test_load_feature_history_empty_by_default():
    history = load_feature_history()
    assert len(history) == 0
    assert "pixel_mean" in history.columns
