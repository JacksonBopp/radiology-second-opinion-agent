"""Structured report schemas (Pydantic models) for the GenAI report layer.

Fulfills Task 4.7. These models define the contract between the agentic
reasoning layer (Amrit's `AgentState`) and the report generation pipeline
(this package), and are what gets serialized back to the frontend / API.

Design notes:
- Kept separate from `src.agent.state` on purpose: the agent state is an
  internal LangGraph working structure, while these models are the
  *external* report contract. Report structure can evolve (e.g. adding
  sections, changing confidence language) without touching the agent
  graph, and vice versa.
- `ConfidenceLevel` gives calibrated, human-readable uncertainty language
  instead of exposing raw floats to clinicians (see `calibration.py`).
- All free-text fields are plain strings so they can be rendered directly
  into a report document or a UI panel without further transformation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Calibrated, clinician-facing confidence bucket.

    Deliberately coarse (5 buckets) rather than a raw percentage — see
    `calibration.py` for the rationale and the mapping from raw model
    probabilities to these levels.
    """

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class GuidelineReference(BaseModel):
    """A clinical guideline citation attached to a report section.

    Sourced from `AgentState.clinical_guidelines` (Literature Search
    Agent output) and surfaced in reports per Task 6.10.
    """

    text: str = Field(description="Guideline citation, e.g. society + title + year")
    relevance: str = Field(
        default="",
        description="Why this guideline applies to the current findings",
    )


class DifferentialEntry(BaseModel):
    """A single ranked differential diagnosis as it appears in a report.

    Mirrors `src.agent.state.DifferentialDiagnosis` but adds
    report-facing fields (`rank`, `confidence_level`, `confidence_phrase`)
    produced by the calibration step (Task 5.7) instead of a raw
    probability, and reformats reasoning into report prose (Task 5.10).
    """

    rank: int = Field(ge=1, description="1 = most likely")
    diagnosis: str
    probability: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    confidence_phrase: str = Field(
        description="Calibrated natural-language uncertainty statement, "
        "e.g. 'moderate confidence (approximately 55%)'"
    )
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    reasoning: str = Field(default="")


class FindingSummary(BaseModel):
    """Report-facing summary of a single ML vision finding."""

    label: str
    location: str = Field(default="")
    severity_descriptor: str = Field(
        default="", description="e.g. 'mild', 'moderate', 'severe'"
    )
    confidence_phrase: str = Field(default="")


class ReportSection(BaseModel):
    """One named section of prose within the final report."""

    heading: str
    body: str


class RadiologyReport(BaseModel):
    """The final structured second-opinion report.

    This is the top-level object returned by `generator.generate_report`
    and is what the frontend report viewer (Task 6.6) and evaluation
    tooling (Tasks 6.9 / 7.8) consume.
    """

    scan_id: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Report body, in conventional radiology report order.
    findings_summary: list[FindingSummary] = Field(default_factory=list)
    sections: list[ReportSection] = Field(
        default_factory=list,
        description="Ordered sections, typically FINDINGS, IMPRESSION, "
        "DIFFERENTIAL DIAGNOSIS, RECOMMENDATION",
    )
    differential_diagnoses: list[DifferentialEntry] = Field(default_factory=list)
    guideline_references: list[GuidelineReference] = Field(default_factory=list)
    similar_case_ids: list[str] = Field(
        default_factory=list,
        description="case_ids of similar historical cases cited as evidence",
    )

    overall_confidence_level: ConfidenceLevel = ConfidenceLevel.MODERATE
    uncertainty_note: str = Field(
        default="",
        description="Plain-language caveat about model limitations / need "
        "for radiologist confirmation",
    )

    model_version: str = Field(
        default="mock-v0", description="Identifier for the generation backend used"
    )

    def as_plain_text(self) -> str:
        """Render the report as a plain-text document (for PDF/print/eval)."""
        lines = [f"RADIOLOGY SECOND OPINION — Scan {self.scan_id}", ""]
        for section in self.sections:
            lines.append(section.heading.upper())
            lines.append(section.body)
            lines.append("")
        if self.guideline_references:
            lines.append("REFERENCED GUIDELINES")
            for ref in self.guideline_references:
                lines.append(f"- {ref.text}")
            lines.append("")
        if self.uncertainty_note:
            lines.append(self.uncertainty_note)
        return "\n".join(lines).strip()
