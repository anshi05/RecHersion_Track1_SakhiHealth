"""Timeline (cycles + day points + markers) and on-demand agent results."""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.agents.registry import AGENTS
from app.api.deps import get_user
from app.db import get_session
from app.errors import AppError
from app.models.tables import User
from app.schemas import AgentResult, DayPoint, Marker, TimelineResponse
from app.services.context import build_context
from app.services.stats import cycle_day_map

router = APIRouter(prefix="/api", tags=["timeline"])


@router.get("/timeline", response_model=TimelineResponse)
def timeline(
    days: int = Query(90, ge=7, le=365),
    user: User = Depends(get_user),
    session: Session = Depends(get_session),
) -> TimelineResponse:
    ctx = build_context(session, user, days)
    cd = cycle_day_map(ctx)
    points = [
        DayPoint(date=x.date, flow=x.flow, pain_level=x.pain_level, mood=x.mood, energy=x.energy,  # type: ignore[arg-type]
                 sleep_hours=x.sleep_hours, stress=x.stress, cycle_day=cd.get(x.date))
        for x in ctx.logs
    ]
    lo = points[0].date if points else None
    cycles = [c for c in ctx.cycles if lo is None or (c.end_date or c.start_date) >= lo]
    markers = [Marker(date=c.start_date, kind="period_start", label="Period start") for c in cycles]
    markers += [
        Marker(date=m.date, kind="measurement", label=f"{m.type} {m.value_1:g}"
               + (f"/{m.value_2:g}" if m.value_2 is not None else ""))
        for m in ctx.measurements if lo is None or m.date >= lo
    ]
    return TimelineResponse(cycles=cycles, days=points, markers=sorted(markers, key=lambda m: m.date))


@router.get("/agents/{name}", response_model=AgentResult)
def agent_result(
    name: str, user: User = Depends(get_user), session: Session = Depends(get_session)
) -> AgentResult:
    """Computed on demand until P5 stores orchestrator runs."""
    agent = AGENTS.get(name)
    if agent is None:
        raise AppError("agent_not_found", f"No result available for agent '{name}'.", 404)
    return agent.run(build_context(session, user))
