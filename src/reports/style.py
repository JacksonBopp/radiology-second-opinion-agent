"""Adapt structured findings/diagnoses into radiology report prose style.

Fulfills Task 5.10. Two responsibilities live here:

1. Mock-mode template rendering: deterministic, rule-based prose
   generation used when no LLM API key is configured (matching the
   "mock data first" pattern used throughout `src.agent`). This keeps
   the pipeline fully runnable and testable without API costs.
2. `enforce_radiology_register()`: a light-touch cleanup pass applied
   to *any* section text — mock-generated or real-LLM-generated —
   so output is consistently declarative, hedged, and free of
   first-person/conversational language before it reaches a report.

Real-LLM section text (once API keys are wired into `generator.py`)
should always be passed through `enforce_radiology_register()` before
being placed into a `ReportSection`, so mock and real paths converge
on the same house style.
"""

from __future__ import annotations

import re

from src.agent.state import DifferentialDiagnosis, Finding
from src.reports import calibration

# Phrases that read as conversational/first-person rather than a clinical
# report register; stripped or replaced if an LLM slips into them.
_BANNED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bI think\b", re.IGNORECASE), "Findings suggest"),
    (re.compile(r"\bI believe\b", re.IGNORECASE), "Findings suggest"),
    (re.compile(r"\bIn my opinion\b", re.IGNORECASE), "Based on the available evidence"),
    (re.compile(r"\bcertainly\b", re.IGNORECASE), "likely"),
    (re.compile(r"\bdefinitely\b", re.IGNORECASE), "likely"),
    (re.compile(r"\b100% (?:certain|sure)\b", re.IGNORECASE), "highly suspicious for"),
]


def enforce_radiology_register(text: str) -> str:
    """Normalize whitespace and strip overconfident/conversational phrasing."""
    cleaned = text.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    for pattern, replacement in _BANNED_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


# ---------------------------------------------------------------------------
# Mock-mode section templates
# ---------------------------------------------------------------------------


def render_findings_section(findings: list[Finding]) -> str:
    if not findings:
        return (
            "No acute abnormalities were flagged by the automated vision "
            "pipeline. Clinical correlation is advised, as subtle findings "
            "may not be captured by automated detection."
        )
    parts = []
    for f in findings:
        loc = f" within the {f.location.lower()}" if f.location else ""
        severity = calibration.severity_descriptor(f.severity)
        severity_clause = f", appearing {severity} in degree" if severity != "not specified" else ""
        parts.append(
            f"{f.label}{loc} is noted{severity_clause} "
            f"({calibration.confidence_phrase(f.confidence)})."
        )
    return " ".join(parts)


def render_impression_section(diagnoses: list[DifferentialDiagnosis]) -> str:
    if not diagnoses:
        return (
            "No specific impression can be generated from the current "
            "findings; overall study appears within normal limits pending "
            "radiologist review."
        )
    top = diagnoses[0]
    lead = (
        f"Findings are most consistent with {top.diagnosis.lower()} "
        f"({calibration.confidence_phrase(top.probability)})."
    )
    if len(diagnoses) > 1:
        alternatives = ", ".join(d.diagnosis for d in diagnoses[1:3])
        lead += f" {alternatives} should also be considered in the differential."
    return lead


def render_recommendation_section(
    diagnoses: list[DifferentialDiagnosis], guideline_texts: list[str]
) -> str:
    if not diagnoses:
        return "Routine follow-up as clinically indicated."

    top = diagnoses[0]
    base = (
        f"Clinical correlation and radiologist confirmation are recommended "
        f"before acting on the leading impression of {top.diagnosis.lower()}."
    )
    if guideline_texts:
        base += (
            f" Management should be guided by applicable clinical guidelines, "
            f"including: {guideline_texts[0]}."
        )
    if top.probability < 0.5:
        base += (
            " Given the relatively low leading probability, consider "
            "additional imaging or follow-up to narrow the differential."
        )
    return base
