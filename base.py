from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str


class LLMError(RuntimeError):
    """Raised when a provider cannot answer (unreachable, bad key, timeout)."""


class LLMProvider(ABC):
    name: str = "base"

    def __init__(self, model: str, timeout: float, temperature: float, max_tokens: int):
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    async def chat(self, messages: list[ChatMessage]) -> str: ...

    async def health(self) -> bool:
        try:
            await self.chat([ChatMessage("user", "ping")])
            return True
        except LLMError:
            return False
