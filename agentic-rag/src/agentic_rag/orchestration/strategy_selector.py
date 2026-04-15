# strategy_selector.py
"""Select retrieval strategy based on intent."""

from dataclasses import dataclass

from agentic_rag.models import IntentType, RetrievalStrategy, SourceType


@dataclass
class RetrievalPlan:
    """Plan for how to execute retrieval."""
    strategy: RetrievalStrategy
    sources: list[SourceType]
    source_order: list[SourceType]  # For sequential strategy
    queries_per_source: dict[SourceType, str]  # Customized queries


class StrategySelector:
    """Select retrieval strategy based on intent."""

    def select(self, intent: IntentType, question: str) -> RetrievalPlan:
        """
        Select a retrieval strategy and plan based on intent.

        Returns a RetrievalPlan with:
        - strategy: how to execute (parallel, sequential, etc.)
        - sources: which sources to query
        - source_order: order for sequential strategy
        - queries_per_source: optional query customization
        """
        if intent == IntentType.CAUSAL:
            # Causal: Start with incidents, then regulations to understand rules
            return RetrievalPlan(
                strategy=RetrievalStrategy.SEQUENTIAL,
                sources=[SourceType.INCIDENTS, SourceType.REGULATIONS, SourceType.NEWS],
                source_order=[SourceType.INCIDENTS, SourceType.REGULATIONS, SourceType.NEWS],
                queries_per_source={
                    SourceType.INCIDENTS: question,
                    SourceType.REGULATIONS: self._extract_regulatory_query(question),
                    SourceType.NEWS: question,
                },
            )

        elif intent == IntentType.COMPLIANCE:
            # Compliance: Regulations first, then incidents to check against
            return RetrievalPlan(
                strategy=RetrievalStrategy.SEQUENTIAL,
                sources=[SourceType.REGULATIONS, SourceType.INCIDENTS],
                source_order=[SourceType.REGULATIONS, SourceType.INCIDENTS],
                queries_per_source={
                    SourceType.REGULATIONS: self._extract_regulatory_query(question),
                    SourceType.INCIDENTS: question,
                },
            )

        elif intent == IntentType.REGULATORY:
            # Regulatory: Only regulations
            return RetrievalPlan(
                strategy=RetrievalStrategy.DIRECT,
                sources=[SourceType.REGULATIONS],
                source_order=[SourceType.REGULATIONS],
                queries_per_source={
                    SourceType.REGULATIONS: question,
                },
            )

        elif intent == IntentType.FACTUAL:
            # Factual: Incidents primary, news for context
            return RetrievalPlan(
                strategy=RetrievalStrategy.PARALLEL,
                sources=[SourceType.INCIDENTS, SourceType.NEWS],
                source_order=[SourceType.INCIDENTS, SourceType.NEWS],
                queries_per_source={
                    SourceType.INCIDENTS: question,
                    SourceType.NEWS: question,
                },
            )

        elif intent == IntentType.COMPARATIVE:
            # Comparative: Multiple incident searches
            return RetrievalPlan(
                strategy=RetrievalStrategy.ITERATIVE,
                sources=[SourceType.INCIDENTS],
                source_order=[SourceType.INCIDENTS],
                queries_per_source={
                    SourceType.INCIDENTS: question,
                },
            )

        elif intent == IntentType.MULTI_SOURCE:
            # Multi-source: All sources in parallel
            return RetrievalPlan(
                strategy=RetrievalStrategy.PARALLEL,
                sources=[SourceType.INCIDENTS, SourceType.REGULATIONS, SourceType.NEWS],
                source_order=[SourceType.INCIDENTS, SourceType.REGULATIONS, SourceType.NEWS],
                queries_per_source={
                    SourceType.INCIDENTS: question,
                    SourceType.REGULATIONS: self._extract_regulatory_query(question),
                    SourceType.NEWS: question,
                },
            )

        else:
            # Default: parallel across all
            return RetrievalPlan(
                strategy=RetrievalStrategy.PARALLEL,
                sources=[SourceType.INCIDENTS, SourceType.REGULATIONS, SourceType.NEWS],
                source_order=[SourceType.INCIDENTS, SourceType.REGULATIONS, SourceType.NEWS],
                queries_per_source={
                    SourceType.INCIDENTS: question,
                    SourceType.REGULATIONS: question,
                    SourceType.NEWS: question,
                },
            )

    def _extract_regulatory_query(self, question: str) -> str:
        """
        Extract/transform question for regulatory search.

        E.g., "Was the pilot certified?" -> "pilot certification requirements"
        """
        # Simple keyword extraction - could be LLM-enhanced
        keywords = []

        regulatory_terms = [
            ("VFR", "VFR weather minimums visual flight rules"),
            ("IFR", "IFR instrument flight rules requirements"),
            ("certified", "pilot certification requirements"),
            ("rating", "pilot rating requirements"),
            ("weather", "weather minimums requirements"),
            ("night", "night flying requirements"),
            ("instrument", "instrument rating requirements currency"),
            ("preflight", "preflight action requirements"),
        ]

        question_lower = question.lower()
        for term, expansion in regulatory_terms:
            if term.lower() in question_lower:
                keywords.append(expansion)

        if keywords:
            return " ".join(keywords)

        # Default: return original question
        return question
