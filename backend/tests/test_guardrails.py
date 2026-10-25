"""Guardrail fixtures + LLM fallback / cache behaviour (no network: _complete is stubbed)."""
import pytest

from app.agents.orchestrator import orchestrate
from app.services import guardrails, llm
from app.services.prompts import SYSTEM, user_prompt

REJECT = [
    "You have PCOS.",
    "You probably have endometriosis, so see someone.",
    "You were diagnosed with diabetes.",
    "Take 500 mg of it every night.",
    "Metformin may help your cycles.",
    "You should start hormone therapy.",
    "This is definitely PCOS.",
    "Your doctor will prescribe something.",
]
ACCEPT = [
    "Your logs show patterns commonly associated with PCOS. Consider discussing them with a doctor.",
    "Your cycles averaged 48 days, which is longer than the usual range. This is not a diagnosis.",
]


@pytest.mark.parametrize("text", REJECT)
def test_rejects_forbidden(text: str) -> None:
    assert guardrails.check(text), text


@pytest.mark.parametrize("text", ACCEPT)
def test_accepts_awareness_wording(text: str) -> None:
    assert guardrails.check(text) == []


def test_rejects_empty() -> None:
    assert guardrails.check("  ") == ["empty"]


def test_prompt_contains_only_facts_and_bans() -> None:
    p = user_prompt("summary", {"age": 29}, "en")
    assert '"age": 29' in p and "Never diagnose" in SYSTEM and "doses" in SYSTEM


@pytest.fixture
def live(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    store: dict[str, str] = {}
    calls: list[int] = []
    monkeypatch.setattr(llm, "_cache_get", store.get)
    monkeypatch.setattr(llm, "_cache_put", store.__setitem__)
    monkeypatch.setattr(llm, "_complete", lambda *a: (calls.append(1), "A calm, safe sentence.")[1])
    return calls


def test_template_without_key() -> None:
    assert llm.generate("summary", {"a": 1}, "en", "tmpl", 1) == ("tmpl", "template")


def test_llm_then_cache(live: list[int]) -> None:
    assert llm.generate("summary", {"a": 1}, "en", "tmpl", 1) == ("A calm, safe sentence.", "llm")
    assert llm.generate("summary", {"a": 1}, "en", "tmpl", 1)[1] == "llm"
    assert len(live) == 1  # second call served from cache


def test_unsafe_llm_text_falls_back(live: list[int], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_complete", lambda *a: "You have PCOS.")
    assert llm.generate("summary", {"a": 2}, "en", "tmpl", 1) == ("tmpl", "template")


def test_llm_error_falls_back(live: list[int], monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a: object) -> str:
        raise TimeoutError

    monkeypatch.setattr(llm, "_complete", boom)
    assert llm.generate("summary", {"a": 3}, "en", "tmpl", 1) == ("tmpl", "template")


def test_urgent_bypasses_llm(live: list[int], personas: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.agents.orchestrator.urgent_check", lambda c: ["bp 170/115"])
    _, _, summary = orchestrate(personas["sunita"])
    assert summary.source == "template" and not live


def test_questions_need_5_to_8_lines() -> None:
    assert not llm.questions_valid("one\ntwo")
    assert llm.questions_valid("\n".join(f"Question number {i}?" for i in range(6)))
