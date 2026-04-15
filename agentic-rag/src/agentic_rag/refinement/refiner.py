# refiner.py
"""Main context refiner that combines dedup, prune, filter, and synthesize."""

from agentic_rag.models import Document, RefinementResult, RefinementMode
from .deduplicator import Deduplicator
from .pruner import Pruner
from .synthesizer import Synthesizer
from .filter import RelevanceFilter


class ContextRefiner:
    """
    Main interface for context refinement.

    Supports four modes:
    - NONE: Pass through without refinement
    - DEDUP: Deduplicate + prune, preserve original text (may lose nuance)
    - FILTER: Score relevance, keep top docs with original text (recommended)
    - SYNTHESIZE: Compress into summary (lossy)
    """

    def __init__(self):
        self.deduplicator = Deduplicator()
        self.pruner = Pruner()
        self.synthesizer = Synthesizer()
        self.filter = RelevanceFilter()

    def refine(
        self,
        documents: list[Document],
        query: str,
        mode: RefinementMode,
    ) -> RefinementResult:
        """Refine documents according to the specified mode."""
        if mode == RefinementMode.NONE:
            return RefinementResult(
                documents=documents,
                mode=mode,
                input_count=len(documents),
                output_count=len(documents),
                dropped=[],
            )

        elif mode == RefinementMode.DEDUP:
            # First deduplicate, then prune
            dedup_result = self.deduplicator.deduplicate(documents, query)
            prune_result = self.pruner.prune(dedup_result.documents, query)

            # Combine dropped lists
            all_dropped = dedup_result.dropped + prune_result.dropped

            return RefinementResult(
                documents=prune_result.documents,
                mode=mode,
                input_count=len(documents),
                output_count=len(prune_result.documents),
                dropped=all_dropped,
            )

        elif mode == RefinementMode.SYNTHESIZE:
            # Deduplicate first, then synthesize
            dedup_result = self.deduplicator.deduplicate(documents, query)
            synth_result = self.synthesizer.synthesize(dedup_result.documents, query)

            return RefinementResult(
                documents=synth_result.documents,
                mode=mode,
                input_count=len(documents),
                output_count=len(synth_result.documents),
                dropped=dedup_result.dropped + synth_result.dropped,
            )

        elif mode == RefinementMode.FILTER:
            # Filter by relevance score, keep original text
            # This is the recommended production approach
            return self.filter.filter(documents, query)

        else:
            raise ValueError(f"Unknown refinement mode: {mode}")
