# traditional_rag.py
"""Traditional RAG pipeline for baseline comparison."""

import time
from typing import Any

from agentic_rag.models import Document, SourceType, LLMCall
from agentic_rag.retrieval import IncidentRetriever, RegulationRetriever, NewsRetriever
from agentic_rag.generation import AnswerGenerator
from agentic_rag.tracing.mlflow_tracer import get_mlflow_tracer


class TraditionalRAGTrace:
    """Trace information for traditional RAG."""
    def __init__(self):
        self.steps: list[dict[str, Any]] = []
        self.total_duration_ms: float | None = None
        self.sources_used: list[str] = []
        self.mlflow_run_id: str | None = None
        self.llm_calls: list[LLMCall] = []


class TraditionalRAG:
    """
    Traditional RAG pipeline.

    Simple approach:
    1. Query all sources with same query
    2. Combine top-k results
    3. Concatenate into context
    4. Generate answer

    No intent classification, no strategy, no refinement.
    """

    def __init__(self):
        self.retrievers = {
            SourceType.INCIDENTS: IncidentRetriever(),
            SourceType.REGULATIONS: RegulationRetriever(),
            SourceType.NEWS: NewsRetriever(),
        }
        self.generator = AnswerGenerator()

    async def query(
        self,
        question: str,
        top_k: int = 10,
        include_trace: bool = False,
    ) -> tuple[str, list[Document], TraditionalRAGTrace | None]:
        """
        Execute traditional RAG query.

        Returns:
            (answer_text, documents_used, trace)
        """
        mlflow_tracer = get_mlflow_tracer()
        trace = TraditionalRAGTrace() if include_trace else None
        start_time = time.time()

        with mlflow_tracer.start_run(run_name=f"traditional-{question[:30]}"):
            with mlflow_tracer.start_trace(
                "traditional_rag_pipeline",
                inputs={"question": question, "top_k": top_k}
            ) as root_span:
                # Capture MLflow run ID
                try:
                    import mlflow
                    if mlflow.active_run() and trace:
                        trace.mlflow_run_id = mlflow.active_run().info.run_id
                except Exception:
                    pass

                # Log parameters
                mlflow_tracer.log_query_params(
                    question=question,
                    refinement_mode="none",
                    top_k=top_k,
                    include_trace=include_trace,
                )

                # Retrieve from all sources
                all_documents = []
                per_source_k = max(1, top_k // 3)

                retrieval_start = time.time()
                with mlflow_tracer.span("retrieval", span_type="RETRIEVER") as span:
                    for source_type, retriever in self.retrievers.items():
                        source_start = time.time()
                        try:
                            result = retriever.retrieve(question, top_k=per_source_k)
                            all_documents.extend(result.documents)
                            if trace:
                                trace.sources_used.append(source_type.value)
                                trace.steps.append({
                                    "name": f"Retrieve from {source_type.value}",
                                    "type": "retriever",
                                    "duration_ms": (time.time() - source_start) * 1000,
                                    "status": "success",
                                    "details": {"documents": len(result.documents)},
                                })
                        except Exception as e:
                            if trace:
                                trace.steps.append({
                                    "name": f"Retrieve from {source_type.value}",
                                    "type": "retriever",
                                    "duration_ms": (time.time() - source_start) * 1000,
                                    "status": "error",
                                    "details": {"error": str(e)},
                                })

                    mlflow_tracer.set_span_outputs(span, {
                        "total_documents": len(all_documents),
                        "sources": [s.value for s in self.retrievers.keys()],
                    })

                retrieval_duration = (time.time() - retrieval_start) * 1000
                mlflow_tracer.log_retrieval_metrics(len(all_documents), retrieval_duration)

                # Sort by score and take top_k
                all_documents.sort(key=lambda d: d.score, reverse=True)
                documents = all_documents[:top_k]

                # Generate answer
                generation_start = time.time()
                with mlflow_tracer.span("generation", span_type="LLM") as span:
                    generation_result = await self.generator.generate_traditional(question, documents)
                    answer = generation_result.answer
                    mlflow_tracer.set_span_outputs(span, {
                        "answer_length": len(answer) if answer else 0,
                    })

                generation_duration = (time.time() - generation_start) * 1000
                mlflow_tracer.log_generation_metrics(generation_duration)

                if trace:
                    trace.steps.append({
                        "name": "Answer Generation",
                        "type": "llm",
                        "duration_ms": generation_duration,
                        "status": "success",
                        "details": {"answer_length": len(answer) if answer else 0},
                    })
                    # Collect LLM call
                    trace.llm_calls.append(generation_result.llm_call)

                # Finalize
                total_duration = (time.time() - start_time) * 1000
                if trace:
                    trace.total_duration_ms = total_duration

                mlflow_tracer.log_total_metrics(total_duration, success=True, answer_type="traditional")
                mlflow_tracer.set_span_outputs(root_span, {
                    "success": True,
                    "total_duration_ms": total_duration,
                })

        return answer, documents, trace
