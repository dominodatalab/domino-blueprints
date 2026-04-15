# filter.py
"""Filter refinement mode - scores relevance but keeps original text.

Unlike dedup/synthesize which rewrite or merge documents, filter mode:
1. Scores each document's relevance to the query (1-10)
2. Keeps top documents above a threshold
3. Preserves original text completely

This is the recommended production approach because:
- No information loss from rewriting
- Original text preserved for accurate citation
- Relevance scoring without semantic merging
- Lets the reasoning model see raw evidence
"""

import json
import logging
import os
import time

from ..llm import get_llm_client
from ..models import Document, RefinementResult, RefinementMode, LLMCall

logger = logging.getLogger(__name__)


class RelevanceFilter:
    """Filter documents by relevance score without rewriting.

    Uses LLM to score each document's relevance to the query,
    then keeps top scoring documents with original text intact.
    """

    def __init__(
        self,
        model: str | None = None,
        relevance_threshold: float = 5.0,
        min_documents: int = 2
    ):
        """Initialize the relevance filter.

        Args:
            model: LLM model to use for scoring
            relevance_threshold: Minimum score (1-10) to keep a document
            min_documents: Minimum number of documents to keep regardless of threshold
        """
        self.model = model or os.environ.get("REFINEMENT_MODEL", "claude-3-haiku-20240307")
        self.relevance_threshold = relevance_threshold
        self.min_documents = min_documents
        self._client = None

    @property
    def client(self):
        """Lazy load LLM client."""
        if self._client is None:
            self._client = get_llm_client()
        return self._client

    def filter(self, documents: list[Document], query: str) -> RefinementResult:
        """Filter documents by relevance score.

        Args:
            documents: Documents to filter
            query: The query to score relevance against

        Returns:
            RefinementResult with filtered documents (original text preserved)
        """
        if len(documents) <= self.min_documents:
            return RefinementResult(
                documents=documents,
                mode=RefinementMode.FILTER,
                input_count=len(documents),
                output_count=len(documents),
                dropped=[]
            )

        start_time = time.time()

        # Build scoring prompt
        prompt = self._build_scoring_prompt(documents, query)

        # Get relevance scores from LLM
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat(
                messages=messages,
                model=self.model,
                max_tokens=1000,
                temperature=0.0
            )

            scores = self._parse_scores(response, len(documents))

        except Exception as e:
            logger.warning(f"Filter scoring failed: {e}. Passing documents through.")
            return RefinementResult(
                documents=documents,
                mode=RefinementMode.FILTER,
                input_count=len(documents),
                output_count=len(documents),
                dropped=[]
            )

        # Score documents and sort by relevance
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Filter by threshold, but keep minimum documents
        kept_docs = []
        dropped = []

        for i, (doc, score) in enumerate(scored_docs):
            if score >= self.relevance_threshold or len(kept_docs) < self.min_documents:
                # Update document metadata with relevance score
                kept_doc = Document(
                    id=doc.id,
                    text=doc.text,  # Original text preserved!
                    source=doc.source,
                    metadata={
                        **doc.metadata,
                        "relevance_score": score,
                        "filter_rank": len(kept_docs) + 1
                    },
                    score=doc.score
                )
                kept_docs.append(kept_doc)
            else:
                dropped.append({
                    "id": doc.id,
                    "reason": f"Below relevance threshold (score: {score:.1f})"
                })

        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Filter refinement: {len(documents)} -> {len(kept_docs)} docs "
            f"(threshold: {self.relevance_threshold}) in {duration_ms:.1f}ms"
        )

        # Create LLM call record for tracing
        llm_call = LLMCall(
            step="refinement_filter",
            model=self.model,
            prompt=prompt,
            response=response,
            duration_ms=duration_ms
        )

        return RefinementResult(
            documents=kept_docs,
            mode=RefinementMode.FILTER,
            input_count=len(documents),
            output_count=len(kept_docs),
            dropped=dropped,
            llm_call=llm_call
        )

    def _build_scoring_prompt(self, documents: list[Document], query: str) -> str:
        """Build the relevance scoring prompt."""
        doc_texts = []
        for i, doc in enumerate(documents):
            doc_texts.append(f"[Document {i+1}]\n{doc.text[:1500]}...")

        docs_section = "\n\n".join(doc_texts)

        return f"""Score each document's relevance to the query on a scale of 1-10.

Query: {query}

Documents:
{docs_section}

Instructions:
- Score 1-3: Not relevant or only tangentially related
- Score 4-6: Somewhat relevant, contains related information
- Score 7-10: Highly relevant, directly answers or informs the query

Return ONLY a JSON array of scores in order, like: [8, 3, 7, 5, ...]
Do not include any other text or explanation.
"""

    def _parse_scores(self, response: str, expected_count: int) -> list[float]:
        """Parse relevance scores from LLM response."""
        # Clean up response
        response = response.strip()

        # Try to find JSON array in response
        try:
            # Handle case where response might have extra text
            if "[" in response and "]" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                json_str = response[start:end]
                scores = json.loads(json_str)
            else:
                scores = json.loads(response)

            # Validate and convert
            if isinstance(scores, list):
                scores = [float(s) for s in scores]

                # Pad or truncate to expected count
                if len(scores) < expected_count:
                    # Default to medium relevance for missing scores
                    scores.extend([5.0] * (expected_count - len(scores)))
                elif len(scores) > expected_count:
                    scores = scores[:expected_count]

                return scores

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse scores: {e}")

        # Default: all documents get medium score
        return [5.0] * expected_count
