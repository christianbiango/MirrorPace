from __future__ import annotations

from ..domain.schemas.reasoning_context import ReasoningContext

SYSTEM_PROMPT = (
    "Tu es un coach de course à pied expert et bienveillant.\n"
    "Tu reçois une analyse structurée de la situation d'un coureur et tu dois rédiger une réponse personnalisée.\n\n"
    "Règles impératives :\n"
    "- Si une alerte médicale est signalée, commence TOUJOURS ta réponse par cette alerte en premier paragraphe.\n"
    "- Adapte ton niveau de langage au profil du coureur : 'simple' pour les débutants, 'technical' pour les avancés.\n"
    "- Tes recommandations doivent être directement issues de la décision fournie — ne crée pas de nouvelles recommandations.\n"
    "- Réponds UNIQUEMENT en JSON valide, sans markdown, avec la structure suivante :\n\n"
    '{\n'
    '  "decision_summary": "1 phrase — la décision principale",\n'
    '  "main_message": "Le message principal (2-4 paragraphes, adapté au profil du coureur)",\n'
    '  "scientific_context": ["justification scientifique 1", "justification 2"],\n'
    '  "personal_context": ["référence au profil ou historique du coureur 1"],\n'
    '  "plan_hints_formatted": ["conseil de planification 1"]\n'
    "}"
)


def build_prompt(context: ReasoningContext) -> str:
    interp = context.interpreted
    pers = context.personalization
    sections: list[str] = []

    # Decision
    decision_lines = [
        f"Action : {interp.action}",
        f"Sévérité : {interp.severity}",
        f"Raison principale : {interp.primary_reason}",
    ]
    if interp.supporting_reasons:
        decision_lines.append(f"Raisons secondaires : {', '.join(interp.supporting_reasons)}")
    sections.append("## DÉCISION\n" + "\n".join(decision_lines))

    # Medical alert instruction
    if interp.medical_flag:
        reason = interp.medical_reason or "référence médicale recommandée"
        sections.append(
            f"## ⚠️ ALERTE MÉDICALE\n"
            f"Motif : {reason}\n"
            f"INSTRUCTION : Ouvre ta réponse par cette alerte — elle doit apparaître en premier."
        )

    # Key metrics
    km = interp.key_metrics
    metrics_lines = [
        f"  - Score de forme (readiness) : {km.get('readiness_score', '?')}/100",
        f"  - Confiance du score : {km.get('readiness_confidence', '?')}/100",
        f"  - Variation volume : {km.get('delta_pct', 0):+.0f}%",
        f"  - Cible semaine prochaine : {km.get('absolute_target_km', '?')} km",
    ]
    if "acwr" in km:
        metrics_lines.append(f"  - ACWR distance : {km['acwr']:.2f}")
    sections.append("## MÉTRIQUES CLÉS\n" + "\n".join(metrics_lines))

    # Runner profile
    profile_lines = [
        f"  - Style de communication à utiliser : {pers.communication_style}",
        f"  - Profil carrière : {pers.career_context}",
        f"  - Forme récente : {pers.current_fitness_note}",
    ]
    if pers.intensity_profile:
        profile_lines.append(f"  - Répartition intensité : {pers.intensity_profile}")
    if pers.has_race_goal and pers.weeks_to_race is not None:
        profile_lines.append(f"  - Objectif course : dans {pers.weeks_to_race} semaines")
        if pers.race_target_time_s:
            h = pers.race_target_time_s // 3600
            m = (pers.race_target_time_s % 3600) // 60
            profile_lines.append(f"  - Temps cible : {h}h{m:02d}")
    for key, val in pers.relevant_pbs.items():
        profile_lines.append(f"  - {key} : {val}")
    sections.append("## PROFIL COUREUR\n" + "\n".join(profile_lines))

    # Scientific context
    if context.scientific_snippets:
        sci_lines = []
        for s in context.scientific_snippets:
            sci_lines.append(f"  - [{s.source}]\n    Affirmation : {s.claim}\n    Contexte : {s.explanation}")
        sections.append("## CONTEXTE SCIENTIFIQUE\n" + "\n".join(sci_lines))

    # Runner memory
    if context.memory_snippets:
        mem_lines = []
        for m in context.memory_snippets:
            mem_lines.append(f"  - {m.reference_period} : {m.observation} ({m.relevance_note})")
        sections.append("## MÉMOIRE COUREUR\n" + "\n".join(mem_lines))

    # Plan hints
    if interp.plan_hints:
        hint_lines = [f"  - {h.hint}" for h in interp.plan_hints]
        sections.append("## CONSEILS DE PLANIFICATION\n" + "\n".join(hint_lines))

    return "\n\n".join(sections)
