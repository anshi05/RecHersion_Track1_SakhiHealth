"""Build a UserContext from the database (rules and agents never touch the DB)."""
from datetime import timedelta

from sqlmodel import Session, select

from app.api.deps import age_from_dob
from app.models import tables as t
from app.schemas import CycleEvent, DailyLog, Measurement, Profile, UserContext


def gestational_week(user: t.User, today) -> int | None:  # noqa: ANN001
    if not user.is_pregnant or user.lmp_date is None:
        return None
    return max(0, (today - user.lmp_date).days // 7)


def build_context(session: Session, user: t.User, days: int = 90) -> UserContext:
    assert user.id is not None
    all_logs = session.exec(
        select(t.DailyLog).where(t.DailyLog.user_id == user.id).order_by(t.DailyLog.date)  # type: ignore[arg-type]
    ).all()
    logs = [DailyLog.model_validate(x, from_attributes=True) for x in all_logs]
    today = logs[-1].date if logs else None
    if today:  # window ends at the latest log, matching rules.window()
        logs = [x for x in logs if x.date >= today - timedelta(days=days - 1)]
    cycles = session.exec(
        select(t.CycleEvent).where(t.CycleEvent.user_id == user.id).order_by(t.CycleEvent.start_date)  # type: ignore[arg-type]
    ).all()
    meas = session.exec(
        select(t.Measurement).where(t.Measurement.user_id == user.id).order_by(t.Measurement.date)  # type: ignore[arg-type]
    ).all()
    profile = Profile.model_validate(user, from_attributes=True)
    profile.age = age_from_dob(user.dob, today)
    return UserContext(
        profile=profile,
        age=profile.age,
        lang=user.language,
        logs=logs,
        cycles=[CycleEvent.model_validate(c, from_attributes=True) for c in cycles],
        measurements=[Measurement.model_validate(m, from_attributes=True) for m in meas],
        gestational_week=gestational_week(user, today) if today else None,
    )
