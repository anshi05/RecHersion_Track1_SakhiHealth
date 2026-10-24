from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.api.deps import get_user
from app.db import get_session
from app.models.tables import DailyLog, User
from app.schemas import DailyLog as DailyLogOut
from app.schemas import DailyLogIn, LogResponse
from app.services.cycles import recompute_cycles

router = APIRouter(prefix="/api", tags=["logs"])


@router.post("/logs", response_model=LogResponse)
def upsert_log(
    body: DailyLogIn, user: User = Depends(get_user), session: Session = Depends(get_session)
) -> LogResponse:
    assert user.id is not None
    row = session.exec(
        select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.date == body.date)
    ).first()
    data = body.model_dump()
    if row is None:
        row = DailyLog(user_id=user.id, **data)
    else:
        for k, v in data.items():
            setattr(row, k, v)
    session.add(row)
    session.commit()
    session.refresh(row)
    recompute_cycles(session, user.id)
    # analysis is None until the Phase 5 orchestrator is wired in.
    return LogResponse(log=DailyLogOut.model_validate(row, from_attributes=True), analysis=None)


@router.get("/logs", response_model=list[DailyLogOut])
def list_logs(
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = None,
    user: User = Depends(get_user),
    session: Session = Depends(get_session),
) -> list[DailyLogOut]:
    q = select(DailyLog).where(DailyLog.user_id == user.id)
    if from_:
        q = q.where(DailyLog.date >= from_)
    if to:
        q = q.where(DailyLog.date <= to)
    rows = session.exec(q.order_by(DailyLog.date)).all()  # type: ignore[arg-type]
    return [DailyLogOut.model_validate(r, from_attributes=True) for r in rows]
