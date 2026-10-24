"""SQLModel tables (guide 3.1)."""
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    persona_key: str | None = None
    name: str = ""
    dob: date | None = None
    language: str = "en"
    life_stage: str = "unknown"
    is_pregnant: bool = False
    lmp_date: date | None = None
    edd_date: date | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    known_conditions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    medications: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    family_history: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    ultrasound_pco: bool | None = None
    region: str | None = None
    created_at: datetime = Field(default_factory=_now)


class DailyLog(SQLModel, table=True):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_log_user_date"),)
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    date: date
    flow: str = "none"
    pain_level: int | None = None
    pain_location: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    pain_interferes: bool | None = None
    mood: int | None = None
    energy: int | None = None
    sleep_hours: float | None = None
    sleep_quality: int | None = None
    stress: int | None = None
    fatigue: int | None = None
    acne: int | None = None
    hirsutism: int | None = None
    hair_thinning: int | None = None
    bloating: bool | None = None
    headache: int | None = None
    nausea: bool | None = None
    hot_flash_count: int | None = None
    night_sweats: bool | None = None
    palpitations: bool | None = None
    vaginal_dryness: bool | None = None
    joint_pain: bool | None = None
    brain_fog: bool | None = None
    breast_tenderness: bool | None = None
    discharge_type: str | None = None
    pain_during_intercourse: bool | None = None
    pain_bowel_urinary: bool | None = None
    swelling: int | None = None
    danger_signs: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    notes: str | None = None
    voice_transcript: str | None = None


class CycleEvent(SQLModel, table=True):
    __tablename__ = "cycle_events"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    start_date: date
    end_date: date | None = None
    length_days: int | None = None
    flow_summary: str | None = None


class Measurement(SQLModel, table=True):
    __tablename__ = "measurements"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    date: date
    type: str
    value_1: float
    value_2: float | None = None
    unit: str = ""


class AgentRun(SQLModel, table=True):
    __tablename__ = "agent_runs"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    run_at: datetime = Field(default_factory=_now)
    orchestrator_decision: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    results: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))


class Report(SQLModel, table=True):
    __tablename__ = "reports"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    generated_at: datetime = Field(default_factory=_now)
    language: str = "en"
    file_path: str = ""
    summary_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))


class LlmCache(SQLModel, table=True):
    __tablename__ = "llm_cache"
    key: str = Field(primary_key=True)
    text: str
    source: str = "template"
    created_at: datetime = Field(default_factory=_now)
