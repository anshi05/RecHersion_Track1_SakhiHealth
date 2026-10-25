from datetime import timedelta

import pytest

from app.agents.orchestrator import orchestrate, route
from app.agents.pcos_endo import PcosEndo
from app.schemas import UserContext

EXPECTED = {
    "priya": ["health_story", "pcos_endo"],
    "meena": ["health_story", "menopause"],
    "sunita": ["health_story", "maternal"],
}


@pytest.mark.parametrize("key", EXPECTED)
def test_routing_snapshot(personas: dict[str, UserContext], key: str) -> None:
    r = route(personas[key])
    assert r.activated == EXPECTED[key]
    assert not r.urgent
    everyone = {"health_story", "maternal", "menopause", "pcos_endo"}
    assert {s.agent for s in r.skipped} == everyone - set(EXPECTED[key])
    assert all(s.reason for s in r.skipped)


def test_meena_pcos_skipped_with_reason(personas: dict[str, UserContext]) -> None:
    r = route(personas["meena"])
    reason = next(s.reason for s in r.skipped if s.agent == "pcos_endo")
    assert "menopause transition" in reason


def test_urgent_bp_sets_flag_but_still_returns_story(personas: dict[str, UserContext]) -> None:
    ctx = personas["sunita"]
    m = ctx.measurements[0].model_copy(update={"type": "bp", "value_1": 165, "value_2": 112,
                                              "date": ctx.measurements[-1].date + timedelta(days=1)})
    urgent = UserContext(**{**ctx.__dict__, "measurements": [*ctx.measurements, m]})
    routing, results, _ = orchestrate(urgent)
    assert routing.urgent and routing.urgent_reasons
    assert results[0].agent == "health_story"


def test_priya_pcos_band_and_evidence(personas: dict[str, UserContext]) -> None:
    r = PcosEndo().run(personas["priya"])
    assert r.band in ("moderate", "high") and r.status in ("watch", "flag")
    assert len(r.evidence) >= 3 and all(e.rule and e.detail for e in r.evidence)
    assert {c.id for c in r.charts} == {"pcos_gauge", "endo_gauge"}
    assert any(c.key == "exclusions" for c in r.cards)
    assert any(c.key == "diagnostic_delay" for c in r.cards)
    assert r.specialist and r.suggested_tests


def test_pcos_low_band_has_no_navigation(personas: dict[str, UserContext]) -> None:
    ctx = personas["priya"]
    bare = ctx.profile.model_copy(
        update={"ultrasound_pco": None, "family_history": [], "height_cm": None, "weight_kg": None}
    )
    quiet = UserContext(**{**ctx.__dict__, "logs": [], "cycles": [], "measurements": [], "profile": bare})
    r = PcosEndo().run(quiet)
    assert r.band == "low" and r.specialist is None and r.questions_for_doctor == []
    assert any(c.key == "exclusions" for c in r.cards)

