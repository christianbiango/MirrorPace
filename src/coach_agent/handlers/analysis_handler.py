"""Run the full coaching pipeline and store results in the session."""

from __future__ import annotations

from dataclasses import dataclass

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
from src.runner_memory.domain import CoachingDecision
from src.runner_memory.indexer import build_runner_context_store
from src.runner_memory.store import MemoryStore
from src.runner_memory.writer import MemoryWriter
from src.runner_model.builder import build_snapshot
from src.runner_model.profile_store import RunnerProfileStore
from src.runner_model.state_builder import build_runner_state


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
        snapshot = build_snapshot(activities)
        state = build_runner_state(activities, profile, runner_id)

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
