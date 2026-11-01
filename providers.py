"""Concrete providers: Ollama (local) and OpenAI / any OpenAI-compatible endpoint."""
from __future__ import annotations

import httpx

from .base import ChatMessage, LLMError, LLMProvider


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, **kw):
        super().__init__(**kw)
        self.base_url = base_url.rstrip("/")

    async def chat(self, messages: list[ChatMessage]) -> str:
        payload = {
            "model": self.model,
            "messages": [m.__dict__ for m in messages],
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(f"{self.base_url}/api/chat", json=payload)
                r.raise_for_status()
                return r.json()["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc


class OpenAIProvider(LLMProvider):
    """Works with OpenAI and any server exposing /v1/chat/completions (LM Studio, vLLM, Azure-compat)."""
    name = "openai"

    def __init__(self, base_url: str, api_key: str, **kw):
        super().__init__(**kw)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def chat(self, messages: list[ChatMessage]) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [m.__dict__ for m in messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMError(f"{self.name} request failed: {exc}") from exc
