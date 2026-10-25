"""Orchestrator: urgent check first, then route to the agents whose `applies()` is true."""
from app.agents.registry import AGENTS
from app.schemas import AgentResult, RoutingDecision, Skipped, Summary, UserContext
from app.services.rules import evaluate


def urgent_check(ctx: UserContext) -> list[str]:
    reasons = []
    bp = evaluate("bp_urgent", ctx)
    if bp.fired:
        reasons.append(bp.evidence)
    if ctx.logs and ctx.logs[-1].danger_signs:
        reasons.append("Danger signs logged: " + ", ".join(ctx.logs[-1].danger_signs))
    return reasons


def route(ctx: UserContext) -> RoutingDecision:
    urgent = urgent_check(ctx)
    activated, skipped, reasons = [], [], {}
    for name, agent in AGENTS.items():
        a = agent.applies(ctx)
        reasons[name] = a.reason
        if a.applies:
            activated.append(name)
        else:
            skipped.append(Skipped(agent=name, reason=a.reason))  # type: ignore[arg-type]
    return RoutingDecision(
        activated=activated,  # type: ignore[arg-type]
        skipped=skipped, reasons=reasons, urgent=bool(urgent), urgent_reasons=urgent,
    )


def orchestrate(ctx: UserContext) -> tuple[RoutingDecision, list[AgentResult], Summary]:
    routing = route(ctx)
    results = [AGENTS[n].run(ctx) for n in routing.activated]
    text = " ".join(r.headline for r in results)  # template summary until the LLM layer (P7)
    return routing, results, Summary(text=text, source="template")
