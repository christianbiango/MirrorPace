"""QA Agent — simulate users and evaluate CoachAgent conversation quality.

Usage:
    python scripts/run_qa.py                              # 3 convs, 5 turns, all profiles
    python scripts/run_qa.py --conversations 20           # 20 conversations
    python scripts/run_qa.py --profile anxious_beginner   # single profile
    python scripts/run_qa.py --budget 2.0                 # override budget cap
    python scripts/run_qa.py --max-turns 8                # more turns per conversation

Requires:
    - data/mirrorpace.db populated
    - data/runner_profile.yaml filled
    - .env with GEMINI_API_KEY and DEEPSEEK_API_KEY

Cost guardrail: estimated cost is checked before any API call.
Default budget: $0.50. Override with --budget.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from collections import Counter
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
from src.qa_agent.evaluation.conversation_judge import ConversationJudge
from src.qa_agent.evaluation.hard_checks import (
    check_ke_coherence,
    check_medical_flag,
    check_memory_utilization,
)
from src.qa_agent.profiles import ALL_PROFILES, PROFILES_BY_ID
from src.qa_agent.reporting.formatter import format_aggregate, format_evaluation
from src.qa_agent.reporting.report_generator import ReportGenerator
from src.qa_agent.simulation.conversation_runner import ConversationRunner
from src.runner_memory.store import MemoryStore
from src.runner_model.profile_store import RunnerProfileStore

_DEFAULT_CONVERSATIONS = 3
_DEFAULT_MAX_TURNS = 5
_DEFAULT_BUDGET = 0.50

# Cost per conversation at default max_turns (5).
# All on Gemini 2.5 Flash: CoachAgent ~$0.0028 + QA runner ~$0.0014 + QA judge ~$0.0024
_COST_PER_CONV_5_TURNS = 0.007


def estimate_cost(n_conversations: int, max_turns: int) -> float:
    turn_factor = max_turns / _DEFAULT_MAX_TURNS
    return round(n_conversations * _COST_PER_CONV_5_TURNS * turn_factor, 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="MirrorPace QA Agent")
    parser.add_argument("--conversations", type=int, default=_DEFAULT_CONVERSATIONS,
                        help=f"Number of conversations to simulate (default: {_DEFAULT_CONVERSATIONS})")
    parser.add_argument("--max-turns", type=int, default=_DEFAULT_MAX_TURNS,
                        help=f"Max turns per conversation (default: {_DEFAULT_MAX_TURNS})")
    parser.add_argument("--profile", type=str, default=None,
                        help=f"Profile ID to test. Available: {[p.id for p in ALL_PROFILES]}")
    parser.add_argument("--budget", type=float, default=_DEFAULT_BUDGET,
                        help=f"Cost budget in USD (default: ${_DEFAULT_BUDGET})")
    args = parser.parse_args()

    # ── Cost guardrail — fail before any API call ─────────────────────────────
    estimated = estimate_cost(args.conversations, args.max_turns)
    if estimated > args.budget:
        print(
            f"ERROR: Estimated cost ~${estimated:.2f} exceeds budget ${args.budget:.2f}. "
            f"Use --budget {estimated + 0.10:.1f} to override."
        )
        sys.exit(1)

    # ── Env vars ───────────────────────────────────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        sys.exit("ERROR: GEMINI_API_KEY not set. Add it to your .env file.")

    # ── Profile selection ──────────────────────────────────────────────────────
    if args.profile:
        if args.profile not in PROFILES_BY_ID:
            print(f"ERROR: Profile '{args.profile}' not found.")
            print(f"Available profiles: {list(PROFILES_BY_ID.keys())}")
            sys.exit(1)
        profiles = [PROFILES_BY_ID[args.profile]]
    else:
        profiles = ALL_PROFILES

    # ── Build CoachAgent ───────────────────────────────────────────────────────
    profile_store = RunnerProfileStore()
    if not profile_store.exists():
        sys.exit("ERROR: data/runner_profile.yaml not found. Fill in athlete profile first.")

    engine_db = build_engine()
    db_session = build_session(engine_db)
    activity_repo = ActivityRepository(db_session)

    llm = GeminiLLMClient(api_key=gemini_key)
    memory_store = MemoryStore()
    feedback_store = FeedbackStore()

    coach = CoachAgent(
        llm_client=llm,
        memory_store=memory_store,
        activity_repo=activity_repo,
        profile_store=profile_store,
        feedback_store=feedback_store,
    )

    conv_runner = ConversationRunner(
        coach_agent=coach,
        api_key=gemini_key,
        max_turns=args.max_turns,
    )
    judge = ConversationJudge(api_key=gemini_key)
    generator = ReportGenerator()

    # ── Output directory ───────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("data/qa_runs") / timestamp
    (out_dir / "conversations").mkdir(parents=True, exist_ok=True)
    (out_dir / "evaluations").mkdir(parents=True, exist_ok=True)

    print(f"MirrorPace QA Agent")
    print(f"  Conversations : {args.conversations} | Tours max : {args.max_turns}")
    print(f"  Coût estimé   : ~${estimated:.3f} (budget : ${args.budget:.2f})")
    print(f"  Profils       : {[p.id for p in profiles]}")
    print(f"  Sortie        : {out_dir}")
    print("=" * 62)

    # ── Run ────────────────────────────────────────────────────────────────────
    all_reports = []
    termination_counts: Counter = Counter()
    profile_cycle = itertools.cycle(profiles)

    for i in range(args.conversations):
        profile = next(profile_cycle)
        print(f"[{i + 1}/{args.conversations}] {profile.display_name}...", end=" ", flush=True)

        try:
            log = conv_runner.run(profile)
            termination_counts[log.termination_reason] += 1

            _save_json(
                out_dir / "conversations" / f"conv_{log.conversation_id}.json",
                _log_to_dict(log),
            )

            failures = (
                check_ke_coherence(log)
                + check_medical_flag(log)
                + check_memory_utilization(log, memory_store)
            )

            report = judge.evaluate(log, failures)
            all_reports.append(report)

            _save_json(
                out_dir / "evaluations" / f"eval_{log.conversation_id}.json",
                _report_to_dict(report),
            )

            status = f"score={report.global_score:.1f}/10 | {log.termination_reason}"
            if failures:
                status += f" | ⚠ {len(failures)} violation(s)"
            print(status)

        except Exception as exc:
            print(f"ERROR: {exc}")
            termination_counts["error"] += 1

    # ── Aggregate ──────────────────────────────────────────────────────────────
    if all_reports:
        aggregate = generator.generate(all_reports, dict(termination_counts))
        _save_json(out_dir / "aggregate.json", _aggregate_to_dict(aggregate))
        print("\n" + format_aggregate(aggregate))

    print(f"\nRapport complet → {out_dir}")
    db_session.close()


# ── Serialization helpers ─────────────────────────────────────────────────────

def _log_to_dict(log) -> dict:
    entries = []
    for e in log.entries:
        env_data = None
        if e.envelope_snapshot is not None:
            env = e.envelope_snapshot
            env_data = {
                "action": env.decision.action,
                "delta_pct": env.decision.delta_pct,
                "readiness": env.readiness.score,
                "medical_referral": env.medical_referral,
                "medical_referral_reason": env.medical_referral_reason,
                "triggered_rules": [r.rule_id for r in env.triggered_rules if r.triggered],
            }
        entries.append({
            "turn_number": e.turn_number,
            "user_message": e.user_message,
            "agent_text": e.agent_response.text,
            "intent": e.agent_response.intent,
            "envelope": env_data,
        })
    return {
        "conversation_id": log.conversation_id,
        "runner_profile_id": log.runner_profile.id,
        "runner_profile_display": log.runner_profile.display_name,
        "runner_id": log.runner_id,
        "termination_reason": log.termination_reason,
        "started_at": log.started_at,
        "ended_at": log.ended_at,
        "total_turns": len(log.entries),
        "entries": entries,
    }


def _report_to_dict(report) -> dict:
    return {
        "conversation_id": report.conversation_id,
        "runner_profile_id": report.runner_profile_id,
        "global_score": report.global_score,
        "hard_check_failures": report.hard_check_failures,
        "scores": {
            dim: {
                "score": s.score,
                "justification": s.justification,
                "cited_turn": s.cited_turn,
            }
            for dim, s in report.scores.items()
        },
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "blockers": report.blockers,
        "suggested_improvements": report.suggested_improvements,
        "evaluated_at": report.evaluated_at,
    }


def _aggregate_to_dict(report) -> dict:
    return {
        "total_conversations": report.total_conversations,
        "mean_global_score": report.mean_global_score,
        "std_global_score": report.std_global_score,
        "scores_by_dimension": report.scores_by_dimension,
        "memory_utilization_rate": report.memory_utilization_rate,
        "ke_contradiction_rate": report.ke_contradiction_rate,
        "medical_flag_miss_rate": report.medical_flag_miss_rate,
        "termination_breakdown": report.termination_breakdown,
        "top_blockers": report.top_blockers,
        "interesting_conversations": report.interesting_conversations,
        "generated_at": report.generated_at,
    }


def _save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
