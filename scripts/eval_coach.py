"""Evaluate Coach Intelligence over N historical weeks with real activities.

Loops over the most recent active weeks in the DB, runs the full pipeline for
each, and writes a structured report to data/eval_outputs/<timestamp>.txt.

Usage:
    python scripts/eval_coach.py            # 5 most recent active weeks
    python scripts/eval_coach.py --weeks 10 # 10 weeks
    python scripts/eval_coach.py --no-llm   # Knowledge Engine only, no LLM call

Requires:
    - data/mirrorpace.db populated
    - data/runner_profile.yaml filled
    - .env with GEMINI_API_KEY (unless --no-llm)
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from src.coach_intelligence.api import build_coach_response
from src.coach_intelligence.llm.gemini_client import GeminiLLMClient
from src.database.connection import build_engine, build_session
from src.database.repository import ActivityRepository
from src.domain.activity import Activity
from src.knowledge_engine.api import load_default_config, run_engine
from src.runner_model.builder import build_snapshot
from src.runner_model.profile_store import RunnerProfileStore
from src.runner_model.state_builder import build_runner_state


def _active_weeks(activities: list[Activity]) -> list[date]:
    """Return Mondays of weeks that have at least one activity, recent first."""
    weeks: dict[date, list[Activity]] = defaultdict(list)
    for a in activities:
        if a.date:
            monday = a.date.date() - timedelta(days=a.date.weekday())
            weeks[monday].append(a)
    return sorted(weeks.keys(), reverse=True)


def _fmt_pace(s: float | None) -> str:
    if s is None:
        return "—"
    m, sec = divmod(int(s), 60)
    return f"{m}:{sec:02d}/km"


def _run_week(
    activities: list[Activity],
    reference_date: date,
    profile_store: RunnerProfileStore,
    config,
    llm,
) -> dict:
    runner_id, profile = profile_store.load()
    snapshot = build_snapshot(activities)
    state = build_runner_state(activities, profile, runner_id, reference_date=reference_date)
    w = state.week
    envelope = run_engine(state, config)
    triggered = [r for r in envelope.triggered_rules if r.triggered]

    result = {
        "week": reference_date.isoformat(),
        "volume_km": w.weekly_distance_km,
        "prev_volume_km": w.previous_week_distance_km,
        "fatigue": w.fatigue_score,
        "sleep": w.sleep_quality_score,
        "readiness": envelope.readiness.score,
        "action": envelope.decision.action,
        "triggered_rules": [(r.rule_id, r.reason) for r in triggered],
        "coach_response": None,
    }

    if llm is not None:
        response = build_coach_response(envelope, snapshot, state, llm_client=llm)
        result["coach_response"] = {
            "decision_summary": response.decision_summary,
            "main_message": response.main_message,
            "plan_hints": response.plan_hints_formatted,
            "scientific_context": response.scientific_context,
            "personal_context": response.personal_context,
            "medical_alert": response.medical_alert,
        }

    return result


def _format_report(results: list[dict]) -> str:
    lines = [
        f"COACH INTELLIGENCE EVAL — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"{len(results)} semaine(s) analysée(s)",
        "=" * 70,
    ]

    for r in results:
        lines += [
            "",
            f"SEMAINE : {r['week']}",
            f"  Volume    : {r['volume_km']:.1f} km  (semaine précédente : {r['prev_volume_km']:.1f} km)",
            f"  Readiness : {r['readiness']:.0f}/100",
            f"  Action KE : {r['action']}",
            f"  Règles déclenchées ({len(r['triggered_rules'])}) :",
        ]
        for rule_id, reason in r["triggered_rules"]:
            lines.append(f"    • [{rule_id}] {reason}")

        cr = r.get("coach_response")
        if cr is None:
            lines.append("  [--no-llm : pas de réponse LLM]")
        else:
            if cr["medical_alert"]:
                lines.append(f"\n  ⚠  ALERTE : {cr['medical_alert']}")
            lines += [
                "",
                f"  RÉSUMÉ   : {cr['decision_summary']}",
                "",
                "  MESSAGE COACH :",
            ]
            for para in cr["main_message"].split("\n"):
                if para.strip():
                    lines.append(f"    {para.strip()}")
            if cr["plan_hints"]:
                lines.append("\n  PLAN :")
                for h in cr["plan_hints"]:
                    lines.append(f"    • {h}")
            if cr["scientific_context"]:
                lines.append("\n  CONTEXTE SCIENTIFIQUE :")
                for s in cr["scientific_context"]:
                    lines.append(f"    — {s}")

        lines.append("-" * 70)

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=int, default=5, help="Number of recent active weeks to evaluate")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM calls, Knowledge Engine only")
    args = parser.parse_args()

    if not args.no_llm and not os.getenv("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY not set. Add it to .env or use --no-llm.")

    engine = build_engine()
    session = build_session(engine)
    activities = ActivityRepository(session).get_all()
    session.close()

    if not activities:
        sys.exit("No activities in DB.")

    weeks = _active_weeks(activities)[: args.weeks]
    print(f"Evaluating {len(weeks)} week(s): {[w.isoformat() for w in weeks]}")

    config = load_default_config()
    profile_store = RunnerProfileStore()
    llm = GeminiLLMClient(api_key=os.getenv("GEMINI_API_KEY")) if not args.no_llm else None

    results = []
    for i, monday in enumerate(weeks, 1):
        label = "no-llm" if llm is None else "LLM"
        print(f"  [{i}/{len(weeks)}] {monday} ({label})…", end=" ", flush=True)
        # Use Sunday so build_week_input covers the full Mon–Sun range
        sunday = monday + timedelta(days=6)
        try:
            r = _run_week(activities, sunday, profile_store, config, llm)
            r["week"] = monday.isoformat()  # label stays as Monday for readability
            results.append(r)
            print(f"{r['action']} | readiness={r['readiness']:.0f}")
        except Exception as exc:
            print(f"ERROR: {exc}")

    report = _format_report(results)

    out_dir = Path("data/eval_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"eval_{timestamp}.txt"
    out_path.write_text(report, encoding="utf-8")

    print(f"\n{report}")
    print(f"\nReport saved → {out_path}")


if __name__ == "__main__":
    main()
