# Principles

Ce dossier contient les connaissances extraites des sources externes.

## Qu'est-ce qu'un principe ?

Un principe est une connaissance générale issue d'une ou plusieurs sources identifiées,
reformulée de manière applicable au contexte de MirrorPace.

Un principe n'est **pas encore une règle**.
Il décrit ce qui est vrai dans un contexte donné, avec ses limites et ses exceptions.

Il répond à la question : *"Que sait-on sur ce sujet ?"*

## Ce qu'un principe n'est pas

- Une opinion de Claude
- Une règle opérationnelle
- Une connaissance sans source

## Organisation

Les principes sont organisés par domaine :

| Dossier | Domaine |
|---|---|
| `periodization/` | structuration des cycles d'entraînement |
| `training_load/` | charge, volume, progression |
| `fatigue_recovery/` | fatigue, récupération, signaux d'alarme |
| `session_design/` | construction des séances |
| `marathon_specificity/` | préparation et spécificité marathon |
| `performance_prediction/` | prédiction de performance, indicateurs |

## Ajout d'un principe

1. Une question dans `research_queue/` doit exister
2. Une source dans `sources/` doit être référencée
3. Copier `principle_template.yaml` dans le bon dossier
4. Remplir tous les champs, notamment `origin_sources`
