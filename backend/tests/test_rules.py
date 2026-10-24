"""Every rule: >=1 fire and >=1 no-fire case on persona fixtures (mutated where no persona fits)."""
from collections.abc import Callable
from dataclasses import replace
from datetime import date

import pytest

from app.schemas import Measurement, UserContext
from app.services.rules import RULES, evaluate, evaluate_all, load_config

Mut = Callable[[UserContext], UserContext]


def same(ctx: UserContext) -> UserContext:
    return ctx


def set_logs(**fields: object) -> Mut:
    """Overwrite fields on every log."""
    return lambda c: replace(c, logs=[x.model_copy(update=fields) for x in c.logs])


def add_meas(typ: str, v1: float, v2: float | None = None, n: int = 1) -> Mut:
    def f(c: UserContext) -> UserContext:
        base = max(m.id for m in c.measurements) + 1 if c.measurements else 1
        extra = [Measurement(id=base + i, user_id=0, date=date(2099, 1, 1 + i), type=typ,  # type: ignore[arg-type]
                             value_1=v1, value_2=v2) for i in range(n)]
        return replace(c, measurements=[*c.measurements, *extra])

    return f


def profile(**fields: object) -> Mut:
    return lambda c: replace(c, profile=c.profile.model_copy(update=fields))


def few_logs(c: UserContext) -> UserContext:
    return replace(c, logs=c.logs[:3])


def no_cycles(c: UserContext) -> UserContext:
    return replace(c, cycles=[])


def pregnant(c: UserContext) -> UserContext:
    return profile(is_pregnant=True)(c)


def with_age(a: int) -> Mut:
    return lambda c: replace(c, age=a)


# rule -> (fire: (persona, mutation), no-fire: (persona, mutation))
CASES: dict[str, tuple[tuple[str, Mut], tuple[str, Mut]]] = {
    "cycle_long": (("priya", same), ("sunita", same)),
    "cycle_variability": (("meena", same), ("priya", same)),
    "hirsutism_persistent": (("priya", same), ("meena", same)),
    "acne_persistent": (("priya", same), ("sunita", same)),
    "pco_ultrasound": (("priya", same), ("meena", same)),
    "family_history_pcos": (("priya", same), ("meena", same)),
    "bmi_elevated": (("priya", same), ("sunita", same)),
    "severe_period_pain": (("priya", same), ("meena", same)),
    "pain_interferes": (("meena", set_logs(pain_interferes=True)), ("priya", same)),
    "dyspareunia_or_bowel_urinary": (("priya", set_logs(pain_bowel_urinary=True)), ("meena", same)),
    "vasomotor_frequent": (("meena", same), ("priya", same)),
    "night_sweats_frequent": (("meena", same), ("sunita", same)),
    "sleep_short": (("meena", same), ("priya", same)),
    "perimenopause_age_window": (("meena", same), ("priya", same)),
    "bp_alert": (("sunita", same), ("meena", same)),
    "bp_urgent": (("sunita", add_meas("bp", 162, 112)), ("sunita", same)),
    "anemia_low_hb": (("sunita", same), ("sunita", add_meas("hemoglobin", 12.5))),
    "low_fetal_movement": (("sunita", add_meas("fetal_movement_count", 5, n=3)), ("sunita", same)),
    "swelling_with_headache": (("sunita", same), ("priya", pregnant)),
}


def test_every_rule_has_cases_and_config() -> None:
    cfg = load_config()["rules"]
    assert set(RULES) == set(CASES) == set(cfg)
    for name, c in cfg.items():
        assert c.get("source"), f"{name} missing source"
        assert isinstance(c.get("weight"), (int, float))


@pytest.mark.parametrize("name", sorted(CASES))
def test_rule_fires(name: str, personas: dict[str, UserContext]) -> None:
    persona, mut = CASES[name][0]
    r = evaluate(name, mut(personas[persona]))
    assert r.fired, r.evidence
    assert r.weight == load_config()["rules"][name]["weight"]
    assert r.evidence


@pytest.mark.parametrize("name", sorted(CASES))
def test_rule_does_not_fire(name: str, personas: dict[str, UserContext]) -> None:
    persona, mut = CASES[name][1]
    r = evaluate(name, mut(personas[persona]))
    assert not r.fired, r.evidence
    assert r.weight == 0


def test_insufficient_data_never_fires(personas: dict[str, UserContext]) -> None:
    ctx = no_cycles(few_logs(personas["priya"]))
    for name in ("cycle_long", "cycle_variability", "hirsutism_persistent", "vasomotor_frequent"):
        assert not evaluate(name, ctx).fired


def test_bp_alert_excludes_severe_range(personas: dict[str, UserContext]) -> None:
    ctx = add_meas("bp", 165, 112)(personas["sunita"])
    assert evaluate("bp_urgent", ctx).fired
    assert not evaluate("bp_alert", ctx).fired


def test_persona_profiles(personas: dict[str, UserContext]) -> None:
    fired = {k: {n for n, r in evaluate_all(c).items() if r.fired} for k, c in personas.items()}
    assert {"cycle_long", "hirsutism_persistent", "pco_ultrasound"} <= fired["priya"]
    assert {"vasomotor_frequent", "perimenopause_age_window"} <= fired["meena"]
    assert {"bp_alert", "anemia_low_hb"} <= fired["sunita"]
    assert "bp_urgent" not in fired["sunita"]
