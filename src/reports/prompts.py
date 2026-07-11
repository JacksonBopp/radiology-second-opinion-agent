"""Prompt engineering for the report generation pipeline.

Fulfills Task 4.8. These prompts are written for the LLM configured in
the "Reviewing Implementation Plan Options" decision (Claude 3 Haiku —
strong reasoning + strict JSON structuring, same model already used by
the Retrieval and Diagnosis agents) but are model-agnostic in shape so
Sonnet/Opus can be swapped in without rewriting the pipeline.

Two prompts are defined:
- SYSTEM_PROMPT: fixed persona + hard rules (used on every call).
- build_report_prompt(): assembles the per-scan user turn from the
  agent state (findings, differential diagnoses, similar cases,
  literature/guidelines).

`generator.py` calls `build_report_prompt()` and, when an API key is
configured, sends both to the LLM and expects back JSON matching
`REPORT_JSON_SCHEMA_HINT` below. In mock mode (no key), `generator.py`
never calls the LLM at all and instead uses deterministic templates —
but these prompts are still exercised/tested so the wording is ready
the moment real API keys are wired in (per the "mock data first, real
APIs later" plan).
"""

from __future__ import annotations

from typing import Any

from src.agent.state import DifferentialDiagnosis, Finding, LiteratureResult, SimilarCase

SYSTEM_PROMPT = """You are a clinical language model assisting a radiologist with a \
SECOND OPINION draft. You do not make final diagnoses and you are not a \
substitute for a licensed radiologist's interpretation.

Hard rules:
1. Only reference findings, diagnoses, cases, and guidelines that are given \
to you in the input. Never invent measurements, patient history, or citations.
2. Write in standard radiology report register: concise, declarative, \
hedged appropriately (e.g. "may represent", "cannot exclude", "favored over").
3. Always state uncertainty explicitly — never present a differential \
diagnosis as a confirmed finding.
4. Preserve the given ranking and probabilities of the differential \
diagnoses; do not re-rank them yourself.
5. Output must be valid JSON matching the requested schema exactly, with \
no markdown fences and no prose outside the JSON object.
"""

# Shown to the LLM so structured output round-trips cleanly. Kept as a
# plain string (not a live JSON-schema export) because it's a prompt
# artifact, not a validator — validation happens via `schemas.py`.
REPORT_JSON_SCHEMA_HINT = """{
  "findings_section": "string, prose summary of ML findings",
  "impression_section": "string, prose overall impression",
  "recommendation_section": "string, prose next-step recommendation",
  "diagnosis_reasoning": [
    {"diagnosis": "string, must exactly match an input diagnosis name",
     "reasoning": "string, 1-3 sentences"}
  ]
}"""


def _format_findings(findings: list[Finding]) -> str:
    if not findings:
        return "No findings were flagged by the vision pipeline."
    lines = []
    for f in findings:
        loc = f" in the {f.location}" if f.location else ""
        lines.append(
            f"- {f.label}{loc} (model confidence {f.confidence:.0%}, "
            f"severity {f.severity:.2f}/1.0)"
        )
    return "\n".join(lines)


def _format_differentials(diagnoses: list[DifferentialDiagnosis]) -> str:
    if not diagnoses:
        return "No differential diagnoses were generated."
    lines = []
    for i, d in enumerate(diagnoses, start=1):
        lines.append(
            f"{i}. {d.diagnosis} — probability {d.probability:.0%}\n"
            f"   supporting: {'; '.join(d.supporting_evidence) or 'none listed'}\n"
            f"   contradicting: {'; '.join(d.contradicting_evidence) or 'none listed'}"
        )
    return "\n".join(lines)


def _format_cases(cases: list[SimilarCase]) -> str:
    if not cases:
        return "No similar historical cases were retrieved."
    lines = []
    for c in cases:
        lines.append(
            f"- Case {c.case_id} (similarity {c.similarity_score:.0%}): "
            f"{c.description} → confirmed diagnosis: "
            f"{c.confirmed_diagnosis or 'unconfirmed'}, outcome: "
            f"{c.outcome or 'unknown'}"
        )
    return "\n".join(lines)


def _format_literature(literature: list[LiteratureResult], guidelines: list[str]) -> str:
    parts = []
    if literature:
        for lit in literature:
            parts.append(
                f"- {lit.title} ({lit.journal}, {lit.year}) — "
                f"{lit.abstract_summary or 'no summary available'}"
            )
    else:
        parts.append("No literature references were retrieved.")
    if guidelines:
        parts.append("\nRelevant clinical guidelines:")
        parts.extend(f"- {g}" for g in guidelines)
    return "\n".join(parts)


def build_report_prompt(
    scan_id: str,
    findings: list[Finding],
    differential_diagnoses: list[DifferentialDiagnosis],
    similar_cases: list[SimilarCase],
    literature_results: list[LiteratureResult],
    clinical_guidelines: list[str],
    metadata: dict[str, Any] | None = None,
) -> str:
    """Assemble the per-scan user prompt for the report generation LLM call.

    Returns a single prompt string, ready to send as the user turn
    alongside `SYSTEM_PROMPT`.
    """
    metadata = metadata or {}
    patient_context = ", ".join(f"{k}: {v}" for k, v in metadata.items()) or "not provided"

    return f"""Scan ID: {scan_id}
Patient context: {patient_context}

ML VISION FINDINGS:
{_format_findings(findings)}

DIFFERENTIAL DIAGNOSES (already ranked and probability-calibrated \
— do not reorder or recompute):
{_format_differentials(differential_diagnoses)}

SIMILAR HISTORICAL CASES:
{_format_cases(similar_cases)}

LITERATURE AND CLINICAL GUIDELINES:
{_format_literature(literature_results, clinical_guidelines)}

Using only the information above, write a radiology second-opinion \
report draft. Respond with a single JSON object matching this shape:
{REPORT_JSON_SCHEMA_HINT}
"""
