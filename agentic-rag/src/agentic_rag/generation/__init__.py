# generation package
"""Answer generation from retrieved context."""

from .generator import AnswerGenerator
from .prompts import GENERATION_PROMPT

__all__ = ["AnswerGenerator", "GENERATION_PROMPT"]
