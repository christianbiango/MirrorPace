# Architectural Decisions

This file records important decisions.

---

# Decision 001

Date:
2026-07-19

Topic:
Project direction

Decision:

The project is not a RAG chatbot over Strava.

Reason:

A RAG system can retrieve information but cannot represent a persistent athlete state.

Status:

Permanent

---

# Decision 002

Topic:
Data architecture

Decision:

Structured quantitative data belongs in a database.

Reason:

Metrics and statistics require deterministic computation.

Status:

Permanent

---

# Decision 003

Topic:
LLM responsibility

Decision:

The LLM does not calculate athlete metrics.

Reason:

Calculations must be deterministic and reproducible.

Status:

Permanent

---

# Decision 004


Topic:
Development order

Decision:

Build athlete understanding before coaching.

Reason:

A coach without athlete understanding is generic.

Status:

Permanent

---

# Decision 005

Date: 2026-07-21

Topic: Coach Intelligence — séparation des responsabilités

Decision:

Coach Intelligence est une couche déterministe entre Knowledge Engine et Coach Agent.
KE = décision, CI = interprétation/personnalisation/génération, CA = actions conversationnelles (futur).
CI n'a aucun comportement agentique.

Reason:

Garder la logique de décision testable et reproductible. Le LLM intervient uniquement pour
la génération de la réponse finale, jamais pour calculer des métriques ou prendre la décision.

Status: Permanent

---

# Decision 006

Date: 2026-07-21

Topic: Medical alert — injection structurelle dans SafetyGuard

Decision:

Les alertes médicales sont injectées par SafetyGuard après la réponse LLM, pas générées par le LLM.
Le LLM ne peut pas atténuer ou ignorer une alerte médicale.

Reason:

La sécurité médicale ne peut pas dépendre de la formulation d'un modèle de langage.
SafetyGuard est déterministe et systématique : si medical_flag=True, l'alerte est toujours présente.

Status: Permanent

---

# Decision 007

Date: 2026-07-21

Topic: RunnerProfileStore — YAML plutôt que table DB

Decision:

Le profil de l'athlète (âge, expérience, pathologies, VMA, objectifs) est stocké dans
`data/runner_profile.yaml`, pas dans une table SQL.

Reason:

Projet mono-athlète. Le profil change rarement (quelques fois par an).
YAML = lisible et éditable directement, versionnable avec git, zéro migration.
Une table SQL apporterait de la complexité sans bénéfice réel à ce stade.

Status: Valide jusqu'à multi-athlète (alors → table profiles)

---

# Decision 008

Date: 2026-07-21

Topic: Single-read pattern pour la cohérence temporelle

Decision:

Les activités sont lues une seule fois depuis le DB, puis la même liste est passée
à `build_snapshot()` et `build_runner_state()`.

```python
activities = repo.get_all()
snapshot   = build_snapshot(activities)
state      = build_runner_state(activities, profile, runner_id)
```

Reason:

RunnerSnapshot et RunnerState.week dérivent tous les deux des activités.
Si on lit deux fois, une nouvelle activité importée entre les deux lectures crée
une incohérence (ex. : ACWR calculé sur N activités, snapshot sur N+1).

Status: Permanent

---

# Decision 009

Date: 2026-07-21

Topic: 4 patches de dette Coach Intelligence (à appliquer avant Coach Agent)

Decision:

Les points suivants ont été identifiés comme dette et doivent être corrigés
avant de construire le Coach Agent :

1. **scientific_context depuis les snippets RAG, pas le LLM** — le LLM fabrique
   des références, risque hallucination critique.
2. **response_ref stable** — actuellement basé sur `date.today()` dans le hash SHA256,
   donc non-déterministe entre appels.
3. **Retirer severity de la query ScientificRetriever** — severity n'est pas dans
   les tags de la KB, c'est du bruit dans la similarité Jaccard.
4. **Store ScientificRetriever en singleton** — le store est reconstruit à chaque
   instantiation alors que la KB est statique.

Reason:

Impact direct sur la fiabilité des réponses et les performances.
Déprioritisés pour valider le flux end-to-end d'abord.

Status: Dette à solder avant Coach Agent

---

# Decision 010

Date: 2026-07-21

Topic: WeekInputBuilder — définition de la semaine courante et de l'historique

Decision:

La semaine courante = lundi de la semaine ISO contenant `reference_date` … `reference_date` inclus.
`weekly_distance_history` contient les N semaines complètes précédentes, semaine en cours exclue.
Default `reference_date = date.today()` ; paramétrable pour les backtests.

Reason:

Le KE calcule ACWR = weekly_distance_km (acute) / mean(weekly_distance_history[:4]) (chronic).
Inclure la semaine en cours dans l'historique doublerait le comptage de la charge aiguë.

Status: Permanent
