"""Differential Diagnosis Agent — generates ranked diagnostic hypotheses.

LangGraph node that synthesizes ML findings, similar historical cases,
and literature evidence to produce a ranked list of differential diagnoses
with confidence scores and supporting reasoning.

In mock mode, uses deterministic rule-based logic to map findings to
diagnoses. In production, this will use Claude 3 Haiku with structured
chain-of-thought output.
"""

from __future__ import annotations

import logging

from src.agent.state import (
    AgentState,
    DifferentialDiagnosis,
    Finding,
    LiteratureResult,
    SimilarCase,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Finding → diagnosis mapping (mock reasoning rules)
# ---------------------------------------------------------------------------

_DIAGNOSIS_RULES: dict[str, list[dict]] = {
    "consolidation": [
        {
            "diagnosis": "Community-acquired pneumonia",
            "base_probability": 0.65,
            "reasoning": "Consolidation with air bronchograms in a lower lobe is the "
            "most common presentation of bacterial pneumonia. Clinical "
            "correlation with fever, cough, and leukocytosis would increase "
            "confidence.",
        },
        {
            "diagnosis": "Lung malignancy (obstructive pneumonitis)",
            "base_probability": 0.15,
            "reasoning": "Post-obstructive consolidation from endobronchial tumor can "
            "mimic pneumonia. Lack of improvement after antibiotic therapy "
            "should raise suspicion.",
        },
        {
            "diagnosis": "Pulmonary infarction",
            "base_probability": 0.10,
            "reasoning": "Wedge-shaped peripheral consolidation may represent pulmonary "
            "infarction secondary to PE. Clinical risk factors (immobilization, "
            "DVT history) should be assessed.",
        },
        {
            "diagnosis": "Organizing pneumonia (COP)",
            "base_probability": 0.07,
            "reasoning": "Migratory or persistent consolidation not responding to "
            "antibiotics may indicate organizing pneumonia. Often bilateral "
            "and subpleural.",
        },
    ],
    "solitary pulmonary nodule": [
        {
            "diagnosis": "Non-small cell lung carcinoma",
            "base_probability": 0.40,
            "reasoning": "Solitary pulmonary nodule >8mm in a patient >50 years carries "
            "significant malignancy risk per Fleischner 2017 criteria. Spiculated "
            "margins and upper lobe location increase suspicion.",
        },
        {
            "diagnosis": "Benign granuloma (histoplasmosis/TB)",
            "base_probability": 0.30,
            "reasoning": "Calcified or stable nodules are more likely granulomatous. "
            "Geographic and exposure history is critical for assessment.",
        },
        {
            "diagnosis": "Pulmonary metastasis",
            "base_probability": 0.15,
            "reasoning": "Solitary metastasis is less common than primary lung cancer but "
            "should be considered in patients with known extrathoracic malignancy.",
        },
        {
            "diagnosis": "Hamartoma",
            "base_probability": 0.10,
            "reasoning": "Benign tumor, typically <2.5cm with popcorn calcification or "
            "fat density on CT. Most common benign lung tumor.",
        },
    ],
    "default": [
        {
            "diagnosis": "No significant pathology identified",
            "base_probability": 0.70,
            "reasoning": "No findings of clinical significance on the current imaging study.",
        },
        {
            "diagnosis": "Incidental finding requiring follow-up",
            "base_probability": 0.20,
            "reasoning": "Minor or indeterminate finding that may warrant follow-up imaging.",
        },
    ],
}


def _match_finding_to_rules(label: str) -> str:
    """Map a finding label to the closest diagnosis rule key."""
    label_lower = label.lower()
    for key in _DIAGNOSIS_RULES:
        if key != "default" and (key in label_lower or label_lower in key):
            return key
    if "nodule" in label_lower or "mass" in label_lower:
        return "solitary pulmonary nodule"
    if "opacity" in label_lower or "infiltrate" in label_lower:
        return "consolidation"
    return "default"


def _update_probabilities_with_evidence(
    diagnoses: list[dict],
    similar_cases: list[SimilarCase],
    literature: list[LiteratureResult],
) -> list[DifferentialDiagnosis]:
    """Apply Bayesian-style evidence updating to base probabilities.

    This is a simplified mock of what Claude 3 Haiku would do in
    production — it adjusts probabilities based on how many similar
    cases confirm each diagnosis and how strongly literature supports it.
    """
    results: list[DifferentialDiagnosis] = []

    # Count how many similar cases support each diagnosis
    case_diagnosis_counts: dict[str, int] = {}
    for case in similar_cases:
        dx = case.confirmed_diagnosis.lower()
        for diag in diagnoses:
            if _diagnoses_match(diag["diagnosis"], dx):
                case_diagnosis_counts[diag["diagnosis"]] = (
                    case_diagnosis_counts.get(diag["diagnosis"], 0) + 1
                )

    total_cases = max(len(similar_cases), 1)

    for diag in diagnoses:
        name = diag["diagnosis"]
        base_prob = diag["base_probability"]

        # Evidence from similar cases
        case_support = case_diagnosis_counts.get(name, 0) / total_cases
        supporting = []
        contradicting = []

        if case_support > 0:
            supporting.append(
                f"{case_diagnosis_counts.get(name, 0)}/{len(similar_cases)} "
                f"similar historical cases had this diagnosis"
            )
            # Bayesian update: shift probability toward case evidence
            updated_prob = base_prob * 0.7 + case_support * 0.3
        else:
            updated_prob = base_prob * 0.9  # Slight decrease without case support
            if similar_cases:
                contradicting.append(
                    "No similar historical cases confirmed this diagnosis"
                )

        # Evidence from literature
        if literature:
            supporting.append(
                f"{len(literature)} relevant literature references retrieved"
            )
            updated_prob *= 1.05  # Small boost for having literature support

        # Clamp to [0, 1]
        updated_prob = min(1.0, max(0.0, updated_prob))

        results.append(
            DifferentialDiagnosis(
                diagnosis=name,
                probability=round(updated_prob, 4),
                supporting_evidence=supporting,
                contradicting_evidence=contradicting,
                reasoning=diag["reasoning"],
            )
        )

    # Normalize so probabilities sum to ~1.0
    total = sum(d.probability for d in results)
    if total > 0:
        for d in results:
            d.probability = round(d.probability / total, 4)

    # Sort by probability (highest first)
    results.sort(key=lambda d: d.probability, reverse=True)
    return results


def _diagnoses_match(diagnosis_a: str, diagnosis_b: str) -> bool:
    """Fuzzy match two diagnosis strings."""
    a = diagnosis_a.lower().strip()
    b = diagnosis_b.lower().strip()
    # Exact match
    if a == b:
        return True
    # One contains the other
    if a in b or b in a:
        return True
    # Keyword overlap (at least 2 shared words)
    words_a = set(a.split())
    words_b = set(b.split())
    common = words_a & words_b - {"the", "a", "an", "of", "in", "with", "and", "or"}
    return len(common) >= 2


# ------------------------------------------------------------------
# LangGraph node function
# ------------------------------------------------------------------


def run_diagnosis(state: AgentState) -> dict:
    """LangGraph node: generate ranked differential diagnoses.

    Reads ``findings``, ``similar_cases``, and ``literature_results``
    from state. Produces ``differential_diagnoses`` with probabilities,
    evidence, and reasoning.
    """
    logger.info(
        "Differential Diagnosis Agent: starting for scan %s",
        state.get("scan_id", "unknown"),
    )

    try:
        findings = state.get("findings", [])
        similar_cases = state.get("similar_cases", [])
        literature = state.get("literature_results", [])

        # Parse findings
        parsed_findings: list[Finding] = []
        for f in findings:
            if isinstance(f, Finding):
                parsed_findings.append(f)
            elif isinstance(f, dict):
                parsed_findings.append(Finding(**f))

        # Determine which diagnosis rules to use based on primary finding
        if parsed_findings:
            primary_label = parsed_findings[0].label
            rule_key = _match_finding_to_rules(primary_label)
        else:
            rule_key = "default"

        base_diagnoses = _DIAGNOSIS_RULES.get(rule_key, _DIAGNOSIS_RULES["default"])

        # Update probabilities with evidence from cases and literature
        differential = _update_probabilities_with_evidence(
            base_diagnoses, similar_cases, literature
        )

        logger.info(
            "Differential Diagnosis Agent: generated %d diagnoses "
            "(top: %s at %.1f%%)",
            len(differential),
            differential[0].diagnosis if differential else "none",
            differential[0].probability * 100 if differential else 0,
        )

        return {
            "differential_diagnoses": differential,
            "current_step": "diagnosis_complete",
        }

    except Exception as exc:
        logger.error("Differential Diagnosis Agent failed: %s", exc)
        return {
            "differential_diagnoses": [],
            "errors": state.get("errors", []) + [f"Diagnosis error: {exc}"],
            "current_step": "diagnosis_failed",
        }
