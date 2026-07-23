"""Computer vision layer for chest imaging findings.

The implementation is intentionally lightweight and deterministic so the
project can run in CI without downloading model weights. The public API mirrors
the production responsibilities: dataset prep, multi-label prediction,
localization, explainability, uncertainty, severity, and evaluation.
"""

from .datasets import DatasetRecord, build_dataset_manifest
from .benchmarks import (
    CHEXPERT_BENCHMARK_TARGETS,
    BenchmarkTarget,
    compare_to_chexpert_benchmarks,
    summarize_chexpert_benchmark,
)
from .evaluation import evaluate_multilabel
from .models import CHEST_XRAY_LABELS, FindingPrediction, VisionModelBaseline
from .pipeline import analyze_image

__all__ = [
    "CHEST_XRAY_LABELS",
    "CHEXPERT_BENCHMARK_TARGETS",
    "BenchmarkTarget",
    "DatasetRecord",
    "FindingPrediction",
    "VisionModelBaseline",
    "analyze_image",
    "build_dataset_manifest",
    "compare_to_chexpert_benchmarks",
    "evaluate_multilabel",
    "summarize_chexpert_benchmark",
]
