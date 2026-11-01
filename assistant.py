"""Health-education assistant over the configurable LLM layer (Ollama / OpenAI / compatible)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..core.config import get_settings
from ..core.logging import get_logger
from ..deps import get_current_user
from ..llm import ChatMessage, LLMError, build_provider
from ..models import User
from ..schemas import AssistantIn

router = APIRouter(prefix="/assistant", tags=["assistant"])
log = get_logger("assistant")

# A safety net that runs before any model call: crisis wording always gets the
# support path immediately, regardless of which provider is configured or reachable.
CRISIS_TERMS = (
    "انتحار", "أنتحر", "اقتل نفسي", "أقتل نفسي", "أؤذي نفسي", "اذي نفسي", "لا أريد أن أعيش", "انهي حياتي", "أنهي حياتي",
    "suicide", "kill myself", "hurt myself", "end my life", "self harm", "self-harm", "want to die",
)

SAFETY = {
    "ar": "يهمّنا أن تكون بأمان الآن. إذا كنت في خطر فوري فاتصل بالطوارئ (999 في الإمارات) مباشرة. "
          "يمكنك أيضاً استخدام زر «الدعم العاجل» في التطبيق للتواصل مع الأخصائي المناوب. لست وحدك.",
    "en": "Your safety matters right now. If you are in immediate danger, call emergency services (999 in the UAE). "
          "You can also tap “Urgent support” in the app to reach the on-call specialist. You are not alone.",
}


def is_crisis(text: str) -> bool:
    t = text.lower()
    return any(term in t for term in CRISIS_TERMS)


@router.post("/chat")
async def chat(body: AssistantIn, user: User = Depends(get_current_user)):
    if is_crisis(body.message):
        log.warning("crisis wording detected user=%s — safety response returned", user.id)
        return {"reply": SAFETY[body.locale], "safety": True, "provider": None}

    s = get_settings()
    lang = "Arabic" if body.locale == "ar" else "English"
    messages = [ChatMessage("system", f"{s.get('llm.system_prompt', '')}\nReply in {lang}.")]
    for turn in body.history[-8:]:
        if turn.get("role") in ("user", "assistant") and isinstance(turn.get("content"), str):
            messages.append(ChatMessage(turn["role"], turn["content"][:2000]))
    messages.append(ChatMessage("user", body.message))

    provider = build_provider()
    try:
        reply = await provider.chat(messages)
    except LLMError as exc:
        log.error("assistant provider=%s failed: %s", provider.name, exc)
        raise HTTPException(503, "assistant_unavailable")
    return {"reply": reply, "safety": False, "provider": provider.name}


@router.get("/status")
async def status(_: User = Depends(get_current_user)):
    s = get_settings()
    name = s.get("llm.provider")
    return {"provider": name, "model": s.get(f"llm.providers.{name}.model")}
