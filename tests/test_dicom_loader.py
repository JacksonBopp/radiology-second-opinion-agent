from src.ingestion.dicom_loader import load_dicom


def test_load_dicom_returns_pixel_array(ct_dicom_path):
    scan = load_dicom(ct_dicom_path)

    assert scan.pixel_array.ndim == 2
    assert scan.pixel_array.shape == (scan.dataset.Rows, scan.dataset.Columns)


def test_load_dicom_applies_modality_lut(ct_dicom_path):
    # CT_small.dcm has RescaleSlope/RescaleIntercept set, so the
    # loaded array should differ from the raw stored pixel values
    # once the modality LUT is applied.
    import pydicom

    raw = pydicom.dcmread(ct_dicom_path)
    scan = load_dicom(ct_dicom_path)

    slope = float(raw.get("RescaleSlope", 1))
    intercept = float(raw.get("RescaleIntercept", 0))
    if slope != 1 or intercept != 0:
        assert not (scan.pixel_array == raw.pixel_array).all()


def test_load_dicom_missing_file_raises():
    import pytest

    with pytest.raises(Exception):
        load_dicom("does_not_exist.dcm")
