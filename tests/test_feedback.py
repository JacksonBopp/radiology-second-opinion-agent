from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_submit_and_list_feedback(auth_headers):
    payload = {
        "scan_id": "1.2.3.4.5",
        "original_findings": [{"label": "pneumonia", "confidence": 0.7}],
        "corrected_findings": [{"label": "pneumonia", "confidence": 0.95}],
        "notes": "Confirmed on follow-up CT",
    }

    post_resp = client.post("/feedback", json=payload, headers=auth_headers)
    assert post_resp.status_code == 200
    body = post_resp.json()
    assert body["scan_id"] == "1.2.3.4.5"
    assert body["reviewer"] == "dev"
    assert body["id"] is not None

    get_resp = client.get("/feedback", params={"scan_id": "1.2.3.4.5"}, headers=auth_headers)
    assert get_resp.status_code == 200
    entries = get_resp.json()
    assert len(entries) == 1
    assert entries[0]["notes"] == "Confirmed on follow-up CT"


def test_list_feedback_filters_by_scan_id(auth_headers):
    client.post("/feedback", json={"scan_id": "scan-a"}, headers=auth_headers)
    client.post("/feedback", json={"scan_id": "scan-b"}, headers=auth_headers)

    resp = client.get("/feedback", params={"scan_id": "scan-a"}, headers=auth_headers)
    entries = resp.json()

    assert len(entries) == 1
    assert entries[0]["scan_id"] == "scan-a"


def test_submit_feedback_requires_auth():
    resp = client.post("/feedback", json={"scan_id": "scan-a"})
    assert resp.status_code == 401
