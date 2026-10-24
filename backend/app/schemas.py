"""Pydantic API models (guide 4). Single Python source of truth."""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AgentName = Literal["health_story", "pcos_endo", "menopause", "maternal"]
Status = Literal["ok", "watch", "flag", "urgent"]
Lang = Literal["en", "hi"]
Flow = Literal["none", "spotting", "light", "medium", "heavy"]
LifeStage = Literal["reproductive", "pregnant", "perimenopausal", "postmenopausal", "unknown"]
MeasurementType = Literal[
    "bp", "hemoglobin", "weight", "glucose", "fetal_movement_count", "tsh", "anc_visit"
]


class Evidence(BaseModel):
    rule: str
    detail: str
    weight: float


class RuleResult(BaseModel):
    fired: bool
    evidence: str
    weight: float


class ChartSpec(BaseModel):
    id: str
    kind: Literal["line", "bar", "heatmap", "gauge", "radar", "band"]
    title_key: str
    data: list[dict[str, Any]] = []
    meta: dict[str, Any] | None = None


class Card(BaseModel):
    key: str
    title: str
    body: str


class AgentResult(BaseModel):
    agent: AgentName
    status: Status
    score: float = 0
    band: str | None = None
    headline: str
    evidence: list[Evidence] = []
    suggested_tests: list[str] = []
    specialist: str | None = None
    questions_for_doctor: list[str] = []
    charts: list[ChartSpec] = []
    cards: list[Card] = []
    disclaimer_key: Literal["not_a_diagnosis", "emergency"] = "not_a_diagnosis"
    text_source: Literal["llm", "template"] = "template"
    stats: dict[str, Any] = {}  # computed facts (cycle stats, correlations, deltas) for dashboards


class ApplicabilityResult(BaseModel):
    applies: bool
    reason: str
    dominance: float = 0


class Skipped(BaseModel):
    agent: AgentName
    reason: str


class RoutingDecision(BaseModel):
    activated: list[AgentName]
    skipped: list[Skipped] = []
    reasons: dict[str, str] = {}
    urgent: bool = False
    urgent_reasons: list[str] = []


class Summary(BaseModel):
    text: str
    source: Literal["llm", "template"]


class AnalyzeResponse(BaseModel):
    run_id: int
    ran_at: str
    routing: RoutingDecision
    results: list[AgentResult]
    summary: Summary


class ProfileBase(BaseModel):
    persona_key: str | None = None
    name: str = ""
    dob: date | None = None
    language: Lang = "en"
    life_stage: LifeStage = "unknown"
    is_pregnant: bool = False
    lmp_date: date | None = None
    edd_date: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    known_conditions: list[str] = []
    medications: list[str] = []
    family_history: list[str] = []
    ultrasound_pco: bool | None = None
    region: str | None = None


class Profile(ProfileBase):
    id: int
    age: int | None = None  # derived from dob
    created_at: datetime | None = None


class ProfileUpdate(BaseModel):
    """Partial<Profile>: only provided fields are applied."""

    name: str | None = None
    dob: date | None = None
    language: Lang | None = None
    life_stage: LifeStage | None = None
    is_pregnant: bool | None = None
    lmp_date: date | None = None
    edd_date: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    known_conditions: list[str] | None = None
    medications: list[str] | None = None
    family_history: list[str] | None = None
    ultrasound_pco: bool | None = None
    region: str | None = None


class DailyLogIn(BaseModel):
    date: date
    flow: Flow = "none"
    pain_level: int | None = Field(default=None, ge=0, le=10)
    pain_location: list[str] = []
    pain_interferes: bool | None = None
    mood: int | None = Field(default=None, ge=1, le=5)
    energy: int | None = Field(default=None, ge=1, le=5)
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    stress: int | None = Field(default=None, ge=1, le=5)
    fatigue: int | None = Field(default=None, ge=1, le=5)
    acne: int | None = Field(default=None, ge=0, le=3)
    hirsutism: int | None = Field(default=None, ge=0, le=3)
    hair_thinning: int | None = Field(default=None, ge=0, le=3)
    bloating: bool | None = None
    headache: int | None = Field(default=None, ge=0, le=3)
    nausea: bool | None = None
    hot_flash_count: int | None = Field(default=None, ge=0)
    night_sweats: bool | None = None
    palpitations: bool | None = None
    vaginal_dryness: bool | None = None
    joint_pain: bool | None = None
    brain_fog: bool | None = None
    breast_tenderness: bool | None = None
    discharge_type: str | None = None
    pain_during_intercourse: bool | None = None
    pain_bowel_urinary: bool | None = None
    swelling: int | None = Field(default=None, ge=0, le=3)
    danger_signs: list[str] = []
    notes: str | None = None
    voice_transcript: str | None = None


class DailyLog(DailyLogIn):
    id: int
    user_id: int


class CycleEvent(BaseModel):
    id: int
    user_id: int
    start_date: date
    end_date: date | None = None
    length_days: int | None = None
    flow_summary: str | None = None


class DayPoint(BaseModel):
    date: date
    flow: Flow = "none"
    pain_level: int | None = None
    mood: int | None = None
    energy: int | None = None
    sleep_hours: float | None = None
    stress: int | None = None
    cycle_day: int | None = None


class Marker(BaseModel):
    date: date
    kind: Literal["period_start", "measurement"]
    label: str


class TimelineResponse(BaseModel):
    cycles: list[CycleEvent]
    days: list[DayPoint]
    markers: list[Marker]


class MeasurementIn(BaseModel):
    date: date
    type: MeasurementType
    value_1: float
    value_2: float | None = None
    unit: str = ""


class Measurement(MeasurementIn):
    id: int
    user_id: int


class LogResponse(BaseModel):
    log: DailyLog
    analysis: AnalyzeResponse | None = None  # None until Phase 5 orchestrator


class MeasurementResponse(BaseModel):
    measurement: Measurement
    analysis: AnalyzeResponse | None = None  # None until Phase 5 orchestrator


@dataclass(frozen=True)
class UserContext:
    profile: Profile
    age: int | None
    lang: str
    logs: list[DailyLog]
    cycles: list[CycleEvent]
    measurements: list[Measurement]
    gestational_week: int | None = None


class Persona(BaseModel):
    key: str
    name: str
    age: int
    life_stage: LifeStage
    tagline: str


class SwitchRequest(BaseModel):
    persona_key: str


class SwitchResponse(BaseModel):
    profile: Profile
    analysis: AnalyzeResponse | None = None  # None until Phase 5 orchestrator


class SessionResponse(BaseModel):
    profile: Profile
