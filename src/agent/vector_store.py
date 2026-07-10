"""ChromaDB vector store wrapper for historical case retrieval.

Manages a persistent ChromaDB collection of radiology cases. Each case
is stored as a document with its clinical description and findings,
enabling semantic similarity search against current scan findings.

The default embedding function (all-MiniLM-L6-v2 via sentence-transformers)
runs locally — no external API calls needed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import chromadb

from src.agent.mock_data import MOCK_CASES
from src.agent.state import SimilarCase

logger = logging.getLogger(__name__)

# Default persistence path — survives restarts so we don't re-seed every time.
_DEFAULT_PERSIST_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chromadb"

COLLECTION_NAME = "radiology_cases"


class CaseVectorStore:
    """Thin wrapper around a ChromaDB collection of radiology cases.

    Args:
        persist_directory: Where ChromaDB stores its data on disk.
            Pass ``None`` for an ephemeral (in-memory) store, useful
            for tests.
    """

    def __init__(self, persist_directory: str | Path | None = _DEFAULT_PERSIST_DIR) -> None:
        if persist_directory is None:
            self._client = chromadb.Client()
        else:
            persist_path = Path(persist_directory)
            persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(persist_path))

        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    def seed_mock_data(self, cases: list[dict] | None = None) -> int:
        """Load mock cases into the collection.

        Skips cases that are already present (idempotent).
        Returns the number of newly added cases.
        """
        cases = cases or MOCK_CASES
        existing_ids = set(self._collection.get()["ids"])
        new_cases = [c for c in cases if c["case_id"] not in existing_ids]

        if not new_cases:
            logger.info("All %d mock cases already present, skipping seed.", len(cases))
            return 0

        documents = []
        metadatas = []
        ids = []

        for case in new_cases:
            # Build a rich text document for embedding — combine description
            # + findings so the embedding captures clinical meaning.
            findings_text = ", ".join(case.get("findings", []))
            doc = f"{case['description']} Findings: {findings_text}"
            documents.append(doc)

            metadatas.append({
                "case_id": case["case_id"],
                "confirmed_diagnosis": case.get("confirmed_diagnosis", ""),
                "outcome": case.get("outcome", ""),
                "patient_age": case.get("patient_age", ""),
                "patient_sex": case.get("patient_sex", ""),
                "modality": case.get("modality", ""),
                "findings_json": json.dumps(case.get("findings", [])),
            })
            ids.append(case["case_id"])

        self._collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info("Seeded %d new cases into ChromaDB.", len(new_cases))
        return len(new_cases)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_similar(
        self,
        findings_text: str,
        top_k: int = 5,
    ) -> list[SimilarCase]:
        """Find the most similar historical cases to the given findings.

        Args:
            findings_text: Free-text description of current findings,
                e.g. ``"Consolidation in right lower lobe with air bronchograms"``.
            top_k: Maximum number of results to return.

        Returns:
            List of ``SimilarCase`` objects sorted by descending similarity.
        """
        if self._collection.count() == 0:
            logger.warning("Vector store is empty — no results to return.")
            return []

        # Clamp top_k to available count
        effective_k = min(top_k, self._collection.count())

        results = self._collection.query(
            query_texts=[findings_text],
            n_results=effective_k,
            include=["metadatas", "distances", "documents"],
        )

        similar_cases: list[SimilarCase] = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            # ChromaDB cosine distance is in [0, 2]; convert to similarity in [0, 1]
            similarity = max(0.0, 1.0 - distance)

            findings_list = json.loads(meta.get("findings_json", "[]"))

            similar_cases.append(
                SimilarCase(
                    case_id=meta.get("case_id", results["ids"][0][i]),
                    description=results["documents"][0][i],
                    findings=findings_list,
                    confirmed_diagnosis=meta.get("confirmed_diagnosis", ""),
                    similarity_score=round(similarity, 4),
                    outcome=meta.get("outcome", ""),
                )
            )

        # Sort by similarity (highest first) — ChromaDB returns by distance
        # (lowest first) so the order should already be correct, but
        # we explicitly sort to be safe.
        similar_cases.sort(key=lambda c: c.similarity_score, reverse=True)
        return similar_cases

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        """Number of cases currently in the collection."""
        return self._collection.count()

    def reset(self) -> None:
        """Delete all cases from the collection."""
        self._client.delete_collection(COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
