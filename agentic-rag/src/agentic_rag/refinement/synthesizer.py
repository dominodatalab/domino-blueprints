# synthesizer.py
"""Synthesize multiple passages into a compressed summary."""

import time

from agentic_rag.config import get_settings
from agentic_rag.llm import get_llm_client
from agentic_rag.models import Document, RefinementResult, RefinementMode, SourceType, LLMCall
from agentic_rag.tracing.mlflow_tracer import get_mlflow_tracer


SYNTHESIZE_PROMPT = """You are synthesizing multiple passages into a single, condensed context for answering a user query.

Your task:
1. Preserve ALL unique facts from the passages
2. Remove redundant information
3. Maintain source attribution using [Source: X] markers
4. Organize information logically

Query: {query}

Passages:
{passages}

Create a synthesized context that contains all relevant information needed to answer the query. Use [Source: incidents/regulations/news] markers to attribute facts.

Output ONLY the synthesized text, no other commentary."""


class Synthesizer:
    """Synthesize passages into compressed summary."""

    def __init__(self):
        settings = get_settings()
        self.llm = get_llm_client()
        self.model = settings.refinement_model

    def synthesize(
        self,
        documents: list[Document],
        query: str,
    ) -> RefinementResult:
        """Synthesize documents into a single summary."""
        if len(documents) == 0:
            return RefinementResult(
                documents=[],
                mode=RefinementMode.SYNTHESIZE,
                input_count=0,
                output_count=0,
                dropped=[],
                llm_call=None,
            )

        if len(documents) == 1:
            return RefinementResult(
                documents=documents,
                mode=RefinementMode.SYNTHESIZE,
                input_count=1,
                output_count=1,
                dropped=[],
                llm_call=None,
            )

        passages_text = self._format_passages(documents)
        prompt = SYNTHESIZE_PROMPT.format(query=query, passages=passages_text)
        mlflow_tracer = get_mlflow_tracer()

        start_time = time.time()
        with mlflow_tracer.span("synthesis_llm", span_type="LLM") as span:
            mlflow_tracer.set_span_inputs(span, {
                "prompt": prompt,
                "model": self.model,
                "input_document_count": len(documents),
            })

            synthesized_text = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0,
            )
            duration_ms = (time.time() - start_time) * 1000

            mlflow_tracer.set_span_outputs(span, {
                "response": synthesized_text,
                "duration_ms": duration_ms,
            })

        llm_call = LLMCall(
            step="refinement_synthesize",
            model=self.model,
            prompt=prompt,
            response=synthesized_text,
            duration_ms=duration_ms,
        )

        # Create a single synthesized document
        synthesized_doc = Document(
            id="synthesized",
            text=synthesized_text,
            source=SourceType.INCIDENTS,  # Mark as mixed
            metadata={
                "synthesized": True,
                "source_count": len(documents),
                "source_ids": [doc.id for doc in documents],
            },
            score=1.0,
        )

        return RefinementResult(
            documents=[synthesized_doc],
            mode=RefinementMode.SYNTHESIZE,
            input_count=len(documents),
            output_count=1,
            dropped=[{"id": doc.id, "reason": "synthesized into summary"} for doc in documents],
            llm_call=llm_call,
        )

    def _format_passages(self, documents: list[Document]) -> str:
        """Format documents as numbered passages with source info."""
        parts = []
        for i, doc in enumerate(documents):
            source = doc.source.value
            parts.append(f"--- Passage {i+1} [Source: {source}] ---")
            parts.append(doc.text)
            parts.append("")
        return "\n".join(parts)
