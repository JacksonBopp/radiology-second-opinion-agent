from pathlib import Path

import pandas as pd
from evidently import Dataset, Report
from evidently.core.report import Snapshot
from evidently.presets import DataDriftPreset


def build_drift_report(reference: pd.DataFrame, current: pd.DataFrame) -> Snapshot:
    """Compare a reference batch of scan-level features against a
    current batch (e.g. pixel intensity stats, image dimensions, and
    eventually model confidence scores) and return an Evidently drift
    snapshot for distribution-shift monitoring in production.
    """
    reference_dataset = Dataset.from_pandas(reference)
    current_dataset = Dataset.from_pandas(current)

    report = Report([DataDriftPreset()])
    return report.run(reference_data=reference_dataset, current_data=current_dataset)


def save_drift_report(snapshot: Snapshot, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot.save_html(str(output_path))
    return output_path


def drift_summary(snapshot: Snapshot) -> dict:
    """Machine-readable drift result for programmatic alerting."""
    return snapshot.dict()
