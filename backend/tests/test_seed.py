from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import app
from app.models.tables import CycleEvent, DailyLog, Measurement
from app.seed.run import seed_all, table_hashes


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture()
def client(engine) -> Iterator[TestClient]:
    def _sess() -> Iterator[Session]:
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _sess
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_seed_twice_identical_hashes(engine) -> None:
    with Session(engine) as s:
        seed_all(s)
        first = table_hashes(s)
        seed_all(s)
        assert table_hashes(s) == first
        assert len({u for u in first.values()}) == len(first)


def test_shape_identical_across_anchors(engine) -> None:
    with Session(engine) as s:
        seed_all(s, date(2026, 1, 1))
        a = [(r.pain_level, r.mood, r.flow) for r in s.exec(select(DailyLog).order_by(DailyLog.id)).all()]
        seed_all(s, date(2026, 6, 1))
        b = [(r.pain_level, r.mood, r.flow) for r in s.exec(select(DailyLog).order_by(DailyLog.id)).all()]
        assert a == b


def test_persona_shapes(engine) -> None:
    with Session(engine) as s:
        users = {u.persona_key: u for u in seed_all(s)}
        pri = s.exec(select(CycleEvent).where(CycleEvent.user_id == users["priya"].id)).all()
        done = [c.length_days for c in pri if c.length_days]
        assert len(done) == 4 and 45 <= sum(done) / 4 <= 51
        sun = s.exec(select(Measurement).where(Measurement.user_id == users["sunita"].id,
                                               Measurement.type == "bp").order_by(Measurement.date)).all()
        assert (sun[-1].value_1, sun[-1].value_2) == (142.0, 92.0)
        assert users["sunita"].is_pregnant and users["sunita"].edd_date


def test_list_and_switch_changes_data(client: TestClient) -> None:
    ps = client.get("/api/personas").json()
    assert [p["key"] for p in ps] == ["priya", "meena", "sunita"]
    assert set(ps[0]) == {"key", "name", "age", "life_stage", "tagline"}
    seen = {}
    for key in ("priya", "meena", "sunita"):
        r = client.post("/api/session/switch", json={"persona_key": key})
        assert r.status_code == 200 and r.json()["profile"]["persona_key"] == key
        assert client.get("/api/session").json()["profile"]["name"] == key.capitalize()
        logs = client.get("/api/logs", params={"from": "2000-01-01"}).json()
        assert len(logs) >= 90
        seen[key] = (r.json()["profile"]["life_stage"], sum(bool(e.get("hot_flash_count")) for e in logs))
    assert len({v[0] for v in seen.values()}) == 3
    assert seen["meena"][1] > 50 and seen["priya"][1] == 0


def test_switch_unknown_persona(client: TestClient) -> None:
    r = client.post("/api/session/switch", json={"persona_key": "nope"})
    assert r.status_code == 404 and r.json()["error"]["code"] == "unknown_persona"


def test_analyze_endpoint_stores_run(client: TestClient) -> None:
    client.post("/api/session/switch", json={"persona_key": "priya"})
    a = client.post("/api/analyze").json()
    assert a["routing"]["activated"] == ["health_story", "pcos_endo"]
    assert a["run_id"] >= 1 and len(a["results"]) == 2
