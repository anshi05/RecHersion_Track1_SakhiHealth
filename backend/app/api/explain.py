"""POST /explain: plain-language 'Why?' for one fired rule, LLM with template fallback."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.agents.registry import AGENTS
from app.api.deps import get_user
from app.db import get_session
from app.errors import AppError
from app.models.tables import User
from app.schemas import AgentName, Lang
from app.services.context import build_context
from app.services.llm import generate
from app.services.prompts import explain_template

router = APIRouter(prefix="/api", tags=["explain"])


class ExplainRequest(BaseModel):
    agent: AgentName
    rule: str
    lang: Lang = "en"


class ExplainResponse(BaseModel):
    text: str
    source: str


@router.post("/explain", response_model=ExplainResponse)
def explain(
    body: ExplainRequest, user: User = Depends(get_user), session: Session = Depends(get_session)
) -> ExplainResponse:
    ctx = build_context(session, user)
    result = AGENTS[body.agent].run(ctx)
    ev = next((e for e in result.evidence if e.rule == body.rule), None)
    if ev is None:
        raise AppError("rule_not_found", f"No evidence for rule '{body.rule}' in {body.agent}.", 404)
    assert user.id is not None
    facts = {"agent": body.agent, "rule": ev.rule, "detail": ev.detail, "age": ctx.age}
    text, source = generate("explain", facts, body.lang, explain_template(ev.detail.rstrip(".")), user.id)
    return ExplainResponse(text=text, source=source)
