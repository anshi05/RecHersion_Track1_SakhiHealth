"""Agent interface: rules decide, text is template-only until the LLM layer (P7)."""
from abc import ABC, abstractmethod
from typing import ClassVar

from app.schemas import AgentName, AgentResult, ApplicabilityResult, Evidence, UserContext
from app.services.rules import evaluate_all, load_config


class Agent(ABC):
    name: ClassVar[AgentName]

    @abstractmethod
    def applies(self, ctx: UserContext) -> ApplicabilityResult: ...

    @abstractmethod
    def run(self, ctx: UserContext) -> AgentResult: ...


def evidence_from_rules(ctx: UserContext, names: list[str]) -> tuple[list[Evidence], float]:
    """Fired rules as Evidence (rule name + detail + weight) and the normalised score 0..1."""
    results = evaluate_all(ctx, names)
    ev = [Evidence(rule=n, detail=r.evidence, weight=r.weight) for n, r in results.items() if r.fired]
    cfg = load_config()["rules"]
    total = sum(float(cfg[n]["weight"]) for n in names)
    return ev, (sum(e.weight for e in ev) / total if total else 0.0)
