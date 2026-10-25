"""Pure rule functions `(ctx, cfg) -> RuleResult`, registered by name. No DB access.
Thresholds live in config/clinical_rules.yaml; rules never hard-code them."""
from collections.abc import Callable
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.schemas import DailyLog, Measurement, RuleResult, UserContext

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "clinical_rules.yaml"
RuleFn = Callable[[UserContext, dict[str, Any]], RuleResult]
RULES: dict[str, RuleFn] = {}


@lru_cache
def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def rule(name: str) -> Callable[[RuleFn], RuleFn]:
    def deco(fn: RuleFn) -> RuleFn:
        RULES[name] = fn
        return fn

    return deco


def evaluate(name: str, ctx: UserContext, cfg: dict[str, Any] | None = None) -> RuleResult:
    return RULES[name](ctx, cfg if cfg is not None else load_config()["rules"][name])


def evaluate_all(ctx: UserContext, names: list[str] | None = None) -> dict[str, RuleResult]:
    return {n: evaluate(n, ctx) for n in (names or list(RULES))}


# helpers ---------------------------------------------------------------------------------------
def _res(cfg: dict[str, Any], fired: bool, evidence: str) -> RuleResult:
    return RuleResult(fired=fired, evidence=evidence, weight=float(cfg["weight"]) if fired else 0.0)


def window(logs: list[DailyLog], days: int) -> list[DailyLog]:
    """Logs in the `days` days ending at the latest log (never wall-clock, so fixtures stay stable)."""
    if not logs:
        return []
    start = max(x.date for x in logs) - timedelta(days=days - 1)
    return [x for x in logs if x.date >= start]


def values(logs: list[DailyLog], field: str) -> list[Any]:
    return [v for x in logs if (v := getattr(x, field)) is not None]


def latest(ctx: UserContext, mtype: str) -> Measurement | None:
    ms = [m for m in ctx.measurements if m.type == mtype]
    return max(ms, key=lambda m: m.date) if ms else None


def cycle_lengths(ctx: UserContext) -> list[int]:
    return [c.length_days for c in ctx.cycles if c.length_days is not None]


def _mean_rule(ctx: UserContext, cfg: dict[str, Any], field: str, label: str) -> RuleResult:
    xs = values(window(ctx.logs, cfg["window_days"]), field)
    if len(xs) < cfg["min_days_logged"]:
        return _res(cfg, False, f"Not enough {label} entries logged ({len(xs)}).")
    m = sum(xs) / len(xs)
    return _res(cfg, m >= cfg["min_mean"], f"Average {label} rating {m:.1f}/3 over {len(xs)} logged days.")


# cycle -----------------------------------------------------------------------------------------
@rule("cycle_long")
def cycle_long(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    ls = cycle_lengths(ctx)
    if len(ls) < cfg["min_cycles"]:
        return _res(cfg, False, "Not enough completed cycles to judge length.")
    n = sum(1 for x in ls if x > cfg["max_normal_days"])
    return _res(cfg, n >= cfg["min_count"],
                f"{n} of {len(ls)} cycles longer than {cfg['max_normal_days']} days "
                f"(average {sum(ls) / len(ls):.0f}).")


@rule("cycle_variability")
def cycle_variability(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    ls = cycle_lengths(ctx)
    if len(ls) < cfg["min_cycles"]:
        return _res(cfg, False, "Not enough completed cycles to judge variability.")
    spread = max(ls) - min(ls)
    return _res(cfg, spread > cfg["max_range_days"],
                f"Cycle lengths ranged {min(ls)}-{max(ls)} days (spread {spread} days).")


# pcos ------------------------------------------------------------------------------------------
@rule("hirsutism_persistent")
def hirsutism_persistent(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    return _mean_rule(ctx, cfg, "hirsutism", "unwanted hair growth")


@rule("acne_persistent")
def acne_persistent(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    return _mean_rule(ctx, cfg, "acne", "acne")


@rule("pco_ultrasound")
def pco_ultrasound(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    on = ctx.profile.ultrasound_pco is True
    return _res(cfg, on, "Ultrasound reported polycystic-appearing ovaries."
                if on else "No ultrasound finding recorded.")


@rule("family_history_pcos")
def family_history_pcos(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    on = any(cfg["keyword"] in h.lower() for h in ctx.profile.family_history)
    return _res(cfg, on, "Family history of PCOS recorded." if on else "No family history of PCOS recorded.")


@rule("bmi_elevated")
def bmi_elevated(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    p = ctx.profile
    if p.is_pregnant or not p.height_cm or not p.weight_kg:
        return _res(cfg, False, "BMI not assessed (pregnant or height/weight missing).")
    bmi = p.weight_kg / (p.height_cm / 100) ** 2
    return _res(cfg, bmi >= cfg["min_bmi"], f"BMI {bmi:.1f} (threshold {cfg['min_bmi']}).")


# endometriosis ---------------------------------------------------------------------------------
@rule("severe_period_pain")
def severe_period_pain(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    n = sum(1 for x in window(ctx.logs, cfg["window_days"]) if (x.pain_level or 0) >= cfg["min_pain"])
    return _res(cfg, n >= cfg["min_days"], f"{n} days with pain rated {cfg['min_pain']}/10 or more.")


@rule("pain_interferes")
def pain_interferes(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    n = sum(1 for x in window(ctx.logs, cfg["window_days"]) if x.pain_interferes)
    return _res(cfg, n >= cfg["min_days"], f"Pain interfered with daily activity on {n} days.")


@rule("dyspareunia_or_bowel_urinary")
def dyspareunia_or_bowel_urinary(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    n = sum(1 for x in window(ctx.logs, cfg["window_days"])
            if x.pain_during_intercourse or x.pain_bowel_urinary)
    return _res(cfg, n >= cfg["min_days"], f"{n} days with pain during intercourse or bowel/urinary pain.")


# menopause -------------------------------------------------------------------------------------
@rule("vasomotor_frequent")
def vasomotor_frequent(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    xs = values(window(ctx.logs, cfg["window_days"]), "hot_flash_count")
    if len(xs) < cfg["min_days_logged"]:
        return _res(cfg, False, "Not enough hot flash entries logged.")
    m = sum(xs) / len(xs)
    return _res(cfg, m >= cfg["min_mean_per_day"],
                f"Average {m:.1f} hot flashes per day over {len(xs)} days.")


@rule("night_sweats_frequent")
def night_sweats_frequent(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    xs = values(window(ctx.logs, cfg["window_days"]), "night_sweats")
    if len(xs) < cfg["min_days_logged"]:
        return _res(cfg, False, "Not enough night sweat entries logged.")
    share = sum(1 for v in xs if v) / len(xs)
    return _res(cfg, share >= cfg["min_share"], f"Night sweats on {share:.0%} of {len(xs)} logged days.")


@rule("sleep_short")
def sleep_short(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    xs = values(window(ctx.logs, cfg["window_days"]), "sleep_hours")
    if len(xs) < cfg["min_days_logged"]:
        return _res(cfg, False, "Not enough sleep entries logged.")
    m = sum(xs) / len(xs)
    return _res(cfg, m < cfg["max_mean_hours"], f"Average sleep {m:.1f} h over {len(xs)} days.")


@rule("perimenopause_age_window")
def perimenopause_age_window(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    a = ctx.age
    ok = a is not None and cfg["min_age"] <= a <= cfg["max_age"]
    return _res(cfg, ok, f"Age {a} is within the usual transition window."
                if ok else "Age is outside the usual transition window.")


# maternal --------------------------------------------------------------------------------------
def _bp_at_least(ctx: UserContext, sys_: float, dia: float) -> tuple[bool, str]:
    m = latest(ctx, "bp")
    if m is None:
        return False, "No blood pressure recorded."
    s, d = m.value_1, m.value_2 or 0
    return s >= sys_ or d >= dia, f"Latest blood pressure {s:.0f}/{d:.0f} mmHg on {m.date}."


@rule("bp_alert")
def bp_alert(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    urgent = load_config()["rules"]["bp_urgent"]
    hit, ev = _bp_at_least(ctx, cfg["systolic"], cfg["diastolic"])
    severe, _ = _bp_at_least(ctx, urgent["systolic"], urgent["diastolic"])
    return _res(cfg, hit and not severe, ev)  # severe range is reported by bp_urgent instead


@rule("bp_urgent")
def bp_urgent(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    hit, ev = _bp_at_least(ctx, cfg["systolic"], cfg["diastolic"])
    return _res(cfg, hit, ev)


@rule("anemia_low_hb")
def anemia_low_hb(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    m = latest(ctx, "hemoglobin")
    if m is None:
        return _res(cfg, False, "No haemoglobin recorded.")
    return _res(cfg, m.value_1 < cfg["max_hb"], f"Latest haemoglobin {m.value_1:.1f} g/dL on {m.date}.")


@rule("low_fetal_movement")
def low_fetal_movement(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    ms = sorted((m for m in ctx.measurements if m.type == "fetal_movement_count"), key=lambda m: m.date)
    recent = [m.value_1 for m in ms[-cfg["recent_counts"]:]]
    if len(recent) < cfg["recent_counts"]:
        return _res(cfg, False, "Not enough movement counts recorded.")
    avg = sum(recent) / len(recent)
    return _res(cfg, avg < cfg["min_kicks_per_2h"],
                f"Average {avg:.1f} movements per 2 h over the last {len(recent)} counts.")


@rule("swelling_with_headache")
def swelling_with_headache(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    n = sum(1 for x in window(ctx.logs, cfg["window_days"])
            if (x.swelling or 0) >= cfg["min_level"] and (x.headache or 0) >= cfg["min_level"])
    return _res(cfg, ctx.profile.is_pregnant and n >= cfg["min_days"],
                f"Swelling and headache both rated {cfg['min_level']}+ on {n} of the last "
                f"{cfg['window_days']} days.")


@rule("anemia_severe")
def anemia_severe(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    m = latest(ctx, "hemoglobin")
    if m is None or not ctx.profile.is_pregnant:
        return _res(cfg, False, "No haemoglobin recorded.")
    return _res(cfg, m.value_1 < cfg["max_hb"], f"Latest haemoglobin {m.value_1:.1f} g/dL on {m.date}.")


@rule("rapid_weight_gain")
def rapid_weight_gain(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    ms = sorted((m for m in ctx.measurements if m.type == "weight"), key=lambda m: m.date)
    if len(ms) < 2:
        return _res(cfg, False, "Not enough weight readings recorded.")
    last = ms[-1]
    first = next((m for m in ms if (last.date - m.date).days <= cfg["window_days"]), ms[-2])
    days = (last.date - first.date).days
    if days < 7:
        return _res(cfg, False, "Weight readings are too close together to compare.")
    rate = (last.value_1 - first.value_1) / days * 7
    return _res(cfg, ctx.profile.is_pregnant and rate > cfg["max_kg_per_week"],
                f"Weight changed {rate:+.1f} kg per week over the last {days} days.")


def anc_progress(ctx: UserContext, cfg: dict[str, Any]) -> tuple[int, int]:
    """(contacts due by the current gestational week, visits recorded)."""
    wk = ctx.gestational_week or 0
    due = sum(1 for w in cfg["schedule_weeks"] if w <= wk)
    return due, sum(1 for m in ctx.measurements if m.type == "anc_visit")


@rule("anc_missed")
def anc_missed(ctx: UserContext, cfg: dict[str, Any]) -> RuleResult:
    due, done = anc_progress(ctx, cfg)
    return _res(cfg, ctx.profile.is_pregnant and done < due,
                f"{done} antenatal visits recorded; about {due} are usually due by week "
                f"{ctx.gestational_week}.")
