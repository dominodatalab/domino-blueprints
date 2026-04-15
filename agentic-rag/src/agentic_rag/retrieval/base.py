# base.py
"""Base retriever interface."""

from abc import ABC, abstractmethod
from typing import Any

from agentic_rag.models import Document, SourceType, RetrievalResult


class BaseRetriever(ABC):
    """Abstract base class for retrievers."""

    source_type: SourceType

    @abstractmethod
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        """Retrieve documents matching the query."""
        pass

    @abstractmethod
    def hybrid_retrieve(
        self,
        query: str,
        header_filters: dict[str, str] | None = None,
        top_k: int = 10,
    ) -> RetrievalResult:
        """Retrieve with header filtering + semantic search."""
        pass
