# mlflow_tracer.py
"""MLflow integration for tracing agentic RAG queries."""

import time
import json
from typing import Any, Generator
from contextlib import contextmanager

from agentic_rag.config import get_settings


# Lazy import to avoid issues when mlflow is not installed
_mlflow = None
_mlflow_tracing = None


def _get_mlflow():
    """Lazy load mlflow."""
    global _mlflow
    if _mlflow is None:
        try:
            import mlflow
            _mlflow = mlflow
        except ImportError:
            _mlflow = False
    return _mlflow if _mlflow else None


def _get_mlflow_tracing():
    """Lazy load mlflow.tracing."""
    global _mlflow_tracing
    if _mlflow_tracing is None:
        try:
            from mlflow.tracing import set_span_attribute
            import mlflow.tracing
            _mlflow_tracing = mlflow.tracing
        except ImportError:
            _mlflow_tracing = False
    return _mlflow_tracing if _mlflow_tracing else None


class MLflowTracer:
    """
    MLflow tracer for logging agentic RAG execution.

    Logs:
    - Query parameters (question, refinement_mode, top_k)
    - Pipeline metrics (duration, document counts, etc.)
    - Execution trace as artifact
    - Structured answer as artifact
    """

    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.mlflow_enabled
        self._initialized = False
        self._current_trace = None

    def _ensure_initialized(self):
        """Initialize MLflow connection lazily."""
        if self._initialized or not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            self.enabled = False
            return

        try:
            mlflow.set_tracking_uri(self.settings.mlflow_tracking_uri)
            mlflow.set_experiment(self.settings.mlflow_experiment_name)
            self._initialized = True
        except Exception as e:
            print(f"Warning: Failed to initialize MLflow: {e}")
            self.enabled = False

    @contextmanager
    def start_run(self, run_name: str | None = None):
        """Start an MLflow run context."""
        if not self.enabled:
            yield None
            return

        self._ensure_initialized()
        if not self._initialized:
            yield None
            return

        mlflow = _get_mlflow()
        run = None
        try:
            run = mlflow.start_run(run_name=run_name)
        except Exception as e:
            print(f"Warning: MLflow start_run failed: {e}")
            yield None
            return

        try:
            yield run
        finally:
            try:
                mlflow.end_run()
            except Exception as e:
                print(f"Warning: MLflow end_run failed: {e}")

    # ==================== TRACING METHODS ====================

    @contextmanager
    def start_trace(self, name: str, inputs: dict[str, Any] | None = None) -> Generator[Any, None, None]:
        """
        Start a root trace for the entire query pipeline.

        Uses mlflow.start_span which automatically creates a trace when there's no
        active trace, and child spans nest under it when called within the context.

        Args:
            name: Name of the trace (e.g., "agentic_rag_query")
            inputs: Input parameters to log with the trace
        """
        if not self.enabled:
            yield None
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            yield None
            return

        try:
            # Use start_span as a context manager - it returns a context manager in newer MLflow
            with mlflow.start_span(name=name) as span:
                if inputs and span:
                    try:
                        span.set_inputs(inputs)
                    except Exception:
                        pass
                self._current_trace = span
                yield span
                self._current_trace = None
        except Exception as e:
            print(f"Warning: MLflow start_trace failed: {e}")
            yield None

    @contextmanager
    def span(self, name: str, span_type: str = "CHAIN") -> Generator[Any, None, None]:
        """
        Create a child span within the current trace.

        Args:
            name: Name of the span (e.g., "intent_classification")
            span_type: Type of span (CHAIN, RETRIEVER, LLM, TOOL, etc.)
        """
        if not self.enabled:
            yield None
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            yield None
            return

        try:
            # Use start_span as a context manager - it returns a context manager in newer MLflow
            with mlflow.start_span(name=name, span_type=span_type) as span:
                yield span
        except Exception as e:
            print(f"Warning: MLflow span failed: {e}")
            yield None

    def set_span_inputs(self, span: Any, inputs: dict[str, Any]):
        """Set inputs on a span."""
        if span is None or not self.enabled:
            return
        try:
            span.set_inputs(inputs)
        except Exception:
            pass

    def set_span_outputs(self, span: Any, outputs: dict[str, Any]):
        """Set outputs on a span."""
        if span is None or not self.enabled:
            return
        try:
            span.set_outputs(outputs)
        except Exception:
            pass

    def set_span_attribute(self, span: Any, key: str, value: Any):
        """Set a single attribute on a span."""
        if span is None or not self.enabled:
            return
        try:
            span.set_attribute(key, value)
        except Exception:
            pass

    def set_span_attributes(self, span: Any, attributes: dict[str, Any]):
        """Set multiple attributes on a span."""
        if span is None or not self.enabled:
            return
        try:
            span.set_attributes(attributes)
        except Exception:
            pass

    # ==================== SPECIALIZED TRACED OPERATIONS ====================

    @contextmanager
    def trace_constraint_extraction(self, question: str) -> Generator[Any, None, None]:
        """Trace constraint extraction from query."""
        with self.span("constraint_extraction", span_type="TOOL") as span:
            self.set_span_inputs(span, {"question": question})
            yield span

    @contextmanager
    def trace_intent_classification(self, question: str) -> Generator[Any, None, None]:
        """Trace intent classification."""
        with self.span("intent_classification", span_type="LLM") as span:
            self.set_span_inputs(span, {"question": question})
            yield span

    @contextmanager
    def trace_strategy_selection(self, intent: str, question: str) -> Generator[Any, None, None]:
        """Trace strategy selection."""
        with self.span("strategy_selection", span_type="CHAIN") as span:
            self.set_span_inputs(span, {"intent": intent, "question": question})
            yield span

    @contextmanager
    def trace_retrieval(self, strategy: str, sources: list[str], iteration: int) -> Generator[Any, None, None]:
        """Trace document retrieval."""
        with self.span(f"retrieval_iteration_{iteration}", span_type="RETRIEVER") as span:
            self.set_span_inputs(span, {
                "strategy": strategy,
                "sources": sources,
                "iteration": iteration,
            })
            yield span

    @contextmanager
    def trace_constraint_validation(self, constraints: dict[str, Any]) -> Generator[Any, None, None]:
        """Trace constraint validation."""
        with self.span("constraint_validation", span_type="TOOL") as span:
            self.set_span_inputs(span, {"constraints": constraints})
            yield span

    @contextmanager
    def trace_context_evaluation(self, question: str, doc_count: int) -> Generator[Any, None, None]:
        """Trace context sufficiency evaluation."""
        with self.span("context_evaluation", span_type="LLM") as span:
            self.set_span_inputs(span, {
                "question": question,
                "document_count": doc_count,
            })
            yield span

    @contextmanager
    def trace_refinement(self, mode: str, input_count: int) -> Generator[Any, None, None]:
        """Trace context refinement."""
        span_type = "LLM" if mode == "synthesize" else "TOOL"
        with self.span("context_refinement", span_type=span_type) as span:
            self.set_span_inputs(span, {
                "mode": mode,
                "input_document_count": input_count,
            })
            yield span

    @contextmanager
    def trace_generation(self, question: str, intent: str, doc_count: int) -> Generator[Any, None, None]:
        """Trace answer generation."""
        with self.span("answer_generation", span_type="LLM") as span:
            self.set_span_inputs(span, {
                "question": question,
                "intent": intent,
                "document_count": doc_count,
            })
            yield span

    # ==================== METRIC LOGGING METHODS ====================

    def log_query_params(
        self,
        question: str,
        refinement_mode: str,
        top_k: int,
        include_trace: bool,
    ):
        """Log query parameters."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_params({
                "question": question[:250],  # Truncate long questions
                "refinement_mode": refinement_mode,
                "top_k": top_k,
                "include_trace": include_trace,
            })
        except Exception as e:
            print(f"Warning: Failed to log params: {e}")

    def log_intent(self, intent: str, confidence: str):
        """Log intent classification results."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_params({
                "intent": intent,
                "intent_confidence": confidence,
            })
        except Exception:
            pass

    def log_strategy(self, strategy: str, sources: list[str]):
        """Log retrieval strategy."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_params({
                "strategy": strategy,
                "sources": ",".join(sources),
            })
        except Exception:
            pass

    def log_constraints(self, constraints: dict[str, Any]):
        """Log extracted constraints."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            # Log non-null constraints
            for key, value in constraints.items():
                if value is not None:
                    mlflow.log_param(f"constraint_{key}", str(value)[:250])
        except Exception:
            pass

    def log_retrieval_metrics(
        self,
        documents_retrieved: int,
        retrieval_duration_ms: float,
        iteration: int = 1,
    ):
        """Log retrieval metrics."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_metrics({
                f"retrieval_{iteration}_docs": documents_retrieved,
                f"retrieval_{iteration}_duration_ms": retrieval_duration_ms,
            })
        except Exception:
            pass

    def log_constraint_validation(
        self,
        is_valid: bool,
        matched_count: int,
        unmatched: list[str],
    ):
        """Log constraint validation results."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_metrics({
                "constraints_valid": 1 if is_valid else 0,
                "constraints_matched_count": matched_count,
                "constraints_unmatched_count": len(unmatched),
            })
        except Exception:
            pass

    def log_refinement_metrics(
        self,
        mode: str,
        input_count: int,
        output_count: int,
        duration_ms: float,
    ):
        """Log refinement metrics."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_param("refinement_mode_used", mode)
            mlflow.log_metrics({
                "refinement_input_docs": input_count,
                "refinement_output_docs": output_count,
                "refinement_dropped_docs": input_count - output_count,
                "refinement_duration_ms": duration_ms,
            })
        except Exception:
            pass

    def log_generation_metrics(self, duration_ms: float):
        """Log generation metrics."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_metric("generation_duration_ms", duration_ms)
        except Exception:
            pass

    def log_total_metrics(
        self,
        total_duration_ms: float,
        success: bool,
        answer_type: str,  # "structured" or "no_data"
    ):
        """Log total execution metrics."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_metrics({
                "total_duration_ms": total_duration_ms,
                "success": 1 if success else 0,
            })
            mlflow.log_param("answer_type", answer_type)
        except Exception:
            pass

    def log_trace_artifact(self, trace: dict[str, Any]):
        """Log the full execution trace as a JSON artifact."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            trace_json = json.dumps(trace, indent=2, default=str)
            mlflow.log_text(trace_json, "trace.json")
        except Exception:
            pass

    def log_answer_artifact(self, answer: dict[str, Any]):
        """Log the structured answer as a JSON artifact."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            answer_json = json.dumps(answer, indent=2, default=str)
            mlflow.log_text(answer_json, "answer.json")
        except Exception:
            pass

    def log_error(self, error: str):
        """Log an error."""
        if not self.enabled:
            return

        mlflow = _get_mlflow()
        if mlflow is None:
            return

        try:
            mlflow.log_param("error", error[:500])
            mlflow.log_metric("success", 0)
        except Exception:
            pass


# Singleton instance
_tracer_instance = None


def get_mlflow_tracer() -> MLflowTracer:
    """Get the singleton MLflow tracer instance."""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = MLflowTracer()
    return _tracer_instance
