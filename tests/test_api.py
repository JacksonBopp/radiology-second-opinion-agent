from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_upload_scan_requires_auth(ct_dicom_path):
    with open(ct_dicom_path, "rb") as f:
        resp = client.post(
            "/scans", files={"file": ("CT_small.dcm", f, "application/dicom")}
        )

    assert resp.status_code == 401


def test_upload_scan_returns_metadata_and_pixel_stats(ct_dicom_path, auth_headers):
    with open(ct_dicom_path, "rb") as f:
        resp = client.post(
            "/scans",
            files={"file": ("CT_small.dcm", f, "application/dicom")},
            headers=auth_headers,
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "analyzed"
    assert body["metadata"]["modality"] is not None
    assert body["pixel_stats"]["processed_shape"] == [224, 224]
    assert isinstance(body["findings"], list)
    assert body["vision"]["model_name"] == "deterministic-vision-baseline"
    assert body["vision"]["explainability"]["heatmap_shape"] == [224, 224]


def test_upload_scan_rejects_empty_file(auth_headers):
    resp = client.post(
        "/scans", files={"file": ("empty.dcm", b"", "application/dicom")}, headers=auth_headers
    )
    assert resp.status_code == 400


def test_upload_scan_rejects_invalid_dicom(auth_headers):
    resp = client.post(
        "/scans",
        files={"file": ("bad.dcm", b"not a dicom file", "application/dicom")},
        headers=auth_headers,
    )
    assert resp.status_code == 422
