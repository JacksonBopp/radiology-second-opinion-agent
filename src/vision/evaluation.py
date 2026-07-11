from __future__ import annotations

import numpy as np


def _binary_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    positives = y_score[y_true == 1]
    negatives = y_score[y_true == 0]
    if positives.size == 0 or negatives.size == 0:
        return 0.0

    wins = 0.0
    total = float(positives.size * negatives.size)
    for pos in positives:
        wins += float(np.sum(pos > negatives))
        wins += 0.5 * float(np.sum(pos == negatives))
    return wins / total


def evaluate_multilabel(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    """Compute core clinical benchmark metrics for a multi-label model."""

    truth = np.asarray(y_true, dtype=int)
    score = np.asarray(y_score, dtype=float)
    if truth.shape != score.shape:
        raise ValueError("y_true and y_score must have matching shapes")

    pred = score >= threshold
    tp = np.logical_and(pred, truth == 1).sum(axis=0)
    fp = np.logical_and(pred, truth == 0).sum(axis=0)
    tn = np.logical_and(~pred, truth == 0).sum(axis=0)
    fn = np.logical_and(~pred, truth == 1).sum(axis=0)

    sensitivity = np.divide(tp, tp + fn, out=np.zeros_like(tp, dtype=float), where=(tp + fn) != 0)
    specificity = np.divide(tn, tn + fp, out=np.zeros_like(tn, dtype=float), where=(tn + fp) != 0)
    auc = np.array([_binary_auc(truth[:, i], score[:, i]) for i in range(truth.shape[1])])

    return {
        "macro_auc": float(np.mean(auc)) if auc.size else 0.0,
        "macro_sensitivity": float(np.mean(sensitivity)) if sensitivity.size else 0.0,
        "macro_specificity": float(np.mean(specificity)) if specificity.size else 0.0,
        "per_label": [
            {
                "auc": float(auc[i]),
                "sensitivity": float(sensitivity[i]),
                "specificity": float(specificity[i]),
            }
            for i in range(truth.shape[1])
        ],
    }
