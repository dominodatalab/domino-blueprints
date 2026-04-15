# orchestrator.py
"""Main orchestration logic for agentic RAG."""

import time
from typing import Any

from agentic_rag.config import get_settings
from agentic_rag.models import (
    Document,
    QueryRequest,
    QueryResponse,
    QueryTrace,
    RefinementMode,
    RerankingMode,
    IntentType,
    RetrievalStrategy,
    SourceType,
    StructuredAnswer,
)
from agentic_rag.retrieval import IncidentRetriever, RegulationRetriever, NewsRetriever
from agentic_rag.refinement import ContextRefiner
from agentic_rag.reranking.reranker import get_reranker
from agentic_rag.generation import AnswerGenerator
from agentic_rag.tracing.mlflow_tracer import get_mlflow_tracer

from .intent_classifier import IntentClassifier
from .strategy_selector import StrategySelector, RetrievalPlan
from .context_evaluator import ContextEvaluator
from .constraint_validator import ConstraintValidator


class Orchestrator:
    """
    Main orchestrator for agentic RAG.

    Pipeline:
    1. Classify intent
    2. Select retrieval strategy
    3. Execute retrieval (possibly iterative)
    4. Refine context
    5. Evaluate sufficiency (iterate if needed)
    6. Generate structured answer
    """

    MAX_ITERATIONS = 3

    def __init__(self):
        # Components
        self.intent_classifier = IntentClassifier()
        self.strategy_selector = StrategySelector()
        self.context_evaluator = ContextEvaluator()
        self.context_refiner = ContextRefiner()
        self.constraint_validator = ConstraintValidator()
        self.generator = AnswerGenerator()

        # Retrievers
        self.retrievers = {
            SourceType.INCIDENTS: IncidentRetriever(),
            SourceType.REGULATIONS: RegulationRetriever(),
            SourceType.NEWS: NewsRetriever(),
        }

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Execute an agentic RAG query."""
        # Get MLflow tracer
        mlflow_tracer = get_mlflow_tracer()

        # Run query with MLflow tracking and tracing
        with mlflow_tracer.start_run(run_name=f"query-{request.question[:30]}"):
            with mlflow_tracer.start_trace(
                "agentic_rag_pipeline",
                inputs={
                    "question": request.question,
                    "refinement_mode": request.refinement_mode.value,
                    "top_k": request.top_k,
                }
            ) as root_span:
                return await self._execute_query(request, mlflow_tracer, root_span)

    async def _execute_query(self, request: QueryRequest, mlflow_tracer, root_span) -> QueryResponse:
        """Internal query execution with MLflow logging and tracing."""
        start_time = time.time()
        trace = QueryTrace()

        # Capture MLflow trace/run IDs
        try:
            import mlflow
            if mlflow.active_run():
                trace.mlflow_run_id = mlflow.active_run().info.run_id
            if root_span:
                trace.mlflow_trace_id = getattr(root_span, 'request_id', None)
        except Exception:
            pass

        # Log query parameters to MLflow
        mlflow_tracer.log_query_params(
            question=request.question,
            refinement_mode=request.refinement_mode.value,
            top_k=request.top_k,
            include_trace=request.include_trace,
        )

        # Step 0: Extract constraints from query (traced)
        step_start = time.time()
        with mlflow_tracer.trace_constraint_extraction(request.question) as span:
            constraints = self.constraint_validator.extract_constraints(request.question)
            constraint_dict = {
                "location": constraints.location,
                "date": constraints.date,
                "aircraft": constraints.aircraft_type,
                "registration": constraints.registration,
                "event_id": constraints.event_id,
                "regulation": constraints.regulation,
            }
            mlflow_tracer.set_span_outputs(span, {
                "has_constraints": constraints.has_constraints(),
                "constraints": constraint_dict,
            })
        step_duration = (time.time() - step_start) * 1000
        trace.steps.append({
            "name": "Constraint Extraction",
            "type": "tool",
            "duration_ms": step_duration,
            "status": "success",
            "details": {"has_constraints": constraints.has_constraints(), **{k: v for k, v in constraint_dict.items() if v}},
        })

        if constraints.has_constraints():
            trace.constraints = constraint_dict
            mlflow_tracer.log_constraints(trace.constraints)

        # Step 1: Classify intent (traced)
        step_start = time.time()
        with mlflow_tracer.trace_intent_classification(request.question) as span:
            intent_result = self.intent_classifier.classify(request.question)
            intent = intent_result.intent
            confidence = intent_result.confidence
            suggested_refinement = intent_result.refinement
            mlflow_tracer.set_span_outputs(span, {
                "intent": intent.value,
                "confidence": confidence,
                "suggested_refinement": suggested_refinement.value if suggested_refinement else None,
            })
        step_duration = (time.time() - step_start) * 1000
        trace.steps.append({
            "name": "Intent Classification",
            "type": "llm",
            "duration_ms": step_duration,
            "status": "success",
            "details": {"intent": intent.value, "confidence": confidence},
        })

        # Collect LLM call
        trace.llm_calls.append(intent_result.llm_call)

        trace.intent = intent
        trace.intent_confidence = confidence
        mlflow_tracer.log_intent(intent.value, confidence)

        # Use requested refinement mode or suggested
        refinement_mode = request.refinement_mode
        if refinement_mode == RefinementMode.NONE and suggested_refinement != RefinementMode.NONE:
            # If user didn't specify, use suggestion
            pass  # Keep user's choice

        # Step 2: Select strategy (traced)
        step_start = time.time()
        with mlflow_tracer.trace_strategy_selection(intent.value, request.question) as span:
            plan = self.strategy_selector.select(intent, request.question)
            mlflow_tracer.set_span_outputs(span, {
                "strategy": plan.strategy.value,
                "sources": [s.value for s in plan.sources],
                "source_order": [s.value for s in plan.source_order] if plan.source_order else None,
            })
        step_duration = (time.time() - step_start) * 1000
        trace.steps.append({
            "name": "Strategy Selection",
            "type": "chain",
            "duration_ms": step_duration,
            "status": "success",
            "details": {"strategy": plan.strategy.value, "sources": [s.value for s in plan.sources]},
        })

        trace.strategy = plan.strategy
        trace.sources_used = [s.value for s in plan.sources]
        mlflow_tracer.log_strategy(plan.strategy.value, [s.value for s in plan.sources])

        # Step 3: Execute retrieval (traced per iteration)
        all_documents: list[Document] = []
        iteration = 0

        while iteration < self.MAX_ITERATIONS:
            iteration += 1

            # Retrieve based on strategy (traced)
            with mlflow_tracer.trace_retrieval(
                plan.strategy.value,
                [s.value for s in plan.sources],
                iteration
            ) as span:
                retrieval_start = time.time()
                docs = await self._execute_retrieval(plan, request.top_k)
                retrieval_duration = (time.time() - retrieval_start) * 1000

                mlflow_tracer.set_span_outputs(span, {
                    "documents_retrieved": len(docs),
                    "duration_ms": retrieval_duration,
                    "document_sources": list(set(d.source.value for d in docs)) if docs else [],
                })

            trace.retrievals.append({
                "iteration": iteration,
                "strategy": plan.strategy.value,
                "sources": [s.value for s in plan.sources],
                "documents_retrieved": len(docs),
                "duration_ms": retrieval_duration,
            })
            trace.steps.append({
                "name": f"Retrieval (iteration {iteration})",
                "type": "retriever",
                "duration_ms": retrieval_duration,
                "status": "success",
                "details": {"documents": len(docs), "sources": [s.value for s in plan.sources]},
            })
            mlflow_tracer.log_retrieval_metrics(len(docs), retrieval_duration, iteration)

            all_documents.extend(docs)

            # Step 4: Quick sufficiency check
            if self.context_evaluator.quick_check(intent, all_documents):
                break

            # Step 5: Full sufficiency evaluation (for iterative strategy, traced)
            if plan.strategy == RetrievalStrategy.ITERATIVE:
                with mlflow_tracer.trace_context_evaluation(
                    request.question, len(all_documents)
                ) as span:
                    eval_result = self.context_evaluator.evaluate(
                        request.question, intent, all_documents
                    )
                    mlflow_tracer.set_span_outputs(span, {
                        "is_sufficient": eval_result.is_sufficient,
                        "missing_aspects": eval_result.missing_aspects,
                        "suggested_queries": eval_result.suggested_queries,
                    })

                trace.sufficiency_checks.append({
                    "iteration": iteration,
                    "is_sufficient": eval_result.is_sufficient,
                    "missing": eval_result.missing_aspects,
                })

                if eval_result.is_sufficient:
                    break

                # Update plan for next iteration
                if eval_result.suggested_queries:
                    for source in eval_result.suggested_sources:
                        if source in plan.queries_per_source:
                            plan.queries_per_source[source] = eval_result.suggested_queries[0]
            else:
                # Non-iterative strategies stop after one retrieval
                break

        # Step 6: Validate constraints (traced)
        step_start = time.time()
        with mlflow_tracer.trace_constraint_validation(constraint_dict) as span:
            validation_result = self.constraint_validator.validate(constraints, all_documents)
            mlflow_tracer.set_span_outputs(span, {
                "is_valid": validation_result.is_valid,
                "matched_count": len(validation_result.matched_documents),
                "unmatched_constraints": validation_result.unmatched_constraints,
                "explanation": validation_result.explanation,
            })
        step_duration = (time.time() - step_start) * 1000
        trace.steps.append({
            "name": "Constraint Validation",
            "type": "tool",
            "duration_ms": step_duration,
            "status": "success" if validation_result.is_valid else "warning",
            "details": {"valid": validation_result.is_valid, "matched": len(validation_result.matched_documents)},
        })

        trace.constraint_validation = {
            "has_constraints": constraints.has_constraints(),
            "is_valid": validation_result.is_valid,
            "unmatched": validation_result.unmatched_constraints,
            "matched_count": len(validation_result.matched_documents),
        }
        mlflow_tracer.log_constraint_validation(
            validation_result.is_valid,
            len(validation_result.matched_documents),
            validation_result.unmatched_constraints,
        )

        # If constraints aren't satisfied, return honest "no data" response
        if constraints.has_constraints() and not validation_result.is_valid:
            total_duration = (time.time() - start_time) * 1000
            trace.total_duration_ms = total_duration

            # Build list of what we DO have
            available_locations = set()
            for doc in all_documents:
                loc = doc.metadata.get("location", "")
                if loc:
                    available_locations.add(loc)

            no_match_answer = StructuredAnswer(
                summary=f"No matching data found. {validation_result.explanation}",
                key_findings=[],
                regulatory_context=[],
                causal_chain=[],
                caveats=[
                    f"The query specified constraints that don't match available data: {', '.join(validation_result.unmatched_constraints)}.",
                    f"Available incident locations in database: {', '.join(available_locations) if available_locations else 'None'}.",
                    "Please verify the location/date/aircraft details or try a broader query.",
                ],
            )

            # Set outputs on root span
            mlflow_tracer.set_span_outputs(root_span, {
                "answer_type": "no_data",
                "success": True,
                "total_duration_ms": total_duration,
            })

            # Log to MLflow
            mlflow_tracer.log_total_metrics(total_duration, success=True, answer_type="no_data")
            mlflow_tracer.log_trace_artifact(trace.model_dump() if hasattr(trace, 'model_dump') else trace.__dict__)
            mlflow_tracer.log_answer_artifact(no_match_answer.model_dump() if hasattr(no_match_answer, 'model_dump') else no_match_answer.__dict__)

            return QueryResponse(
                answer=no_match_answer,
                trace=trace if request.include_trace else None,
            )

        # Use matched documents if constraints were applied
        documents_for_refinement = (
            validation_result.matched_documents
            if constraints.has_constraints() and validation_result.matched_documents
            else all_documents
        )

        # Step 6.5: Rerank documents (traced)
        reranking_mode = request.reranking_mode
        reranker = get_reranker(reranking_mode)

        reranking_start = time.time()
        reranking_result = reranker.rerank(
            query=request.question,
            documents=documents_for_refinement,
            top_k=request.top_k  # Apply top_k after reranking
        )
        reranking_duration = (time.time() - reranking_start) * 1000

        # Update documents for refinement with reranked results
        documents_for_refinement = reranking_result.documents

        # Log reranking step
        trace.reranking = {
            "mode": reranking_mode.value,
            "model": reranking_result.model,
            "input_count": reranking_result.input_count,
            "output_count": reranking_result.output_count,
            "duration_ms": reranking_duration,
        }
        trace.steps.append({
            "name": "Reranking",
            "type": "model" if reranking_mode != RerankingMode.NONE else "tool",
            "duration_ms": reranking_duration,
            "status": "success",
            "details": {
                "mode": reranking_mode.value,
                "model": reranking_result.model,
                "input": reranking_result.input_count,
                "output": reranking_result.output_count
            },
        })

        # Step 7: Refine context (traced)
        with mlflow_tracer.trace_refinement(refinement_mode.value, len(documents_for_refinement)) as span:
            refinement_start = time.time()
            refinement_result = self.context_refiner.refine(
                documents_for_refinement, request.question, refinement_mode
            )
            refinement_duration = (time.time() - refinement_start) * 1000

            mlflow_tracer.set_span_outputs(span, {
                "output_document_count": refinement_result.output_count,
                "dropped_documents": refinement_result.dropped,
                "duration_ms": refinement_duration,
            })

        trace.refinement = {
            "mode": refinement_mode.value,
            "input_count": refinement_result.input_count,
            "output_count": refinement_result.output_count,
            "dropped": refinement_result.dropped,
            "duration_ms": refinement_duration,
        }
        trace.steps.append({
            "name": "Context Refinement",
            "type": "llm" if refinement_mode.value == "synthesize" else "tool",
            "duration_ms": refinement_duration,
            "status": "success",
            "details": {"mode": refinement_mode.value, "input": refinement_result.input_count, "output": refinement_result.output_count},
        })

        # Collect LLM call from refinement if present
        if refinement_result.llm_call:
            trace.llm_calls.append(refinement_result.llm_call)

        mlflow_tracer.log_refinement_metrics(
            refinement_mode.value,
            refinement_result.input_count,
            refinement_result.output_count,
            refinement_duration,
        )

        # Step 8: Generate answer (traced)
        with mlflow_tracer.trace_generation(
            request.question, intent.value, len(refinement_result.documents)
        ) as span:
            generation_start = time.time()
            generation_result = await self.generator.generate(
                question=request.question,
                intent=intent,
                documents=refinement_result.documents,
            )
            answer = generation_result.answer
            generation_duration = (time.time() - generation_start) * 1000

            mlflow_tracer.set_span_outputs(span, {
                "summary_length": len(answer.summary) if answer.summary else 0,
                "key_findings_count": len(answer.key_findings),
                "regulatory_context_count": len(answer.regulatory_context),
                "causal_chain_length": len(answer.causal_chain),
                "duration_ms": generation_duration,
            })

        mlflow_tracer.log_generation_metrics(generation_duration)

        # Collect LLM call from generation
        trace.llm_calls.append(generation_result.llm_call)

        trace.generation = {
            "duration_ms": generation_duration,
            "summary_length": len(answer.summary) if answer.summary else 0,
            "findings_count": len(answer.key_findings),
            "documents_used": len(refinement_result.documents),
        }
        trace.steps.append({
            "name": "Answer Generation",
            "type": "llm",
            "duration_ms": generation_duration,
            "status": "success",
            "details": {"findings": len(answer.key_findings), "summary_chars": len(answer.summary) if answer.summary else 0},
        })

        # Finalize trace
        total_duration = (time.time() - start_time) * 1000
        trace.total_duration_ms = total_duration

        # Set outputs on root span
        mlflow_tracer.set_span_outputs(root_span, {
            "answer_type": "structured",
            "success": True,
            "total_duration_ms": total_duration,
            "summary": answer.summary[:200] if answer.summary else None,
        })

        # Log final metrics and artifacts to MLflow
        mlflow_tracer.log_total_metrics(total_duration, success=True, answer_type="structured")
        mlflow_tracer.log_trace_artifact(trace.model_dump() if hasattr(trace, 'model_dump') else trace.__dict__)
        mlflow_tracer.log_answer_artifact(answer.model_dump() if hasattr(answer, 'model_dump') else answer.__dict__)

        return QueryResponse(
            answer=answer,
            trace=trace if request.include_trace else None,
        )

    async def _execute_retrieval(
        self,
        plan: RetrievalPlan,
        top_k: int,
    ) -> list[Document]:
        """Execute retrieval based on the plan."""
        documents = []

        if plan.strategy == RetrievalStrategy.DIRECT:
            # Single source
            source = plan.sources[0]
            query = plan.queries_per_source.get(source, "")
            result = self.retrievers[source].retrieve(query, top_k)
            documents.extend(result.documents)

        elif plan.strategy == RetrievalStrategy.SEQUENTIAL:
            # Sources in order
            for source in plan.source_order:
                query = plan.queries_per_source.get(source, "")
                result = self.retrievers[source].retrieve(query, top_k // len(plan.sources))
                documents.extend(result.documents)

        elif plan.strategy == RetrievalStrategy.PARALLEL:
            # All sources at once (could use asyncio.gather in production)
            for source in plan.sources:
                query = plan.queries_per_source.get(source, "")
                result = self.retrievers[source].retrieve(query, top_k // len(plan.sources))
                documents.extend(result.documents)

        elif plan.strategy == RetrievalStrategy.ITERATIVE:
            # Start with primary source
            source = plan.sources[0]
            query = plan.queries_per_source.get(source, "")
            result = self.retrievers[source].retrieve(query, top_k)
            documents.extend(result.documents)

        return documents
