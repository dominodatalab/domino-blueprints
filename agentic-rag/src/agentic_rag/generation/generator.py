# generator.py
"""Answer generation from retrieved context."""

import json
import time
from dataclasses import dataclass

from agentic_rag.config import get_settings
from agentic_rag.llm import get_llm_client
from agentic_rag.models import (
    Document,
    IntentType,
    StructuredAnswer,
    Finding,
    RegulatoryContext,
    LLMCall,
)
from agentic_rag.tracing.mlflow_tracer import get_mlflow_tracer
from .prompts import GENERATION_PROMPT, TRADITIONAL_RAG_PROMPT


@dataclass
class GenerationResult:
    """Result from answer generation including raw LLM data."""
    answer: StructuredAnswer
    llm_call: LLMCall


@dataclass
class TraditionalGenerationResult:
    """Result from traditional RAG generation including raw LLM data."""
    answer: str
    llm_call: LLMCall


class AnswerGenerator:
    """Generate structured answers from context."""

    def __init__(self):
        settings = get_settings()
        self.llm = get_llm_client()
        self.model = settings.generation_model

    async def generate(
        self,
        question: str,
        intent: IntentType,
        documents: list[Document],
    ) -> GenerationResult:
        """Generate a structured answer from documents."""
        mlflow_tracer = get_mlflow_tracer()

        if not documents:
            return GenerationResult(
                answer=StructuredAnswer(
                    summary="Unable to answer - no relevant documents were found.",
                    caveats=["No documents were retrieved for this query."],
                ),
                llm_call=LLMCall(
                    step="generation",
                    model=self.model,
                    prompt="(skipped - no documents)",
                    response="(skipped - no documents)",
                ),
            )

        context = self._format_context(documents)
        prompt = GENERATION_PROMPT.format(
            question=question,
            intent=intent.value,
            context=context,
        )

        start_time = time.time()
        with mlflow_tracer.span("generation_llm", span_type="LLM") as span:
            mlflow_tracer.set_span_inputs(span, {
                "prompt": prompt,
                "model": self.model,
                "intent": intent.value,
                "document_count": len(documents),
            })

            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0,
                json_output=True,
            )
            duration_ms = (time.time() - start_time) * 1000

            mlflow_tracer.set_span_outputs(span, {
                "response": response,
                "duration_ms": duration_ms,
            })

        llm_call = LLMCall(
            step="generation",
            model=self.model,
            prompt=prompt,
            response=response,
            duration_ms=duration_ms,
        )

        try:
            result = json.loads(response)

            # Parse findings
            findings = []
            for f in result.get("key_findings", []):
                findings.append(Finding(
                    finding=f.get("finding", ""),
                    source=f.get("source", ""),
                    confidence=f.get("confidence", "medium"),
                ))

            # Parse regulatory context
            regulatory = []
            for r in result.get("regulatory_context", []):
                regulatory.append(RegulatoryContext(
                    regulation=r.get("regulation", ""),
                    relevance=r.get("relevance", ""),
                    compliance_status=r.get("compliance_status"),
                ))

            return GenerationResult(
                answer=StructuredAnswer(
                    summary=result.get("summary", ""),
                    key_findings=findings,
                    regulatory_context=regulatory,
                    causal_chain=result.get("causal_chain", []),
                    caveats=result.get("caveats", []),
                ),
                llm_call=llm_call,
            )

        except json.JSONDecodeError:
            # Return raw response as summary
            return GenerationResult(
                answer=StructuredAnswer(
                    summary=response,
                    caveats=["Response could not be parsed into structured format."],
                ),
                llm_call=llm_call,
            )

    async def generate_traditional(
        self,
        question: str,
        documents: list[Document],
    ) -> TraditionalGenerationResult:
        """Generate a simple answer for traditional RAG comparison."""
        mlflow_tracer = get_mlflow_tracer()

        if not documents:
            return TraditionalGenerationResult(
                answer="Unable to answer - no relevant documents were found.",
                llm_call=LLMCall(
                    step="generation_traditional",
                    model=self.model,
                    prompt="(skipped - no documents)",
                    response="(skipped - no documents)",
                ),
            )

        context = self._format_context(documents)
        prompt = TRADITIONAL_RAG_PROMPT.format(
            question=question,
            context=context,
        )

        start_time = time.time()
        with mlflow_tracer.span("generation_traditional_llm", span_type="LLM") as span:
            mlflow_tracer.set_span_inputs(span, {
                "prompt": prompt,
                "model": self.model,
                "document_count": len(documents),
            })

            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0,
            )
            duration_ms = (time.time() - start_time) * 1000

            mlflow_tracer.set_span_outputs(span, {
                "response": response,
                "duration_ms": duration_ms,
            })

        return TraditionalGenerationResult(
            answer=response,
            llm_call=LLMCall(
                step="generation_traditional",
                model=self.model,
                prompt=prompt,
                response=response,
                duration_ms=duration_ms,
            ),
        )

    def _format_context(self, documents: list[Document]) -> str:
        """Format documents as context for generation."""
        parts = []
        for i, doc in enumerate(documents):
            source = doc.source.value
            header = doc.metadata.get("header_l3", doc.id)
            parts.append(f"--- Document {i+1} [{source}]: {header} ---")
            parts.append(doc.text)
            parts.append("")
        return "\n".join(parts)
