"""Maternal agent: BP / haemoglobin / ANC monitoring with threshold alerts. Urgent states are decided
by the orchestrator's urgent_check (rules, no LLM) and surface here as status "urgent"."""
from typing import Any

from app.agents.base import Agent, band_for, evidence_from_rules
from app.agents.pcos_endo import navigator
from app.schemas import AgentResult, ApplicabilityResult, Card, ChartSpec, Status, UserContext
from app.services.rules import anc_progress, evaluate, load_config

RULES = [
    "bp_alert", "anemia_low_hb", "low_fetal_movement", "swelling_with_headache",
    "rapid_weight_gain", "anc_missed",
]
FLAG_RULES = ("bp_alert", "low_fetal_movement", "swelling_with_headache")  # same-day-visit patterns
STATUS: dict[str, Status] = {"low": "ok", "moderate": "watch", "high": "flag"}
TERM_WEEKS = 40


def _series(ctx: UserContext, mtype: str) -> list[Any]:
    return sorted((m for m in ctx.measurements if m.type == mtype), key=lambda m: m.date)


def charts(ctx: UserContext) -> list[ChartSpec]:
    rules = load_config()["rules"]
    wk = ctx.gestational_week or 0
    out = [ChartSpec(
        id="gestation", kind="bar", title_key="chart.gestation",
        data=[{"week": wk, "total": TERM_WEEKS, "trimester": 1 if wk < 14 else 2 if wk < 28 else 3}])]
    bp = _series(ctx, "bp")
    if bp:
        out.append(ChartSpec(
            id="bp_trend", kind="band", title_key="chart.bp_trend",
            data=[{"date": m.date.isoformat(), "systolic": m.value_1, "diastolic": m.value_2} for m in bp],
            meta={"bands": [
                {"label": "Raised: discuss with your doctor", "systolic": rules["bp_alert"]["systolic"],
                 "diastolic": rules["bp_alert"]["diastolic"]},
                {"label": "Severe: get help now", "systolic": rules["bp_urgent"]["systolic"],
                 "diastolic": rules["bp_urgent"]["diastolic"]}]}))
    hb = _series(ctx, "hemoglobin")
    if hb:
        out.append(ChartSpec(
            id="hb_trend", kind="band", title_key="chart.hb_trend",
            data=[{"date": m.date.isoformat(), "value": m.value_1} for m in hb],
            meta={"bands": [{"label": "Below usual range", "max": rules["anemia_low_hb"]["max_hb"]},
                            {"label": "Severe: get help now", "max": rules["anemia_severe"]["max_hb"]}]}))
    return out


def anc_checklist(ctx: UserContext) -> list[dict[str, Any]]:
    cfg = load_config()["rules"]["anc_missed"]
    _, done = anc_progress(ctx, cfg)
    wk = ctx.gestational_week or 0
    return [{"week": w, "due": w <= wk, "done": i < done} for i, w in enumerate(cfg["schedule_weeks"])]


class Maternal(Agent):
    name = "maternal"

    def applies(self, ctx: UserContext) -> ApplicabilityResult:
        if ctx.profile.is_pregnant:
            return ApplicabilityResult(
                applies=True, reason=f"Pregnant, week {ctx.gestational_week}: maternal monitoring applies.",
                dominance=3)
        return ApplicabilityResult(applies=False, reason="Not pregnant.")

    def run(self, ctx: UserContext) -> AgentResult:
        from app.agents.orchestrator import urgent_check  # local: orchestrator imports the registry

        nav = navigator()["maternal"]
        ev, score = evidence_from_rules(ctx, RULES)
        band = band_for(score)
        urgent = urgent_check(ctx)
        flagged = any(e.rule in FLAG_RULES for e in ev)
        status: Status = "urgent" if urgent else "flag" if flagged else STATUS[band]
        if urgent:
            headline = ("Please get medical help now: " + "; ".join(urgent)
                        + ". Call 108 (ambulance) or 112.")
        elif flagged:
            headline = ("Some readings are patterns commonly associated with pregnancy complications. "
                        "Consider discussing them with your doctor or midwife today.")
        elif ev:
            headline = "Some pregnancy readings are worth discussing at your next antenatal visit."
        else:
            headline = "Your pregnancy readings look steady. Keep logging and attend your antenatal visits."
        cards = [Card(key="when_to_call", title="When to call for help", body=nav["when_to_call"]),
                 Card(key="exclusions", title="What a doctor would also check", body=nav["exclusions"])]
        has_signal = bool(ev) or bool(urgent)
        return AgentResult(
            agent="maternal", status=status, score=round(score, 2), band=band, headline=headline,
            evidence=sorted(ev, key=lambda e: -e.weight),
            suggested_tests=nav["suggested_tests"] if has_signal else [],
            specialist=nav["specialist"] if has_signal else None,
            questions_for_doctor=nav["questions"] if has_signal else [],
            charts=charts(ctx), cards=cards,
            disclaimer_key="emergency" if urgent else "not_a_diagnosis",
            stats={"gestational_week": ctx.gestational_week, "anc": anc_checklist(ctx),
                   "urgent_reasons": urgent,
                   "bp_alert": evaluate("bp_alert", ctx).fired},
        )
