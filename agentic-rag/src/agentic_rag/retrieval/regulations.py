# regulations.py
"""FAR regulation retriever."""

from typing import Any

from agentic_rag.models import SourceType, RetrievalResult
from agentic_rag.data.indexers.vector_store import get_regulations_store
from .base import BaseRetriever


class RegulationRetriever(BaseRetriever):
    """Retriever for FAR regulations."""

    source_type = SourceType.REGULATIONS

    def __init__(self):
        self.store = get_regulations_store()

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        """Retrieve regulations matching the query."""
        documents = self.store.search(query=query, top_k=top_k, filters=filters)

        return RetrievalResult(
            documents=documents,
            source=self.source_type,
            query=query,
            total_found=len(documents),
        )

    def hybrid_retrieve(
        self,
        query: str,
        header_filters: dict[str, str] | None = None,
        top_k: int = 10,
    ) -> RetrievalResult:
        """
        Hybrid retrieval for regulations.

        Useful filters:
        - header_l1: "14 CFR Part {part}"
        - header_l2: "Subpart {subpart}"
        - part: "91", "61", etc.
        - section: "91.103"
        """
        documents = self.store.hybrid_search(
            query=query,
            header_filters=header_filters,
            top_k=top_k,
        )

        return RetrievalResult(
            documents=documents,
            source=self.source_type,
            query=query,
            total_found=len(documents),
        )

    def retrieve_by_part(self, part: str, query: str, top_k: int = 10) -> RetrievalResult:
        """Retrieve regulations from a specific FAR part."""
        return self.hybrid_retrieve(
            query=query,
            header_filters={"part": part},
            top_k=top_k,
        )

    def retrieve_by_section(self, section: str) -> RetrievalResult:
        """Retrieve a specific FAR section."""
        return self.hybrid_retrieve(
            query=section,
            header_filters={"section": section},
            top_k=3,
        )

    def retrieve_vfr_rules(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Retrieve VFR-related regulations."""
        return self.hybrid_retrieve(
            query=f"VFR {query}",
            header_filters={"part": "91"},
            top_k=top_k,
        )

    def retrieve_pilot_certification(self, query: str, top_k: int = 5) -> RetrievalResult:
        """Retrieve pilot certification regulations."""
        return self.hybrid_retrieve(
            query=query,
            header_filters={"part": "61"},
            top_k=top_k,
        )
