from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".dcm"}


@dataclass(frozen=True)
class DatasetRecord:
    """A single image entry in a prepared CheXpert/NIH-style manifest."""

    image_path: str
    dataset: str
    split: str
    labels: dict[str, int]


def _read_labels(labels_csv: Path | None) -> dict[str, dict[str, int]]:
    if labels_csv is None or not labels_csv.exists():
        return {}

    with labels_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        rows: dict[str, dict[str, int]] = {}
        for row in reader:
            path = row.get("Path") or row.get("path") or row.get("image_path")
            if not path:
                continue
            labels: dict[str, int] = {}
            for key, value in row.items():
                if key in {"Path", "path", "image_path", "split"}:
                    continue
                if value in {"", None}:
                    continue
                try:
                    labels[key] = 1 if float(value) > 0 else 0
                except ValueError:
                    continue
            rows[Path(path).name] = labels
        return rows


def build_dataset_manifest(
    data_root: str | Path,
    dataset_name: str,
    split: str = "train",
    labels_csv: str | Path | None = None,
) -> list[DatasetRecord]:
    """Create a normalized manifest for CheXpert or NIH ChestX-ray14 files.

    The function works with the local filesystem only. It does not download the
    source datasets because both datasets require separate access/acceptance
    steps outside the repo.
    """

    root = Path(data_root)
    labels_by_name = _read_labels(Path(labels_csv) if labels_csv else None)
    records: list[DatasetRecord] = []

    for image_path in sorted(root.rglob("*")):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        records.append(
            DatasetRecord(
                image_path=str(image_path),
                dataset=dataset_name,
                split=split,
                labels=labels_by_name.get(image_path.name, {}),
            )
        )

    return records
