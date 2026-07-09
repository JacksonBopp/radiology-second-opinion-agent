import json
import os
import sqlite3
from pathlib import Path

from pydantic import BaseModel

DEFAULT_FEEDBACK_DB = Path(__file__).resolve().parent.parent.parent / "feedback.db"


def _get_feedback_db_path() -> Path:
    return Path(os.environ.get("FEEDBACK_DB_PATH", str(DEFAULT_FEEDBACK_DB)))


def init_feedback_db(db_path: Path | None = None) -> None:
    db_path = db_path or _get_feedback_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                original_findings TEXT,
                corrected_findings TEXT,
                notes TEXT,
                reviewer TEXT NOT NULL
            )
            """
        )


class FeedbackIn(BaseModel):
    scan_id: str
    original_findings: list[dict] = []
    corrected_findings: list[dict] = []
    notes: str | None = None


class FeedbackOut(FeedbackIn):
    id: int
    timestamp: str
    reviewer: str


def save_feedback(
    feedback: FeedbackIn, reviewer: str, db_path: Path | None = None
) -> FeedbackOut:
    db_path = db_path or _get_feedback_db_path()
    init_feedback_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO feedback
                (timestamp, scan_id, original_findings, corrected_findings, notes, reviewer)
            VALUES (datetime('now'), ?, ?, ?, ?, ?)
            """,
            (
                feedback.scan_id,
                json.dumps(feedback.original_findings),
                json.dumps(feedback.corrected_findings),
                feedback.notes,
                reviewer,
            ),
        )
        row = conn.execute(
            "SELECT * FROM feedback WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    return _row_to_feedback_out(row)


def list_feedback(scan_id: str | None = None, db_path: Path | None = None) -> list[FeedbackOut]:
    db_path = db_path or _get_feedback_db_path()
    init_feedback_db(db_path)
    with sqlite3.connect(db_path) as conn:
        if scan_id:
            rows = conn.execute(
                "SELECT * FROM feedback WHERE scan_id = ? ORDER BY id DESC", (scan_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM feedback ORDER BY id DESC").fetchall()

    return [_row_to_feedback_out(row) for row in rows]


def _row_to_feedback_out(row: tuple) -> FeedbackOut:
    (id_, timestamp, scan_id, original_findings, corrected_findings, notes, reviewer) = row
    return FeedbackOut(
        id=id_,
        timestamp=timestamp,
        scan_id=scan_id,
        original_findings=json.loads(original_findings) if original_findings else [],
        corrected_findings=json.loads(corrected_findings) if corrected_findings else [],
        notes=notes,
        reviewer=reviewer,
    )
