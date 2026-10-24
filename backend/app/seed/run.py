"""Seed persona users. `python -m app.seed.run [--export]` (from backend/)."""
import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import delete
from sqlmodel import Session, SQLModel, select

from app.db import engine
from app.models import tables
from app.models.tables import AgentRun, CycleEvent, DailyLog, Measurement, Report, User
from app.seed.generators import generate
from app.seed.personas import PERSONAS, PersonaSpec
from app.services.cycles import recompute_cycles

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
_DEPENDENTS = (DailyLog, CycleEvent, Measurement, AgentRun, Report)


def _years_ago(anchor: date, years: int) -> date:
    try:
        return anchor.replace(year=anchor.year - years)
    except ValueError:  # Feb 29
        return anchor.replace(year=anchor.year - years, day=28)


def clear_user(session: Session, user_id: int) -> None:
    for model in _DEPENDENTS:
        session.execute(delete(model).where(model.user_id == user_id))  # type: ignore[arg-type]


def seed_persona(session: Session, key: str, anchor: date | None = None) -> User:
    """(Re)create one persona's user and all its rows. Idempotent: same shape every time."""
    anchor = anchor or date.today()
    spec: PersonaSpec = PERSONAS[key]
    old = session.exec(select(User).where(User.persona_key == key)).all()
    for u in old:
        assert u.id is not None
        clear_user(session, u.id)
        session.delete(u)
    session.commit()

    lmp = anchor - timedelta(weeks=spec.gestation_weeks) if spec.gestation_weeks else None
    user = User(
        persona_key=key, name=spec.name, dob=_years_ago(anchor, spec.age), language=spec.language,
        life_stage=spec.life_stage, is_pregnant=spec.is_pregnant, lmp_date=lmp,
        edd_date=lmp + timedelta(days=280) if lmp else None, height_cm=spec.height_cm,
        weight_kg=spec.weight_kg, known_conditions=list(spec.known_conditions),
        medications=list(spec.medications), family_history=list(spec.family_history),
        ultrasound_pco=spec.ultrasound_pco, region=spec.region,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    assert user.id is not None
    logs, meas = generate(spec, anchor)
    session.add_all(DailyLog(user_id=user.id, **r) for r in logs)
    session.add_all(Measurement(user_id=user.id, **m) for m in meas)
    session.commit()
    recompute_cycles(session, user.id)
    session.refresh(user)
    return user


def seed_all(session: Session, anchor: date | None = None) -> list[User]:
    return [seed_persona(session, k, anchor) for k in PERSONAS]


def _row(obj: object, drop: set[str]) -> dict:
    d = obj.model_dump(mode="json")  # type: ignore[attr-defined]
    return {k: v for k, v in d.items() if k not in drop}


def table_hashes(session: Session) -> dict[str, str]:
    """sha256 per table over rows ordered by persona, ignoring surrogate ids and timestamps."""
    persona = {u.id: u.persona_key for u in session.exec(select(User)).all()}
    out: dict[str, str] = {}
    users = sorted((_row(u, {"id", "created_at"}) for u in session.exec(select(User)).all()),
                   key=lambda r: r["persona_key"] or "")
    out["users"] = hashlib.sha256(json.dumps(users, sort_keys=True).encode()).hexdigest()
    for model in (DailyLog, CycleEvent, Measurement):
        rows = [{"persona": persona[r.user_id], **_row(r, {"id", "user_id"})}
                for r in session.exec(select(model)).all()]
        rows.sort(key=lambda r: json.dumps(r, sort_keys=True))
        out[model.__tablename__] = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return out


def export_fixtures(session: Session) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for u in session.exec(select(User)).all():
        assert u.id is not None and u.persona_key
        data = {
            "anchor": date.today().isoformat(),
            "profile": _row(u, {"id", "created_at"}),
            "logs": [_row(r, {"id", "user_id"}) for r in session.exec(
                select(DailyLog).where(DailyLog.user_id == u.id).order_by(DailyLog.date)).all()],
            "cycles": [_row(r, {"id", "user_id"}) for r in session.exec(
                select(CycleEvent).where(CycleEvent.user_id == u.id).order_by(CycleEvent.start_date)).all()],
            "measurements": [_row(r, {"id", "user_id"}) for r in session.exec(
                select(Measurement).where(Measurement.user_id == u.id)
                .order_by(Measurement.date, Measurement.type)).all()],
        }
        (FIXTURES / f"{u.persona_key}.json").write_text(json.dumps(data, indent=1), encoding="utf-8")


def main() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        users = seed_all(s)
        print(f"seeded {[u.persona_key for u in users]}")
        for k, v in table_hashes(s).items():
            print(f"  {k}: {v[:12]}")
        if "--export" in sys.argv:
            export_fixtures(s)
            print(f"fixtures -> {FIXTURES}")


_ = tables  # ensure tables registered before create_all

if __name__ == "__main__":
    main()
