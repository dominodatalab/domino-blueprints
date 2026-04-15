# vector_store.py
"""
Vector store abstraction using Qdrant.

Supports hybrid search: metadata filtering + semantic similarity.
"""

from typing import Any, Iterator
from urllib.parse import urljoin
import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from agentic_rag.config import get_settings, get_domino_access_token
from agentic_rag.models import Document, SourceType
from agentic_rag.indexers.embeddings import get_embedder, Embedder


class BearerAuthQdrantClient:
    """
    Qdrant client wrapper that uses Bearer token authentication.

    Used for Domino deployments where the reverse proxy requires
    Authorization: Bearer header. Fetches a fresh token for each request
    since tokens are only valid for 5 minutes.
    """

    def __init__(self, url: str):
        self.url = url.rstrip("/")

    def _get_headers(self) -> dict:
        """Build headers with fresh Bearer token."""
        headers = {"Content-Type": "application/json"}
        token = get_domino_access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _request(self, method: str, endpoint: str, json_data: dict = None, expect_json: bool = True) -> dict | str:
        """Make authenticated request to Qdrant with fresh token."""
        url = f"{self.url}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            json=json_data,
            timeout=30,
        )
        response.raise_for_status()
        if expect_json:
            return response.json()
        return response.text

    def health_check(self) -> str:
        """Check Qdrant health (returns plain text)."""
        return self._request("GET", "/healthz", expect_json=False)

    def get_collections(self):
        """List all collections."""
        result = self._request("GET", "/collections")
        # Return object with .collections attribute to match QdrantClient API
        class Collections:
            def __init__(self, data):
                self.collections = [
                    type("Col", (), {"name": c["name"]})()
                    for c in data.get("result", {}).get("collections", [])
                ]
        return Collections(result)

    def get_collection(self, collection_name: str):
        """Get collection info."""
        result = self._request("GET", f"/collections/{collection_name}")
        info = result.get("result", {})
        return type("CollectionInfo", (), {
            "vectors_count": info.get("vectors_count", 0),
            "points_count": info.get("points_count", 0),
            "status": type("Status", (), {"value": info.get("status", "unknown")})(),
        })()

    def create_collection(self, collection_name: str, vectors_config: VectorParams):
        """Create a collection."""
        data = {
            "vectors": {
                "size": vectors_config.size,
                "distance": vectors_config.distance.value,
            }
        }
        return self._request("PUT", f"/collections/{collection_name}", data)

    def delete_collection(self, collection_name: str):
        """Delete a collection."""
        return self._request("DELETE", f"/collections/{collection_name}")

    def upsert(self, collection_name: str, points: list[PointStruct]):
        """Upsert points into collection."""
        data = {
            "points": [
                {
                    "id": p.id,
                    "vector": p.vector,
                    "payload": p.payload,
                }
                for p in points
            ]
        }
        return self._request("PUT", f"/collections/{collection_name}/points", data)

    def query_points(
        self,
        collection_name: str,
        query: list[float],
        query_filter: qdrant_models.Filter = None,
        limit: int = 10,
    ):
        """Search for similar vectors."""
        data = {
            "vector": query,
            "limit": limit,
            "with_payload": True,
        }
        if query_filter:
            data["filter"] = self._convert_filter(query_filter)

        result = self._request("POST", f"/collections/{collection_name}/points/search", data)

        # Convert to match QdrantClient response format
        class Point:
            def __init__(self, hit):
                self.id = hit["id"]
                self.score = hit["score"]
                self.payload = hit.get("payload", {})

        class QueryResult:
            def __init__(self, hits):
                self.points = [Point(h) for h in hits]

        return QueryResult(result.get("result", []))

    def _convert_filter(self, filter_obj: qdrant_models.Filter) -> dict:
        """Convert qdrant filter object to dict for REST API."""
        result = {}
        if filter_obj.must:
            result["must"] = []
            for condition in filter_obj.must:
                if hasattr(condition, "key"):
                    cond = {"key": condition.key}
                    if hasattr(condition, "match"):
                        if hasattr(condition.match, "value"):
                            cond["match"] = {"value": condition.match.value}
                        elif hasattr(condition.match, "text"):
                            cond["match"] = {"text": condition.match.text}
                    result["must"].append(cond)
        return result


def create_qdrant_client() -> QdrantClient | BearerAuthQdrantClient:
    """
    Create Qdrant client with appropriate authentication.

    - If DOMINO_API_PROXY is set, uses BearerAuthQdrantClient for reverse proxy
      (fetches fresh token per request since tokens expire in 5 minutes)
    - Otherwise uses standard QdrantClient
    """
    settings = get_settings()

    # Check for Domino environment (reverse proxy with Bearer auth)
    if settings.domino_api_proxy:
        return BearerAuthQdrantClient(url=settings.qdrant_url)

    # Standard connection (local or with API key)
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )


class VectorStore:
    """Vector store interface using Qdrant."""

    def __init__(
        self,
        collection_name: str,
        source_type: SourceType,
        embedding_dim: int | None = None,  # Auto-detected from embedder if not provided
    ):
        settings = get_settings()
        self.collection_name = collection_name
        self.source_type = source_type

        # Initialize Qdrant client
        self.client = create_qdrant_client()

        # Initialize embedder (local or openai based on config)
        self.embedder: Embedder = get_embedder(
            provider=settings.embedder,
            model_name=settings.embedding_model,
        )
        self.embedding_dim = embedding_dim or self.embedder.dimension

    def create_collection(self, recreate: bool = False) -> None:
        """Create the collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if exists and recreate:
            self.client.delete_collection(self.collection_name)
            exists = False

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE,
                ),
            )
            print(f"Created collection: {self.collection_name}")

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text using configured embedder."""
        return self.embedder.embed(text)

    def embed_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return self.embedder.embed_batch(texts)

    def index_documents(self, documents: Iterator[dict], batch_size: int = 100) -> int:
        """Index documents into the collection."""
        self.create_collection()

        batch = []
        total_indexed = 0

        for doc in documents:
            batch.append(doc)

            if len(batch) >= batch_size:
                self._index_batch(batch)
                total_indexed += len(batch)
                print(f"Indexed {total_indexed} documents...")
                batch = []

        # Index remaining
        if batch:
            self._index_batch(batch)
            total_indexed += len(batch)

        print(f"Total indexed: {total_indexed} documents")
        return total_indexed

    def _index_batch(self, documents: list[dict]) -> None:
        """Index a batch of documents."""
        texts = [doc["text"] for doc in documents]
        embeddings = self.embed_batch(texts)

        points = [
            PointStruct(
                id=hash(doc["id"]) % (2**63),  # Convert string ID to int
                vector=embedding,
                payload={
                    "id": doc["id"],
                    "text": doc["text"],
                    "source": self.source_type.value,
                    **doc.get("metadata", {}),
                },
            )
            for doc, embedding in zip(documents, embeddings)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Search for similar documents with optional filtering."""
        # Check if collection exists
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                return []  # Collection doesn't exist, return empty
        except Exception:
            return []

        query_embedding = self.embed_text(query)

        # Build filter conditions
        filter_conditions = None
        if filters:
            must_conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    must_conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchValue(value=value),
                        )
                    )
                elif isinstance(value, dict) and "$contains" in value:
                    must_conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchText(text=value["$contains"]),
                        )
                    )

            if must_conditions:
                filter_conditions = qdrant_models.Filter(must=must_conditions)

        # Execute search using query_points (new API)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=filter_conditions,
            limit=top_k,
        )

        # Convert to Document objects
        documents = []
        for result in results.points:
            payload = result.payload
            documents.append(
                Document(
                    id=payload.get("id", str(result.id)),
                    text=payload.get("text", ""),
                    source=SourceType(payload.get("source", self.source_type.value)),
                    metadata={k: v for k, v in payload.items() if k not in ("id", "text", "source")},
                    score=result.score,
                )
            )

        return documents

    def hybrid_search(
        self,
        query: str,
        header_filters: dict[str, str] | None = None,
        top_k: int = 10,
    ) -> list[Document]:
        """
        Two-stage hybrid search:
        1. Filter by headers (text attributes)
        2. Semantic search within filtered set
        """
        # Build header filter
        filters = {}
        if header_filters:
            for key, value in header_filters.items():
                filters[key] = {"$contains": value}

        return self.search(query=query, top_k=top_k, filters=filters if filters else None)

    def get_collection_info(self) -> dict:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
            }
        except Exception as e:
            return {"name": self.collection_name, "error": str(e)}


# Convenience functions for each source type
def get_incidents_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(
        collection_name=settings.incidents_collection,
        source_type=SourceType.INCIDENTS,
    )


def get_regulations_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(
        collection_name=settings.regulations_collection,
        source_type=SourceType.REGULATIONS,
    )


def get_news_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(
        collection_name=settings.news_collection,
        source_type=SourceType.NEWS,
    )
