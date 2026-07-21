"""Public entry point for Coach Intelligence."""

from __future__ import annotations

from src.knowledge_engine.api import DecisionEnvelope, RunnerState
from src.runner_model.snapshot import RunnerSnapshot

from .assembler.response_assembler import LLMClient, ResponseAssembler
from .domain.schemas.coach_response import CoachResponse
from .feedback.collector import FeedbackCollector, NullFeedbackCollector
from .interpreter.envelope_interpreter import EnvelopeInterpreter
from .personalizer.runner_personalizer import RunnerPersonalizer
from .rag.context.retriever import RunnerContextRetriever
from .rag.scientific.retriever import ScientificRetriever
from .reasoning.context_builder import ReasoningContextBuilder
from .safety.safety_guard import SafetyGuard


def build_coach_response(
    envelope: DecisionEnvelope,
    snapshot: RunnerSnapshot,
    state: RunnerState,
    *,
    llm_client: LLMClient,
    scientific_retriever: ScientificRetriever | None = None,
    context_retriever: RunnerContextRetriever | None = None,
    feedback_collector: FeedbackCollector | None = None,
) -> CoachResponse:
    """
    Transform a DecisionEnvelope into a personalized coaching response.

    Args:
        envelope:              Output from Knowledge Engine (run_engine).
        snapshot:              Runner's historical profile from Runner Model.
        state:                 Current week state used to produce the envelope.
        llm_client:            Injectable LLM client (AnthropicLLMClient or stub).
        scientific_retriever:  Scientific RAG — uses built-in knowledge base if None.
        context_retriever:     Runner memory RAG — returns empty list if None.
        feedback_collector:    Feedback interface — no-op if None.
    """
    scientific_retriever = scientific_retriever or ScientificRetriever()
    context_retriever = context_retriever or RunnerContextRetriever()
    feedback_collector = feedback_collector or NullFeedbackCollector()

    interpreted = EnvelopeInterpreter().interpret(envelope)
    personalization = RunnerPersonalizer().personalize(snapshot, state.profile, state.context)
    scientific_snippets = scientific_retriever.retrieve(interpreted)
    memory_snippets = context_retriever.retrieve(state.meta.runner_id, interpreted)
    reasoning = ReasoningContextBuilder().build(
        interpreted, personalization, scientific_snippets, memory_snippets
    )
    raw = ResponseAssembler(llm_client).assemble(reasoning)
    return SafetyGuard().apply(raw, reasoning)
