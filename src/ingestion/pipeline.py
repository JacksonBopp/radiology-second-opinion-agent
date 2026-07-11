import tempfile
from pathlib import Path

from .dicom_loader import load_dicom
from .metadata import extract_metadata
from .preprocess import normalize_pixels, resize_image, to_uint8
from src.vision.pipeline import analyze_image


def process_scan_bytes(filename: str, content: bytes) -> dict:
    """Run raw DICOM bytes through ingestion + preprocessing and return
    a JSON-safe result. Shared by the FastAPI endpoint and the async
    worker task so both entry points stay in sync.

    The vision layer uses a deterministic baseline so local tests and demos do
    not require downloading large model weights.
    """
    suffix = Path(filename).suffix or ".dcm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        scan = load_dicom(tmp_path)
        metadata = extract_metadata(scan.dataset)
        normalized = normalize_pixels(scan.pixel_array)
        resized = resize_image(normalized, target_size=(224, 224))
        image_uint8 = to_uint8(resized)
        vision = analyze_image(image_uint8)

        return {
            "filename": filename,
            "metadata": metadata.__dict__,
            "pixel_stats": {
                "mean": float(normalized.mean()),
                "std": float(normalized.std()),
                "processed_shape": list(image_uint8.shape),
            },
            "findings": vision["findings"],
            "vision": vision,
            "status": "analyzed",
        }
    finally:
        tmp_path.unlink(missing_ok=True)
