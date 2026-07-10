"""Agent state schema for the LangGraph radiology analysis pipeline.

Defines the central `AgentState` TypedDict that flows through every node
in the graph, plus the Pydantic models for each data structure within
the state (findings, cases, literature, diagnoses).

Design notes:
- TypedDict is used for AgentState because LangGraph requires it for
  state channels (Pydantic BaseModel is not directly supported as state).
- Pydantic models are used for the *nested* data structures to get
  serialization, validation, and clear schemas for downstream consumers
  (the report generator, the frontend API, etc.).
"""

from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models for structured data within the state
# ---------------------------------------------------------------------------


class Finding(BaseModel):
    """A single finding from the ML vision pipeline.

    In mock mode these are fabricated; in production they come from
    Nick's anomaly detection + localization models.
    """

    label: str = Field(description="Pathology label, e.g. 'Consolidation'")
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence 0-1")
    location: str = Field(
        default="", description="Anatomical location, e.g. 'Right lower lobe'"
    )
    severity: float = Field(
        ge=0.0, le=1.0, default=0.5, description="Severity score 0-1"
    )


class SimilarCase(BaseModel):
    """A historical case retrieved from the ChromaDB vector store."""

    case_id: str
    description: str = Field(description="Brief clinical description")
    findings: list[str] = Field(
        default_factory=list, description="Key findings from this case"
    )
    confirmed_diagnosis: str = Field(
        default="", description="Final confirmed diagnosis if available"
    )
    similarity_score: float = Field(
        ge=0.0, le=1.0, description="Cosine similarity to current case"
    )
    outcome: str = Field(
        default="", description="Patient outcome, e.g. 'Resolved with antibiotics'"
    )


class LiteratureResult(BaseModel):
    """A paper or guideline retrieved from PubMed / clinical sources."""

    title: str
    authors: list[str] = Field(default_factory=list)
    journal: str = Field(default="")
    year: int = Field(default=0)
    pmid: str = Field(default="", description="PubMed ID")
    abstract_summary: str = Field(
        default="", description="LLM-generated summary of relevance"
    )
    relevance_score: float = Field(
        ge=0.0, le=1.0, default=0.5, description="How relevant to current findings"
    )


class DifferentialDiagnosis(BaseModel):
    """A single entry in the ranked differential diagnosis list."""

    diagnosis: str = Field(description="Diagnosis name, e.g. 'Community-acquired pneumonia'")
    probability: float = Field(
        ge=0.0, le=1.0, description="Posterior probability after evidence updating"
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence supporting this diagnosis",
    )
    contradicting_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence against this diagnosis",
    )
    reasoning: str = Field(
        default="", description="Chain-of-thought reasoning for this diagnosis"
    )


# ---------------------------------------------------------------------------
# LangGraph AgentState — the data that flows through the graph
# ---------------------------------------------------------------------------


class AgentState(TypedDict, total=False):
    """Central state schema for the LangGraph analysis pipeline.

    Every node in the graph reads from and writes to this dict.
    `total=False` means all keys are optional, which lets us build
    the state incrementally as each agent contributes its output.

    Flow:
        Input (scan_id, findings, metadata)
          → Case Retrieval Agent (similar_cases)
          → Literature Search Agent (literature_results, clinical_guidelines)
          → Differential Diagnosis Agent (differential_diagnoses)
          → Output (full state with all fields populated)
    """

    # --- Input (provided at graph invocation) ---
    scan_id: str
    findings: list[Finding]
    metadata: dict  # ScanMetadata as dict (from ingestion pipeline)

    # --- Case Retrieval Agent output ---
    similar_cases: list[SimilarCase]

    # --- Literature Search Agent output ---
    literature_results: list[LiteratureResult]
    clinical_guidelines: list[str]

    # --- Differential Diagnosis Agent output ---
    differential_diagnoses: list[DifferentialDiagnosis]

    # --- Orchestrator control ---
    current_step: str
    errors: list[str]
    retry_count: int
    status: Literal["pending", "running", "completed", "failed"]
