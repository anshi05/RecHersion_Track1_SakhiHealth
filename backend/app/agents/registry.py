"""Agent registry, in routing order."""
from app.agents.base import Agent
from app.agents.health_story import HealthStory
from app.agents.maternal import Maternal
from app.agents.menopause import Menopause
from app.agents.pcos_endo import PcosEndo

AGENTS: dict[str, Agent] = {a.name: a for a in (HealthStory(), Maternal(), Menopause(), PcosEndo())}
