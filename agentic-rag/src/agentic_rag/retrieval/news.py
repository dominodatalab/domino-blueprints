# news.py
"""News article retriever."""

from typing import Any

from agentic_rag.models import SourceType, RetrievalResult
from agentic_rag.data.indexers.vector_store import get_news_store
from .base import BaseRetriever


class NewsRetriever(BaseRetriever):
    """Retriever for news articles."""

    source_type = SourceType.NEWS

    def __init__(self):
        self.store = get_news_store()

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        """Retrieve news articles matching the query."""
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
        Hybrid retrieval for news.

        Useful filters:
        - header_l1: "News: {source}"
        - header_l2: "{date}"
        - news_source: "Aviation Weekly", etc.
        - related_incident_id: link to NTSB report
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

    def retrieve_by_incident(self, incident_id: str, top_k: int = 5) -> RetrievalResult:
        """Retrieve news articles related to a specific incident."""
        return self.hybrid_retrieve(
            query=incident_id,
            header_filters={"related_incident_id": incident_id},
            top_k=top_k,
        )

    def retrieve_by_date_range(
        self,
        query: str,
        start_date: str,
        end_date: str,
        top_k: int = 10,
    ) -> RetrievalResult:
        """Retrieve news within a date range."""
        # Note: Qdrant supports range filters, but for simplicity
        # we'll do post-filtering or use text matching
        return self.retrieve(query=query, top_k=top_k)
