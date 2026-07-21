# Instructions pour Claude — Knowledge Engine

## Règle absolue

Ne jamais ajouter de contenu dans `principles/` ou `rules/` sans qu'une source externe soit référencée dans `sources/` et enregistrée dans `metadata/sources.yaml`.

## Ordre d'ajout obligatoire

1. Identifier une source externe (livre, article, étude, interview)
2. La documenter dans `sources/` avec le template approprié
3. L'enregistrer dans `metadata/sources.yaml`
4. Extraire un ou plusieurs principes dans `principles/`
5. Transformer les principes en règles dans `rules/` si applicable

## Ce qui est interdit

- Ajouter un principe basé sur la connaissance propre de Claude
- Inventer une règle sans principe associé
- Créer un principe sans source identifiée
- Paraphraser des connaissances générales sans les attribuer

## Niveaux de confiance

Chaque principe et chaque règle doit avoir un champ `confidence` :

- `high` — issu d'études peer-reviewed ou de consensus fort dans la littérature
- `medium` — issu de praticiens reconnus, pas encore validé scientifiquement
- `low` — issu d'une seule source, à confirmer

## En cas de doute

Ajouter la question dans `research_queue/questions_to_answer.md` plutôt que d'inventer une réponse.
