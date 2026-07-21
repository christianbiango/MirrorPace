"""Interactive CLI coach — conversational loop over the full pipeline.

Usage:
    python scripts/run_agent.py

Requires:
    - data/mirrorpace.db populated (run scripts/import_strava.py first)
    - data/runner_profile.yaml filled
    - .env file with GEMINI_API_KEY

Example conversation:
    Toi: analyse ma semaine
    Coach: [full analysis from CI]

    Toi: pourquoi tu me demandes de réduire ?
    Coach: [explanation grounded in envelope rules]

    Toi: et si j'augmentais quand même ?
    Coach: [hypothetical response with risk context]

    Toi: c'était en fait assez difficile cette semaine
    Coach: [feedback acknowledged and stored]
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from src.coach_agent.agent import CoachAgent
from src.coach_agent.session.feedback_store import FeedbackStore
from src.coach_intelligence.llm.gemini_client import GeminiLLMClient
from src.database.connection import build_engine, build_session
from src.database.repository import ActivityRepository
from src.runner_memory.store import MemoryStore
from src.runner_model.profile_store import RunnerProfileStore

_BANNER = """\
╔═══════════════════════════════════════════════════╗
║           MirrorPace — Coach conversationnel      ║
╚═══════════════════════════════════════════════════╝
Commandes utiles :
  "analyse ma semaine"    → analyse complète
  "pourquoi ?"            → explication de la décision
  "et si j'augmentais ?"  → scénario hypothétique
  "exit" / Ctrl-C         → quitter
"""


def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY not set. Add it to your .env file.")

    profile_store = RunnerProfileStore()
    if not profile_store.exists():
        sys.exit(
            "data/runner_profile.yaml not found. "
            "Fill in the athlete profile first."
        )

    engine_db = build_engine()
    db_session = build_session(engine_db)
    activity_repo = ActivityRepository(db_session)

    llm = GeminiLLMClient(api_key=api_key)
    memory_store = MemoryStore()
    feedback_store = FeedbackStore()

    agent = CoachAgent(
        llm_client=llm,
        memory_store=memory_store,
        activity_repo=activity_repo,
        profile_store=profile_store,
        feedback_store=feedback_store,
    )

    session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(_BANNER)

    while True:
        try:
            user_input = input("Toi: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Au revoir.")
            break

        try:
            response = agent.ask(user_input, session_id=session_id)
        except RuntimeError as exc:
            print(f"\n[Erreur] {exc}\n")
            continue
        except Exception as exc:
            print(f"\n[Erreur inattendue] {exc}\n")
            continue

        print(f"\nCoach: {response.text}")

        if response.sources:
            print(f"\n  [mémoire: {len(response.sources)} snippet(s) utilisé(s)]")

        print()

    db_session.close()


if __name__ == "__main__":
    main()
