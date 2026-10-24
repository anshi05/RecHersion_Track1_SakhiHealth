"""Deterministic log/measurement generators. Shape depends only on day index and
random.Random(persona_seed); only the calendar dates move with the anchor."""
import random
from datetime import date, timedelta
from typing import Any

from app.seed.personas import PersonaSpec

LogRow = dict[str, Any]
MeasRow = dict[str, Any]

FLOW_SHAPE = ["light", "medium", "heavy", "medium", "light"]


def _c(v: float, lo: int, hi: int) -> int:
    return max(lo, min(hi, round(v)))


def _base(d: date) -> LogRow:
    return {"date": d, "flow": "none", "pain_location": [], "danger_signs": []}


def _m(anchor: date, ago: int, typ: str, v1: float, v2: float | None, unit: str) -> MeasRow:
    return {"date": anchor - timedelta(days=ago), "type": typ, "value_1": v1, "value_2": v2, "unit": unit}


def _priya(rng: random.Random, spec: PersonaSpec, anchor: date) -> tuple[list[LogRow], list[MeasRow]]:
    n = spec.days
    # Period starts at day indexes 5, 53, 102, 150, 199-... -> cycle lengths 48, 49, 48, 48.
    starts = [5, 53, 102, 150, 198]
    period_day: dict[int, int] = {}
    for s in starts:
        for k in range(5):
            if s + k < n:
                period_day[s + k] = k
    logs: list[LogRow] = []
    for i in range(n):
        r = _base(anchor - timedelta(days=n - 1 - i))
        pd = period_day.get(i)
        if pd is not None:
            r["flow"] = FLOW_SHAPE[pd]
        elif period_day.get(i + 1) == 0 and rng.random() < 0.5:
            r["flow"] = "spotting"
        on = pd is not None
        r["pain_level"] = _c((5 if on else 1) + rng.gauss(0, 1.2), 0, 10)
        if on and r["pain_level"] >= 5:
            r["pain_location"] = ["lower_abdomen"]
        r["mood"] = _c(3 + rng.gauss(0, 0.9) - (0.5 if on else 0), 1, 5)
        r["energy"] = _c(3 + rng.gauss(0, 0.9), 1, 5)
        r["sleep_hours"] = round(max(4.5, min(9.0, 6.6 + rng.gauss(0, 0.8))), 1)
        r["sleep_quality"] = _c(3 + rng.gauss(0, 0.9), 1, 5)
        r["stress"] = _c(3.4 + rng.gauss(0, 0.9), 1, 5)
        r["fatigue"] = _c(2.8 + rng.gauss(0, 0.9), 1, 5)
        r["acne"] = _c(2.1 + rng.gauss(0, 0.7), 0, 3)
        r["hirsutism"] = _c(1.8 + rng.gauss(0, 0.6), 0, 3)
        r["hair_thinning"] = _c(1.3 + rng.gauss(0, 0.7), 0, 3)
        r["bloating"] = rng.random() < 0.35
        r["headache"] = _c(0.6 + rng.gauss(0, 0.8), 0, 3)
        logs.append(r)
    meas = [
        _m(anchor, 89, "weight", 71.2, None, "kg"),
        _m(anchor, 59, "weight", 71.8, None, "kg"),
        _m(anchor, 29, "weight", 72.1, None, "kg"),
        _m(anchor, 0, "weight", 72.4, None, "kg"),
        _m(anchor, 20, "glucose", 98.0, None, "mg/dL"),
    ]
    return logs, meas


def _meena(rng: random.Random, spec: PersonaSpec, anchor: date) -> tuple[list[LogRow], list[MeasRow]]:
    n = spec.days
    starts = [4, 30, 71]  # irregular gaps (26, 41 days), heavier flow
    shape = ["medium", "heavy", "heavy", "medium", "light", "light"]
    period_day: dict[int, int] = {}
    for s in starts:
        for k in range(6):
            if s + k < n:
                period_day[s + k] = k
    logs: list[LogRow] = []
    for i in range(n):
        r = _base(anchor - timedelta(days=n - 1 - i))
        pd = period_day.get(i)
        if pd is not None:
            r["flow"] = shape[pd]
        trend = i / n  # symptoms worsen gently over the window
        r["pain_level"] = _c((3 if pd is not None else 0.6) + rng.gauss(0, 1), 0, 10)
        r["mood"] = _c(2.9 - 0.4 * trend + rng.gauss(0, 0.8), 1, 5)
        r["energy"] = _c(2.7 + rng.gauss(0, 0.8), 1, 5)
        r["sleep_hours"] = round(max(3.5, min(8.5, 5.4 + rng.gauss(0, 0.9))), 1)
        r["sleep_quality"] = _c(2.2 + rng.gauss(0, 0.8), 1, 5)
        r["stress"] = _c(3.2 + rng.gauss(0, 0.9), 1, 5)
        r["fatigue"] = _c(3.5 + rng.gauss(0, 0.8), 1, 5)
        r["hot_flash_count"] = max(0, round(3.0 + 2.0 * trend + rng.gauss(0, 1.5)))
        r["night_sweats"] = rng.random() < 0.55
        r["palpitations"] = rng.random() < 0.2
        r["vaginal_dryness"] = rng.random() < 0.5
        r["joint_pain"] = rng.random() < 0.55
        r["brain_fog"] = rng.random() < 0.5
        r["breast_tenderness"] = rng.random() < 0.2
        r["hair_thinning"] = _c(1.0 + rng.gauss(0, 0.6), 0, 3)
        r["headache"] = _c(0.8 + rng.gauss(0, 0.8), 0, 3)
        logs.append(r)
    meas = [
        _m(anchor, 60, "bp", 126.0, 82.0, "mmHg"),
        _m(anchor, 2, "bp", 128.0, 84.0, "mmHg"),
        _m(anchor, 30, "tsh", 2.6, None, "mIU/L"),
        _m(anchor, 60, "weight", 63.0, None, "kg"),
        _m(anchor, 1, "weight", 64.2, None, "kg"),
    ]
    return logs, meas


def _sunita(rng: random.Random, spec: PersonaSpec, anchor: date) -> tuple[list[LogRow], list[MeasRow]]:
    n = spec.days
    logs: list[LogRow] = []
    for i in range(n):
        r = _base(anchor - timedelta(days=n - 1 - i))
        t = i / (n - 1)
        r["pain_level"] = _c(1 + 1.5 * t + rng.gauss(0, 0.8), 0, 10)
        r["mood"] = _c(3.4 + rng.gauss(0, 0.8), 1, 5)
        r["energy"] = _c(3.0 - 0.5 * t + rng.gauss(0, 0.8), 1, 5)
        r["sleep_hours"] = round(max(4.5, min(9.0, 7.0 - 0.8 * t + rng.gauss(0, 0.7))), 1)
        r["sleep_quality"] = _c(3.2 - 0.6 * t + rng.gauss(0, 0.8), 1, 5)
        r["stress"] = _c(2.6 + 0.6 * t + rng.gauss(0, 0.8), 1, 5)
        r["fatigue"] = _c(2.8 + 0.6 * t + rng.gauss(0, 0.8), 1, 5)
        r["nausea"] = rng.random() < max(0.0, 0.4 - 0.4 * t)
        r["headache"] = _c(0.3 + 1.4 * t + rng.gauss(0, 0.6), 0, 3)
        r["swelling"] = _c(0.2 + 1.9 * t + rng.gauss(0, 0.5), 0, 3)
        r["bloating"] = rng.random() < 0.25
        logs.append(r)
    # (days ago, systolic, diastolic): rises gradually and ends at exactly 142/92 (alert, not urgent)
    bp = [(85, 108, 70), (70, 112, 72), (56, 118, 76), (42, 122, 78), (28, 128, 82),
          (14, 134, 86), (7, 138, 90), (0, 142, 92)]
    meas = [_m(anchor, a, "bp", float(s), float(d), "mmHg") for a, s, d in bp]
    meas += [_m(anchor, a, "hemoglobin", v, None, "g/dL") for a, v in ((80, 11.4), (40, 10.6), (3, 10.2))]
    meas += [_m(anchor, a, "weight", w, None, "kg") 
            for a, w in ((85, 60.0), (55, 62.2), (28, 64.0), (0, 66.0))]
    meas += [_m(anchor, a, "anc_visit", float(v), None, "visit") for a, v in ((75, 1), (47, 2), (19, 3))]
    for ago in range(13, -1, -1):
        kicks = float(_c(10 + rng.gauss(0, 1.5), 6, 16))
        meas.append(_m(anchor, ago, "fetal_movement_count", kicks, None, "kicks/2h"))
    return logs, meas


_GEN = {"priya": _priya, "meena": _meena, "sunita": _sunita}


def generate(spec: PersonaSpec, anchor: date) -> tuple[list[LogRow], list[MeasRow]]:
    return _GEN[spec.key](random.Random(spec.seed), spec, anchor)
