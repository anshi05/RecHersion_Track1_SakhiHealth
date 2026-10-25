"""Prompts and template fallbacks. The LLM only sees computed facts JSON and only explains them."""
import json
from typing import Any

from app.schemas import AgentResult

SYSTEM = """You are Sakhi, a women's health awareness companion.
You explain pre-computed health facts in plain, warm language.
Rules you never break:
- Use ONLY the facts in the JSON the user sends. Never add numbers, causes or conditions that are not in it.
- Never diagnose. Never say the person has, probably has, or is diagnosed with any condition.
  Say "patterns commonly associated with ..." instead.
- Never name medicines, supplements, hormone treatments or doses.
  Never tell her to start or stop anything.
- Point toward "consider discussing this with a doctor" when a pattern is flagged.
- Plain text only: no markdown, no headings, no emojis."""

LANG_LINE = {
    "en": "Write in simple English.",
    "hi": "Write in simple Hindi (Devanagari script). Keep medical terms short and familiar.",
}

TASKS = {
    "summary": "Write a 3 to 4 sentence summary of these findings for the person, at most 90 words.",
    "questions": (
        "Write between 5 and 8 questions she could ask her doctor about these findings. "
        "First person, one question per line, no numbering, no bullets, each under 25 words."
    ),
    "explain": "Explain in 2 to 3 sentences why this one finding was flagged and what it may mean for her.",
}


def user_prompt(task: str, facts: dict[str, Any], lang: str) -> str:
    facts_json = json.dumps(facts, default=str, sort_keys=True)
    return f"{TASKS[task]} {LANG_LINE.get(lang, LANG_LINE['en'])}\n\nFacts:\n{facts_json}"


def facts_for(results: list[AgentResult], age: int | None, life_stage: str) -> dict[str, Any]:
    """Compact, name-free facts: only what rules computed."""
    return {
        "age": age,
        "life_stage": life_stage,
        "agents": [
            {
                "agent": r.agent, "status": r.status, "band": r.band, "headline": r.headline,
                "evidence": [{"rule": e.rule, "detail": e.detail} for e in r.evidence],
            }
            for r in results
        ],
    }


def summary_template(results: list[AgentResult]) -> str:
    return " ".join(r.headline for r in results)


def questions_template(results: list[AgentResult]) -> list[str]:
    seen: list[str] = []
    for r in results:
        for q in r.questions_for_doctor:
            if q not in seen:
                seen.append(q)
    return seen


def explain_template(detail: str) -> str:
    return (f"{detail}. This is a pattern commonly associated with changes worth tracking. "
            "Consider discussing it with a doctor; this is not a diagnosis.")
