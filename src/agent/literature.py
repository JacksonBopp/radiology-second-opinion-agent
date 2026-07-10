"""Literature Search Agent — retrieves PubMed papers and clinical guidelines.

LangGraph node that searches medical literature relevant to the current
findings, extracts clinical guidelines, and returns structured results.

In mock mode, all PubMed calls are stubbed with realistic paper metadata.
In production, this will use the NCBI E-utilities API and Gemini 1.5 Flash
for summarization via a RAG pipeline (LlamaIndex).
"""

from __future__ import annotations

import logging
from typing import Any

from src.agent.state import AgentState, Finding, LiteratureResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Clinical guidelines database (hardcoded for common chest findings)
# ---------------------------------------------------------------------------

_CLINICAL_GUIDELINES: dict[str, list[str]] = {
    "consolidation": [
        "ACR Appropriateness Criteria: Acute Respiratory Illness in Immunocompetent Patients (2022)",
        "IDSA/ATS Guidelines for Community-Acquired Pneumonia in Adults (2019)",
    ],
    "solitary pulmonary nodule": [
        "Fleischner Society Guidelines for Management of Solid Pulmonary Nodules (2017)",
        "ACR Lung-RADS v2022 Assessment Categories for Lung CT Screening",
        "NCCN Guidelines for Lung Cancer Screening (2023)",
    ],
    "pleural effusion": [
        "BTS Guidelines for Investigation of Pleural Effusion in Adults (2023)",
        "ACR Appropriateness Criteria: Nontraumatic Pleural Effusion (2020)",
    ],
    "pneumothorax": [
        "BTS Guidelines for the Management of Spontaneous Pneumothorax (2023)",
        "ACEP Clinical Policy: Critical Issues in the Evaluation of Adult Patients with Suspected Pneumothorax (2021)",
    ],
    "cardiomegaly": [
        "ACC/AHA Guidelines for the Management of Heart Failure (2022 Update)",
        "ESC Guidelines for Acute and Chronic Heart Failure (2021)",
    ],
    "rib fracture": [
        "Eastern Association for the Surgery of Trauma (EAST) Practice Guideline: Rib Fracture Management (2020)",
        "ACR Appropriateness Criteria: Blunt Chest Trauma (2021)",
    ],
    "ground-glass opacity": [
        "Fleischner Society Position Paper: Management of Subsolid Pulmonary Nodules (2017)",
        "ACR Appropriateness Criteria: Chronic Dyspnea — Suspected Pulmonary Origin (2022)",
    ],
    "hilar lymphadenopathy": [
        "ATS/ERS/WASOG Statement on Sarcoidosis (2020 Update)",
        "ACR Appropriateness Criteria: Mediastinal and Hilar Masses (2022)",
    ],
    "pulmonary embolism": [
        "ESC/ERS Guidelines for Diagnosis and Management of Acute Pulmonary Embolism (2019)",
        "ACEP Clinical Policy: Pulmonary Embolism (2018)",
        "PIOPED III Criteria for CT Pulmonary Angiography",
    ],
}


# ---------------------------------------------------------------------------
# Mock PubMed search results
# ---------------------------------------------------------------------------

_MOCK_PAPERS: dict[str, list[dict[str, Any]]] = {
    "consolidation": [
        {
            "title": "Radiographic Features of Community-Acquired Pneumonia: A Systematic Review",
            "authors": ["Chen L", "Wang X", "Patel S"],
            "journal": "Radiology",
            "year": 2023,
            "pmid": "37654321",
            "abstract_summary": "Systematic review of 45 studies analyzing radiographic patterns "
            "in CAP. Consolidation with air bronchograms in lower lobes has 87% PPV "
            "for bacterial pneumonia. Bilateral involvement suggests atypical organisms.",
            "relevance_score": 0.92,
        },
        {
            "title": "Differentiating Pneumonia from Lung Malignancy on Chest Radiograph: "
            "A Machine Learning Approach",
            "authors": ["Kim J", "Lee M", "Park H"],
            "journal": "European Radiology",
            "year": 2024,
            "pmid": "38765432",
            "abstract_summary": "CNN-based model achieving 0.91 AUC in differentiating consolidation "
            "due to pneumonia vs. obstructive pneumonitis from lung cancer. Key distinguishing "
            "features include air bronchogram morphology and temporal evolution.",
            "relevance_score": 0.85,
        },
    ],
    "solitary pulmonary nodule": [
        {
            "title": "Fleischner Society 2017 Guidelines: Clinical Implementation and Outcomes",
            "authors": ["MacMahon H", "Naidich DP", "Goo JM"],
            "journal": "Radiology",
            "year": 2022,
            "pmid": "36543210",
            "abstract_summary": "5-year follow-up data on Fleischner 2017 guideline adherence. "
            "Risk stratification by nodule size and morphology effectively identifies "
            "malignant nodules while reducing unnecessary interventions by 34%.",
            "relevance_score": 0.95,
        },
    ],
    "default": [
        {
            "title": "Artificial Intelligence in Chest Radiograph Interpretation: "
            "Current Status and Future Directions",
            "authors": ["Rajpurkar P", "Irvin J", "Ball RL"],
            "journal": "Nature Medicine",
            "year": 2024,
            "pmid": "39876543",
            "abstract_summary": "Review of AI applications in chest X-ray interpretation. "
            "Current models achieve radiologist-level performance on 8/14 pathologies "
            "but struggle with rare conditions and multi-finding cases.",
            "relevance_score": 0.60,
        },
    ],
}


def _match_finding_to_key(label: str) -> str:
    """Map a finding label to the closest key in our mock databases."""
    label_lower = label.lower()
    for key in _CLINICAL_GUIDELINES:
        if key in label_lower or label_lower in key:
            return key
    # Partial matches
    if "nodule" in label_lower or "mass" in label_lower:
        return "solitary pulmonary nodule"
    if "opacity" in label_lower or "infiltrate" in label_lower:
        return "consolidation"
    if "effusion" in label_lower:
        return "pleural effusion"
    if "fracture" in label_lower:
        return "rib fracture"
    return ""


def _search_mock_pubmed(findings: list[Finding]) -> list[LiteratureResult]:
    """Simulate PubMed API search with realistic results."""
    results: list[LiteratureResult] = []
    seen_pmids: set[str] = set()

    for finding in findings:
        label = finding.label if hasattr(finding, "label") else finding.get("label", "")
        key = _match_finding_to_key(label)
        papers = _MOCK_PAPERS.get(key, _MOCK_PAPERS["default"])

        for paper in papers:
            if paper["pmid"] not in seen_pmids:
                seen_pmids.add(paper["pmid"])
                results.append(LiteratureResult(**paper))

    # Always include at least the default paper
    if not results:
        for paper in _MOCK_PAPERS["default"]:
            results.append(LiteratureResult(**paper))

    return results


def _extract_clinical_guidelines(findings: list[Finding]) -> list[str]:
    """Return applicable clinical guidelines for the given findings."""
    guidelines: list[str] = []
    seen: set[str] = set()

    for finding in findings:
        label = finding.label if hasattr(finding, "label") else finding.get("label", "")
        key = _match_finding_to_key(label)
        for guideline in _CLINICAL_GUIDELINES.get(key, []):
            if guideline not in seen:
                seen.add(guideline)
                guidelines.append(guideline)

    return guidelines


# ------------------------------------------------------------------
# LangGraph node function
# ------------------------------------------------------------------


def run_literature_search(state: AgentState) -> dict:
    """LangGraph node: search medical literature and extract guidelines.

    Reads ``findings`` from state, queries (mock) PubMed, extracts
    relevant clinical guidelines, and returns results to merge into state.
    """
    logger.info(
        "Literature Search Agent: starting for scan %s",
        state.get("scan_id", "unknown"),
    )

    try:
        findings = state.get("findings", [])

        # Convert dicts to Finding objects if needed
        parsed_findings: list[Finding] = []
        for f in findings:
            if isinstance(f, Finding):
                parsed_findings.append(f)
            elif isinstance(f, dict):
                parsed_findings.append(Finding(**f))

        literature = _search_mock_pubmed(parsed_findings)
        guidelines = _extract_clinical_guidelines(parsed_findings)

        logger.info(
            "Literature Search Agent: found %d papers, %d applicable guidelines",
            len(literature),
            len(guidelines),
        )

        return {
            "literature_results": literature,
            "clinical_guidelines": guidelines,
            "current_step": "literature_complete",
        }

    except Exception as exc:
        logger.error("Literature Search Agent failed: %s", exc)
        return {
            "literature_results": [],
            "clinical_guidelines": [],
            "errors": state.get("errors", []) + [f"Literature search error: {exc}"],
            "current_step": "literature_failed",
        }
