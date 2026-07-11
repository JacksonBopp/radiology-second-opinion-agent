from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


CHEST_XRAY_LABELS = [
    "Atelectasis",
    "Cardiomegaly",
    "Consolidation",
    "Edema",
    "Pleural Effusion",
    "Pneumonia",
    "Pneumothorax",
    "Lung Lesion",
    "Lung Opacity",
    "Fracture",
    "Support Devices",
    "Enlarged Cardiomediastinum",
    "No Finding",
    "Uncertain Finding",
]


@dataclass(frozen=True)
class FindingPrediction:
    label: str
    confidence: float
    location: str
    severity: float
    uncertainty: float
    bbox: list[int]

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": self.confidence,
            "location": self.location,
            "severity": self.severity,
            "uncertainty": self.uncertainty,
            "bbox": self.bbox,
        }


class VisionModelBaseline:
    """Deterministic multi-label chest finding baseline.

    This stands in for the planned ViT/EfficientNet + multi-label head while
    keeping the repo runnable without GPU dependencies or external weights.
    """

    def __init__(self, labels: list[str] | None = None, threshold: float = 0.55):
        self.labels = labels or CHEST_XRAY_LABELS
        self.threshold = threshold
        self.weights = self._default_weights(len(self.labels))
        self.bias = np.linspace(-1.1, 0.2, len(self.labels), dtype=np.float32)

    @staticmethod
    def _default_weights(label_count: int) -> np.ndarray:
        rng = np.random.default_rng(4002)
        weights = rng.normal(0.0, 0.45, size=(label_count, 8)).astype(np.float32)
        weights[:, 0] += np.linspace(-0.3, 0.5, label_count)
        weights[:, 2] += np.linspace(0.5, -0.3, label_count)
        return weights

    def extract_features(self, image: np.ndarray) -> np.ndarray:
        img = np.asarray(image, dtype=np.float32)
        if img.ndim == 3:
            img = img.mean(axis=2)
        if img.max() > 1.0:
            img = img / 255.0

        height, width = img.shape[:2]
        center = img[height // 4 : 3 * height // 4, width // 4 : 3 * width // 4]
        edges = cv2.Canny((img * 255).astype(np.uint8), 40, 120)
        hist = np.histogram(img, bins=16, range=(0.0, 1.0), density=True)[0]
        entropy = -float(np.sum(hist * np.log(hist + 1e-6))) / 16.0

        return np.array(
            [
                float(img.mean()),
                float(img.std()),
                float(edges.mean() / 255.0),
                float(center.mean()),
                float(np.percentile(img, 95)),
                float(np.percentile(img, 5)),
                entropy,
                float(abs(img[:, : width // 2].mean() - img[:, width // 2 :].mean())),
            ],
            dtype=np.float32,
        )

    def predict_proba(self, image: np.ndarray) -> np.ndarray:
        features = self.extract_features(image)
        logits = self.weights @ features + self.bias
        probs = 1.0 / (1.0 + np.exp(-logits))

        no_finding_idx = self.labels.index("No Finding")
        uncertain_idx = self.labels.index("Uncertain Finding")
        abnormality = float(np.mean(np.delete(probs, [no_finding_idx, uncertain_idx])))
        probs[no_finding_idx] = np.clip(1.0 - abnormality, 0.05, 0.95)
        probs[uncertain_idx] = np.clip(1.0 - abs(0.5 - abnormality) * 2.0, 0.05, 0.85)
        return probs.astype(np.float32)

    def monte_carlo_uncertainty(self, image: np.ndarray, samples: int = 12) -> np.ndarray:
        base = np.asarray(image, dtype=np.float32)
        rng = np.random.default_rng(2026)
        draws = []
        for _ in range(samples):
            noise = rng.normal(0.0, 0.015, size=base.shape).astype(np.float32)
            draws.append(self.predict_proba(np.clip(base + noise, 0.0, 1.0)))
        return np.std(np.stack(draws, axis=0), axis=0).astype(np.float32)

    def predict_findings(self, image: np.ndarray, localization: dict) -> list[FindingPrediction]:
        probs = self.predict_proba(image)
        uncertainty = self.monte_carlo_uncertainty(image)
        bbox = localization["bbox"]
        area = float(localization["area_fraction"])
        predictions: list[FindingPrediction] = []

        for idx, label in enumerate(self.labels):
            confidence = float(probs[idx])
            if label == "No Finding":
                continue
            if confidence < self.threshold and label != "Uncertain Finding":
                continue
            severity = float(np.clip(0.6 * confidence + 0.4 * area, 0.0, 1.0))
            predictions.append(
                FindingPrediction(
                    label=label,
                    confidence=round(confidence, 4),
                    location=_location_from_bbox(bbox),
                    severity=round(severity, 4),
                    uncertainty=round(float(uncertainty[idx]), 4),
                    bbox=bbox,
                )
            )

        predictions.sort(key=lambda item: item.confidence, reverse=True)
        return predictions[:5]


def _location_from_bbox(bbox: list[int]) -> str:
    x, y, w, h = bbox
    horizontal = "left" if x + w / 2 < 112 else "right"
    vertical = "upper" if y + h / 2 < 112 else "lower"
    return f"{horizontal} {vertical} lung zone"
