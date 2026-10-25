"""PCOS / Endometriosis awareness agent: weighted rule patterns, bands and care navigation."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.agents.base import Agent, band_for, evidence_from_rules
from app.schemas import AgentResult, ApplicabilityResult, Card, ChartSpec, Status, UserContext
from app.services.rules import evaluate

NAVIGATOR_PATH = Path(__file__).resolve().parents[2] / "config" / "navigator.json"
PCOS_RULES = [
    "cycle_long", "cycle_variability", "hirsutism_persistent", "acne_persistent",
    "pco_ultrasound", "family_history_pcos", "bmi_elevated",
]
ENDO_RULES = ["severe_period_pain", "pain_interferes", "dyspareunia_or_bowel_urinary"]
STATUS: dict[str, Status] = {"low": "ok", "moderate": "watch", "high": "flag"}


@lru_cache
def navigator() -> dict[str, Any]:
    return json.loads(NAVIGATOR_PATH.read_text(encoding="utf-8"))


def hyperandrogenism(ctx: UserContext) -> bool:
    return any(evaluate(n, ctx).fired for n in ("hirsutism_persistent", "acne_persistent"))


def _gauge(gid: str, score: float, band: str) -> ChartSpec:
    return ChartSpec(id=gid, kind="gauge", title_key=f"chart.{gid}",
                     data=[{"score": round(score, 2), "band": band}], meta={"max": 1})


class PcosEndo(Agent):
    name = "pcos_endo"

    def applies(self, ctx: UserContext) -> ApplicabilityResult:
        if ctx.profile.is_pregnant:
            return ApplicabilityResult(
                applies=False, reason="Pregnancy: cycle-pattern screening does not apply."
            )
        late = ctx.profile.life_stage in ("perimenopausal", "postmenopausal") or (ctx.age or 0) >= 40
        if late and not hyperandrogenism(ctx):
            return ApplicabilityResult(
                applies=False,
                reason=f"Age {ctx.age}: the menopause transition explains cycle changes better, "
                "and no persistent acne or unwanted hair growth was logged.",
            )
        return ApplicabilityResult(
            applies=True, reason="Reproductive-age cycle and symptom patterns apply.", dominance=1
        )

    def run(self, ctx: UserContext) -> AgentResult:
        pcos_ev, pcos = evidence_from_rules(ctx, PCOS_RULES)
        endo_ev, endo = evidence_from_rules(ctx, ENDO_RULES)
        pcos_band, endo_band = band_for(pcos), band_for(endo)
        lead_pcos = pcos >= endo
        score, key = (pcos, "pcos") if lead_pcos else (endo, "endo")
        band = pcos_band if lead_pcos else endo_band
        nav = navigator()[key]
        label = "PCOS" if lead_pcos else "endometriosis"
        if band == "low":
            headline = "Your logs do not show many patterns commonly associated with PCOS or endometriosis."
        else:
            headline = (f"Your logs show a {band} number of patterns commonly associated with {label}. "
                        "Consider discussing them with a doctor.")
        cards = [Card(key="exclusions", title="What a doctor would also check", body=nav["exclusions"])]
        if band != "low":
            cards.append(Card(key="diagnostic_delay", title=nav["delay"]["title"],
                              body=f"{nav['delay']['body']} ({nav['delay']['source']})"))
        return AgentResult(
            agent="pcos_endo",
            status=STATUS[band],
            score=round(score, 2),
            band=band,
            headline=headline,
            evidence=sorted(pcos_ev + endo_ev, key=lambda e: -e.weight),
            suggested_tests=nav["suggested_tests"] if band != "low" else [],
            specialist=nav["specialist"] if band != "low" else None,
            questions_for_doctor=nav["questions"] if band != "low" else [],
            charts=[_gauge("pcos_gauge", pcos, pcos_band), _gauge("endo_gauge", endo, endo_band)],
            cards=cards,
            stats={"pcos_score": round(pcos, 2), "endo_score": round(endo, 2), "pcos_band": pcos_band,
                   "endo_band": endo_band, "lead": key},
        )
