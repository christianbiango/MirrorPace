"""Run the full coaching pipeline and store results in the session."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.coach_intelligence.api import build_coach_response
from src.coach_intelligence.assembler.response_assembler import LLMClient
from src.coach_intelligence.domain.schemas.coach_response import CoachResponse
from src.coach_intelligence.rag.context.retriever import RunnerContextRetriever
from src.database.repository import ActivityRepository
from src.knowledge_engine.api import (
    DecisionEnvelope,
    EngineConfig,
    RunnerState,
    load_default_config,
    run_engine,
)
from src.knowledge_engine.domain.schemas.runner_state import PlanContext, RunnerProfile
from src.runner_memory.domain import CoachingDecision
from src.runner_memory.indexer import build_runner_context_store
from src.runner_memory.store import MemoryStore
from src.runner_memory.writer import MemoryWriter
from src.runner_model.builder import build_snapshot
from src.runner_model.profile_store import RunnerProfileStore
from src.runner_model.state_builder import build_runner_state

# Mirrors the phase/weeks_to_race bands the readiness formula already assumes
# (_phase_coherence_component in domain/formulas/readiness.py) — keeping the
# derivation consistent with what the KE itself considers coherent.
_SPECIFIC_MARATHON_MAX_WEEKS = 12


def weeks_to_race(profile: RunnerProfile, reference_date: date) -> int | None:
    """Weeks remaining until profile.race_target_date, or None if unset/past."""
    if not profile.race_target_date:
        return None
    race_date = date.fromisoformat(profile.race_target_date)
    days = (race_date - reference_date).days
    if days < 0:
        return None
    return days // 7


def derive_current_phase(weeks_out: int | None, cfg: EngineConfig) -> str:
    """Auto-derive the training phase from weeks_to_race so RULE-021 (taper) and
    the GF-07 taper safety invariant can actually fire — previously current_phase
    always defaulted to "general" and never changed."""
    if weeks_out is None:
        return "general"
    if weeks_out <= cfg.get("taper_duration_weeks"):
        return "taper"
    if weeks_out <= _SPECIFIC_MARATHON_MAX_WEEKS:
        return "specific_marathon"
    return "general"


def build_plan_context(profile: RunnerProfile, cfg: EngineConfig, reference_date: date) -> PlanContext:
    weeks_out = weeks_to_race(profile, reference_date)
    return PlanContext(
        current_phase=derive_current_phase(weeks_out, cfg),
        weeks_to_race=weeks_out,
    )


@dataclass
class AnalysisResult:
    coach_response: CoachResponse
    envelope: DecisionEnvelope
    state: RunnerState
    decision_record: CoachingDecision
    runner_id: str


class AnalysisHandler:
    def __init__(
        self,
        llm_client: LLMClient,
        memory_store: MemoryStore,
        activity_repo: ActivityRepository,
        profile_store: RunnerProfileStore,
        engine_config: EngineConfig | None = None,
    ) -> None:
        self._llm = llm_client
        self._memory_store = memory_store
        self._repo = activity_repo
        self._profile_store = profile_store
        self._config = engine_config or load_default_config()

    def handle(self) -> AnalysisResult:
        # 1. Load activities — single-read pattern (D-008)
        activities = self._repo.get_all()
        if not activities:
            raise RuntimeError("No activities in database. Run import_strava.py first.")

        # 2. Build snapshot and state
        runner_id, profile = self._profile_store.load()
        reference_date = date.today()
        plan_context = build_plan_context(profile, self._config, reference_date)
        snapshot = build_snapshot(activities)
        state = build_runner_state(
            activities, profile, runner_id,
            plan_context=plan_context,
            reference_date=reference_date,
        )

        # 3. Knowledge Engine decision
        envelope = run_engine(state, self._config)

        # 4. Record in memory before CI (D-013)
        decision_record = MemoryWriter(store=self._memory_store).record(envelope, state)

        # 5. Build context retriever from updated memory
        context_store = build_runner_context_store(runner_id, self._memory_store)
        context_retriever = RunnerContextRetriever(store=context_store)

        # 6. Coach Intelligence
        coach_response = build_coach_response(
            envelope, snapshot, state,
            llm_client=self._llm,
            context_retriever=context_retriever,
        )

        return AnalysisResult(
            coach_response=coach_response,
            envelope=envelope,
            state=state,
            decision_record=decision_record,
            runner_id=runner_id,
        )
