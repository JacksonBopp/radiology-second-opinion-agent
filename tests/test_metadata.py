import pydicom

from src.ingestion.metadata import extract_metadata


def test_extract_metadata_pulls_known_fields(ct_dicom_path):
    dataset = pydicom.dcmread(ct_dicom_path)
    meta = extract_metadata(dataset)

    assert meta.modality == dataset.Modality
    assert meta.rows == dataset.Rows
    assert meta.columns == dataset.Columns


def test_extract_metadata_excludes_direct_identifiers(ct_dicom_path):
    dataset = pydicom.dcmread(ct_dicom_path)
    meta = extract_metadata(dataset)

    assert not hasattr(meta, "patient_name")
    assert not hasattr(meta, "patient_id")


def test_extract_metadata_handles_missing_tags():
    dataset = pydicom.Dataset()
    meta = extract_metadata(dataset)

    assert meta.modality is None
    assert meta.pixel_spacing is None
