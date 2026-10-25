from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.analyze import analyze_user
from app.api.deps import get_user
from app.db import get_session
from app.models.tables import Measurement, User
from app.schemas import Measurement as MeasurementOut
from app.schemas import MeasurementIn, MeasurementResponse

router = APIRouter(prefix="/api", tags=["measurements"])


@router.post("/measurements", response_model=MeasurementResponse)
def add_measurement(
    body: MeasurementIn, user: User = Depends(get_user), session: Session = Depends(get_session)
) -> MeasurementResponse:
    assert user.id is not None
    row = Measurement(user_id=user.id, **body.model_dump())
    session.add(row)
    session.commit()
    session.refresh(row)
    return MeasurementResponse(
        measurement=MeasurementOut.model_validate(row, from_attributes=True),
        analysis=analyze_user(session, user),
    )


@router.get("/measurements", response_model=list[MeasurementOut])
def list_measurements(
    type: str | None = None,
    user: User = Depends(get_user),
    session: Session = Depends(get_session),
) -> list[MeasurementOut]:
    q = select(Measurement).where(Measurement.user_id == user.id)
    if type:
        q = q.where(Measurement.type == type)
    rows = session.exec(q.order_by(Measurement.date)).all()  # type: ignore[arg-type]
    return [MeasurementOut.model_validate(r, from_attributes=True) for r in rows]
