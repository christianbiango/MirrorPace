"""End-to-end pipeline: DB → RunnerState → KnowledgeEngine → CoachResponse.

Usage:
    python scripts/run_coach.py

Requires:
    - data/mirrorpace.db populated (run scripts/import_strava.py first)
    - data/runner_profile.yaml filled
    - .env file with GEMINI_API_KEY
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from src.coach_intelligence.api import build_coach_response
from src.coach_intelligence.llm.gemini_client import GeminiLLMClient
from src.coach_intelligence.rag.context.retriever import RunnerContextRetriever
from src.database.connection import build_engine, build_session
from src.database.repository import ActivityRepository
from src.knowledge_engine.api import load_default_config, run_engine
from src.runner_memory.indexer import build_runner_context_store
from src.runner_memory.store import MemoryStore
from src.runner_memory.writer import MemoryWriter
from src.runner_model.builder import build_snapshot
from src.runner_model.profile_store import RunnerProfileStore
from src.runner_model.state_builder import build_runner_state


def main() -> None:
    if not os.getenv("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY not set. Add it to your .env file.")

    # --- 1. Load activities (single read) ---
    engine = build_engine()
    session = build_session(engine)
    activities = ActivityRepository(session).get_all()
    session.close()

    if not activities:
        sys.exit("No activities in DB. Run `python scripts/import_strava.py` first.")

    print(f"[1/5] Activities loaded: {len(activities)}")

    # --- 2. Build RunnerSnapshot ---
    snapshot = build_snapshot(activities)
    print(
        f"[2/5] Snapshot — "
        f"{snapshot.total_distance_km:.0f} km total, "
        f"trend: {snapshot.fitness_trend}"
    )

    # --- 3. Build RunnerState ---
    runner_id, profile = RunnerProfileStore().load()
    state = build_runner_state(activities, profile, runner_id)
    w = state.week
    print(
        f"[3/5] RunnerState — "
        f"week: {state.meta.week_start_date}, "
        f"volume: {w.weekly_distance_km:.1f} km, "
        f"fatigue: {w.fatigue_score}/5, "
        f"sleep: {w.sleep_quality_score}/5"
    )

    # --- 4. Run Knowledge Engine ---
    envelope = run_engine(state, load_default_config())
    triggered = [r for r in envelope.triggered_rules if r.triggered]
    print(
        f"[4/5] Knowledge Engine — "
        f"action: {envelope.decision.action}, "
        f"readiness: {envelope.readiness.score:.0f}/100, "
        f"{len(triggered)} rule(s) triggered"
    )
    for r in triggered:
        print(f"       • [{r.rule_id}] {r.reason}")

    # --- 4b. Record decision in Runner Memory ---
    memory_store = MemoryStore()
    decision_record = MemoryWriter(store=memory_store).record(envelope, state)
    context_store = build_runner_context_store(runner_id, memory_store)
    memory_count = len(memory_store.get_decisions(runner_id)) + len(memory_store.get_events(runner_id))
    print(f"[4b]  Memory — {memory_count} entrée(s) indexées (décision {decision_record.id} enregistrée)")

    # --- 5. Build CoachResponse (LLM call) ---
    print("[5/5] Calling LLM …")
    llm = GeminiLLMClient(api_key=os.getenv("GEMINI_API_KEY"))
    context_retriever = RunnerContextRetriever(store=context_store)
    response = build_coach_response(
        envelope, snapshot, state,
        llm_client=llm,
        context_retriever=context_retriever,
    )

    # --- Output ---
    print("\n" + "=" * 60)
    print("COACH RESPONSE")
    print("=" * 60)

    if response.medical_alert:
        print(f"\n⚠  ALERTE MÉDICALE : {response.medical_alert}\n")

    print(f"\nRésumé : {response.decision_summary}")
    print(f"\n{response.main_message}")

    if response.plan_hints_formatted:
        print("\nPlan suggéré :")
        for hint in response.plan_hints_formatted:
            print(f"  • {hint}")

    if response.scientific_context:
        print("\nContexte scientifique :")
        for snippet in response.scientific_context:
            print(f"  — {snippet}")

    if response.personal_context:
        print("\nContexte personnel :")
        for item in response.personal_context:
            print(f"  — {item}")

    if response.confidence_note:
        print(f"\nNote : {response.confidence_note}")

    print(f"\nref: {response.response_ref} | envelope: {response.envelope_ref}")


if __name__ == "__main__":
    main()
