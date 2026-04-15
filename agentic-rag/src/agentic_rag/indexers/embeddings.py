"""
Embedding providers for indexers.

Supports both local (sentence-transformers) and remote (OpenAI) embeddings.

Usage:
    from agentic_rag.indexers.embeddings import get_embedder

    # Local embeddings (fast, free)
    embedder = get_embedder("local")

    # OpenAI embeddings (requires API key)
    embedder = get_embedder("openai")

    # Get embedding
    vector = embedder.embed("Some text to embed")
"""

from abc import ABC, abstractmethod
from typing import Literal

# Lazy imports to avoid requiring all dependencies
_sentence_transformers = None
_openai = None


def _get_sentence_transformers():
    global _sentence_transformers
    if _sentence_transformers is None:
        try:
            import sentence_transformers
            _sentence_transformers = sentence_transformers
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
    return _sentence_transformers


def _get_openai():
    global _openai
    if _openai is None:
        try:
            import openai
            _openai = openai
        except ImportError:
            raise ImportError(
                "openai not installed. "
                "Install with: pip install openai"
            )
    return _openai


class Embedder(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        pass

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts. Override for batch optimization."""
        return [self.embed(text) for text in texts]


class LocalEmbedder(Embedder):
    """
    Local embeddings using sentence-transformers.

    Recommended models:
    - all-MiniLM-L6-v2: Fast, 384 dims, good quality (default)
    - all-mpnet-base-v2: Better quality, 768 dims, slower
    - BAAI/bge-small-en-v1.5: Great quality/speed, 384 dims
    - BAAI/bge-base-en-v1.5: Higher quality, 768 dims
    """

    # Model dimensions lookup
    MODEL_DIMENSIONS = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "BAAI/bge-small-en-v1.5": 384,
        "BAAI/bge-base-en-v1.5": 768,
        "BAAI/bge-large-en-v1.5": 1024,
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        st = _get_sentence_transformers()
        print(f"Loading local embedding model: {model_name}...")
        self.model = st.SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Dimension: {self._dimension}")

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        # Truncate very long texts
        text = text[:8000]
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding is much faster with sentence-transformers."""
        texts = [t[:8000] for t in texts]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()


class OpenAIEmbedder(Embedder):
    """
    OpenAI API embeddings.

    Models:
    - text-embedding-3-small: 1536 dims, cheapest (default)
    - text-embedding-3-large: 3072 dims, best quality
    - text-embedding-ada-002: 1536 dims, legacy
    """

    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, model_name: str = "text-embedding-3-small", client=None):
        self.model_name = model_name
        openai = _get_openai()
        self.client = client or openai.OpenAI()
        self._dimension = self.MODEL_DIMENSIONS.get(model_name, 1536)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        text = text[:8000]
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """OpenAI supports batch embedding in a single API call."""
        texts = [t[:8000] for t in texts]
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [d.embedding for d in sorted_data]


def get_embedder(
    provider: Literal["local", "openai"] = "local",
    model_name: str | None = None,
    **kwargs
) -> Embedder:
    """
    Get an embedder instance.

    Args:
        provider: "local" for sentence-transformers, "openai" for OpenAI API
        model_name: Model to use (defaults vary by provider)
        **kwargs: Additional arguments passed to embedder constructor

    Returns:
        Embedder instance

    Examples:
        # Fast local embeddings (default)
        embedder = get_embedder("local")

        # Higher quality local model
        embedder = get_embedder("local", model_name="BAAI/bge-base-en-v1.5")

        # OpenAI embeddings
        embedder = get_embedder("openai")
    """
    if provider == "local":
        model = model_name or "all-MiniLM-L6-v2"
        return LocalEmbedder(model_name=model, **kwargs)
    elif provider == "openai":
        model = model_name or "text-embedding-3-small"
        return OpenAIEmbedder(model_name=model, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'local' or 'openai'.")
