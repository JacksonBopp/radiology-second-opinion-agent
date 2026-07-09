from dataclasses import dataclass

from pydicom.dataset import FileDataset

# Tags pulled for downstream pipeline stages (case retrieval, report
# generation). Deliberately excludes direct patient identifiers
# (PatientName, PatientID, PatientBirthDate) since those shouldn't
# flow past ingestion into the modeling/reasoning layers.
_FIELDS = (
    "Modality",
    "BodyPartExamined",
    "PatientAge",
    "PatientSex",
    "StudyDate",
    "Manufacturer",
    "Rows",
    "Columns",
    "PixelSpacing",
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "SOPInstanceUID",
)


@dataclass
class ScanMetadata:
    modality: str | None
    body_part_examined: str | None
    patient_age: str | None
    patient_sex: str | None
    study_date: str | None
    manufacturer: str | None
    rows: int | None
    columns: int | None
    pixel_spacing: list[float] | None
    study_instance_uid: str | None
    series_instance_uid: str | None
    sop_instance_uid: str | None


def extract_metadata(dataset: FileDataset) -> ScanMetadata:
    """Pull the subset of DICOM tags relevant to downstream pipeline
    stages, tolerating missing tags (common in de-identified or
    non-standard files) by falling back to None.
    """
    values = {field: dataset.get(field, None) for field in _FIELDS}

    pixel_spacing = values["PixelSpacing"]
    if pixel_spacing is not None:
        pixel_spacing = [float(v) for v in pixel_spacing]

    return ScanMetadata(
        modality=_as_str(values["Modality"]),
        body_part_examined=_as_str(values["BodyPartExamined"]),
        patient_age=_as_str(values["PatientAge"]),
        patient_sex=_as_str(values["PatientSex"]),
        study_date=_as_str(values["StudyDate"]),
        manufacturer=_as_str(values["Manufacturer"]),
        rows=int(values["Rows"]) if values["Rows"] is not None else None,
        columns=int(values["Columns"]) if values["Columns"] is not None else None,
        pixel_spacing=pixel_spacing,
        study_instance_uid=_as_str(values["StudyInstanceUID"]),
        series_instance_uid=_as_str(values["SeriesInstanceUID"]),
        sop_instance_uid=_as_str(values["SOPInstanceUID"]),
    )


def _as_str(value: object) -> str | None:
    return None if value is None else str(value)
