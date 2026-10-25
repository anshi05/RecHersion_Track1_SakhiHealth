"""Persona list + session switch (uid cookie)."""
from fastapi import APIRouter, Depends, Response
from sqlmodel import Session, select

from app.api.analyze import analyze_user
from app.api.deps import age_from_dob, get_user
from app.api.profile import to_profile
from app.db import get_session
from app.errors import AppError
from app.models.tables import DailyLog, User
from app.schemas import Persona, SessionResponse, SwitchRequest, SwitchResponse
from app.seed.personas import PERSONAS
from app.seed.run import seed_persona

router = APIRouter(prefix="/api", tags=["personas"])


@router.get("/personas", response_model=list[Persona])
def list_personas() -> list[Persona]:
    return [
        Persona(key=p.key, name=p.name, age=p.age, life_stage=p.life_stage, tagline=p.tagline)  # type: ignore[arg-type]
        for p in PERSONAS.values()
    ]


@router.post("/session/switch", response_model=SwitchResponse)
def switch(
    body: SwitchRequest, response: Response, session: Session = Depends(get_session)
) -> SwitchResponse:
    if body.persona_key not in PERSONAS:
        raise AppError("unknown_persona", f"Unknown persona '{body.persona_key}'.", 404)
    user = session.exec(select(User).where(User.persona_key == body.persona_key)).first()
    has_logs = user is not None and session.exec(
        select(DailyLog.id).where(DailyLog.user_id == user.id).limit(1)
    ).first() is not None
    if user is None or not has_logs:  # first visit, or data was deleted: (re)seed
        user = seed_persona(session, body.persona_key)
    response.set_cookie("uid", str(user.id), httponly=True, samesite="lax", path="/", max_age=86400 * 30)
    return SwitchResponse(profile=to_profile(user), analysis=analyze_user(session, user))


@router.get("/session", response_model=SessionResponse)
def current_session(user: User = Depends(get_user)) -> SessionResponse:
    p = to_profile(user)
    p.age = age_from_dob(user.dob)
    return SessionResponse(profile=p)
