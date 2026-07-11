from __future__ import annotations

import cv2
import numpy as np


def segment_candidate_region(image: np.ndarray, min_area_fraction: float = 0.01) -> dict:
    """Segment the most suspicious high-contrast region in an image."""

    img = np.asarray(image, dtype=np.float32)
    if img.ndim == 3:
        img = img.mean(axis=2)

    norm = img
    if float(norm.max()) > float(norm.min()):
        norm = (norm - norm.min()) / (norm.max() - norm.min())
    edges = cv2.Canny((norm * 255).astype(np.uint8), 40, 120)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width = img.shape[:2]
    min_area = height * width * min_area_fraction
    mask = np.zeros((height, width), dtype=np.uint8)
    best_box = [0, 0, width, height]
    best_area = 0.0

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area or area <= best_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        best_area = area
        best_box = [int(x), int(y), int(w), int(h)]

    if best_area > 0:
        x, y, w, h = best_box
        mask[y : y + h, x : x + w] = 1

    return {
        "mask": mask,
        "bbox": best_box,
        "area_fraction": float(mask.mean()),
    }
