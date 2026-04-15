# pruner.py
"""Remove marginally relevant passages."""

import json
import time

from agentic_rag.config import get_settings
from agentic_rag.llm import get_llm_client
from agentic_rag.models import Document, RefinementResult, RefinementMode, LLMCall
from agentic_rag.tracing.mlflow_tracer import get_mlflow_tracer


PRUNE_PROMPT = """You are analyzing passages retrieved for a user query. Your task is to identify and remove MARGINALLY RELEVANT passages.

A passage is MARGINALLY RELEVANT if it:
- Discusses a tangentially related topic
- Contains information that doesn't help answer the query
- Is too general to be useful for the specific question

Query: {query}

Passages:
{passages}

For each passage, decide: KEEP (directly relevant) or DROP (marginally relevant).

Output ONLY valid JSON:
{{
    "keep": [
        {{"id": "p0", "relevance": "Directly answers the question about..."}}
    ],
    "drop": [
        {{"id": "p2", "reason": "Discusses unrelated topic..."}}
    ]
}}"""


class Pruner:
    """Remove marginally relevant passages."""

    def __init__(self):
        settings = get_settings()
        self.llm = get_llm_client()
        self.model = settings.refinement_model

    def prune(
        self,
        documents: list[Document],
        query: str,
        min_keep: int = 2,
    ) -> RefinementResult:
        """Remove marginally relevant documents."""
        if len(documents) <= min_keep:
            return RefinementResult(
                documents=documents,
                mode=RefinementMode.DEDUP,
                input_count=len(documents),
                output_count=len(documents),
                dropped=[],
                llm_call=None,
            )

        passages_text = self._format_passages(documents)
        prompt = PRUNE_PROMPT.format(query=query, passages=passages_text)
        mlflow_tracer = get_mlflow_tracer()

        start_time = time.time()
        with mlflow_tracer.span("pruning_llm", span_type="LLM") as span:
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
            step="refinement_prune",
            model=self.model,
            prompt=prompt,
            response=response,
            duration_ms=duration_ms,
        )

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            return RefinementResult(
                documents=documents,
                mode=RefinementMode.DEDUP,
                input_count=len(documents),
                output_count=len(documents),
                dropped=[],
                llm_call=llm_call,
            )

        keep_ids = {item["id"] for item in result.get("keep", [])}
        dropped = result.get("drop", [])

        # Ensure we keep at least min_keep documents
        if len(keep_ids) < min_keep:
            # Add back highest-scored documents
            for i, doc in enumerate(documents):
                if len(keep_ids) >= min_keep:
                    break
                keep_ids.add(f"p{i}")

        kept_documents = []
        for i, doc in enumerate(documents):
            if f"p{i}" in keep_ids:
                kept_documents.append(doc)

        return RefinementResult(
            documents=kept_documents,
            mode=RefinementMode.DEDUP,
            input_count=len(documents),
            output_count=len(kept_documents),
            dropped=[{"id": d.get("id"), "reason": d.get("reason", "marginally relevant")} for d in dropped],
            llm_call=llm_call,
        )

    def _format_passages(self, documents: list[Document]) -> str:
        """Format documents as numbered passages."""
        parts = []
        for i, doc in enumerate(documents):
            source_info = f"[{doc.source.value}]"
            parts.append(f"--- Passage p{i} {source_info} ---")
            text = doc.text[:800] + "..." if len(doc.text) > 800 else doc.text
            parts.append(text)
            parts.append("")
        return "\n".join(parts)
