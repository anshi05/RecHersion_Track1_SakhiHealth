from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import age_from_dob, get_user
from app.db import get_session
from app.models.tables import User
from app.schemas import Profile, ProfileUpdate

router = APIRouter(prefix="/api", tags=["profile"])


def to_profile(u: User) -> Profile:
    p = Profile.model_validate(u, from_attributes=True)
    p.age = age_from_dob(u.dob)
    return p


@router.get("/profile", response_model=Profile)
def get_profile(user: User = Depends(get_user)) -> Profile:
    return to_profile(user)


@router.put("/profile", response_model=Profile)
def put_profile(
    body: ProfileUpdate, user: User = Depends(get_user), session: Session = Depends(get_session)
) -> Profile:
    # TODO(P5): re-run analysis after update.
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    session.add(user)
    session.commit()
    session.refresh(user)
    return to_profile(user)
