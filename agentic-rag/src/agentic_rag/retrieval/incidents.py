# incidents.py
"""NTSB incident report retriever."""

from typing import Any

from agentic_rag.models import SourceType, RetrievalResult
from agentic_rag.data.indexers.vector_store import get_incidents_store
from .base import BaseRetriever


class IncidentRetriever(BaseRetriever):
    """Retriever for NTSB incident reports."""

    source_type = SourceType.INCIDENTS

    def __init__(self):
        self.store = get_incidents_store()

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        """Retrieve incident reports matching the query."""
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
        Hybrid retrieval for incidents.

        Useful filters:
        - header_l1: "NTSB Report {event_id}"
        - header_l2: "{date} - {location}"
        - injury_severity: "Fatal", "Serious", etc.
        - weather_condition: "VMC", "IMC"
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

    def retrieve_by_event_id(self, event_id: str) -> RetrievalResult:
        """Retrieve a specific incident by event ID."""
        return self.hybrid_retrieve(
            query=event_id,
            header_filters={"event_id": event_id},
            top_k=5,
        )

    def retrieve_by_location(self, location: str, top_k: int = 10) -> RetrievalResult:
        """Retrieve incidents by location."""
        return self.hybrid_retrieve(
            query=location,
            header_filters={"location": location},
            top_k=top_k,
        )
