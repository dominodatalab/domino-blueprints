# llm.py
"""LLM abstraction layer supporting OpenAI and Anthropic."""

import json
from abc import ABC, abstractmethod
from typing import Literal

from agentic_rag.config import get_settings


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0,
        json_output: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request and return the response text."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client."""

    def __init__(self, api_key: str):
        import openai
        self.client = openai.OpenAI(api_key=api_key)

    def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0,
        json_output: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_output:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


class AnthropicClient(LLMClient):
    """Anthropic API client."""

    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def chat(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0,
        json_output: bool = False,
        max_tokens: int = 4096,
    ) -> str:
        # Anthropic uses a different message format
        # Extract system message if present
        system_content = None
        chat_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                chat_messages.append(msg)

        # If json_output requested, add instruction to the last user message
        if json_output and chat_messages:
            last_msg = chat_messages[-1]
            if last_msg["role"] == "user":
                last_msg["content"] = last_msg["content"] + "\n\nIMPORTANT: Output ONLY valid JSON, no other text or markdown formatting."

        kwargs = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_content:
            kwargs["system"] = system_content

        response = self.client.messages.create(**kwargs)
        content = response.content[0].text

        # Clean up JSON if needed (Anthropic sometimes wraps in markdown)
        if json_output:
            content = self._extract_json(content)

        return content

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might have markdown formatting."""
        text = text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()


# Singleton client instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get the configured LLM client (singleton)."""
    global _llm_client
    if _llm_client is None:
        settings = get_settings()
        if settings.llm_provider == "anthropic":
            _llm_client = AnthropicClient(api_key=settings.anthropic_api_key)
        else:
            _llm_client = OpenAIClient(api_key=settings.openai_api_key)
    return _llm_client


def reset_llm_client():
    """Reset the singleton client (useful for testing or config changes)."""
    global _llm_client
    _llm_client = None
