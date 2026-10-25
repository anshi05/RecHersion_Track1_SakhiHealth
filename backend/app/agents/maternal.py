"""Maternal agent. Applicability now; the full result and urgent handling arrive in Phase 9."""
from app.agents.base import Agent, band_for, evidence_from_rules
from app.schemas import AgentResult, ApplicabilityResult, Status, UserContext

RULES = ["bp_alert", "anemia_low_hb", "low_fetal_movement", "swelling_with_headache"]
STATUS: dict[str, Status] = {"low": "ok", "moderate": "watch", "high": "flag"}


class Maternal(Agent):
    name = "maternal"

    def applies(self, ctx: UserContext) -> ApplicabilityResult:
        if ctx.profile.is_pregnant:
            return ApplicabilityResult(
                applies=True, reason=f"Pregnant, week {ctx.gestational_week}: maternal monitoring applies.",
                dominance=3)
        return ApplicabilityResult(applies=False, reason="Not pregnant.")

    def run(self, ctx: UserContext) -> AgentResult:
        ev, score = evidence_from_rules(ctx, RULES)
        band = band_for(score)
        return AgentResult(
            agent="maternal", status=STATUS[band], score=round(score, 2), band=band,
            headline="Some pregnancy readings are worth discussing with your doctor or midwife "
            "at your next visit.",
            evidence=ev,
        )
