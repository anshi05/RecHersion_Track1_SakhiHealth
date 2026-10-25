"""Orchestrator: urgent check first, then route to the agents whose `applies()` is true."""
from app.agents.registry import AGENTS
from app.schemas import AgentResult, RoutingDecision, Skipped, Summary, UserContext
from app.services.llm import generate, questions_valid, split_questions
from app.services.prompts import facts_for, questions_template, summary_template
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
    # Urgent bypasses the LLM: template text only, instant.
    use_llm = not routing.urgent
    uid, facts = ctx.profile.id, facts_for(results, ctx.age, ctx.profile.life_stage)
    text, source = generate("summary", facts, ctx.lang, summary_template(results), uid, allow_llm=use_llm)
    qs, qs_source = generate(
        "questions", facts, ctx.lang, "\n".join(questions_template(results)), uid,
        valid=questions_valid, allow_llm=use_llm,
    )
    if qs_source == "llm":
        lead = results[0]  # Health Story always runs first and carries the doctor questions
        lead.questions_for_doctor, lead.text_source = split_questions(qs), "llm"
    return routing, results, Summary(text=text, source=source)
