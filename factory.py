"""Build the active provider from config.yaml (llm.provider) + .env (URLs / keys)."""
from __future__ import annotations

from ..core.config import get_settings
from .base import LLMProvider
from .providers import OllamaProvider, OpenAIProvider


def build_provider(name: str | None = None) -> LLMProvider:
    s = get_settings()
    name = (name or s.get("llm.provider", "ollama")).lower()
    common = {
        "model": s.get(f"llm.providers.{name}.model", ""),
        "timeout": float(s.get("llm.timeout_seconds", 60)),
        "temperature": float(s.get("llm.temperature", 0.3)),
        "max_tokens": int(s.get("llm.max_tokens", 700)),
    }
    if name == "ollama":
        return OllamaProvider(base_url=s.env["OLLAMA_BASE_URL"], **common)
    if name == "openai":
        p = OpenAIProvider(base_url=s.env["OPENAI_BASE_URL"], api_key=s.env["OPENAI_API_KEY"], **common)
        return p
    if name == "openai_compatible":
        p = OpenAIProvider(base_url=s.env["OPENAI_COMPAT_BASE_URL"], api_key=s.env["OPENAI_COMPAT_API_KEY"], **common)
        p.name = "openai_compatible"
        return p
    raise ValueError(f"Unknown LLM provider '{name}'. Use ollama | openai | openai_compatible.")
