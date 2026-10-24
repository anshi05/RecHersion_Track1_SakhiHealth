"""Active-user dependency (uid cookie)."""
from datetime import date

from fastapi import Cookie, Depends
from sqlmodel import Session

from app.db import get_session
from app.errors import AppError
from app.models.tables import User


def get_user(
    uid: str | None = Cookie(default=None), session: Session = Depends(get_session)
) -> User:
    if not uid or not uid.isdigit():
        raise AppError("unauthenticated", "No active user session.", 401)
    user = session.get(User, int(uid))
    if user is None:
        raise AppError("unauthenticated", "Unknown user session.", 401)
    return user


def age_from_dob(dob: date | None, today: date | None = None) -> int | None:
    if dob is None:
        return None
    t = today or date.today()
    return t.year - dob.year - ((t.month, t.day) < (dob.month, dob.day))
