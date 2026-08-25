"""Deterministic formatting of DecisionEnvelope facts (plan hints, target pace).

Shared between the initial analysis response and follow-up conversation
grounding — quantitative plan facts must be exact, rendered in code, never
reconstructed from memory by the LLM.
"""

from __future__ import annotations

PACE_SOURCE_LABELS = {
    "race_target_time": "objectif déclaré",
    "riegel_from_half": "projection Riegel depuis semi récent",
    "riegel_from_10k": "projection Riegel depuis 10k récent",
    "vma_only": "VMA seule",
}


def format_pace_min_per_km(pace_min_per_km: float) -> str:
    minutes = int(pace_min_per_km)
    seconds = round((pace_min_per_km - minutes) * 60)
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"


def format_target_pace(envelope) -> str | None:
    pace = envelope.target_marathon_pace_min_km
    if pace is None:
        return None
    source_label = PACE_SOURCE_LABELS.get(
        envelope.target_marathon_pace_source, envelope.target_marathon_pace_source
    )
    return f"Allure marathon cible : {format_pace_min_per_km(pace)}/km ({source_label})"


def format_plan_hints(plan_hints) -> list[str]:
    """Render P4 plan hints (RULE-015/RULE-027 phase skeleton, RULE-021 taper
    detail, etc.) from real numbers — never let the LLM paraphrase them."""
    lines: list[str] = []
    for h in plan_hints:
        if h.rule_id in ("RULE-015", "RULE-027") and "suggested_phases" in h.params:
            p = h.params["suggested_phases"]
            phase_parts = []
            if "general" in p:
                phase_parts.append(f"{p['general']} sem. base")
            phase_parts.append(f"{p['specific']} sem. spécifique")
            phase_parts.append(f"{p['taper']} sem. affûtage")
            lines.append(f"{h.reason} → " + ", ".join(phase_parts))
        elif h.reason:
            lines.append(h.reason)
    return lines
