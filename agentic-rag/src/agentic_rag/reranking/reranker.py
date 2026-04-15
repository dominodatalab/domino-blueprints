# reranker.py
"""Cross-encoder reranking for improved retrieval quality.

Cross-encoders score query-document pairs directly, providing more accurate
relevance scores than bi-encoder (embedding) similarity. This allows us to:
1. Retrieve more documents with high recall (large K)
2. Re-score with cross-encoder for precision
3. Keep top documents with accurate relevance ordering

Unlike synthesis/dedup which rewrites text, reranking preserves original documents.
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..models import Document, RerankingMode

logger = logging.getLogger(__name__)


@dataclass
class RerankingResult:
    """Result from reranking operation."""
    documents: list[Document]
    mode: RerankingMode
    input_count: int
    output_count: int
    model: str | None = None
    duration_ms: float | None = None


class Reranker(ABC):
    """Abstract base class for rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int | None = None
    ) -> RerankingResult:
        """Rerank documents by relevance to query.

        Args:
            query: The search query
            documents: Documents to rerank
            top_k: Number of top documents to return (None = return all, reordered)

        Returns:
            RerankingResult with reranked documents
        """
        pass


class NoOpReranker(Reranker):
    """No-op reranker that passes documents through unchanged."""

    def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int | None = None
    ) -> RerankingResult:
        """Pass documents through unchanged."""
        output_docs = documents[:top_k] if top_k else documents
        return RerankingResult(
            documents=output_docs,
            mode=RerankingMode.NONE,
            input_count=len(documents),
            output_count=len(output_docs),
            model=None,
            duration_ms=0.0
        )


class CrossEncoderReranker(Reranker):
    """Cross-encoder based reranker using sentence-transformers.

    Cross-encoders process query and document together, allowing for
    more accurate relevance scoring than bi-encoder similarity.

    Default model: cross-encoder/ms-marco-MiniLM-L-6-v2
    - Fast inference
    - Good quality for general retrieval
    - Trained on MS MARCO passage ranking
    """

    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model_name: str | None = None):
        """Initialize cross-encoder reranker.

        Args:
            model_name: HuggingFace model name. Defaults to ms-marco-MiniLM-L-6-v2
        """
        self.model_name = model_name or os.environ.get(
            "CROSS_ENCODER_MODEL",
            self.DEFAULT_MODEL
        )
        self._model = None

    @property
    def model(self):
        """Lazy load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading cross-encoder model: {self.model_name}")
                self._model = CrossEncoder(self.model_name)
                logger.info("Cross-encoder model loaded successfully")
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for cross-encoder reranking. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int | None = None
    ) -> RerankingResult:
        """Rerank documents using cross-encoder scores.

        Args:
            query: The search query
            documents: Documents to rerank
            top_k: Number of top documents to return

        Returns:
            RerankingResult with documents sorted by cross-encoder relevance
        """
        if not documents:
            return RerankingResult(
                documents=[],
                mode=RerankingMode.CROSS_ENCODER,
                input_count=0,
                output_count=0,
                model=self.model_name,
                duration_ms=0.0
            )

        start_time = time.time()

        # Create query-document pairs for cross-encoder
        pairs = [(query, doc.text) for doc in documents]

        # Get cross-encoder scores
        scores = self.model.predict(pairs)

        # Pair documents with their new scores
        scored_docs = list(zip(documents, scores))

        # Sort by cross-encoder score (descending)
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Update document scores and take top_k
        reranked_docs = []
        for doc, score in scored_docs:
            # Create new document with updated score
            reranked_doc = Document(
                id=doc.id,
                text=doc.text,
                source=doc.source,
                metadata={
                    **doc.metadata,
                    "original_score": doc.score,
                    "cross_encoder_score": float(score)
                },
                score=float(score)  # Use cross-encoder score as primary score
            )
            reranked_docs.append(reranked_doc)

        # Apply top_k limit
        output_docs = reranked_docs[:top_k] if top_k else reranked_docs

        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Cross-encoder reranking: {len(documents)} -> {len(output_docs)} docs "
            f"in {duration_ms:.1f}ms"
        )

        return RerankingResult(
            documents=output_docs,
            mode=RerankingMode.CROSS_ENCODER,
            input_count=len(documents),
            output_count=len(output_docs),
            model=self.model_name,
            duration_ms=duration_ms
        )


def get_reranker(mode: RerankingMode) -> Reranker:
    """Factory function to get appropriate reranker.

    Args:
        mode: The reranking mode to use

    Returns:
        Appropriate Reranker instance
    """
    if mode == RerankingMode.NONE:
        return NoOpReranker()
    elif mode == RerankingMode.CROSS_ENCODER:
        return CrossEncoderReranker()
    else:
        logger.warning(f"Unknown reranking mode: {mode}, using NoOp")
        return NoOpReranker()
