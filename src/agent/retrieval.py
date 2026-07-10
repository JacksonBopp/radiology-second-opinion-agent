"""Case Retrieval Agent — finds similar historical cases via ChromaDB.

LangGraph node that queries the vector store for cases with findings
similar to the current scan, then ranks them by outcome relevance.

In mock mode, the vector store is pre-seeded with 10 cases and the
search is purely embedding-based. In production, a Claude 3 Haiku
call will refine the query before searching.
"""

from __future__ import annotations

import logging

from src.agent.state import AgentState, SimilarCase
from src.agent.vector_store import CaseVectorStore

logger = logging.getLogger(__name__)

# Module-level store instance — lazily initialized on first call.
_store: CaseVectorStore | None = None


def _get_store() -> CaseVectorStore:
    """Get or create the shared vector store, seeding mock data if empty."""
    global _store
    if _store is None:
        _store = CaseVectorStore()
        if _store.count == 0:
            _store.seed_mock_data()
    return _store


def set_store(store: CaseVectorStore) -> None:
    """Inject a custom store (useful for testing with ephemeral ChromaDB)."""
    global _store
    _store = store


def _build_query_text(state: AgentState) -> str:
    """Compose a free-text search query from the current findings.

    Combines finding labels, locations, and metadata into a single
    string that will be embedded and matched against historical cases.
    """
    findings = state.get("findings", [])
    metadata = state.get("metadata", {})

    parts: list[str] = []

    # Patient demographics for context
    age = metadata.get("patient_age", "")
    sex = metadata.get("patient_sex", "")
    if age or sex:
        parts.append(f"Patient: {age} {sex}".strip())

    # Findings
    for finding in findings:
        label = finding.label if hasattr(finding, "label") else finding.get("label", "")
        location = finding.location if hasattr(finding, "location") else finding.get("location", "")
        if label:
            entry = label
            if location:
                entry += f" in {location}"
            parts.append(entry)

    if not parts:
        parts.append("Chest radiograph with no significant abnormalities")

    return ". ".join(parts)


def _rank_by_outcome(cases: list[SimilarCase]) -> list[SimilarCase]:
    """Re-rank cases so those with confirmed diagnoses float to the top.

    Cases with a confirmed diagnosis are more valuable for differential
    reasoning than cases still awaiting follow-up.
    """
    def _score(case: SimilarCase) -> float:
        base = case.similarity_score
        # Boost cases that have a confirmed diagnosis
        if case.confirmed_diagnosis and case.confirmed_diagnosis.lower() != "unknown":
            base += 0.1
        # Boost cases that have documented outcomes
        if case.outcome:
            base += 0.05
        return base

    return sorted(cases, key=_score, reverse=True)


# ------------------------------------------------------------------
# LangGraph node function
# ------------------------------------------------------------------


def run_retrieval(state: AgentState) -> dict:
    """LangGraph node: retrieve similar historical cases.

    Reads ``findings`` and ``metadata`` from state, queries ChromaDB,
    and returns ``similar_cases`` to be merged back into the state.
    """
    logger.info("Case Retrieval Agent: starting for scan %s", state.get("scan_id", "unknown"))

    try:
        store = _get_store()
        query_text = _build_query_text(state)
        logger.debug("Search query: %s", query_text)

        cases = store.search_similar(query_text, top_k=5)
        ranked = _rank_by_outcome(cases)

        logger.info(
            "Case Retrieval Agent: found %d similar cases (top match: %s, score=%.3f)",
            len(ranked),
            ranked[0].case_id if ranked else "none",
            ranked[0].similarity_score if ranked else 0.0,
        )

        return {
            "similar_cases": ranked,
            "current_step": "retrieval_complete",
        }

    except Exception as exc:
        logger.error("Case Retrieval Agent failed: %s", exc)
        return {
            "similar_cases": [],
            "errors": state.get("errors", []) + [f"Retrieval error: {exc}"],
            "current_step": "retrieval_failed",
        }
