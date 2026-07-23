"""CoachAgent — conversational orchestration layer.

Sits above Coach Intelligence, Knowledge Engine, and Runner Memory.
Does not modify any existing layer.

Flow per turn:
    user_message
        → IntentClassifier.classify()
        → route to handler
        → update session
        → AgentResponse
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.coach_agent.domain.intent import AgentResponse, UserIntent
from src.coach_agent.domain.session import ConversationSession, ConversationTurn
from src.coach_agent.handlers.analysis_handler import AnalysisHandler
from src.coach_agent.handlers.feedback_handler import FeedbackHandler
from src.coach_agent.handlers.followup_handler import FollowupHandler
from src.coach_agent.intent.classifier import IntentClassifier
from src.coach_agent.session.feedback_store import FeedbackStore
from src.coach_agent.session.session_store import SessionStore
from src.coach_intelligence.assembler.response_assembler import LLMClient
from src.database.repository import ActivityRepository
from src.knowledge_engine.api import EngineConfig
from src.runner_memory.store import MemoryStore
from src.runner_model.profile_store import RunnerProfileStore

_UNKNOWN_RUNNER = "default"


class CoachAgent:
    def __init__(
        self,
        llm_client: LLMClient,
        memory_store: MemoryStore,
        activity_repo: ActivityRepository,
        profile_store: RunnerProfileStore,
        feedback_store: FeedbackStore | None = None,
        engine_config: EngineConfig | None = None,
    ) -> None:
        self._profile_store = profile_store
        self._session_store = SessionStore()
        self._classifier = IntentClassifier(llm_client=llm_client)

        self._analysis_handler = AnalysisHandler(
            llm_client=llm_client,
            memory_store=memory_store,
            activity_repo=activity_repo,
            profile_store=profile_store,
            engine_config=engine_config,
        )
        self._followup_handler = FollowupHandler(
            llm_client=llm_client,
            memory_store=memory_store,
        )
        self._feedback_handler = FeedbackHandler(
            feedback_store=feedback_store or FeedbackStore(),
        )

    def ask(self, user_message: str, session_id: str = "default") -> AgentResponse:
        session = self._session_store.get_or_create(session_id)

        classification = self._classifier.classify(
            user_message,
            recent_turns=session.turns[-3:] if session.turns else [],
        )
        intent = classification.intent

        text, sources, coach_response = self._route(user_message, intent, session)

        turn_number = len(session.turns) // 2 + 1
        now = datetime.now(tz=timezone.utc).isoformat()

        session.turns.append(ConversationTurn(
            turn_number=turn_number,
            role="user",
            text=user_message,
            intent=intent.value,
            timestamp=now,
        ))
        session.turns.append(ConversationTurn(
            turn_number=turn_number,
            role="agent",
            text=text,
            intent=None,
            timestamp=now,
        ))
        self._session_store.save(session)

        return AgentResponse(
            text=text,
            intent=intent.value,
            session_id=session_id,
            turn_number=turn_number,
            coach_response=coach_response,
            sources=sources,
        )

    # ── routing ───────────────────────────────────────────────────────────────

    def _route(
        self,
        user_message: str,
        intent: UserIntent,
        session: ConversationSession,
    ):
        """Return (text, sources, coach_response)."""
        if intent == UserIntent.ANALYSIS_REQUEST:
            # First analysis of this session → run full KE pipeline
            # Subsequent ANALYSIS_REQUESTs are follow-up questions about
            # the existing recommendation (user correcting context, asking why, etc.)
            if session.last_envelope is None:
                return self._handle_analysis(session)
            intent = UserIntent.EXPLANATION_REQUEST

        if intent == UserIntent.FEEDBACK:
            return self._handle_feedback(user_message, session)

        # EXPLANATION_REQUEST, HYPOTHETICAL, GENERAL_QUESTION → follow-up
        text, sources = self._followup_handler.handle(user_message, session)
        return text, sources, None

    def _handle_analysis(self, session: ConversationSession):
        result = self._analysis_handler.handle()

        session.last_coach_response = result.coach_response
        session.last_envelope = result.envelope
        session.last_state = result.state
        session.last_decision_record = result.decision_record

        response = result.coach_response
        text = _format_analysis_response(response)
        return text, [], response

    def _handle_feedback(self, user_message: str, session: ConversationSession):
        runner_id = self._resolve_runner_id(session)
        ack, _entry = self._feedback_handler.handle(user_message, session, runner_id)
        return ack, [], None

    def _resolve_runner_id(self, session: ConversationSession) -> str:
        if session.last_state is not None:
            return session.last_state.meta.runner_id
        try:
            runner_id, _ = self._profile_store.load()
            return runner_id
        except Exception:
            return _UNKNOWN_RUNNER


# ── formatting ────────────────────────────────────────────────────────────────

def _format_analysis_response(response) -> str:
    parts: list[str] = []

    if response.medical_alert:
        parts.append(f"ALERTE MÉDICALE : {response.medical_alert}")

    parts.append(response.decision_summary)
    parts.append(response.main_message)

    if response.plan_hints_formatted:
        hints = "\n".join(f"  • {h}" for h in response.plan_hints_formatted)
        parts.append(f"Plan suggéré :\n{hints}")

    if response.confidence_note:
        parts.append(f"Note : {response.confidence_note}")

    return "\n\n".join(parts)
