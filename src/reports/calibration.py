"""Confidence calibration and uncertainty communication.

Fulfills Task 5.7. Takes the raw probabilities produced by the
Differential Diagnosis Agent (already Bayesian-updated in
`src.agent.diagnosis`) and the raw per-finding confidences from the ML
vision pipeline, and turns them into calibrated, clinician-facing
language.

Why this exists as its own step (rather than reporting raw floats):
- Radiologists reading a second-opinion draft need consistent,
  well-hedged language, not a bare percentage that implies false
  precision.
- Raw model confidence is not the same as calibrated probability of
  correctness — vision models in particular are frequently
  overconfident. Once Nick's models are trained, `temperature` below
  is the hook for applying a fitted calibration curve (e.g. Platt
  scaling / temperature scaling) before bucketing; today it defaults
  to 1.0 (no-op) since no calibration set exists yet.
"""

from __future__ import annotations

import math

from src.reports.schemas import ConfidenceLevel

# ---------------------------------------------------------------------------
# Bucket thresholds
# ---------------------------------------------------------------------------

_THRESHOLDS: list[tuple[float, ConfidenceLevel]] = [
    (0.85, ConfidenceLevel.VERY_HIGH),
    (0.65, ConfidenceLevel.HIGH),
    (0.40, ConfidenceLevel.MODERATE),
    (0.20, ConfidenceLevel.LOW),
    (0.0, ConfidenceLevel.VERY_LOW),
]

_PHRASES: dict[ConfidenceLevel, str] = {
    ConfidenceLevel.VERY_HIGH: "very high confidence",
    ConfidenceLevel.HIGH: "high confidence",
    ConfidenceLevel.MODERATE: "moderate confidence",
    ConfidenceLevel.LOW: "low confidence",
    ConfidenceLevel.VERY_LOW: "very low confidence",
}

# Language used in the report's overall caveat, scaled by how much the
# top differential dominates the distribution (see `summarize_uncertainty`).
_UNCERTAINTY_NOTES: dict[ConfidenceLevel, str] = {
    ConfidenceLevel.VERY_HIGH: (
        "The leading diagnosis is well supported by the available evidence, "
        "but this remains an AI-assisted draft and requires radiologist "
        "confirmation before any clinical action is taken."
    ),
    ConfidenceLevel.HIGH: (
        "The leading diagnosis is reasonably well supported, though "
        "meaningful alternatives remain. Radiologist review is required."
    ),
    ConfidenceLevel.MODERATE: (
        "No single diagnosis clearly dominates the differential. This "
        "draft should be treated as a starting point for radiologist "
        "review, not a conclusion."
    ),
    ConfidenceLevel.LOW: (
        "The available evidence does not strongly favor any diagnosis in "
        "the differential. Additional clinical correlation and radiologist "
        "review are strongly recommended before proceeding."
    ),
    ConfidenceLevel.VERY_LOW: (
        "Confidence across the differential is low. This draft is not "
        "sufficient on its own to guide clinical decisions and requires "
        "full radiologist evaluation."
    ),
}


def apply_temperature(probability: float, temperature: float = 1.0) -> float:
    """Apply temperature scaling to a probability before bucketing.

    `temperature > 1.0` softens (reduces) overconfident probabilities;
    `temperature < 1.0` sharpens them. Defaults to a no-op (1.0) until a
    calibration set is available from Nick's trained models (Task 3.6 /
    7.5), at which point a fitted temperature can be passed in here.
    """
    if temperature == 1.0 or probability <= 0.0 or probability >= 1.0:
        return min(1.0, max(0.0, probability))

    # Standard logit-space temperature scaling.
    logit = math.log(probability / (1 - probability))
    scaled_logit = logit / temperature
    return 1 / (1 + math.exp(-scaled_logit))


def confidence_level_for(probability: float, temperature: float = 1.0) -> ConfidenceLevel:
    """Map a (temperature-scaled) probability to a calibrated confidence bucket."""
    calibrated = apply_temperature(probability, temperature)
    for threshold, level in _THRESHOLDS:
        if calibrated >= threshold:
            return level
    return ConfidenceLevel.VERY_LOW


def confidence_phrase(probability: float, temperature: float = 1.0) -> str:
    """Human-readable confidence statement, e.g. 'moderate confidence (approximately 55%)'."""
    calibrated = apply_temperature(probability, temperature)
    level = confidence_level_for(probability, temperature)
    return f"{_PHRASES[level]} (approximately {calibrated:.0%})"


def summarize_uncertainty(
    top_probability: float, num_diagnoses: int, temperature: float = 1.0
) -> tuple[ConfidenceLevel, str]:
    """Produce the report's overall confidence level and uncertainty note.

    Uses the top-ranked differential diagnosis probability, discounted
    slightly when the differential is very short (fewer alternatives
    considered means less confidence the space of possibilities was
    adequately explored).
    """
    adjusted = top_probability
    if num_diagnoses <= 1:
        adjusted *= 0.85

    level = confidence_level_for(adjusted, temperature)
    return level, _UNCERTAINTY_NOTES[level]


def severity_descriptor(severity: float) -> str:
    """Map a 0-1 severity score to a plain-language descriptor."""
    if severity >= 0.75:
        return "severe"
    if severity >= 0.45:
        return "moderate"
    if severity > 0.0:
        return "mild"
    return "not specified"
