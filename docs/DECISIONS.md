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

---

# Decision 011

Date: 2026-07-22

Topic: Runner Memory — format de stockage V1 (YAML, deux fichiers)

Decision:

La mémoire coureur est stockée dans deux fichiers YAML append-only :
- `data/memory/decisions.yaml` — historique des décisions de coaching
- `data/memory/events.yaml` — événements coureur (blessures, courses, arrêts)

Chaque entrée a un `id` déterministe (SHA256[:12] des champs clés) qui garantit la déduplication :
ajouter une entrée déjà existante est un no-op.

Reason:

Projet mono-athlète à ce stade. Peu d'entrées (quelques dizaines par an).
YAML = human-readable, éditable directement, versionnable avec git.
Cohérent avec `runner_profile.yaml` déjà en place.
Une DB supplémentaire ou du JSON Lines apporterait de la complexité sans bénéfice réel.
Le protocole `VectorStore` permet de remplacer le store par un embedding store plus tard sans toucher au reste.

Status: Valide jusqu'à multi-athlète ou volume élevé d'entrées (alors → SQLite ou vector DB)

---

# Decision 012

Date: 2026-07-22

Topic: CoachingDecision — champs de contexte pour la traçabilité longitudinale

Decision:

`CoachingDecision` capture trois champs au-delà du résultat brut :

- `decision_ref` : SHA256[:12] de `computed_at + action + readiness_score` — identifiant stable de l'envelope
- `dominant_rules` : liste des rule_id déclenchés — les raisons déterministes de la décision
- `key_metrics_snapshot` : snapshot des métriques au moment de la décision
  (weekly_distance_km, previous_week_distance_km, readiness_score, readiness_confidence,
  fatigue_score, sleep_quality_score, days_since_last_run, target_next_week_km, acwr si disponible)

Reason:

Une mémoire qui stocke uniquement l'action ("slight_increase") est inutile sans contexte.
Dans 6 mois, il doit être possible de répondre à : "Pourquoi cette décision avait été prise ?"
Les champs de contexte permettent de retrouver les conditions exactes sans relire la DB.

Status: Permanent

---

# Decision 013

Date: 2026-07-22

Topic: MemoryWriter branché sur DecisionEnvelope, pas sur CoachResponse

Decision:

`MemoryWriter.record(envelope, state)` est appelé entre le Knowledge Engine et Coach Intelligence :

```
envelope = run_engine(state, config)
MemoryWriter(store).record(envelope, state)   ← ici
response = build_coach_response(envelope, ...)
```

La mémoire n'est pas alimentée après `build_coach_response()`.

Reason:

La mémoire doit enregistrer la décision du système (KE), pas la formulation du LLM.
Si le LLM reformule ou atténue la recommandation, la mémoire reste fidèle à la décision réelle.
Cela garantit aussi que la mémoire est alimentée même si l'appel LLM échoue.

Status: Permanent

---

# Decision 014

Date: 2026-07-22

Topic: RunnerEvent manuel V1 — BehavioralPattern différé à V2

Decision:

En V1 :
- `RunnerEvent` (blessures, courses, arrêts) = saisie manuelle dans `data/memory/events.yaml`
- `BehavioralPattern` (ex : "réagit mal aux augmentations >10%") = non implémenté

Reason:

`RunnerEvent` nécessite une source externe (le coureur lui-même). Il n'existe pas encore
de mécanisme d'input utilisateur (ce sera le Coach Agent). La saisie YAML directe est
suffisante et sans risque pour la V1.

`BehavioralPattern` est une donnée dérivée : elle n'est pertinente qu'après accumulation
de plusieurs `CoachingDecision` avec `actual_outcome` renseigné. Le construire maintenant
serait prématuré — aucune donnée ne l'alimente encore.

Status: RunnerEvent manuel jusqu'au Coach Agent / BehavioralPattern différé à V2

---

# Decision 015

Date: 2026-07-22

Topic: Runner Memory RAG — Jaccard V1, embeddings différés

Decision:

`RunnerContextRetriever` utilise `InMemoryVectorStore` (Jaccard sur tokens) pour indexer
les entrées mémoire, identique à `ScientificRetriever`.

Reason:

Pour ~50 entrées mémoire par an, la similarité sémantique par embeddings n'apporte pas
de valeur mesurable par rapport à Jaccard sur les tokens clés (action, rule_ids, body_part, etc.).
Le protocole `VectorStore` est déjà en place — swapper vers un embedding store est
une substitution sans impact sur le reste du pipeline.

Status: Valide jusqu'à ~200 entrées ou besoin de recherche sémantique avérée

---

# Decision 016

Date: 2026-07-22

Topic: Coach Agent V1 — IntentClassifier hybride (patterns + LLM fallback)

Decision:

L'`IntentClassifier` utilise une première passe déterministe (regex sur texte normalisé),
et ne fait appel au LLM que si l'intention est ambiguë (0 ou plusieurs catégories matchées).

Règle de routage :
- Exactement 1 catégorie matche → intent retourné, confidence="high", method="pattern"
- 0 ou 2+ catégories matchent → appel LLM avec prompt contraint → {"intent": "..."}
- LLM absent → fallback GENERAL_QUESTION, confidence="low"

L'interface `IntentClassifier.classify()` est unique — l'implémentation interne peut
être swappée sans toucher aux handlers ou à l'agent.

Reason:

Un appel LLM systématique par turn pour la classification seule est disproportionné
pour un usage CLI mono-athlète. Les patterns couvrent les cas courants (~80%) avec
latence nulle. Le fallback LLM gère les formulations ambiguës sans maintenir une liste
de patterns exhaustive.

Status: Permanent jusqu'à besoin de classification multilingue ou domaine élargi

---

# Decision 017

Date: 2026-07-22

Topic: Coach Agent V1 — FeedbackEntry lié à decision_ref dès V1

Decision:

`FeedbackEntry` capture `decision_ref` (SHA256[:12] de l'envelope KE) au moment
où le feedback est reçu. Stocké dans `data/memory/feedback.yaml`.

```python
@dataclass
class FeedbackEntry:
    id: str
    runner_id: str
    decision_ref: str | None   # None si aucune analyse en session
    session_id: str
    text: str
    timestamp: str
```

Le `decision_ref` provient de `session.last_decision_record.decision_ref`,
qui est l'identifiant stable de la décision KE ayant produit la recommandation.

Reason:

Un feedback sans ancrage décisionnel est inutile pour la traçabilité longitudinale.
La question "pourquoi le coureur a abandonné la semaine après une décision slight_increase ?"
ne peut être répondue qu'en liant le feedback à la décision exacte du système.
Le lien est établi dès V1 même si le traitement du feedback est différé à V2.

Status: Permanent

---

# Decision 018

Date: 2026-07-22

Topic: Coach Agent V1 — FollowupHandler query directe sur InMemoryVectorStore

Decision:

Le `FollowupHandler` accède à la mémoire via `build_runner_context_store()` +
`InMemoryVectorStore.query(text, k)` directement, sans passer par `RunnerContextRetriever`.

Reason:

`RunnerContextRetriever.retrieve()` prend un `InterpretedDecision` comme paramètre
de query (construit à partir d'un `DecisionEnvelope`). Les follow-ups arrivent
après la phase d'analyse : relancer l'interprétation juste pour une query mémoire
serait un couplage inutile.

L'`InMemoryVectorStore` expose `query(text, k)` directement, ce qui suffit
pour une recherche par tokens sur le message utilisateur.

Status: Permanent V1. Si besoin de sémantique avancée → implémenter un QueryBuilder
dédié qui construit la query depuis un message libre.
