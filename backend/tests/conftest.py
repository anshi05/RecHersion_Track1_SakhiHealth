"""Persona fixtures (exported from the seed) as UserContext objects."""
import json
from datetime import date
from pathlib import Path

import pytest

from app.api.deps import age_from_dob
from app.schemas import CycleEvent, DailyLog, Measurement, Profile, UserContext

FIXTURES = Path(__file__).parent / "fixtures"


def load_ctx(key: str) -> UserContext:
    d = json.loads((FIXTURES / f"{key}.json").read_text(encoding="utf-8"))
    anchor = date.fromisoformat(d["anchor"])
    logs = [DailyLog(id=i, user_id=0, **r) for i, r in enumerate(d["logs"])][-90:]
    profile = Profile(id=0, **d["profile"])
    profile.age = age_from_dob(profile.dob, anchor)
    return UserContext(
        profile=profile,
        age=profile.age,
        lang="en",
        logs=logs,
        cycles=[CycleEvent(id=i, user_id=0, **c) for i, c in enumerate(d["cycles"])],
        measurements=[Measurement(id=i, user_id=0, **m) for i, m in enumerate(d["measurements"])],
        gestational_week=28 if profile.is_pregnant else None,
    )


@pytest.fixture(autouse=True)
def no_live_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests never hit the network: force template mode unless a test installs its own settings."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")


@pytest.fixture(scope="session")
def personas() -> dict[str, UserContext]:
    return {k: load_ctx(k) for k in ("priya", "meena", "sunita")}
