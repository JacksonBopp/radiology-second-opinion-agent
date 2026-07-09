from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pydicom
from pydicom.dataset import FileDataset
from pydicom.pixels import apply_modality_lut, apply_voi_lut


@dataclass
class DicomScan:
    dataset: FileDataset
    pixel_array: np.ndarray
    source_path: Path


def load_dicom(path: str | Path, apply_voi: bool = False) -> DicomScan:
    """Read a DICOM file and return its raw dataset alongside a
    modality-LUT-corrected pixel array (real-world intensity values,
    e.g. Hounsfield units for CT).

    apply_voi additionally applies the VOI LUT / windowing baked into
    the file's own tags, when present. Leave this off if you plan to
    apply your own windowing via preprocess.apply_windowing.
    """
    path = Path(path)
    dataset = pydicom.dcmread(path)

    if not hasattr(dataset, "PixelData"):
        raise ValueError(f"{path} has no PixelData element")

    pixels = dataset.pixel_array.astype(np.float64)
    pixels = apply_modality_lut(pixels, dataset)

    if apply_voi:
        pixels = apply_voi_lut(pixels, dataset)

    return DicomScan(dataset=dataset, pixel_array=pixels, source_path=path)
