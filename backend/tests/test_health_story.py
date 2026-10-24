from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.agents.health_story import HealthStory
from app.db import get_session
from app.main import app
from app.schemas import UserContext
from app.services.stats import compute_stats, pearson


@pytest.fixture()
def client() -> Iterator[TestClient]:
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(eng)

    def _sess() -> Iterator[Session]:
        with Session(eng) as s:
            yield s

    app.dependency_overrides[get_session] = _sess
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_priya_cycle_stats_and_evidence(personas: dict[str, UserContext]) -> None:
    r = HealthStory().run(personas["priya"])
    c = r.stats["cycle"]
    assert c["count"] == 4 and 47 <= c["mean"] <= 50
    assert r.status == "watch"
    assert "cycle_long" in {e.rule for e in r.evidence}
    assert "longer than" in r.headline


def test_priya_heatmap_has_acne_and_hirsutism(personas: dict[str, UserContext]) -> None:
    r = HealthStory().run(personas["priya"])
    hm = r.charts[0]
    keys = {row["key"] for row in hm.data}
    assert {"acne", "hirsutism"} <= keys
    assert all(len(row["levels"]) == len(hm.meta["dates"]) for row in hm.data)  # type: ignore[index]
    assert len(hm.data) <= 8


def test_sunita_without_cycles_is_ok(personas: dict[str, UserContext]) -> None:
    r = HealthStory().run(personas["sunita"])
    assert r.status == "ok" and r.stats["cycle"]["count"] == 0
    assert "swelling" in {row["key"] for row in r.charts[0].data}


def test_meena_irregular_by_variability(personas: dict[str, UserContext]) -> None:
    assert "cycle_variability" in {e.rule for e in HealthStory().run(personas["meena"]).evidence}


def test_stats_blocks(personas: dict[str, UserContext]) -> None:
    s = compute_stats(personas["priya"])
    assert s["phase_frequency"] and {d["metric"] for d in s["deltas"]} >= {"mood", "pain_level"}
    assert all(abs(c["r"]) >= 0.3 and c["n"] >= 14 for c in s["correlations"])


def test_pearson() -> None:
    assert pearson([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert pearson([1, 1, 1], [1, 2, 3]) is None


def test_timeline_and_agent_endpoints(client: TestClient) -> None:
    assert client.get("/api/timeline").status_code == 401
    client.post("/api/session/switch", json={"persona_key": "priya"})
    t = client.get("/api/timeline?days=200").json()
    assert [c["length_days"] for c in t["cycles"] if c["length_days"]] == [48, 49, 48, 48]
    assert len(t["days"]) == 200 and any(d["cycle_day"] for d in t["days"])
    assert any(m["kind"] == "period_start" for m in t["markers"])
    a = client.get("/api/agents/health_story").json()
    assert a["agent"] == "health_story" and a["stats"]["cycle"]["count"] == 4
    err = client.get("/api/agents/nope")
    assert err.status_code == 404 and err.json()["error"]["code"] == "agent_not_found"
