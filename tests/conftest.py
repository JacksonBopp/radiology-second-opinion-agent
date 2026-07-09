import pytest
from pydicom.data import get_testdata_file


@pytest.fixture
def ct_dicom_path() -> str:
    return get_testdata_file("CT_small.dcm")


@pytest.fixture
def mr_dicom_path() -> str:
    return get_testdata_file("MR_small.dcm")


@pytest.fixture(autouse=True)
def isolated_sqlite_stores(tmp_path, monkeypatch):
    """Point the audit log and feedback stores at per-test tmp files
    so tests never read/write the real project-root databases.
    """
    monkeypatch.setenv("AUDIT_DB_PATH", str(tmp_path / "audit_log.db"))
    monkeypatch.setenv("FEEDBACK_DB_PATH", str(tmp_path / "feedback.db"))


@pytest.fixture
def auth_headers() -> dict:
    return {"X-API-Key": "dev-local-key"}
