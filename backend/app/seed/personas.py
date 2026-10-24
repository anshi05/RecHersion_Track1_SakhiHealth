"""Persona definitions (brief 4/14). Static data only; dates are derived from the anchor."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PersonaSpec:
    key: str
    seed: int
    name: str
    age: int
    life_stage: str
    tagline: str
    days: int  # days of history ending at the anchor
    region: str
    height_cm: float
    weight_kg: float
    is_pregnant: bool = False
    gestation_weeks: int | None = None  # at anchor
    known_conditions: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    family_history: list[str] = field(default_factory=list)
    ultrasound_pco: bool | None = None
    language: str = "en"


PERSONAS: dict[str, PersonaSpec] = {
    "priya": PersonaSpec(
        key="priya", seed=1101, name="Priya", age=24, life_stage="reproductive",
        tagline="Irregular cycles, acne and unwanted hair for a while now",
        days=200, region="Delhi", height_cm=160, weight_kg=72,
        family_history=["pcos"], ultrasound_pco=True,
    ),
    "meena": PersonaSpec(
        key="meena", seed=2202, name="Meena", age=47, life_stage="perimenopausal",
        tagline="Hot flashes, poor sleep and cycles that keep changing",
        days=90, region="Pune", height_cm=156, weight_kg=64,
    ),
    "sunita": PersonaSpec(
        key="sunita", seed=3303, name="Sunita", age=28, life_stage="pregnant",
        tagline="28 weeks pregnant, tracking blood pressure and baby movements",
        days=90, region="Patna", height_cm=158, weight_kg=66,
        is_pregnant=True, gestation_weeks=28,
    ),
}
