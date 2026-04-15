# context_evaluator.py
"""Evaluate whether retrieved context is sufficient to answer the question."""

import json

from agentic_rag.config import get_settings
from agentic_rag.llm import get_llm_client
from agentic_rag.models import Document, IntentType, SourceType


EVALUATE_PROMPT = """You are evaluating whether the retrieved context is SUFFICIENT to answer the user's question.

Question: {question}
Intent: {intent}

Retrieved Context:
{context}

Evaluate:
1. Does the context contain the necessary information to answer the question?
2. What specific information is MISSING (if any)?
3. Which sources would help fill the gaps?

Output JSON:
{{
    "is_sufficient": true/false,
    "confidence": "high"/"medium"/"low",
    "missing_aspects": ["list of missing information"],
    "suggested_sources": ["incidents", "regulations", "news"],
    "suggested_queries": ["additional queries to run"],
    "reasoning": "explanation"
}}"""


class EvaluationResult:
    """Result of context sufficiency evaluation."""

    def __init__(
        self,
        is_sufficient: bool,
        confidence: str,
        missing_aspects: list[str],
        suggested_sources: list[SourceType],
        suggested_queries: list[str],
        reasoning: str,
    ):
        self.is_sufficient = is_sufficient
        self.confidence = confidence
        self.missing_aspects = missing_aspects
        self.suggested_sources = suggested_sources
        self.suggested_queries = suggested_queries
        self.reasoning = reasoning


class ContextEvaluator:
    """Evaluate context sufficiency."""

    def __init__(self):
        settings = get_settings()
        self.llm = get_llm_client()
        self.model = settings.refinement_model

    def evaluate(
        self,
        question: str,
        intent: IntentType,
        documents: list[Document],
    ) -> EvaluationResult:
        """Evaluate whether context is sufficient."""
        if not documents:
            return EvaluationResult(
                is_sufficient=False,
                confidence="high",
                missing_aspects=["No documents retrieved"],
                suggested_sources=[SourceType.INCIDENTS, SourceType.REGULATIONS],
                suggested_queries=[question],
                reasoning="No context available",
            )

        context_text = self._format_context(documents)

        response = self.llm.chat(
            messages=[
                {
                    "role": "user",
                    "content": EVALUATE_PROMPT.format(
                        question=question,
                        intent=intent.value,
                        context=context_text,
                    ),
                }
            ],
            model=self.model,
            temperature=0,
            json_output=True,
        )

        try:
            result = json.loads(response)

            suggested_sources = []
            for s in result.get("suggested_sources", []):
                try:
                    suggested_sources.append(SourceType(s))
                except ValueError:
                    pass

            return EvaluationResult(
                is_sufficient=result.get("is_sufficient", True),
                confidence=result.get("confidence", "medium"),
                missing_aspects=result.get("missing_aspects", []),
                suggested_sources=suggested_sources,
                suggested_queries=result.get("suggested_queries", []),
                reasoning=result.get("reasoning", ""),
            )

        except json.JSONDecodeError:
            # Default to sufficient if parsing fails
            return EvaluationResult(
                is_sufficient=True,
                confidence="low",
                missing_aspects=[],
                suggested_sources=[],
                suggested_queries=[],
                reasoning="Evaluation failed, assuming sufficient",
            )

    def _format_context(self, documents: list[Document]) -> str:
        """Format documents as context."""
        parts = []
        for doc in documents:
            source = doc.source.value
            parts.append(f"[{source}] {doc.text[:500]}...")
            parts.append("")
        return "\n".join(parts)

    def quick_check(self, intent: IntentType, documents: list[Document]) -> bool:
        """
        Quick heuristic check for sufficiency without LLM call.

        Returns True if basic requirements are likely met.
        """
        source_types = {doc.source for doc in documents}

        if intent == IntentType.CAUSAL:
            # Need at least incident data
            return SourceType.INCIDENTS in source_types

        elif intent == IntentType.COMPLIANCE:
            # Need both regulations and incident data
            return (
                SourceType.REGULATIONS in source_types
                and SourceType.INCIDENTS in source_types
            )

        elif intent == IntentType.REGULATORY:
            # Only need regulations
            return SourceType.REGULATIONS in source_types

        elif intent == IntentType.FACTUAL:
            # Need incident data
            return SourceType.INCIDENTS in source_types

        else:
            # For complex intents, always do full evaluation
            return False
