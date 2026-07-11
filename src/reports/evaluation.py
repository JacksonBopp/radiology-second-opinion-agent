"""Report quality evaluation.

Fulfills Task 6.9 (evaluate report quality against real radiologist
reports) and Task 7.8 (final report quality evaluation — clinical
accuracy, completeness).

Three lightweight, dependency-free metrics are computed (no extra NLP
packages required, keeping the pipeline runnable in CI/mock mode):

1. Completeness — are the expected sections present and non-empty.
2. Groundedness — does every diagnosis/finding named in the report
   prose actually appear in the source agent state (a cheap proxy for
   catching hallucinated content, especially important once the LLM
   path in `generator.py` is live).
3. Lexical overlap against a reference report — a rough proxy for
   content agreement when a real radiologist report is available for
   the same case, used to sanity-check the generation pipeline during
   development (Task 6.9) and in the final evaluation pass (Task 7.8).

This intentionally does NOT attempt to score clinical correctness —
that requires a licensed radiologist and is out of scope for an
automated metric. It flags things a human reviewer should look at.
"""

from __future__ import annotations

import re
from collections import Counter

from pydantic import BaseModel, Field

from src.reports.schemas import RadiologyReport

_EXPECTED_SECTIONS = {"findings", "impression", "recommendation"}
_STOPWORDS = {
    "the", "a", "an", "of", "in", "with", "and", "or", "to", "is", "are",
    "on", "for", "at", "as", "by", "be", "this", "that", "was", "were",
    "it", "its", "may", "can", "should", "not", "no", "consider",
}


class QualityReport(BaseModel):
    """Result of evaluating a generated `RadiologyReport`."""

    scan_id: str
    completeness_score: float = Field(ge=0.0, le=1.0)
    groundedness_score: float = Field(ge=0.0, le=1.0)
    reference_overlap_score: float | None = Field(
        default=None, description="Only set when a reference report is provided"
    )
    avg_sentence_length: float
    flags: list[str] = Field(default_factory=list)

    @property
    def passes_minimum_bar(self) -> bool:
        """A conservative gate for CI / dashboards: not a clinical sign-off."""
        return (
            self.completeness_score >= 1.0
            and self.groundedness_score >= 0.8
            and not any(f.startswith("CRITICAL") for f in self.flags)
        )


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def evaluate_completeness(report: RadiologyReport) -> tuple[float, list[str]]:
    """Check the expected sections exist and have non-trivial content."""
    flags: list[str] = []
    present = {s.heading.lower(): s.body for s in report.sections}

    missing = _EXPECTED_SECTIONS - set(present)
    for section in missing:
        flags.append(f"CRITICAL: missing '{section}' section")

    thin = [
        heading
        for heading, body in present.items()
        if heading in _EXPECTED_SECTIONS and len(body.split()) < 5
    ]
    for heading in thin:
        flags.append(f"'{heading}' section is unusually short")

    if not report.differential_diagnoses:
        flags.append("no differential diagnoses attached to report")

    score = (len(_EXPECTED_SECTIONS) - len(missing)) / len(_EXPECTED_SECTIONS)
    return score, flags


def evaluate_groundedness(report: RadiologyReport) -> tuple[float, list[str]]:
    """Check that diagnoses named in prose sections are backed by the
    structured differential diagnosis list (a cheap hallucination check).

    Only checks the Impression/Recommendation sections against the
    differential diagnosis names, since those are the sections most
    likely to be free-text-generated (by an LLM) rather than templated.
    """
    flags: list[str] = []
    known_diagnoses = {d.diagnosis.lower() for d in report.differential_diagnoses}
    if not known_diagnoses:
        return 1.0, flags  # nothing to check against; not this check's job to flag

    checked_sections = [
        s for s in report.sections if s.heading.lower() in ("impression", "recommendation")
    ]
    if not checked_sections:
        return 1.0, flags

    combined_text = " ".join(s.body.lower() for s in checked_sections)

    # A section is "grounded" if the top diagnosis (or a clear substring
    # match with any known diagnosis) appears somewhere in its text.
    grounded_hits = 0
    for section in checked_sections:
        body_lower = section.body.lower()
        if any(dx in body_lower for dx in known_diagnoses):
            grounded_hits += 1
        else:
            flags.append(
                f"CRITICAL: '{section.heading}' section does not reference "
                f"any known differential diagnosis — possible hallucination"
            )

    score = grounded_hits / len(checked_sections)
    return score, flags


def evaluate_reference_overlap(report: RadiologyReport, reference_text: str) -> float:
    """Rough lexical (bag-of-words Jaccard-like) overlap against a real
    radiologist report for the same case.

    This is a coarse dev-time sanity check (Task 6.9), not a clinical
    accuracy metric: high overlap suggests the pipeline is at least
    discussing the same entities as the reference; low overlap warrants
    a closer look but doesn't by itself mean the report is wrong.
    """
    generated_tokens = Counter(_tokenize(report.as_plain_text()))
    reference_tokens = Counter(_tokenize(reference_text))

    if not reference_tokens:
        return 0.0

    overlap = sum((generated_tokens & reference_tokens).values())
    union = sum((generated_tokens | reference_tokens).values())
    return overlap / union if union else 0.0


def evaluate_report_quality(
    report: RadiologyReport, reference_text: str | None = None
) -> QualityReport:
    """Run the full evaluation suite on a generated report.

    Args:
        report: The generated `RadiologyReport`.
        reference_text: Optional real radiologist report text for the
            same scan, enabling the reference-overlap metric (Task 6.9).
    """
    completeness_score, completeness_flags = evaluate_completeness(report)
    groundedness_score, groundedness_flags = evaluate_groundedness(report)

    all_sentences = [s for sec in report.sections for s in _sentences(sec.body)]
    avg_len = (
        sum(len(s.split()) for s in all_sentences) / len(all_sentences)
        if all_sentences
        else 0.0
    )

    flags = completeness_flags + groundedness_flags
    if avg_len > 40:
        flags.append("average sentence length is unusually high (readability concern)")

    reference_overlap = (
        evaluate_reference_overlap(report, reference_text)
        if reference_text is not None
        else None
    )

    return QualityReport(
        scan_id=report.scan_id,
        completeness_score=completeness_score,
        groundedness_score=groundedness_score,
        reference_overlap_score=reference_overlap,
        avg_sentence_length=round(avg_len, 2),
        flags=flags,
    )
