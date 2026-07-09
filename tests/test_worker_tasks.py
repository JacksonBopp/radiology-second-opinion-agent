from src.worker.tasks import process_scan


def test_process_scan_task_runs_synchronously(ct_dicom_path):
    with open(ct_dicom_path, "rb") as f:
        content = f.read()

    result = process_scan.run("CT_small.dcm", content)

    assert result["status"] == "preprocessed"
    assert result["metadata"]["rows"] is not None
