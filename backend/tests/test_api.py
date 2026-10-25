from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import get_session
from app.main import app
from app.models.tables import CycleEvent, User


@pytest.fixture()
def env() -> Iterator[tuple[TestClient, Session]]:
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(eng)

    def _sess() -> Iterator[Session]:
        with Session(eng) as s:
            yield s

    app.dependency_overrides[get_session] = _sess
    with Session(eng) as s:
        u = User(name="T", dob=date(1990, 1, 1))
        s.add(u)
        s.commit()
        s.refresh(u)
        c = TestClient(app)
        c.cookies.set("uid", str(u.id))
        yield c, s
    app.dependency_overrides.clear()


def test_requires_uid() -> None:
    r = TestClient(app).get("/api/profile")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthenticated"


def test_profile_get_put_age(env: tuple[TestClient, Session]) -> None:
    c, _ = env
    assert c.get("/api/profile").json()["age"] >= 30
    r = c.put("/api/profile", json={"name": "Z", "weight_kg": 60})
    assert r.json()["name"] == "Z" and r.json()["weight_kg"] == 60
    assert r.json()["dob"] == "1990-01-01"


def test_post_log_then_get_and_upsert(env: tuple[TestClient, Session]) -> None:
    c, _ = env
    r = c.post("/api/logs", json={"date": "2026-01-05", "flow": "light", "mood": 3})
    assert r.status_code == 200 and r.json()["analysis"]["run_id"]
    c.post("/api/logs", json={"date": "2026-01-05", "flow": "heavy", "mood": 4})
    got = c.get("/api/logs", params={"from": "2026-01-01", "to": "2026-01-31"}).json()
    assert len(got) == 1 and got[0]["flow"] == "heavy" and got[0]["mood"] == 4
    assert c.get("/api/logs", params={"from": "2026-02-01"}).json() == []


def test_three_periods_make_two_cycles(env: tuple[TestClient, Session]) -> None:
    c, s = env
    start = date(2026, 1, 1)
    for off, n in ((0, 4), (30, 4), (58, 3)):
        for i in range(n):
            c.post("/api/logs", json={"date": str(start + timedelta(off + i)), "flow": "medium"})
        c.post("/api/logs", json={"date": str(start + timedelta(off + n + 1)), "flow": "spotting"})
    s.expire_all()
    ev = s.exec(select(CycleEvent).order_by(CycleEvent.start_date)).all()  # type: ignore[arg-type]
    complete = [e for e in ev if e.length_days is not None]
    assert len(ev) == 3 and len(complete) == 2
    assert [e.length_days for e in complete] == [30, 28]


def test_measurement(env: tuple[TestClient, Session]) -> None:
    c, _ = env
    r = c.post(
        "/api/measurements",
        json={"date": "2026-01-05", "type": "bp", "value_1": 120, "value_2": 80, "unit": "mmHg"},
    )
    assert r.status_code == 200 and r.json()["measurement"]["value_2"] == 80
    assert len(c.get("/api/measurements", params={"type": "bp"}).json()) == 1
