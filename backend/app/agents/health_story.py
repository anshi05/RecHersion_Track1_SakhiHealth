"""Health Story agent: explains the last ~90 days from computed stats. Applies to everyone."""
from typing import Any

from app.agents.base import Agent, evidence_from_rules
from app.schemas import AgentResult, ApplicabilityResult, ChartSpec, Evidence, UserContext
from app.services.rules import load_config, values
from app.services.stats import compute_stats

CYCLE_RULES = ["cycle_long", "cycle_variability"]
HEATMAP_ROWS = 8

# symptom key -> (log field, kind). Levels are scaled to the 0..5 heat ramp.
SYMPTOMS: list[tuple[str, str, str]] = [
    ("pain", "pain_level", "ten"), ("acne", "acne", "three"), ("hirsutism", "hirsutism", "three"),
    ("hair_thinning", "hair_thinning", "three"), ("headache", "headache", "three"),
    ("swelling", "swelling", "three"), ("fatigue", "fatigue", "five"), ("low_mood", "mood", "inv5"),
    ("hot_flashes", "hot_flash_count", "count"), ("bloating", "bloating", "bool"),
    ("night_sweats", "night_sweats", "bool"), ("joint_pain", "joint_pain", "bool"),
    ("brain_fog", "brain_fog", "bool"), ("vaginal_dryness", "vaginal_dryness", "bool"),
    ("nausea", "nausea", "bool"),
]


def _level(v: Any, kind: str) -> int | None:
    if v is None:
        return None
    if kind == "bool":
        return 4 if v else 0
    if kind == "three":
        return round(v * 5 / 3)
    if kind == "ten":
        return round(v / 2)
    if kind == "five":
        return round((v - 1) * 5 / 4)
    if kind == "inv5":
        return round((5 - v) * 5 / 4)
    return min(5, int(v))  # count


def heatmap(ctx: UserContext) -> ChartSpec:
    logs = sorted(ctx.logs, key=lambda x: x.date)
    rows = []
    for key, field, kind in SYMPTOMS:
        if not values(logs, field):
            continue
        levels = [_level(getattr(x, field), kind) for x in logs]
        seen = [lv for lv in levels if lv is not None]
        rows.append({"key": key, "levels": levels, "mean": sum(seen) / len(seen)})
    rows = sorted(rows, key=lambda r: -r["mean"])[:HEATMAP_ROWS]
    return ChartSpec(id="symptom_heatmap", kind="heatmap", title_key="chart.symptom_heatmap",
                     data=[{"key": r["key"], "levels": r["levels"]} for r in rows],
                     meta={"dates": [x.date.isoformat() for x in logs], "max_level": 5})


def _headline(stats: dict[str, Any], fired: set[str]) -> str:
    c = stats["cycle"]
    if "cycle_long" in fired:
        return (f"Your cycles average {c['mean']:.0f} days, longer than the 21-35 day range "
                "commonly seen. Worth discussing with a doctor.")
    if "cycle_variability" in fired:
        return (f"Your cycle length varies by {c['max'] - c['min']} days from one cycle to the next, "
                "a pattern commonly worth discussing with a doctor.")
    if c["count"]:
        return f"Your cycles look steady at about {c['mean']:.0f} days. Here is your last 90 days."
    return "Here is your last 90 days at a glance."


class HealthStory(Agent):
    name = "health_story"

    def applies(self, ctx: UserContext) -> ApplicabilityResult:
        return ApplicabilityResult(applies=True, reason="Health Story runs for everyone.", dominance=0)

    def run(self, ctx: UserContext) -> AgentResult:
        stats = compute_stats(ctx)
        evidence, score = evidence_from_rules(ctx, CYCLE_RULES)
        w = load_config()["stats"]["corr_weight"]
        evidence += [
            Evidence(rule=f"corr_{c['key']}", detail=f"r={c['r']} over {c['n']} paired days", weight=w)
            for c in stats["correlations"]
        ]
        fired = {e.rule for e in evidence}
        questions = []
        if fired & set(CYCLE_RULES):
            questions = [
                "My cycles have been longer or more variable than usual. What could explain this?",
                "Are there any tests worth considering for my cycle pattern?",
            ]
        return AgentResult(
            agent="health_story",
            status="watch" if fired & set(CYCLE_RULES) else "ok",
            score=round(score, 2),
            headline=_headline(stats, fired),
            evidence=evidence,
            questions_for_doctor=questions,
            charts=[heatmap(ctx)],
            stats=stats,
        )
