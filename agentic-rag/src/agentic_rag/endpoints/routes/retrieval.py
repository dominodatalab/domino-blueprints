# retrieval.py
"""Retrieval endpoints for individual sources."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

from agentic_rag.models import RetrievalRequest, RetrievalResult
from agentic_rag.retrieval import IncidentRetriever, RegulationRetriever, NewsRetriever

router = APIRouter()

# Initialize retrievers
incident_retriever = IncidentRetriever()
regulation_retriever = RegulationRetriever()
news_retriever = NewsRetriever()


class HybridRetrievalRequest(BaseModel):
    """Request for hybrid retrieval with header filters."""
    query: str
    top_k: int = 10
    header_filters: dict[str, str] | None = None


@router.post("/incidents", response_model=RetrievalResult)
async def retrieve_incidents(request: HybridRetrievalRequest):
    """
    Retrieve NTSB incident reports.

    Supports header filters:
    - event_id: Specific incident ID
    - location: Incident location
    - injury_severity: Fatal, Serious, Minor
    - weather_condition: VMC, IMC
    """
    try:
        if request.header_filters:
            result = incident_retriever.hybrid_retrieve(
                query=request.query,
                header_filters=request.header_filters,
                top_k=request.top_k,
            )
        else:
            result = incident_retriever.retrieve(
                query=request.query,
                top_k=request.top_k,
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regulations", response_model=RetrievalResult)
async def retrieve_regulations(request: HybridRetrievalRequest):
    """
    Retrieve FAR regulations.

    Supports header filters:
    - part: FAR part number (e.g., "91", "61")
    - subpart: Subpart letter (e.g., "B")
    - section: Full section number (e.g., "91.103")
    """
    try:
        if request.header_filters:
            result = regulation_retriever.hybrid_retrieve(
                query=request.query,
                header_filters=request.header_filters,
                top_k=request.top_k,
            )
        else:
            result = regulation_retriever.retrieve(
                query=request.query,
                top_k=request.top_k,
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news", response_model=RetrievalResult)
async def retrieve_news(request: HybridRetrievalRequest):
    """
    Retrieve news articles.

    Supports header filters:
    - news_source: Source name (e.g., "Aviation Weekly")
    - related_incident_id: Link to NTSB report
    """
    try:
        if request.header_filters:
            result = news_retriever.hybrid_retrieve(
                query=request.query,
                header_filters=request.header_filters,
                top_k=request.top_k,
            )
        else:
            result = news_retriever.retrieve(
                query=request.query,
                top_k=request.top_k,
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
