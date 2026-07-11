"""Report generation pipeline — turns agent output into a RadiologyReport.

Fulfills Tasks 5.8 (report generation pipeline), 5.9 (differential
diagnosis ranking in reports), and 6.10 (clinical guideline references
in reports).

Two backends:
- Mock mode (default, no API key required): deterministic templates
  from `style.py` + calibrated language from `calibration.py`. This is
  what runs today and in CI, consistent with the project's
  "mock data first, real APIs later" decision.
- LLM mode (`ANTHROPIC_API_KEY` set): sends `prompts.build_report_prompt()`
  to Claude 3 Haiku (the model already selected for the Retrieval/
  Diagnosis agents) and parses structured JSON back into the same
  `RadiologyReport` schema. Falls back to mock mode on any error
  (missing package, network failure, malformed JSON) so the pipeline
  never hard-fails because of the language layer.

Usage:
    from src.reports.generator import generate_report

    report = generate_report(agent_state)   # agent_state from run_analysis_graph
    print(report.as_plain_text())
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from src.agent.state import DifferentialDiagnosis, Finding, LiteratureResult, SimilarCase
from src.reports import calibration, style
from src.reports.prompts import SYSTEM_PROMPT, build_report_prompt
from src.reports.schemas import (
    DifferentialEntry,
    FindingSummary,
    GuidelineReference,
    RadiologyReport,
    ReportSection,
)

logger = logging.getLogger(__name__)

_MODEL_NAME = "claude-3-haiku-20240307"


# ---------------------------------------------------------------------------
# Input normalization (AgentState may hold dicts or already-parsed models,
# same tolerant pattern used in src.agent.orchestrator / diagnosis)
# ---------------------------------------------------------------------------


def _parse_findings(raw: list[Any]) -> list[Finding]:
    return [f if isinstance(f, Finding) else Finding(**f) for f in raw]


def _parse_diagnoses(raw: list[Any]) -> list[DifferentialDiagnosis]:
    return [
        d if isinstance(d, DifferentialDiagnosis) else DifferentialDiagnosis(**d)
        for d in raw
    ]


def _parse_cases(raw: list[Any]) -> list[SimilarCase]:
    return [c if isinstance(c, SimilarCase) else SimilarCase(**c) for c in raw]


def _parse_literature(raw: list[Any]) -> list[LiteratureResult]:
    return [
        lit if isinstance(lit, LiteratureResult) else LiteratureResult(**lit)
        for lit in raw
    ]


# ---------------------------------------------------------------------------
# Differential diagnosis ranking → report entries (Task 5.9)
# ---------------------------------------------------------------------------


def _build_differential_entries(
    diagnoses: list[DifferentialDiagnosis],
) -> list[DifferentialEntry]:
    """Convert ranked DifferentialDiagnosis objects into report entries.

    The Diagnosis Agent (`src.agent.diagnosis`) already sorts by
    probability descending; this preserves that order and adds the
    1-indexed `rank` plus calibrated confidence language, without
    re-sorting (the prompt in `prompts.py` explicitly forbids the LLM
    path from re-ranking either, for the same reason: ranking is the
    Diagnosis Agent's job, not the report layer's).
    """
    entries: list[DifferentialEntry] = []
    for i, d in enumerate(diagnoses, start=1):
        entries.append(
            DifferentialEntry(
                rank=i,
                diagnosis=d.diagnosis,
                probability=d.probability,
                confidence_level=calibration.confidence_level_for(d.probability),
                confidence_phrase=calibration.confidence_phrase(d.probability),
                supporting_evidence=d.supporting_evidence,
                contradicting_evidence=d.contradicting_evidence,
                reasoning=d.reasoning,
            )
        )
    return entries


def _build_finding_summaries(findings: list[Finding]) -> list[FindingSummary]:
    return [
        FindingSummary(
            label=f.label,
            location=f.location,
            severity_descriptor=calibration.severity_descriptor(f.severity),
            confidence_phrase=calibration.confidence_phrase(f.confidence),
        )
        for f in findings
    ]


# ---------------------------------------------------------------------------
# Guideline references (Task 6.10)
# ---------------------------------------------------------------------------


def _build_guideline_references(
    clinical_guidelines: list[str], top_diagnosis: str
) -> list[GuidelineReference]:
    refs = []
    for text in clinical_guidelines:
        relevance = (
            f"Cited as relevant to the leading impression of {top_diagnosis.lower()}."
            if top_diagnosis
            else "Cited as relevant to the current findings."
        )
        refs.append(GuidelineReference(text=text, relevance=relevance))
    return refs


# ---------------------------------------------------------------------------
# Mock-mode section generation
# ---------------------------------------------------------------------------


def _generate_sections_mock(
    findings: list[Finding],
    diagnoses: list[DifferentialDiagnosis],
    clinical_guidelines: list[str],
) -> list[ReportSection]:
    return [
        ReportSection(
            heading="Findings",
            body=style.enforce_radiology_register(style.render_findings_section(findings)),
        ),
        ReportSection(
            heading="Impression",
            body=style.enforce_radiology_register(
                style.render_impression_section(diagnoses)
            ),
        ),
        ReportSection(
            heading="Recommendation",
            body=style.enforce_radiology_register(
                style.render_recommendation_section(diagnoses, clinical_guidelines)
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# LLM-mode section generation (real Claude 3 Haiku call)
# ---------------------------------------------------------------------------


def _generate_sections_llm(
    scan_id: str,
    findings: list[Finding],
    diagnoses: list[DifferentialDiagnosis],
    cases: list[SimilarCase],
    literature: list[LiteratureResult],
    clinical_guidelines: list[str],
    metadata: dict[str, Any],
) -> list[ReportSection] | None:
    """Attempt real-LLM section generation. Returns None on any failure
    so the caller can fall back to mock mode."""
    try:
        import anthropic  # local import: optional dependency, mock mode works without it
    except ImportError:
        logger.info("anthropic package not installed; using mock report generation.")
        return None

    try:
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        prompt = build_report_prompt(
            scan_id=scan_id,
            findings=findings,
            differential_diagnoses=diagnoses,
            similar_cases=cases,
            literature_results=literature,
            clinical_guidelines=clinical_guidelines,
            metadata=metadata,
        )
        response = client.messages.create(
            model=_MODEL_NAME,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        parsed = json.loads(text)

        return [
            ReportSection(
                heading="Findings",
                body=style.enforce_radiology_register(parsed["findings_section"]),
            ),
            ReportSection(
                heading="Impression",
                body=style.enforce_radiology_register(parsed["impression_section"]),
            ),
            ReportSection(
                heading="Recommendation",
                body=style.enforce_radiology_register(parsed["recommendation_section"]),
            ),
        ]
    except Exception as exc:  # noqa: BLE001 - deliberately broad: never break the pipeline
        logger.warning("LLM report generation failed (%s); falling back to mock mode.", exc)
        return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def generate_report(state: dict[str, Any]) -> RadiologyReport:
    """Generate a `RadiologyReport` from a completed (or partial) AgentState.

    Args:
        state: The dict returned by `run_analysis_graph`, or any dict with
            the same keys (`scan_id`, `findings`, `differential_diagnoses`,
            `similar_cases`, `literature_results`, `clinical_guidelines`,
            `metadata`).

    Returns:
        A fully populated `RadiologyReport`. Never raises for missing/
        empty state fields — mirrors the defensive style used in
        `src.agent.diagnosis.run_diagnosis`.
    """
    scan_id = state.get("scan_id", "unknown")
    metadata = state.get("metadata", {}) or {}

    findings = _parse_findings(state.get("findings", []) or [])
    diagnoses = _parse_diagnoses(state.get("differential_diagnoses", []) or [])
    cases = _parse_cases(state.get("similar_cases", []) or [])
    literature = _parse_literature(state.get("literature_results", []) or [])
    clinical_guidelines = state.get("clinical_guidelines", []) or []

    sections = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        sections = _generate_sections_llm(
            scan_id, findings, diagnoses, cases, literature, clinical_guidelines, metadata
        )
        model_version = "claude-3-haiku-20240307" if sections else "mock-v0-fallback"
    else:
        model_version = "mock-v0"

    if sections is None:
        sections = _generate_sections_mock(findings, diagnoses, clinical_guidelines)

    differential_entries = _build_differential_entries(diagnoses)
    top_diagnosis = differential_entries[0].diagnosis if differential_entries else ""

    overall_level, uncertainty_note = calibration.summarize_uncertainty(
        top_probability=differential_entries[0].probability if differential_entries else 0.0,
        num_diagnoses=len(differential_entries),
    )

    report = RadiologyReport(
        scan_id=scan_id,
        findings_summary=_build_finding_summaries(findings),
        sections=sections,
        differential_diagnoses=differential_entries,
        guideline_references=_build_guideline_references(clinical_guidelines, top_diagnosis),
        similar_case_ids=[c.case_id for c in cases],
        overall_confidence_level=overall_level,
        uncertainty_note=uncertainty_note,
        model_version=model_version,
    )

    logger.info(
        "Generated report for scan %s (%s, %d sections, %d differentials)",
        scan_id,
        model_version,
        len(report.sections),
        len(report.differential_diagnoses),
    )
    return report
