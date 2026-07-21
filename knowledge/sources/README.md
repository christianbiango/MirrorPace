# Sources

Ce dossier contient les documents externes bruts référencés par le Knowledge Engine.

Une source décrit ce qu'un auteur ou chercheur affirme.
Elle n'est pas encore interprétée — c'est le rôle des principes.

## Types de sources

| Type | Dossier | Exemples |
|---|---|---|
| Livre | `books/` | ouvrages de physiologie, guides d'entraînement |
| Article scientifique | `scientific_papers/` | études peer-reviewed |
| Interview | `interviews/` | entretiens avec entraîneurs ou athlètes |
| Vidéo | `videos/` | conférences, podcasts avec transcript |
| Article | `articles/` | articles de presse spécialisée, blogs de référence |

## Ajout d'une source

1. Copier `source_template.yaml` dans le dossier correspondant
2. Renommer avec l'identifiant de la source (ex: `daniels_running_formula_2014.yaml`)
3. Remplir tous les champs
4. Enregistrer dans `../metadata/sources.yaml`

## Champ `credibility`

- `peer_reviewed` — étude scientifique avec comité de lecture
- `expert_practitioner` — praticien reconnu dans le domaine
- `community` — source communautaire, à recouper
