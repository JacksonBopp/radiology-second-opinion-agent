import pytest

from src.agent.state import DifferentialDiagnosis, Finding, LiteratureResult, SimilarCase
from src.reports import calibration, style
from src.reports.evaluation import evaluate_report_quality
from src.reports.generator import generate_report
from src.reports.prompts import build_report_prompt
from src.reports.schemas import ConfidenceLevel, RadiologyReport


# ---------------------------------------------------------------------------
# Fixtures — a representative completed AgentState
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_state() -> dict:
    return {
        "scan_id": "scan-report-001",
        "findings": [
            {
                "label": "Consolidation",
                "confidence": 0.87,
                "location": "Right lower lobe",
                "severity": 0.65,
            }
        ],
        "metadata": {"patient_age": "065Y", "patient_sex": "M"},
        "similar_cases": [
            {
                "case_id": "case-001",
                "description": "Elderly male with fever and cough",
                "findings": ["Consolidation"],
                "confirmed_diagnosis": "Community-acquired pneumonia",
                "similarity_score": 0.82,
                "outcome": "Resolved with antibiotics",
            }
        ],
        "literature_results": [
            {
                "title": "IDSA/ATS CAP Guidelines",
                "authors": ["Metlay JP"],
                "journal": "Am J Respir Crit Care Med",
                "year": 2019,
                "pmid": "31573350",
                "abstract_summary": "Guideline for diagnosis and treatment of CAP.",
                "relevance_score": 0.9,
            }
        ],
        "clinical_guidelines": [
            "IDSA/ATS Guidelines for Community-Acquired Pneumonia in Adults (2019)"
        ],
        "differential_diagnoses": [
            {
                "diagnosis": "Community-acquired pneumonia",
                "probability": 0.72,
                "supporting_evidence": ["1/1 similar historical cases had this diagnosis"],
                "contradicting_evidence": [],
                "reasoning": "Consolidation with air bronchograms in a lower lobe is "
                "the most common presentation of bacterial pneumonia.",
            },
            {
                "diagnosis": "Lung malignancy (obstructive pneumonitis)",
                "probability": 0.18,
                "supporting_evidence": [],
                "contradicting_evidence": ["No similar historical cases confirmed this diagnosis"],
                "reasoning": "Post-obstructive consolidation from endobronchial tumor "
                "can mimic pneumonia.",
            },
        ],
        "status": "completed",
    }


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


def test_confidence_level_buckets():
    assert calibration.confidence_level_for(0.9) == ConfidenceLevel.VERY_HIGH
    assert calibration.confidence_level_for(0.7) == ConfidenceLevel.HIGH
    assert calibration.confidence_level_for(0.5) == ConfidenceLevel.MODERATE
    assert calibration.confidence_level_for(0.3) == ConfidenceLevel.LOW
    assert calibration.confidence_level_for(0.05) == ConfidenceLevel.VERY_LOW


def test_confidence_phrase_contains_percentage():
    phrase = calibration.confidence_phrase(0.72)
    assert "72%" in phrase
    assert "confidence" in phrase


def test_temperature_scaling_is_noop_at_one():
    assert calibration.apply_temperature(0.6, temperature=1.0) == pytest.approx(0.6)


def test_temperature_scaling_softens_with_high_temperature():
    scaled = calibration.apply_temperature(0.9, temperature=2.0)
    assert scaled < 0.9


def test_severity_descriptor_buckets():
    assert calibration.severity_descriptor(0.9) == "severe"
    assert calibration.severity_descriptor(0.5) == "moderate"
    assert calibration.severity_descriptor(0.1) == "mild"
    assert calibration.severity_descriptor(0.0) == "not specified"


def test_summarize_uncertainty_single_diagnosis_is_discounted():
    level_one, _ = calibration.summarize_uncertainty(0.9, num_diagnoses=1)
    level_many, _ = calibration.summarize_uncertainty(0.9, num_diagnoses=4)
    # Discounting a single-diagnosis differential should never yield a
    # *higher* confidence bucket than having multiple diagnoses considered.
    order = list(ConfidenceLevel)
    assert order.index(level_one) <= order.index(level_many)


# ---------------------------------------------------------------------------
# Style / register enforcement
# ---------------------------------------------------------------------------


def test_enforce_radiology_register_strips_first_person():
    text = "I think this is certainly pneumonia."
    cleaned = style.enforce_radiology_register(text)
    assert "I think" not in cleaned
    assert "certainly" not in cleaned


def test_render_findings_section_handles_empty_findings():
    section = style.render_findings_section([])
    assert "No acute abnormalities" in section


def test_render_impression_section_lists_alternatives():
    diagnoses = [
        DifferentialDiagnosis(diagnosis="Pneumonia", probability=0.6),
        DifferentialDiagnosis(diagnosis="Malignancy", probability=0.2),
    ]
    section = style.render_impression_section(diagnoses)
    assert "pneumonia" in section.lower()
    assert "Malignancy" in section


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


def test_build_report_prompt_includes_key_sections(sample_state):
    findings = [Finding(**f) for f in sample_state["findings"]]
    diagnoses = [DifferentialDiagnosis(**d) for d in sample_state["differential_diagnoses"]]
    cases = [SimilarCase(**c) for c in sample_state["similar_cases"]]
    literature = [LiteratureResult(**l) for l in sample_state["literature_results"]]

    prompt = build_report_prompt(
        scan_id=sample_state["scan_id"],
        findings=findings,
        differential_diagnoses=diagnoses,
        similar_cases=cases,
        literature_results=literature,
        clinical_guidelines=sample_state["clinical_guidelines"],
        metadata=sample_state["metadata"],
    )
    assert "Consolidation" in prompt
    assert "Community-acquired pneumonia" in prompt
    assert "JSON" in prompt


def test_build_report_prompt_handles_empty_inputs():
    prompt = build_report_prompt("scan-empty", [], [], [], [], [])
    assert "No findings were flagged" in prompt
    assert "No differential diagnoses were generated" in prompt


# ---------------------------------------------------------------------------
# Generator (mock mode — no ANTHROPIC_API_KEY set in test env)
# ---------------------------------------------------------------------------


def test_generate_report_mock_mode(sample_state, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    report = generate_report(sample_state)

    assert isinstance(report, RadiologyReport)
    assert report.scan_id == "scan-report-001"
    assert report.model_version == "mock-v0"

    headings = {s.heading for s in report.sections}
    assert {"Findings", "Impression", "Recommendation"} <= headings

    assert report.differential_diagnoses[0].rank == 1
    assert report.differential_diagnoses[0].diagnosis == "Community-acquired pneumonia"
    # Preserves the incoming (already Bayesian-sorted) order.
    assert [d.probability for d in report.differential_diagnoses] == sorted(
        [d.probability for d in report.differential_diagnoses], reverse=True
    )

    assert len(report.guideline_references) == 1
    assert "IDSA/ATS" in report.guideline_references[0].text
    assert report.similar_case_ids == ["case-001"]
    assert report.uncertainty_note


def test_generate_report_handles_empty_state():
    report = generate_report({"scan_id": "scan-empty"})
    assert report.scan_id == "scan-empty"
    assert report.differential_diagnoses == []
    assert report.sections  # still produces a templated report, not an empty one


def test_generate_report_as_plain_text(sample_state):
    report = generate_report(sample_state)
    text = report.as_plain_text()
    assert "FINDINGS" in text
    assert report.scan_id in text


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def test_evaluate_report_quality_complete_report(sample_state):
    report = generate_report(sample_state)
    quality = evaluate_report_quality(report)

    assert quality.completeness_score == 1.0
    assert quality.groundedness_score == 1.0
    assert quality.passes_minimum_bar
    assert not any(f.startswith("CRITICAL") for f in quality.flags)


def test_evaluate_report_quality_flags_missing_sections(sample_state):
    report = generate_report(sample_state)
    report.sections = [s for s in report.sections if s.heading != "Impression"]

    quality = evaluate_report_quality(report)
    assert quality.completeness_score < 1.0
    assert any("missing 'impression'" in f for f in quality.flags)
    assert not quality.passes_minimum_bar


def test_evaluate_report_quality_flags_hallucinated_diagnosis(sample_state):
    report = generate_report(sample_state)
    # Corrupt the impression section so it no longer references any
    # known differential diagnosis — simulates an LLM hallucination.
    for section in report.sections:
        if section.heading == "Impression":
            section.body = "Findings are most consistent with a rare tropical parasite."

    quality = evaluate_report_quality(report)
    assert quality.groundedness_score < 1.0
    assert any("hallucination" in f for f in quality.flags)


def test_evaluate_report_quality_reference_overlap(sample_state):
    report = generate_report(sample_state)
    reference = (
        "FINDINGS: Consolidation in the right lower lobe. "
        "IMPRESSION: Community-acquired pneumonia."
    )
    quality = evaluate_report_quality(report, reference_text=reference)
    assert quality.reference_overlap_score is not None
    assert 0.0 < quality.reference_overlap_score <= 1.0
