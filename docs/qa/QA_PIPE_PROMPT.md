# QA Pipe — Prompt de relance

Copie-colle ce prompt à Claude Code pour relancer le pipe complet.

---

Mets en place ce pipe :
- Tu lances une conversation (1 conversation via `python scripts/run_qa.py --conversations 1`)
- Chaque échange de la conversation, puis ton rapport, doivent être sauvegardés dans `data/qa_pipe/pipe_<timestamp>.md`
- Suite à ton rapport, tu dois répondre à la question "Que proposerais-tu pour fixer cela ?" Si aucune amélioration nécessaire, note que le test est pas mal. Sinon, implémente le fix — fais attention aux régressions (lance `uv run pytest` avant de valider).
- Tu notes aussi si on se rapproche d'un coach de meilleure qualité pour MirrorPace, et le chemin restant pour atteindre un niveau MVP. Utilise le tableau de progression MVP défini dans `data/qa_pipe/mvp_progress.md`.
- Note le coût estimé de chaque conversation (~$0.007 par conversation, 5 tours max).
- Enregistre tout dans le fichier pipe en cours.
- Répète pour chaque conversation. Lance 5 conversations d'affilée en autonomie.

## Seuils MVP de référence

| Dimension | Seuil MVP |
|---|---|
| Score global moyen | ≥ 7.5/10 |
| Cohérence KE | 100% |
| Question answered | ≥ 4/5 moyen |
| Mémoire utilisée | ≥ 50% des convs |
| Ton approprié | ≥ 4/5 moyen |
| Qualité pédago | ≥ 4/5 moyen |
| Intent classification | ≥ 95% correct |
| Medical flag respecté | 100% |
