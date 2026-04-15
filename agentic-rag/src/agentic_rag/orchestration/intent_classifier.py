# intent_classifier.py
"""Classify query intent to determine retrieval strategy."""

import json
import time
from dataclasses import dataclass

from agentic_rag.config import get_settings
from agentic_rag.llm import get_llm_client
from agentic_rag.models import IntentType, RefinementMode, LLMCall
from agentic_rag.tracing.mlflow_tracer import get_mlflow_tracer


@dataclass
class IntentClassificationResult:
    """Result from intent classification including raw LLM data."""
    intent: IntentType
    confidence: str
    refinement: RefinementMode
    llm_call: LLMCall


INTENT_PROMPT = """Classify the user's question about aviation safety into one of these intent types:

- CAUSAL: Questions about what caused something (accidents, failures, incidents)
- COMPLIANCE: Questions about legal/regulatory compliance (was X allowed, was Y certified)
- FACTUAL: Questions about what happened (timeline, conditions, facts)
- COMPARATIVE: Questions comparing multiple incidents or situations
- REGULATORY: Questions about what regulations say (not checking compliance, just asking about rules)
- MULTI_SOURCE: Complex questions requiring cross-referencing multiple sources

Question: {question}

Output JSON with:
- "intent": one of [causal, compliance, factual, comparative, regulatory, multi_source]
- "confidence": high, medium, or low
- "reasoning": one sentence explanation
- "suggested_refinement": one of [none, dedup, synthesize] - which refinement mode best suits this question

Example:
{{"intent": "compliance", "confidence": "high", "reasoning": "User is asking whether the pilot met legal requirements", "suggested_refinement": "dedup"}}"""


class IntentClassifier:
    """Classify user query intent."""

    def __init__(self):
        settings = get_settings()
        self.llm = get_llm_client()
        self.model = settings.refinement_model

    def classify(self, question: str) -> IntentClassificationResult:
        """
        Classify the intent of a question.

        Returns:
            IntentClassificationResult with intent, confidence, refinement, and raw LLM data
        """
        prompt = INTENT_PROMPT.format(question=question)
        mlflow_tracer = get_mlflow_tracer()

        start_time = time.time()
        with mlflow_tracer.span("intent_classification_llm", span_type="LLM") as span:
            mlflow_tracer.set_span_inputs(span, {
                "prompt": prompt,
                "model": self.model,
                "temperature": 0,
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
            step="intent_classification",
            model=self.model,
            prompt=prompt,
            response=response,
            duration_ms=duration_ms,
        )

        try:
            result = json.loads(response)
            intent = IntentType(result.get("intent", "factual"))
            confidence = result.get("confidence", "medium")
            refinement = RefinementMode(result.get("suggested_refinement", "dedup"))
            return IntentClassificationResult(
                intent=intent,
                confidence=confidence,
                refinement=refinement,
                llm_call=llm_call,
            )
        except (json.JSONDecodeError, ValueError):
            # Default to factual with dedup
            return IntentClassificationResult(
                intent=IntentType.FACTUAL,
                confidence="low",
                refinement=RefinementMode.DEDUP,
                llm_call=llm_call,
            )

    def get_default_refinement(self, intent: IntentType) -> RefinementMode:
        """Get default refinement mode for an intent type."""
        mapping = {
            IntentType.CAUSAL: RefinementMode.DEDUP,
            IntentType.COMPLIANCE: RefinementMode.DEDUP,
            IntentType.FACTUAL: RefinementMode.SYNTHESIZE,
            IntentType.COMPARATIVE: RefinementMode.DEDUP,
            IntentType.REGULATORY: RefinementMode.DEDUP,
            IntentType.MULTI_SOURCE: RefinementMode.SYNTHESIZE,
        }
        return mapping.get(intent, RefinementMode.DEDUP)
