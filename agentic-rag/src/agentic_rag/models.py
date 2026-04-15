# models.py
"""Shared data models for agentic RAG."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class RefinementMode(str, Enum):
    """Context refinement strategy."""
    NONE = "none"           # Skip refinement, pass all passages
    DEDUP = "dedup"         # Deduplicate + prune, preserve original text
    SYNTHESIZE = "synthesize"  # Compress into summary
    FILTER = "filter"       # Score relevance, keep top chunks with original text (no rewriting)


class RerankingMode(str, Enum):
    """Reranking strategy applied before refinement."""
    NONE = "none"                   # No reranking, use retrieval scores
    CROSS_ENCODER = "cross_encoder" # Use cross-encoder model for relevance scoring


class IntentType(str, Enum):
    """Query intent classification."""
    CAUSAL = "causal"           # What caused X?
    COMPLIANCE = "compliance"   # Was X legal/compliant?
    FACTUAL = "factual"         # What happened?
    COMPARATIVE = "comparative" # Compare to similar events
    REGULATORY = "regulatory"   # What does regulation say?
    MULTI_SOURCE = "multi_source"  # Cross-reference required


class RetrievalStrategy(str, Enum):
    """Retrieval execution strategy."""
    DIRECT = "direct"       # Single source
    SEQUENTIAL = "sequential"  # Source A then B
    PARALLEL = "parallel"   # Multiple sources at once
    ITERATIVE = "iterative" # Retrieve, evaluate, repeat


class SourceType(str, Enum):
    """Document source types."""
    INCIDENTS = "incidents"
    REGULATIONS = "regulations"
    NEWS = "news"


# --- Request/Response Models ---

class QueryRequest(BaseModel):
    """Incoming query request."""
    question: str
    refinement_mode: RefinementMode = RefinementMode.DEDUP
    reranking_mode: RerankingMode = RerankingMode.NONE
    top_k: int = Field(default=10, ge=1, le=50)
    include_trace: bool = True
    sources: list[SourceType] | None = None  # None = auto-select


class RetrievalRequest(BaseModel):
    """Request to a retrieval endpoint."""
    query: str
    top_k: int = 10
    filters: dict[str, Any] | None = None


class Document(BaseModel):
    """Retrieved document."""
    id: str
    text: str
    source: SourceType
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0


class RetrievalResult(BaseModel):
    """Result from a retrieval endpoint."""
    documents: list[Document]
    source: SourceType
    query: str
    total_found: int


class RefinementResult(BaseModel):
    """Result from context refinement."""
    documents: list[Document]
    mode: RefinementMode
    input_count: int
    output_count: int
    dropped: list[dict[str, str]] = Field(default_factory=list)
    llm_call: "LLMCall | None" = None  # Raw LLM data if LLM was used


class Finding(BaseModel):
    """A structured finding in the answer."""
    finding: str
    source: str
    confidence: str = "medium"


class RegulatoryContext(BaseModel):
    """Regulatory information in the answer."""
    regulation: str
    relevance: str
    compliance_status: str | None = None


class StructuredAnswer(BaseModel):
    """Structured answer from agentic RAG."""
    summary: str
    key_findings: list[Finding] = Field(default_factory=list)
    regulatory_context: list[RegulatoryContext] = Field(default_factory=list)
    causal_chain: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class TraceEntry(BaseModel):
    """Single entry in the execution trace."""
    step: str
    data: dict[str, Any]
    duration_ms: float | None = None


class LLMCall(BaseModel):
    """Raw LLM interaction for debugging/transparency."""
    step: str  # e.g., "intent_classification", "refinement_dedup", "generation"
    model: str  # Model used
    prompt: str  # The actual prompt sent
    response: str  # Raw response from LLM
    duration_ms: float | None = None


class QueryTrace(BaseModel):
    """Full execution trace for a query."""
    mlflow_trace_id: str | None = None  # MLflow trace ID for linking
    mlflow_run_id: str | None = None  # MLflow run ID
    intent: IntentType | None = None
    intent_confidence: str | None = None
    strategy: RetrievalStrategy | None = None
    sources_used: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] | None = None  # Extracted query constraints
    constraint_validation: dict[str, Any] | None = None  # Validation results
    retrievals: list[dict[str, Any]] = Field(default_factory=list)
    reranking: dict[str, Any] | None = None  # Reranking step info
    refinement: dict[str, Any] | None = None
    generation: dict[str, Any] | None = None  # Generation step info
    sufficiency_checks: list[dict[str, Any]] = Field(default_factory=list)
    total_duration_ms: float | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)  # Ordered list of steps for timeline
    llm_calls: list[LLMCall] = Field(default_factory=list)  # Raw LLM inputs/outputs for debugging


class QueryResponse(BaseModel):
    """Response to a query."""
    answer: StructuredAnswer
    trace: QueryTrace | None = None
    raw_answer: str | None = None  # For traditional RAG comparison
