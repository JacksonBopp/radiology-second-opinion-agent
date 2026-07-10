"""Agentic reasoning layer for radiology second-opinion analysis.

This package implements a LangGraph-based multi-agent system that:
1. Retrieves similar historical cases from a ChromaDB vector store
2. Searches medical literature via PubMed (mocked for now)
3. Generates differential diagnoses with confidence scores
4. Orchestrates the full analysis pipeline as a state machine

Usage:
    from src.agent import run_analysis_graph, AgentState
    result = run_analysis_graph(scan_id="scan-001", findings=[...], metadata={...})
"""

from src.agent.state import (
    AgentState,
    DifferentialDiagnosis,
    Finding,
    LiteratureResult,
    SimilarCase,
)

__all__ = [
    "AgentState",
    "DifferentialDiagnosis",
    "Finding",
    "LiteratureResult",
    "SimilarCase",
]
