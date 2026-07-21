# Rules

Ce dossier contient les règles décisionnelles du coach.

## Qu'est-ce qu'une règle ?

Une règle est la transformation opérationnelle d'un principe en logique utilisable par l'agent coach.

Elle répond à la question :
*"Dans cette situation précise, quelle décision un coach pourrait-il prendre ?"*

## Ce qu'une règle n'est pas

- Un principe général (voir `principles/`)
- Une règle sans principe associé
- Une règle sans source traçable

## Structure d'une règle

Une règle a toujours la forme :

```
SI   [conditions mesurables depuis les données du coureur]
ALORS [décision ou action recommandée]
SAUF SI [exceptions]
```

Les conditions doivent être exprimables à partir des données disponibles :
- Runner Model (état actuel)
- Analytics (weekly stats, pace trend, personal bests)
- Activity Intelligence (classification des séances)
- Personal Memory RAG (historique du coureur)

## Organisation

| Dossier | Domaine |
|---|---|
| `volume/` | décisions sur le volume hebdomadaire |
| `intensity/` | décisions sur la répartition des intensités |
| `recovery/` | décisions sur la récupération |
| `adaptation/` | décisions d'adaptation à la progression |
| `race_preparation/` | décisions en phase de préparation à une course |

## Ajout d'une règle

1. Un principe dans `principles/` doit exister
2. Ce principe doit avoir au moins une source dans `sources/`
3. Copier `rule_template.yaml` dans le bon dossier
4. Remplir `supporting_principles` et `origin_sources`
