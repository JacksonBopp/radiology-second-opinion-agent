import os
import sqlite3
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

DEFAULT_AUDIT_DB = Path(__file__).resolve().parent.parent.parent / "audit_log.db"


def _get_audit_db_path() -> Path:
    return Path(os.environ.get("AUDIT_DB_PATH", str(DEFAULT_AUDIT_DB)))


def init_audit_db(db_path: Path | None = None) -> None:
    db_path = db_path or _get_audit_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                actor TEXT,
                client_host TEXT
            )
            """
        )


def log_request(
    method: str,
    path: str,
    status_code: int,
    actor: str | None,
    client_host: str | None,
    db_path: Path | None = None,
) -> None:
    db_path = db_path or _get_audit_db_path()
    init_audit_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO audit_log (timestamp, method, path, status_code, actor, client_host) "
            "VALUES (datetime('now'), ?, ?, ?, ?, ?)",
            (method, path, status_code, actor, client_host),
        )


def list_audit_events(db_path: Path | None = None, limit: int = 100) -> list[dict]:
    db_path = db_path or _get_audit_db_path()
    init_audit_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Logs every request to a SQLite audit trail: who (via the
    authenticated actor set on request.state by the auth dependency),
    what endpoint, and the resulting status code. Required for medical
    systems where every access to patient scan data must be traceable.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        actor = getattr(request.state, "actor", None)
        client_host = request.client.host if request.client else None
        log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            actor=actor,
            client_host=client_host,
        )
        return response
