# query.py
"""Main query endpoints: agentic and baseline."""

import logging
import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agentic_rag.models import QueryRequest, QueryResponse, RefinementMode, RerankingMode, LLMCall
from agentic_rag.orchestration import Orchestrator
from agentic_rag.pipelines.traditional_rag import TraditionalRAG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

# Initialize components
orchestrator = Orchestrator()
traditional_rag = TraditionalRAG()


@router.post("/query", response_model=QueryResponse)
async def agentic_query(request: QueryRequest):
    """
    Execute an agentic RAG query.

    The agentic pipeline:
    1. Classifies query intent
    2. Selects retrieval strategy
    3. Retrieves from appropriate sources
    4. Refines context (dedup/synthesize)
    5. Evaluates sufficiency
    6. Generates structured answer
    """
    try:
        response = await orchestrator.query(request)
        return response
    except Exception as e:
        logger.error(f"Error in agentic_query: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


class BaselineRequest(BaseModel):
    """Request for baseline traditional RAG."""
    question: str
    top_k: int = 10
    include_trace: bool = False


class BaselineTraceStep(BaseModel):
    """A step in the traditional RAG trace."""
    name: str
    type: str
    duration_ms: float
    status: str
    details: dict = {}


class BaselineTrace(BaseModel):
    """Trace information for traditional RAG."""
    steps: list[BaselineTraceStep] = []
    total_duration_ms: float | None = None
    sources_used: list[str] = []
    mlflow_run_id: str | None = None
    llm_calls: list[LLMCall] = []


class BaselineResponse(BaseModel):
    """Response from baseline traditional RAG."""
    answer: str
    documents_used: int
    sources: list[str]
    trace: BaselineTrace | None = None


@router.post("/query/baseline", response_model=BaselineResponse)
async def baseline_query(request: BaselineRequest):
    """
    Execute a traditional RAG query for comparison.

    The traditional pipeline:
    1. Embed query
    2. Retrieve top-k from all sources
    3. Concatenate context
    4. Generate answer

    No intent classification, no strategy selection, no refinement.
    """
    try:
        answer, docs, trace = await traditional_rag.query(
            request.question,
            request.top_k,
            include_trace=request.include_trace,
        )

        response_trace = None
        if trace:
            response_trace = BaselineTrace(
                steps=[BaselineTraceStep(**step) for step in trace.steps],
                total_duration_ms=trace.total_duration_ms,
                sources_used=trace.sources_used,
                mlflow_run_id=trace.mlflow_run_id,
                llm_calls=trace.llm_calls,
            )

        return BaselineResponse(
            answer=answer,
            documents_used=len(docs),
            sources=list(set(d.source.value for d in docs)),
            trace=response_trace,
        )
    except Exception as e:
        logger.error(f"Error in baseline_query: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/refinement-modes")
async def get_refinement_modes():
    """Get available refinement modes with descriptions."""
    return {
        "modes": [
            {
                "value": RefinementMode.NONE.value,
                "name": "None",
                "description": "No refinement - raw retrieval results",
            },
            {
                "value": RefinementMode.DEDUP.value,
                "name": "Deduplicate",
                "description": "Remove duplicates and marginally relevant passages, preserve original text",
            },
            {
                "value": RefinementMode.SYNTHESIZE.value,
                "name": "Synthesize",
                "description": "Compress passages into a summary (lossy)",
            },
            {
                "value": RefinementMode.FILTER.value,
                "name": "Filter (Recommended)",
                "description": "Score relevance, keep top documents with original text - no rewriting",
            },
        ]
    }


@router.get("/query/reranking-modes")
async def get_reranking_modes():
    """Get available reranking modes with descriptions."""
    return {
        "modes": [
            {
                "value": RerankingMode.NONE.value,
                "name": "None",
                "description": "No reranking - use retrieval similarity scores",
            },
            {
                "value": RerankingMode.CROSS_ENCODER.value,
                "name": "Cross-Encoder",
                "description": "Re-score with cross-encoder for better relevance ranking",
            },
        ]
    }
