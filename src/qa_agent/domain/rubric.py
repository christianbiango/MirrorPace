"""Evaluation rubric — constants and judge prompt. No LLM calls."""

from __future__ import annotations

HARD_DIMENSIONS = ["ke_coherence", "medical_flag", "memory_utilization"]
SOFT_DIMENSIONS = [
    "question_answered",
    "factual_groundedness",
    "tone_appropriateness",
    "pedagogical_quality",
    "conversation_coherence",
    "empathy",
]
ALL_DIMENSIONS = HARD_DIMENSIONS + SOFT_DIMENSIONS

# Hard dimensions contribute via hard_check_failures; soft dimensions are scored 1-5.
# Weights for soft dimensions only (must sum to 1.0).
DIMENSION_WEIGHTS: dict[str, float] = {
    "question_answered": 0.30,
    "factual_groundedness": 0.20,
    "tone_appropriateness": 0.15,
    "pedagogical_quality": 0.15,
    "conversation_coherence": 0.12,
    "empathy": 0.08,
}

DIMENSION_DESCRIPTIONS: dict[str, str] = {
    "ke_coherence": "La recommandation du coach respecte-t-elle la décision du Knowledge Engine (deload/increase/maintain) ?",
    "medical_flag": "Si le KE a signalé un renvoi médical, le coach l'a-t-il communiqué au coureur ?",
    "memory_utilization": "Le coach a-t-il référencé des décisions passées pertinentes issues de la Runner Memory ?",
    "question_answered": "Le coach a-t-il réellement répondu à la question posée par le coureur ?",
    "factual_groundedness": "Tous les chiffres et faits cités par le coach sont-ils ancrés dans les données réelles (pas de chiffres inventés) ?",
    "tone_appropriateness": "Le ton du coach correspond-il au profil et à l'état émotionnel du coureur ?",
    "pedagogical_quality": "L'explication est-elle claire, compréhensible et actionnable pour ce coureur ?",
    "conversation_coherence": "La conversation est-elle exempte de contradictions entre les tours ?",
    "empathy": "Le coach a-t-il reconnu la dimension humaine (effort, fatigue, motivation, stress) ?",
}

_SCORE_EXAMPLES: dict[str, dict[int, str]] = {
    "question_answered": {
        1: "Le coureur demande pourquoi réduire, le coach répète uniquement la recommandation sans expliquer.",
        3: "Le coach explique une raison principale mais en omet d'importantes.",
        5: "Le coach répond directement avec les éléments précis (règles, métriques) qui motivent la décision.",
    },
    "factual_groundedness": {
        1: "Le coach cite un ACWR de 1.6 alors que l'enveloppe indique 1.1 — chiffre inventé.",
        3: "Les tendances sont correctes mais certains chiffres sont arrondis de façon inexacte.",
        5: "Tous les chiffres correspondent exactement aux données de l'enveloppe et du profil coureur.",
    },
    "tone_appropriateness": {
        1: "Coureur anxieux débutant — coach répond de façon très technique et froide sans rassurer.",
        3: "Ton globalement correct mais quelques formulations trop abruptes pour le profil.",
        5: "Ton parfaitement adapté — rassurant pour l'anxieux, challengeant pour l'ambitieux.",
    },
    "pedagogical_quality": {
        1: "Utilise des termes techniques (ACWR, ATL, CTL) sans les définir pour un débutant.",
        3: "Explication correcte mais sans suggestion d'action concrète pour la semaine suivante.",
        5: "Explication claire avec analogie accessible, raison précise, et action concrète recommandée.",
    },
    "conversation_coherence": {
        1: "Tour 1 : 'je te recommande de réduire'. Tour 3 : 'tu peux augmenter ta charge' — contradiction directe.",
        3: "Pas de contradiction flagrante mais le ton change sans raison entre les tours.",
        5: "Chaque réponse s'appuie sur les précédentes, cohérence parfaite sur toute la conversation.",
    },
    "empathy": {
        1: "Le coureur dit être épuisé — le coach répond uniquement avec des données sans reconnaître la fatigue.",
        3: "Le coach mentionne brièvement que la fatigue est normale sans s'y attarder.",
        5: "Le coach reconnaît explicitement l'effort, valide la fatigue, et adapte sa recommandation.",
    },
}


def build_judge_system_prompt() -> str:
    dims = "\n".join(
        f"- **{dim}** : {DIMENSION_DESCRIPTIONS[dim]}"
        for dim in SOFT_DIMENSIONS
    )

    examples_lines: list[str] = []
    for dim, examples in _SCORE_EXAMPLES.items():
        examples_lines.append(f"\n### {dim}")
        for score, example in sorted(examples.items()):
            examples_lines.append(f"Score {score} : {example}")

    examples_text = "\n".join(examples_lines)

    return f"""Tu es un évaluateur expert en coaching sportif et en qualité conversationnelle pour MirrorPace.

Tu reçois une conversation entre un coureur simulé et le coach IA MirrorPace, accompagnée des données objectives du Knowledge Engine.

Évalue la conversation selon les 6 dimensions suivantes (score 1 à 5) :

{dims}

## Exemples de scores par dimension
{examples_text}

## Format de réponse (JSON strict, aucun texte avant ou après)

{{
  "scores": {{
    "question_answered": {{"score": <1-5>, "justification": "<explication courte>", "cited_turn": <numéro ou null>}},
    "factual_groundedness": {{"score": <1-5>, "justification": "<explication courte>", "cited_turn": <numéro ou null>}},
    "tone_appropriateness": {{"score": <1-5>, "justification": "<explication courte>", "cited_turn": <numéro ou null>}},
    "pedagogical_quality": {{"score": <1-5>, "justification": "<explication courte>", "cited_turn": <numéro ou null>}},
    "conversation_coherence": {{"score": <1-5>, "justification": "<explication courte>", "cited_turn": <numéro ou null>}},
    "empathy": {{"score": <1-5>, "justification": "<explication courte>", "cited_turn": <numéro ou null>}}
  }},
  "strengths": ["<force concrète 1>", "<force concrète 2>"],
  "weaknesses": ["<faiblesse concrète 1>", "<faiblesse concrète 2>"],
  "blockers": ["<point qui empêche une bonne expérience utilisateur>"],
  "suggested_improvements": ["<amélioration précise et actionnable 1>", "<amélioration 2>"]
}}

## Règles d'évaluation

- Cite le tour exact (cited_turn) qui justifie chaque score
- Sois critique — un score 5 doit être réellement mérité
- Forces et faiblesses doivent être spécifiques, pas génériques ("bonne réponse" n'est pas une force)
- Un blocker empêche concrètement le coureur d'agir ou de comprendre
"""
