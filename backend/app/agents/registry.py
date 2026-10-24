"""Agent registry. P5 adds the other agents and the orchestrator."""
from app.agents.base import Agent
from app.agents.health_story import HealthStory

AGENTS: dict[str, Agent] = {"health_story": HealthStory()}
