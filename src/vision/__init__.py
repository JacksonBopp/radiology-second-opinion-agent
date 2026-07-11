"""Computer vision layer for chest imaging findings.

The implementation is intentionally lightweight and deterministic so the
project can run in CI without downloading model weights. The public API mirrors
the production responsibilities: dataset prep, multi-label prediction,
localization, explainability, uncertainty, severity, and evaluation.
"""

from .datasets import DatasetRecord, build_dataset_manifest
from .evaluation import evaluate_multilabel
from .models import CHEST_XRAY_LABELS, FindingPrediction, VisionModelBaseline
from .pipeline import analyze_image

__all__ = [
    "CHEST_XRAY_LABELS",
    "DatasetRecord",
    "FindingPrediction",
    "VisionModelBaseline",
    "analyze_image",
    "build_dataset_manifest",
    "evaluate_multilabel",
]
