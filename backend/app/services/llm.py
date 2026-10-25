"""Claude calls with cache, guardrails and template fallback. Failures degrade, never raise."""
import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any, Literal

import anthropic
from sqlmodel import Session

from app.config import get_settings
from app.db import engine
from app.models.tables import LlmCache
from app.services import guardrails
from app.services.prompts import SYSTEM, user_prompt

log = logging.getLogger(__name__)
Source = Literal["llm", "template"]


def _complete(task: str, facts: dict[str, Any], lang: str) -> str:
    s = get_settings()
    client = anthropic.Anthropic(api_key=s.anthropic_api_key, timeout=s.llm_timeout_s, max_retries=0)
    msg = client.messages.create(
        model=s.anthropic_model,
        max_tokens=1024,
        system=SYSTEM,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": user_prompt(task, facts, lang)}],
    )
    if msg.stop_reason != "end_turn":
        raise RuntimeError(f"unusable stop_reason {msg.stop_reason}")
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def cache_key(user_id: int, task: str, facts: dict[str, Any], lang: str) -> str:
    data_hash = hashlib.sha256(json.dumps(facts, default=str, sort_keys=True).encode()).hexdigest()
    return hashlib.sha256(f"{user_id}|{task}|{data_hash}|{lang}".encode()).hexdigest()


def _cache_get(key: str) -> str | None:
    try:
        with Session(engine) as db:
            row = db.get(LlmCache, key)
            return row.text if row else None
    except Exception:  # cache is best-effort (e.g. table missing in unit tests)
        return None


def _cache_put(key: str, text: str) -> None:
    try:
        with Session(engine) as db:
            db.merge(LlmCache(key=key, text=text, source="llm"))
            db.commit()
    except Exception:
        log.warning("llm cache write failed", exc_info=True)


def generate(
    task: str,
    facts: dict[str, Any],
    lang: str,
    template: str,
    user_id: int,
    valid: Callable[[str], bool] = guardrails.is_safe,
    allow_llm: bool = True,
) -> tuple[str, Source]:
    """Return (text, source): LLM text if a key is set and it passes `valid`, else the template."""
    if not allow_llm or not get_settings().llm_live:
        return template, "template"
    key = cache_key(user_id, task, facts, lang)
    cached = _cache_get(key)
    if cached and valid(cached):
        return cached, "llm"
    try:
        text = _complete(task, facts, lang)
    except Exception as exc:  # timeout, rate limit, refusal, network: the demo must continue
        log.warning("llm %s failed: %s", task, exc)
        return template, "template"
    if not valid(text):
        log.warning("llm %s rejected by guardrails: %s", task, guardrails.check(text))
        return template, "template"
    _cache_put(key, text)
    return text, "llm"


def questions_valid(text: str) -> bool:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return 5 <= len(lines) <= 8 and all(guardrails.is_safe(ln) for ln in lines)


def split_questions(text: str) -> list[str]:
    return [ln.strip(" -•*0123456789.)") for ln in text.splitlines() if ln.strip()]
