# agentic_rag.py
"""Agentic RAG pipeline - wrapper around orchestrator."""

from agentic_rag.models import QueryRequest, QueryResponse, RefinementMode
from agentic_rag.orchestration import Orchestrator


class AgenticRAG:
    """
    Agentic RAG pipeline.

    This is a convenience wrapper around the Orchestrator
    for programmatic use outside of the API.
    """

    def __init__(self):
        self.orchestrator = Orchestrator()

    async def query(
        self,
        question: str,
        refinement_mode: RefinementMode = RefinementMode.DEDUP,
        top_k: int = 10,
        include_trace: bool = True,
    ) -> QueryResponse:
        """Execute an agentic RAG query."""
        request = QueryRequest(
            question=question,
            refinement_mode=refinement_mode,
            top_k=top_k,
            include_trace=include_trace,
        )
        return await self.orchestrator.query(request)

    async def compare(
        self,
        question: str,
        top_k: int = 10,
    ) -> dict:
        """
        Run both traditional and agentic RAG for comparison.

        Returns dict with both results.
        """
        from .traditional_rag import TraditionalRAG

        traditional = TraditionalRAG()

        # Run both
        trad_answer, trad_docs, trad_trace = await traditional.query(question, top_k)
        agentic_response = await self.query(question, top_k=top_k)

        return {
            "question": question,
            "traditional": {
                "answer": trad_answer,
                "documents_used": len(trad_docs),
                "trace": trad_trace.__dict__ if trad_trace else None,
            },
            "agentic": {
                "answer": agentic_response.answer.model_dump(),
                "trace": agentic_response.trace.model_dump() if agentic_response.trace else None,
            },
        }
