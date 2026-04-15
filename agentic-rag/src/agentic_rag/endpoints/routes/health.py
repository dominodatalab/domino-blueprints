# health.py
"""Health check endpoint."""

from fastapi import APIRouter

from agentic_rag.config import get_settings
from agentic_rag.data.indexers.vector_store import create_qdrant_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check service health and dependencies."""
    settings = get_settings()

    # Check Qdrant using appropriate auth method
    qdrant_status = "unknown"
    try:
        client = create_qdrant_client()
        collections = client.get_collections()
        qdrant_status = "healthy"
        collection_count = len(collections.collections)
    except Exception as e:
        qdrant_status = f"unhealthy: {str(e)}"
        collection_count = 0

    return {
        "status": "healthy" if qdrant_status == "healthy" else "degraded",
        "components": {
            "qdrant": {
                "status": qdrant_status,
                "url": settings.qdrant_url,
                "collections": collection_count,
            },
        },
        "config": {
            "embedding_model": settings.embedding_model,
            "refinement_model": settings.refinement_model,
            "generation_model": settings.generation_model,
        },
    }
