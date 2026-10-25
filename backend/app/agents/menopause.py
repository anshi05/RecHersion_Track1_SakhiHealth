"""Menopause agent. Applicability now; the full MRS-based result arrives in Phase 10."""
from app.agents.base import Agent, band_for, evidence_from_rules
from app.schemas import AgentResult, ApplicabilityResult, Status, UserContext
from app.services.rules import evaluate

RULES = [
    "vasomotor_frequent", "night_sweats_frequent", "sleep_short",
    "perimenopause_age_window", "cycle_variability",
]
STATUS: dict[str, Status] = {"low": "ok", "moderate": "watch", "high": "flag"}


class Menopause(Agent):
    name = "menopause"

    def applies(self, ctx: UserContext) -> ApplicabilityResult:
        if ctx.profile.is_pregnant:
            return ApplicabilityResult(applies=False, reason="Pregnancy: menopause patterns do not apply.")
        if ctx.profile.life_stage in ("perimenopausal", "postmenopausal"):
            return ApplicabilityResult(
                applies=True, dominance=2,
                reason=f"Age {ctx.age}, {ctx.profile.life_stage}: menopause-transition patterns apply.")
        if (ctx.age or 0) >= 40 and evaluate("vasomotor_frequent", ctx).fired:
            return ApplicabilityResult(
                applies=True, reason=f"Age {ctx.age} with frequent hot flashes logged.", dominance=2)
        return ApplicabilityResult(applies=False, reason="No menopause-transition signs for this profile.")

    def run(self, ctx: UserContext) -> AgentResult:
        ev, score = evidence_from_rules(ctx, RULES)
        band = band_for(score)
        return AgentResult(
            agent="menopause", status=STATUS[band], score=round(score, 2), band=band,
            headline="Your logs show patterns commonly associated with the menopause transition. "
            "Consider discussing them with a doctor.",
            evidence=ev,
        )
