from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_rejects_missing_api_key():
    resp = client.get("/feedback")
    assert resp.status_code == 401


def test_rejects_wrong_api_key():
    resp = client.get("/feedback", headers={"X-API-Key": "not-a-real-key"})
    assert resp.status_code == 401


def test_accepts_valid_api_key(auth_headers):
    resp = client.get("/feedback", headers=auth_headers)
    assert resp.status_code == 200
