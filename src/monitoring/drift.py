from pathlib import Path

import pandas as pd
from evidently import Dataset, Report
from evidently.core.report import Snapshot
from evidently.presets import DataDriftPreset

from .store import load_feature_history

# Identifier/bookkeeping columns that aren't monitored features —
# "id" is monotonically increasing so it would always look drifted,
# and timestamp/scan_id aren't distributional signals.
_NON_FEATURE_COLUMNS = {"id", "timestamp", "scan_id"}


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


def compute_current_drift(min_samples: int = 10, reference_fraction: float = 0.5) -> Snapshot:
    """Build a drift report from real production traffic: splits the
    logged scan-feature history into an earlier "reference" window
    and a later "current" window, so drift reflects how the actual
    scan population is shifting over time rather than a synthetic
    batch.

    Raises ValueError if fewer than min_samples scans have been
    logged yet — there isn't enough history to compare against.
    """
    history = load_feature_history()
    if len(history) < min_samples:
        raise ValueError(
            f"Need at least {min_samples} logged scans to compute drift, "
            f"have {len(history)}. Process more scans through /scans first."
        )

    feature_columns = [c for c in history.columns if c not in _NON_FEATURE_COLUMNS]
    split_at = max(1, int(len(history) * reference_fraction))
    reference = history.iloc[:split_at][feature_columns]
    current = history.iloc[split_at:][feature_columns]

    return build_drift_report(reference, current)
