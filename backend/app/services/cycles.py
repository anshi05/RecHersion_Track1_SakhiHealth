"""Cycle detection: a cycle starts on the first light/medium/heavy flow day
after >=3 days of none|spotting (unlogged days count as none)."""
from datetime import date
from typing import Any

from sqlalchemy import delete
from sqlmodel import Session, select

from app.models.tables import CycleEvent, DailyLog

FLOW_DAYS = {"light", "medium", "heavy"}
_RANK = {"light": 1, "medium": 2, "heavy": 3}
MIN_GAP = 3


def compute_cycles(logs: list[DailyLog]) -> list[dict[str, Any]]:
    cycles: list[dict[str, Any]] = []
    last_flow: date | None = None
    for log in sorted(logs, key=lambda x: x.date):
        if log.flow not in FLOW_DAYS:
            continue
        if last_flow is None or (log.date - last_flow).days - 1 >= MIN_GAP:
            cycles.append({"start_date": log.date, "end_date": log.date, "peak": log.flow})
        else:
            cur = cycles[-1]
            cur["end_date"] = log.date
            if _RANK[log.flow] > _RANK[cur["peak"]]:
                cur["peak"] = log.flow
        last_flow = log.date
    return cycles


def recompute_cycles(session: Session, user_id: int) -> list[CycleEvent]:
    logs = list(session.exec(select(DailyLog).where(DailyLog.user_id == user_id)).all())
    found = compute_cycles(logs)
    session.execute(delete(CycleEvent).where(CycleEvent.user_id == user_id))  # type: ignore[arg-type]
    rows = []
    for i, c in enumerate(found):
        nxt = found[i + 1]["start_date"] if i + 1 < len(found) else None
        rows.append(
            CycleEvent(
                user_id=user_id,
                start_date=c["start_date"],
                end_date=c["end_date"],
                length_days=(nxt - c["start_date"]).days if nxt else None,
                flow_summary=c["peak"],
            )
        )
    session.add_all(rows)
    session.commit()
    return rows
