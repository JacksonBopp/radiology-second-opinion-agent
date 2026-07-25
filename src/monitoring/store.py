import os
import sqlite3
from pathlib import Path

import pandas as pd

DEFAULT_FEATURES_DB = Path(__file__).resolve().parent.parent.parent / "scan_features.db"


def _get_features_db_path() -> Path:
    return Path(os.environ.get("SCAN_FEATURES_DB_PATH", str(DEFAULT_FEATURES_DB)))


def init_features_db(db_path: Path | None = None) -> None:
    db_path = db_path or _get_features_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scan_id TEXT,
                rows INTEGER,
                columns INTEGER,
                pixel_mean REAL,
                pixel_std REAL,
                findings_count INTEGER,
                mean_probability REAL,
                max_probability REAL
            )
            """
        )


def log_scan_features(result: dict, db_path: Path | None = None) -> None:
    """Persist the feature set Evidently monitors from a single
    process_scan_bytes() result. Called on every /scans upload so
    drift reports have real production data to compare against,
    not just synthetic test batches.
    """
    db_path = db_path or _get_features_db_path()
    init_features_db(db_path)

    metadata = result.get("metadata", {})
    pixel_stats = result.get("pixel_stats", {})
    vision = result.get("vision", {})
    probabilities = vision.get("probabilities", [])

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO scan_features
                (timestamp, scan_id, rows, columns, pixel_mean, pixel_std,
                 findings_count, mean_probability, max_probability)
            VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata.get("sop_instance_uid") or result.get("filename"),
                metadata.get("rows"),
                metadata.get("columns"),
                pixel_stats.get("mean"),
                pixel_stats.get("std"),
                len(result.get("findings", [])),
                float(sum(probabilities) / len(probabilities)) if probabilities else None,
                float(max(probabilities)) if probabilities else None,
            ),
        )


def load_feature_history(db_path: Path | None = None) -> pd.DataFrame:
    db_path = db_path or _get_features_db_path()
    init_features_db(db_path)
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT * FROM scan_features ORDER BY id ASC", conn
        )
