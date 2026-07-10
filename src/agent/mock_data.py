"""Mock radiology case data for development and testing.

Provides 10 realistic chest radiology cases that seed the ChromaDB
vector store and serve as mock ML vision pipeline output. Each case
represents a plausible clinical scenario with findings, demographics,
confirmed diagnosis, and outcome.

These cases are intentionally diverse — covering pneumonia, lung nodules,
pleural effusion, pneumothorax, cardiomegaly, rib fractures, and normal
studies — so the retrieval and diagnosis agents get meaningful variety.
"""

from __future__ import annotations

from src.agent.state import Finding


# ---------------------------------------------------------------------------
# Mock ML vision findings (simulating Nick's model output)
# ---------------------------------------------------------------------------

MOCK_FINDINGS_PNEUMONIA: list[dict] = [
    {
        "label": "Consolidation",
        "confidence": 0.87,
        "location": "Right lower lobe",
        "severity": 0.65,
    },
    {
        "label": "Air bronchograms",
        "confidence": 0.72,
        "location": "Right lower lobe",
        "severity": 0.50,
    },
]

MOCK_FINDINGS_NODULE: list[dict] = [
    {
        "label": "Solitary pulmonary nodule",
        "confidence": 0.91,
        "location": "Left upper lobe",
        "severity": 0.70,
    },
]

MOCK_FINDINGS_NORMAL: list[dict] = []


def get_mock_findings(case_type: str = "pneumonia") -> list[Finding]:
    """Return mock Finding objects for a given case type."""
    mapping = {
        "pneumonia": MOCK_FINDINGS_PNEUMONIA,
        "nodule": MOCK_FINDINGS_NODULE,
        "normal": MOCK_FINDINGS_NORMAL,
    }
    raw = mapping.get(case_type, MOCK_FINDINGS_PNEUMONIA)
    return [Finding(**f) for f in raw]


# ---------------------------------------------------------------------------
# Mock historical cases (seeded into ChromaDB)
# ---------------------------------------------------------------------------

MOCK_CASES: list[dict] = [
    {
        "case_id": "CASE-001",
        "description": "65-year-old male presenting with fever, productive cough, "
        "and right lower lobe consolidation on chest X-ray.",
        "findings": ["Consolidation", "Air bronchograms", "Right lower lobe opacity"],
        "confirmed_diagnosis": "Community-acquired pneumonia",
        "outcome": "Resolved with 7-day course of amoxicillin-clavulanate",
        "patient_age": "065Y",
        "patient_sex": "M",
        "modality": "CR",
    },
    {
        "case_id": "CASE-002",
        "description": "72-year-old female with chronic cough and a 1.5cm solitary "
        "pulmonary nodule in the left upper lobe.",
        "findings": ["Solitary pulmonary nodule", "Left upper lobe mass"],
        "confirmed_diagnosis": "Non-small cell lung carcinoma (adenocarcinoma)",
        "outcome": "Lobectomy performed; Stage IA, no recurrence at 2-year follow-up",
        "patient_age": "072Y",
        "patient_sex": "F",
        "modality": "CT",
    },
    {
        "case_id": "CASE-003",
        "description": "58-year-old male with shortness of breath and bilateral "
        "pleural effusions, larger on the right side.",
        "findings": [
            "Bilateral pleural effusion",
            "Right-sided predominance",
            "Meniscus sign",
        ],
        "confirmed_diagnosis": "Congestive heart failure exacerbation",
        "outcome": "Improved with diuretic therapy and fluid restriction",
        "patient_age": "058Y",
        "patient_sex": "M",
        "modality": "CR",
    },
    {
        "case_id": "CASE-004",
        "description": "23-year-old male presenting with sudden chest pain and "
        "dyspnea. Visible pneumothorax on left side.",
        "findings": [
            "Left pneumothorax",
            "Visceral pleural line",
            "Absent lung markings left apex",
        ],
        "confirmed_diagnosis": "Primary spontaneous pneumothorax",
        "outcome": "Resolved with chest tube drainage over 3 days",
        "patient_age": "023Y",
        "patient_sex": "M",
        "modality": "CR",
    },
    {
        "case_id": "CASE-005",
        "description": "70-year-old female with progressive dyspnea. Chest X-ray "
        "shows enlarged cardiac silhouette (CTR >0.55).",
        "findings": [
            "Cardiomegaly",
            "Cephalization of pulmonary vessels",
            "Bilateral interstitial edema",
        ],
        "confirmed_diagnosis": "Dilated cardiomyopathy with decompensated heart failure",
        "outcome": "Stabilized with ACE inhibitor, beta-blocker, and diuretic therapy",
        "patient_age": "070Y",
        "patient_sex": "F",
        "modality": "CR",
    },
    {
        "case_id": "CASE-006",
        "description": "45-year-old male with right-sided chest pain after motor "
        "vehicle collision. X-ray reveals fractures of ribs 5-7.",
        "findings": [
            "Rib fractures (5th-7th right)",
            "Small right hemothorax",
            "Subcutaneous emphysema",
        ],
        "confirmed_diagnosis": "Traumatic rib fractures with associated hemothorax",
        "outcome": "Conservative management; pain control and incentive spirometry",
        "patient_age": "045Y",
        "patient_sex": "M",
        "modality": "CR",
    },
    {
        "case_id": "CASE-007",
        "description": "80-year-old female with fever, leukocytosis, and bilateral "
        "patchy infiltrates on chest X-ray.",
        "findings": [
            "Bilateral patchy infiltrates",
            "Ground-glass opacities",
            "Perihilar predominance",
        ],
        "confirmed_diagnosis": "Hospital-acquired pneumonia (MRSA)",
        "outcome": "Treated with IV vancomycin; prolonged ICU stay, eventual recovery",
        "patient_age": "080Y",
        "patient_sex": "F",
        "modality": "CR",
    },
    {
        "case_id": "CASE-008",
        "description": "35-year-old female with dry cough and bilateral hilar "
        "lymphadenopathy on CT scan.",
        "findings": [
            "Bilateral hilar lymphadenopathy",
            "Interstitial reticular pattern",
            "Non-caseating granulomas on biopsy",
        ],
        "confirmed_diagnosis": "Pulmonary sarcoidosis (Stage II)",
        "outcome": "Symptom improvement with oral prednisone taper over 6 months",
        "patient_age": "035Y",
        "patient_sex": "F",
        "modality": "CT",
    },
    {
        "case_id": "CASE-009",
        "description": "50-year-old male with acute pleuritic chest pain and wedge-shaped "
        "opacity on CT pulmonary angiography.",
        "findings": [
            "Wedge-shaped peripheral opacity",
            "Filling defect in right pulmonary artery",
            "Hampton hump sign",
        ],
        "confirmed_diagnosis": "Pulmonary embolism with infarction",
        "outcome": "Anticoagulation with heparin bridge to warfarin; full recovery",
        "patient_age": "050Y",
        "patient_sex": "M",
        "modality": "CT",
    },
    {
        "case_id": "CASE-010",
        "description": "28-year-old female, routine pre-employment chest X-ray. "
        "No abnormalities detected.",
        "findings": [],
        "confirmed_diagnosis": "Normal chest radiograph",
        "outcome": "No follow-up required",
        "patient_age": "028Y",
        "patient_sex": "F",
        "modality": "CR",
    },
]


def get_mock_metadata(case_type: str = "pneumonia") -> dict:
    """Return mock ScanMetadata-like dict matching the ingestion pipeline format."""
    base = {
        "modality": "CR",
        "body_part_examined": "CHEST",
        "patient_age": "065Y",
        "patient_sex": "M",
        "study_date": "20260710",
        "manufacturer": "Mock Medical Imaging Co.",
        "rows": 2048,
        "columns": 2048,
        "pixel_spacing": [0.139, 0.139],
        "study_instance_uid": "1.2.840.113619.2.55.3.604688119.1.mock001",
        "series_instance_uid": "1.2.840.113619.2.55.3.604688119.2.mock001",
        "sop_instance_uid": "1.2.840.113619.2.55.3.604688119.3.mock001",
    }
    if case_type == "nodule":
        base.update(
            patient_age="072Y",
            patient_sex="F",
            modality="CT",
            study_instance_uid="1.2.840.113619.2.55.3.604688119.1.mock002",
        )
    return base
