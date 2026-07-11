from __future__ import annotations

import numpy as np

from .explainability import gradcam_heatmap
from .localization import segment_candidate_region
from .models import VisionModelBaseline


def analyze_image(image: np.ndarray, model: VisionModelBaseline | None = None) -> dict:
    """Run the complete vision baseline on a preprocessed image."""

    active_model = model or VisionModelBaseline()
    localization = segment_candidate_region(image)
    heatmap = gradcam_heatmap(image)
    findings = active_model.predict_findings(image, localization)
    probabilities = active_model.predict_proba(image)

    return {
        "model_name": "deterministic-vision-baseline",
        "labels": active_model.labels,
        "probabilities": [round(float(p), 4) for p in probabilities],
        "findings": [finding.to_dict() for finding in findings],
        "localization": {
            "bbox": localization["bbox"],
            "area_fraction": round(float(localization["area_fraction"]), 4),
        },
        "explainability": {
            "heatmap_shape": list(heatmap.shape),
            "heatmap_max": round(float(heatmap.max()), 4),
        },
    }
