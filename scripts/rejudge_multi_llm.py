"""Re-judge already-recorded QA conversations with Groq and Mistral, alongside
the original Gemini judge score — without re-running the full pipe (no coach
or persona LLM calls, only the judges). Lets 3 independent model families vote
on a conversation's score instead of trusting a single LLM judge (self-bias risk
when the judge shares a family with the coach/persona models).

Each directory under data/qa_runs/ holds exactly one conversation (one
run_qa.py invocation = one conversation), so by default this scans ALL of
them for a meaningful comparison sample.

Usage:
    python scripts/rejudge_multi_llm.py [--run <run_dir_name>]

Pass --run to restrict to a single run directory instead of scanning all of
data/qa_runs/.

Requires:
    - GROQ_API_KEY and MISTRAL_API_KEY in .env
    - existing data/qa_runs/*/{conversations,evaluations}/ from prior
      `python scripts/run_qa.py` invocations
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

import openai

from src.qa_agent.evaluation.conversation_judge import ConversationJudge
from src.qa_agent.llm import QAGroqClient, QAMistralClient
from src.qa_agent.profiles import PROFILES_BY_ID

QA_RUNS_DIR = Path("data/qa_runs")
MVP_THRESHOLD = 7.5

_MAX_RETRIES = 3
_FALLBACK_WAIT_S = 20.0
_RETRY_WAIT_RE = re.compile(r"try again in ([\d.]+)s")


def _evaluate_with_retry(judge: ConversationJudge, **kwargs):
    """Free tiers (Groq in particular) have low tokens-per-minute limits —
    retry on 429 using the API's suggested wait, falling back to a fixed delay."""
    for attempt in range(_MAX_RETRIES):
        try:
            return judge.evaluate_raw(**kwargs)
        except openai.RateLimitError as e:
            if attempt == _MAX_RETRIES - 1:
                raise
            match = _RETRY_WAIT_RE.search(str(e))
            wait_s = float(match.group(1)) + 1.0 if match else _FALLBACK_WAIT_S
            print(f"  ...rate limited, waiting {wait_s:.0f}s")
            time.sleep(wait_s)


def _conversation_files(run: str | None) -> list[Path]:
    if run:
        conv_dir = QA_RUNS_DIR / run / "conversations"
        if not conv_dir.exists():
            sys.exit(f"No conversations/ directory in {QA_RUNS_DIR / run}")
        return sorted(conv_dir.glob("conv_*.json"))
    return sorted(QA_RUNS_DIR.glob("*/conversations/conv_*.json"))


def _build_prompt_from_stored(conv: dict, tags: list[str], hard_check_failures: list[str]) -> str:
    lines = [
        f"## Profil du coureur simulé : {conv['runner_profile_display']}",
        f"Tags : {', '.join(tags)}",
        "",
        "## Conversation",
    ]

    for entry in conv["entries"]:
        lines.append(f"\n**Tour {entry['turn_number']} — Coureur :** {entry['user_message']}")
        lines.append(f"**Tour {entry['turn_number']} — Coach :** {entry['agent_text']}")

        env = entry.get("envelope")
        if env:
            lines.append(
                f"*[KE : action={env['action']}, "
                f"readiness={env['readiness']}/100, "
                f"règles={env['triggered_rules']}, "
                f"renvoi_médical={env['medical_referral']}]*"
            )

    lines.append(f"\n**Fin de conversation :** {conv['termination_reason']}")

    if hard_check_failures:
        lines.append("\n## Violations objectives détectées")
        for failure in hard_check_failures:
            lines.append(f"- {failure}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", help="Run directory name under data/qa_runs/ (default: scan all)")
    args = parser.parse_args()

    groq_key = os.getenv("GROQ_API_KEY")
    mistral_key = os.getenv("MISTRAL_API_KEY")
    if not groq_key:
        sys.exit("GROQ_API_KEY not set in .env")
    if not mistral_key:
        sys.exit("MISTRAL_API_KEY not set in .env")

    conv_paths = _conversation_files(args.run)
    if not conv_paths:
        sys.exit(f"No conversations found under {QA_RUNS_DIR}" + (f"/{args.run}" if args.run else ""))

    groq_judge = ConversationJudge(client=QAGroqClient(api_key=groq_key))
    mistral_judge = ConversationJudge(client=QAMistralClient(api_key=mistral_key))

    print(f"Re-judging {len(conv_paths)} conversation(s) with Groq + Mistral "
          f"(Gemini score reused from the original eval)...\n")
    print(f"{'profile':<25}{'gemini':>8}{'groq':>8}{'mistral':>8}{'spread':>8}  majority")
    print("-" * 80)

    rows: list[tuple[str, float | None, float, float]] = []
    for conv_path in conv_paths:
        conv = json.loads(conv_path.read_text())
        conv_id = conv["conversation_id"]

        eval_path = conv_path.parents[1] / "evaluations" / f"eval_{conv_id}.json"
        original = json.loads(eval_path.read_text()) if eval_path.exists() else {}
        hard_check_failures = original.get("hard_check_failures", [])
        gemini_score = original.get("global_score")

        tags = PROFILES_BY_ID[conv["runner_profile_id"]].tags
        prompt = _build_prompt_from_stored(conv, tags, hard_check_failures)

        groq_report = _evaluate_with_retry(
            groq_judge,
            conversation_id=conv_id,
            runner_profile_id=conv["runner_profile_id"],
            user_prompt=prompt,
            hard_check_failures=hard_check_failures,
        )
        mistral_report = _evaluate_with_retry(
            mistral_judge,
            conversation_id=conv_id,
            runner_profile_id=conv["runner_profile_id"],
            user_prompt=prompt,
            hard_check_failures=hard_check_failures,
        )

        groq_score = groq_report.global_score
        mistral_score = mistral_report.global_score
        scores = [s for s in (gemini_score, groq_score, mistral_score) if s is not None]
        spread = max(scores) - min(scores) if scores else 0.0
        votes_pass = sum(1 for s in scores if s >= MVP_THRESHOLD)
        majority = "PASS" if votes_pass >= 2 else "FAIL"

        rows.append((conv["runner_profile_id"], gemini_score, groq_score, mistral_score))
        gemini_str = f"{gemini_score:.2f}" if gemini_score is not None else "n/a"
        print(
            f"{conv['runner_profile_id']:<25}{gemini_str:>8}{groq_score:>8.2f}"
            f"{mistral_score:>8.2f}{spread:>8.2f}  {majority} ({votes_pass}/3)"
        )

    if not rows:
        print("No conversations found.")


if __name__ == "__main__":
    main()
