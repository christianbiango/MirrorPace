from __future__ import annotations

from src.qa_agent.profiles.anxious_beginner import PROFILE as ANXIOUS_BEGINNER
from src.qa_agent.profiles.ambitious_marathoner import PROFILE as AMBITIOUS_MARATHONER
from src.qa_agent.profiles.injured_runner import PROFILE as INJURED_RUNNER
from src.qa_agent.profiles.cautious_runner import PROFILE as CAUTIOUS_RUNNER
from src.qa_agent.profiles.busy_parent import PROFILE as BUSY_PARENT
from src.qa_agent.profiles.performance_obsessed import PROFILE as PERFORMANCE_OBSESSED

ALL_PROFILES = [
    ANXIOUS_BEGINNER,
    AMBITIOUS_MARATHONER,
    INJURED_RUNNER,
    CAUTIOUS_RUNNER,
    BUSY_PARENT,
    PERFORMANCE_OBSESSED,
]

PROFILES_BY_ID = {p.id: p for p in ALL_PROFILES}
