"""SQLModel engine and session dependency."""
from collections.abc import Iterator

from sqlmodel import Session, create_engine

from app.config import get_settings

_url = get_settings().database_url
engine = create_engine(
    _url,
    connect_args={"check_same_thread": False} if _url.startswith("sqlite") else {},
)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
