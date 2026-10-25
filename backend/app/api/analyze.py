"""Run the orchestrator, store the run, and return the routing + results."""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.agents.orchestrator import orchestrate
from app.api.deps import get_user
from app.db import get_session
from app.models.tables import AgentRun, User
from app.schemas import AnalyzeResponse
from app.services.context import build_context

router = APIRouter(prefix="/api", tags=["analyze"])


def analyze_user(session: Session, user: User) -> AnalyzeResponse:
    routing, results, summary = orchestrate(build_context(session, user))
    assert user.id is not None
    run = AgentRun(
        user_id=user.id,
        orchestrator_decision=routing.model_dump(mode="json"),
        results=[r.model_dump(mode="json") for r in results],
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    assert run.id is not None
    return AnalyzeResponse(
        run_id=run.id, ran_at=run.run_at.isoformat(), routing=routing, results=results, summary=summary
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(user: User = Depends(get_user), session: Session = Depends(get_session)) -> AnalyzeResponse:
    return analyze_user(session, user)
