from fastapi.testclient import TestClient

from src.api.audit import list_audit_events
from src.api.main import app

client = TestClient(app)


def test_request_is_recorded_in_audit_log(auth_headers):
    resp = client.get("/feedback", headers=auth_headers)
    assert resp.status_code == 200

    events = list_audit_events()
    matching = [e for e in events if e["path"] == "/feedback" and e["method"] == "GET"]

    assert matching
    assert matching[0]["status_code"] == 200
    assert matching[0]["actor"] == "dev"


def test_unauthenticated_request_still_logged_without_actor():
    client.get("/feedback")

    events = list_audit_events()
    matching = [e for e in events if e["path"] == "/feedback" and e["status_code"] == 401]

    assert matching
    assert matching[0]["actor"] is None
