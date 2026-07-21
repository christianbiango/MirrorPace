# Instructions pour Claude — Rules

- Une règle ne peut exister sans au moins un principe dans `../principles/`.
- Les `conditions` doivent référencer des données réellement disponibles dans le système (runner_model, analytics, activity_intelligence).
- Ne pas inventer de seuils numériques sans source. Si un seuil est inconnu, l'indiquer avec `confidence: low` et ajouter la question dans `../../research_queue/questions_to_answer.md`.
- Le champ `supporting_principles` est obligatoire.
- Une règle doit être testable : si on ne peut pas évaluer ses conditions à partir des données du système, elle n'est pas encore opérationnelle.
