from __future__ import annotations

import cv2
import numpy as np


def gradcam_heatmap(image: np.ndarray) -> np.ndarray:
    """Return a GradCAM-style saliency heatmap for the baseline model.

    A true GradCAM implementation needs a trained CNN/ViT. For this offline
    baseline, saliency is approximated from local contrast, matching the model's
    feature source and producing a stable overlay for the frontend contract.
    """

    img = np.asarray(image, dtype=np.float32)
    if img.ndim == 3:
        img = img.mean(axis=2)

    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=7)
    heatmap = np.abs(img - blurred)
    if float(heatmap.max()) > float(heatmap.min()):
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
    else:
        heatmap = np.zeros_like(heatmap, dtype=np.float32)
    return heatmap.astype(np.float32)


def heatmap_overlay(image: np.ndarray, heatmap: np.ndarray, alpha: float = 0.35) -> np.ndarray:
    base = np.asarray(image, dtype=np.float32)
    if base.ndim == 2:
        base = np.repeat(base[..., None], 3, axis=2)
    if base.max() <= 1.0:
        base = base * 255.0

    hm = np.clip(heatmap, 0.0, 1.0)
    color = cv2.applyColorMap((hm * 255).astype(np.uint8), cv2.COLORMAP_JET).astype(np.float32)
    overlay = (1.0 - alpha) * base + alpha * color
    return np.clip(overlay, 0, 255).astype(np.uint8)
