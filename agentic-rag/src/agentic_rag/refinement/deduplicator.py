# deduplicator.py
"""Remove redundant passages that cover the same information."""

import json
import time

from agentic_rag.config import get_settings
from agentic_rag.llm import get_llm_client
from agentic_rag.models import Document, RefinementResult, RefinementMode, LLMCall
from agentic_rag.tracing.mlflow_tracer import get_mlflow_tracer


DEDUP_PROMPT = """You are analyzing passages retrieved for a user query. Your task is to identify and remove REDUNDANT passages.

A passage is REDUNDANT if it contains substantially the same information as another passage. Keep the passage with more detail or from a more authoritative source.

Query: {query}

Passages:
{passages}

Analyze each passage and return a JSON object with:
- "keep": list of passage IDs to KEEP, each with a brief reason
- "drop": list of passage IDs to DROP, each with the ID of the passage it duplicates

Output ONLY valid JSON, no other text.

Example output:
{{
    "keep": [
        {{"id": "p1", "reason": "Primary NTSB source with full details"}},
        {{"id": "p3", "reason": "Contains unique regulatory information"}}
    ],
    "drop": [
        {{"id": "p2", "duplicates": "p1", "reason": "Same accident, less detail"}}
    ]
}}"""


class Deduplicator:
    """Remove redundant passages from retrieved context."""

    def __init__(self):
        settings = get_settings()
        self.llm = get_llm_client()
        self.model = settings.refinement_model

    def deduplicate(
        self,
        documents: list[Document],
        query: str,
    ) -> RefinementResult:
        """Remove redundant documents."""
        if len(documents) <= 2:
            # Not worth deduplicating small sets
            return RefinementResult(
                documents=documents,
                mode=RefinementMode.DEDUP,
                input_count=len(documents),
                output_count=len(documents),
                dropped=[],
                llm_call=None,
            )

        # Format passages for the prompt
        passages_text = self._format_passages(documents)
        prompt = DEDUP_PROMPT.format(query=query, passages=passages_text)
        mlflow_tracer = get_mlflow_tracer()

        # Call LLM for deduplication analysis
        start_time = time.time()
        with mlflow_tracer.span("deduplication_llm", span_type="LLM") as span:
            mlflow_tracer.set_span_inputs(span, {
                "prompt": prompt,
                "model": self.model,
                "input_document_count": len(documents),
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
            step="refinement_dedup",
            model=self.model,
            prompt=prompt,
            response=response,
            duration_ms=duration_ms,
        )

        # Parse response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # If parsing fails, return all documents
            return RefinementResult(
                documents=documents,
                mode=RefinementMode.DEDUP,
                input_count=len(documents),
                output_count=len(documents),
                dropped=[],
                llm_call=llm_call,
            )

        # Filter documents based on LLM decision
        keep_ids = {item["id"] for item in result.get("keep", [])}
        dropped = result.get("drop", [])

        # If LLM didn't specify, keep all
        if not keep_ids:
            keep_ids = {f"p{i}" for i in range(len(documents))}

        # Map back to documents
        kept_documents = []
        for i, doc in enumerate(documents):
            if f"p{i}" in keep_ids:
                kept_documents.append(doc)

        return RefinementResult(
            documents=kept_documents,
            mode=RefinementMode.DEDUP,
            input_count=len(documents),
            output_count=len(kept_documents),
            dropped=[{"id": d.get("id"), "reason": d.get("reason", "redundant")} for d in dropped],
            llm_call=llm_call,
        )

    def _format_passages(self, documents: list[Document]) -> str:
        """Format documents as numbered passages."""
        parts = []
        for i, doc in enumerate(documents):
            source_info = f"[{doc.source.value}]"
            if doc.metadata.get("header_l3"):
                source_info += f" {doc.metadata['header_l3']}"

            parts.append(f"--- Passage p{i} {source_info} ---")
            # Truncate long passages
            text = doc.text[:1000] + "..." if len(doc.text) > 1000 else doc.text
            parts.append(text)
            parts.append("")

        return "\n".join(parts)
