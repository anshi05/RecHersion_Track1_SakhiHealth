"""Health Story statistics: cycle stats, phase-wise symptom frequency, trends, correlations,
last-14 vs previous-14 deltas. Pure functions over a UserContext; thresholds from the YAML `stats:` block."""
from datetime import date, timedelta
from typing import Any

import numpy as np

from app.schemas import DailyLog, UserContext
from app.services.rules import cycle_lengths, load_config, values

METRICS = ["mood", "energy", "sleep_hours", "pain_level", "stress", "fatigue"]
MAX_CYCLE_DAY = 60
PHASES = ["menstrual", "follicular", "ovulatory", "luteal"]


def cycle_day_map(ctx: UserContext) -> dict[date, int]:
    """1-based day within the cycle for each log date (None-equivalent: absent)."""
    starts = sorted(c.start_date for c in ctx.cycles)
    out: dict[date, int] = {}
    for x in ctx.logs:
        prior = [s for s in starts if s <= x.date]
        if prior and (d := (x.date - prior[-1]).days + 1) <= MAX_CYCLE_DAY:
            out[x.date] = d
    return out


def phase_of(day: int, cfg: dict[str, Any]) -> str:
    p = cfg["phases"]
    if day <= p["menstrual"]:
        return "menstrual"
    if day <= p["follicular"]:
        return "follicular"
    return "ovulatory" if day <= p["ovulatory"] else "luteal"


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or np.std(xs) == 0 or np.std(ys) == 0:
        return None
    return float(np.corrcoef(xs, ys)[0, 1])


def cycle_stats(ctx: UserContext) -> dict[str, Any]:
    ls = cycle_lengths(ctx)
    if not ls:
        return {"count": 0, "lengths": []}
    return {
        "count": len(ls), "lengths": ls, "mean": round(float(np.mean(ls)), 1),
        "min": min(ls), "max": max(ls), "sd": round(float(np.std(ls)), 1),
        "last_start": max(c.start_date for c in ctx.cycles).isoformat(),
    }


def phase_frequency(ctx: UserContext, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    days = cycle_day_map(ctx)
    rows: list[dict[str, Any]] = []
    for phase in PHASES:
        in_phase = [x for x in ctx.logs if x.date in days and phase_of(days[x.date], cfg) == phase]
        if not in_phase:
            continue
        for sym, rule in cfg["phase_symptoms"].items():
            vals = values(in_phase, rule["field"])
            if not vals:
                continue
            hit = sum(1 for v in vals
                      if ("min" in rule and v >= rule["min"]) or ("max" in rule and v <= rule["max"]))
            rows.append({"phase": phase, "symptom": sym, "pct": round(100 * hit / len(vals)), "n": len(vals)})
    return rows


def trends(logs: list[DailyLog], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for m in METRICS:
        pts = [((x.date - logs[0].date).days, getattr(x, m)) for x in logs if getattr(x, m) is not None]
        if len(pts) < cfg["min_pairs"]:
            continue
        xs, ys = zip(*pts, strict=True)
        change = float(np.polyfit(xs, ys, 1)[0] * (xs[-1] - xs[0]))
        direction = "up" if change >= cfg["min_delta"] else "down" if change <= -cfg["min_delta"] else "flat"
        out.append({"metric": m, "change": round(change, 2), "direction": direction})
    return out


def deltas(logs: list[DailyLog], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    if not logs:
        return []
    n, end = cfg["delta_days"], max(x.date for x in logs)
    recent = [x for x in logs if x.date > end - timedelta(days=n)]
    prev = [x for x in logs if end - timedelta(days=2 * n) < x.date <= end - timedelta(days=n)]
    out = []
    for m in METRICS:
        a, b = values(recent, m), values(prev, m)
        if a and b:
            d = float(np.mean(a) - np.mean(b))
            out.append({"metric": m, "recent": round(float(np.mean(a)), 2),
                        "previous": round(float(np.mean(b)), 2), "delta": round(d, 2),
                        "notable": abs(d) >= cfg["min_delta"]})
    return out


def correlations(ctx: UserContext, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    by_date = {x.date: x for x in ctx.logs}
    days = cycle_day_map(ctx)
    pairs: dict[str, list[tuple[float, float]]] = {
        "sleep_next_day_mood": [
            (x.sleep_hours, n.mood)
            for x in ctx.logs
            if x.sleep_hours is not None
            and (n := by_date.get(x.date + timedelta(days=1))) and n.mood is not None
        ],
        "pain_cycle_day": [(days[x.date], x.pain_level) for x in ctx.logs
                           if x.date in days and x.pain_level is not None],
        "stress_headache": [(x.stress, x.headache) for x in ctx.logs
                            if x.stress is not None and x.headache is not None],
    }
    out = []
    for key, ps in pairs.items():
        if len(ps) < cfg["min_pairs"]:
            continue
        r = pearson([p[0] for p in ps], [p[1] for p in ps])
        if r is not None and abs(r) >= cfg["min_corr"]:
            out.append({"key": key, "r": round(r, 2), "n": len(ps)})
    return out


def compute_stats(ctx: UserContext) -> dict[str, Any]:
    cfg = load_config()["stats"]
    logs = sorted(ctx.logs, key=lambda x: x.date)
    return {
        "cycle": cycle_stats(ctx),
        "phase_frequency": phase_frequency(ctx, cfg),
        "trends": trends(logs, cfg),
        "deltas": deltas(logs, cfg),
        "correlations": correlations(ctx, cfg),
        "days_logged": len(logs),
    }
