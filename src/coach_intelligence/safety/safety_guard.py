from __future__ import annotations

import hashlib
import json

from ..domain.schemas.coach_response import CoachResponse, RawLLMResponse
from ..domain.schemas.reasoning_context import ReasoningContext

_MEDICAL_ALERTS: dict[str, str] = {
    "pain_critical": (
        "⚠️ ALERTE MÉDICALE : Douleur critique détectée. "
        "Arrêt immédiat de l'entraînement recommandé. "
        "Consultez un médecin ou un kinésithérapeute avant toute reprise."
    ),
    "pain_tendon": (
        "⚠️ ALERTE MÉDICALE : Pathologie tendineuse suspectée. "
        "Repos et consultation médicale recommandés avant de reprendre l'entraînement."
    ),
    "known_pathology": (
        "⚠️ RAPPEL MÉDICAL : Pathologie connue active. "
        "Suivez les recommandations de votre praticien de santé."
    ),
}

_FALLBACK_ALERT = _MEDICAL_ALERTS["known_pathology"]


class SafetyGuard:
    def apply(self, raw: RawLLMResponse, context: ReasoningContext) -> CoachResponse:
        parsed = _parse_llm_response(raw.text)

        medical_alert: str | None = None
        if context.interpreted.medical_flag:
            reason = context.interpreted.medical_reason or ""
            medical_alert = _MEDICAL_ALERTS.get(reason, _FALLBACK_ALERT)

        confidence_note: str | None = None
        if context.interpreted.confidence != "high":
            confidence_note = (
                f"Données insuffisantes pour une recommandation de haute confiance "
                f"(niveau : {context.interpreted.confidence}). "
                f"Interprétez ces conseils avec prudence."
            )

        response_ref = _generate_ref(context)
        envelope_ref = context.interpreted.action

        return CoachResponse(
            decision_summary=parsed.get("decision_summary", ""),
            main_message=parsed.get("main_message", ""),
            scientific_context=parsed.get("scientific_context", []),
            personal_context=parsed.get("personal_context", []),
            plan_hints_formatted=parsed.get("plan_hints_formatted", []),
            medical_alert=medical_alert,
            confidence_note=confidence_note,
            response_ref=response_ref,
            envelope_ref=envelope_ref,
        )


def _parse_llm_response(text: str) -> dict:
    text = text.strip()
    # Strip markdown code blocks
    if text.startswith("```"):
        lines = text.splitlines()
        inner = [l for l in lines[1:] if l.strip() != "```"]
        text = "\n".join(inner).strip()
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    # Fallback: raw text as main_message
    return {
        "decision_summary": "",
        "main_message": text,
        "scientific_context": [],
        "personal_context": [],
        "plan_hints_formatted": [],
    }


def _generate_ref(context: ReasoningContext) -> str:
    key = (
        f"{context.interpreted.action}:"
        f"{context.interpreted.medical_flag}:"
        f"{context.personalization.career_context}"
    )
    return hashlib.sha256(key.encode()).hexdigest()[:12]
