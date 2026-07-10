"""LangGraph Orchestrator — the central state machine for analysis.

Defines the directed graph that chains the three sub-agents:

    START → case_retrieval → literature_search → diagnosis → END
                  ↓ (on error)        ↓ (on error)
              error_handler        error_handler

Each node is a function that receives the full AgentState, runs its
logic, and returns a partial dict that gets merged back into state.

Usage:
    from src.agent.orchestrator import run_analysis_graph

    result = run_analysis_graph(
        scan_id="scan-001",
        findings=[{"label": "Consolidation", "confidence": 0.87, ...}],
        metadata={"patient_age": "065Y", "patient_sex": "M", ...},
    )
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.agent.diagnosis import run_diagnosis
from src.agent.literature import run_literature_search
from src.agent.retrieval import run_retrieval
from src.agent.state import AgentState, Finding

logger = logging.getLogger(__name__)

# Maximum retries before marking the analysis as failed
MAX_RETRIES = 2


# ------------------------------------------------------------------
# Error handling node
# ------------------------------------------------------------------


def handle_error(state: AgentState) -> dict:
    """Handle errors from any agent node.

    Increments retry count. If retries exhausted, marks status as failed.
    Otherwise, logs the error and allows the graph to continue.
    """
    errors = state.get("errors", [])
    retry_count = state.get("retry_count", 0) + 1

    logger.warning(
        "Error handler invoked (retry %d/%d). Errors: %s",
        retry_count,
        MAX_RETRIES,
        errors[-1] if errors else "unknown",
    )

    if retry_count >= MAX_RETRIES:
        return {
            "retry_count": retry_count,
            "status": "failed",
            "current_step": "failed",
        }

    return {
        "retry_count": retry_count,
        "current_step": "retrying",
    }


# ------------------------------------------------------------------
# Router functions (conditional edges)
# ------------------------------------------------------------------


def after_retrieval(state: AgentState) -> str:
    """Route after case retrieval: continue or handle error."""
    step = state.get("current_step", "")
    if step == "retrieval_failed":
        return "error_handler"
    return "literature_search"


def after_literature(state: AgentState) -> str:
    """Route after literature search: continue or handle error."""
    step = state.get("current_step", "")
    if step == "literature_failed":
        return "error_handler"
    return "diagnosis"


def after_diagnosis(state: AgentState) -> str:
    """Route after diagnosis: complete or handle error."""
    step = state.get("current_step", "")
    if step == "diagnosis_failed":
        return "error_handler"
    return "finalize"


def after_error(state: AgentState) -> str:
    """Route after error handling: retry or give up."""
    if state.get("status") == "failed":
        return "finalize"
    # Retry: go back to wherever we failed
    step = state.get("current_step", "")
    if "retrieval" in step:
        return "case_retrieval"
    if "literature" in step:
        return "literature_search"
    if "diagnosis" in step:
        return "diagnosis"
    return "finalize"


# ------------------------------------------------------------------
# Finalize node
# ------------------------------------------------------------------


def finalize(state: AgentState) -> dict:
    """Mark the analysis as completed (or confirm failure)."""
    if state.get("status") == "failed":
        logger.error("Analysis pipeline failed for scan %s", state.get("scan_id"))
        return {"current_step": "done"}

    logger.info(
        "Analysis pipeline completed for scan %s. "
        "%d cases, %d papers, %d diagnoses",
        state.get("scan_id"),
        len(state.get("similar_cases", [])),
        len(state.get("literature_results", [])),
        len(state.get("differential_diagnoses", [])),
    )

    return {
        "status": "completed",
        "current_step": "done",
    }


# ------------------------------------------------------------------
# Graph construction
# ------------------------------------------------------------------


def build_graph() -> StateGraph:
    """Construct the LangGraph state machine.

    Returns the uncompiled StateGraph so callers can inspect or
    modify it before compilation.
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("case_retrieval", run_retrieval)
    graph.add_node("literature_search", run_literature_search)
    graph.add_node("diagnosis", run_diagnosis)
    graph.add_node("error_handler", handle_error)
    graph.add_node("finalize", finalize)

    # Entry edge
    graph.add_edge(START, "case_retrieval")

    # Conditional edges after each agent
    graph.add_conditional_edges("case_retrieval", after_retrieval)
    graph.add_conditional_edges("literature_search", after_literature)
    graph.add_conditional_edges("diagnosis", after_diagnosis)
    graph.add_conditional_edges("error_handler", after_error)

    # Terminal edge
    graph.add_edge("finalize", END)

    return graph


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------


def run_analysis_graph(
    scan_id: str,
    findings: list[dict | Finding],
    metadata: dict[str, Any],
) -> dict:
    """Run the full analysis pipeline for a scan.

    This is the main entry point that compiles the graph, sets up
    initial state, and returns the completed state dict.

    Args:
        scan_id: Unique identifier for the scan being analyzed.
        findings: List of findings from the ML vision pipeline (dicts or
            Finding objects).
        metadata: ScanMetadata-like dict from the ingestion pipeline.

    Returns:
        The final AgentState dict with all fields populated.
    """
    logger.info("Starting analysis graph for scan %s", scan_id)

    # Normalize findings to Finding objects
    parsed_findings = []
    for f in findings:
        if isinstance(f, Finding):
            parsed_findings.append(f)
        elif isinstance(f, dict):
            parsed_findings.append(Finding(**f))

    # Build initial state
    initial_state: AgentState = {
        "scan_id": scan_id,
        "findings": parsed_findings,
        "metadata": metadata,
        "similar_cases": [],
        "literature_results": [],
        "clinical_guidelines": [],
        "differential_diagnoses": [],
        "current_step": "starting",
        "errors": [],
        "retry_count": 0,
        "status": "running",
    }

    # Compile and invoke
    graph = build_graph()
    compiled = graph.compile()
    result = compiled.invoke(initial_state)

    logger.info(
        "Analysis graph finished for scan %s with status: %s",
        scan_id,
        result.get("status", "unknown"),
    )

    return result
