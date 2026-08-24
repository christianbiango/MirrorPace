# CLAUDE.md

This file provides guidance to Claude Code when working on this repository.

---

# Project Identity

This project builds a personal AI running coach for a single athlete over time.

The objective is not to build a chatbot over Strava data.

The objective is to progressively build a digital twin of a runner:
a persistent model that understands the athlete, follows its evolution,
and eventually helps make better training decisions.

The fundamental question:

"If a professional coach had followed this runner for several years,
what would they already know?"

---

# Core Principle

Do not build an AI coach first.

Build an understanding of the athlete first.

The development order is:

Data Engine
↓
Runner Intelligence
↓
Activity Intelligence
↓
Runner Model
↓
Knowledge Engine
↓
Coach Agent

Do not skip layers.

Coach Intelligence sits between Knowledge Engine and Coach Agent:

Data Engine
↓
Runner Intelligence
↓
Activity Intelligence
↓
Runner Model
↓
Knowledge Engine
↓
Coach Intelligence   ← interprétation, personnalisation, génération LLM
↓
Coach Agent

Do not skip layers.

---

# Completed Layers

All layers up to and including QA Agent are implemented and tested (434 tests).

- **Data Engine** — parsing FIT/GPX, normalisation Activity, SQLite via ActivityRepository
- **Activity Intelligence** — classifier intensité, pace trends, personal bests
- **Analytics** — weekly stats, progression slope, coefficient of variation
- **Runner Model** — RunnerSnapshot (build_snapshot), WeekInputBuilder, RunnerProfileStore, RunnerStateBuilder
- **Knowledge Engine** — ACWR, readiness score, règles P0–P4, DecisionEnvelope — gelé v1.3.1
- **Coach Intelligence v1.0.1** — EnvelopeInterpreter, RunnerPersonalizer, ScientificRetriever (13 entrées KB),
  RunnerContextRetriever, ReasoningContextBuilder, PromptBuilder, ResponseAssembler, SafetyGuard, FeedbackCollector
- **Runner Memory** — CoachingDecision + RunnerEvent, MemoryStore YAML, MemoryWriter (branché sur DecisionEnvelope)
- **Coach Agent V1** — CoachAgent, IntentClassifier (hybride patterns/LLM), AnalysisHandler, FollowupHandler,
  FeedbackHandler (avec decision_ref), SessionStore, FeedbackStore, scripts/run_agent.py
- **QA Agent** — SimulatedRunner (Gemini 2.5 Flash), ConversationRunner, HardChecks (déterministes),
  ConversationJudge (Gemini 2.5 Flash), ReportGenerator, 6 profils (anxious_beginner, ambitious_marathoner,
  injured_runner, cautious_runner, busy_parent, performance_obsessed), scripts/run_qa.py

---

# Non Negotiable Decisions

- This is not a RAG-first project.
- The database is the source of truth for quantitative data.
- RAG is only for semantic knowledge and context.
- The LLM is a reasoning engine, not the source of athlete facts.
- The Runner Model is a persistent state, not a collection of activities.
- Raw data must always be preserved.
- Manual activity annotation is optional.
- The product is not a dashboard.

---

# Current Phase

The project is currently in:

Phase 8 — QA conversationnel en cours

Completed: toutes les couches jusqu'à QA Agent (434 tests verts).

Current objective:

Atteindre les seuils MVP sur les 8 critères QA via des itérations sur Coach Intelligence.

## État QA (2026-07-30)

Premier pipe QA sur données réelles (39 activités Strava importées, profil minimal
runner_id=christian/age=23/sex=male). 8 conversations lancées (5 officielles + 3
vérifications post-fix). Score moyen : **8.11/10** (seuil MVP : 7.5) — **seuil atteint**,
avec variance élevée (σ≈1.99) et un résultat porté surtout par 3 bugs corrigés
(voir ci-dessous), pas par une résolution des gaps produits connus.

Résultats par profil :
- anxious_beginner : 10.0/10 ✅ (était 9.60)
- ambitious_marathoner : 4.66/10 ❌ (était 8.04 — chute due au gap #2, déclenché cette fois)
- injured_runner : 7.4/10 ❌ proche seuil (était 4.42 — net progrès)
- cautious_runner : 10.0/10 ✅ (était 7.58)
- performance_obsessed : 8.48/10 ✅ (était 5.18 — net progrès)

Détail complet : `data/qa_pipe/mvp_progress.md`
Transcripts + rapports : `data/qa_pipe/pipe_20260730_183347.md`

### Bugs corrigés pendant ce pipe

1. **Troncature JSON du coach** — les tokens de "thinking" de Gemini 2.5 Flash comptaient
   dans `max_output_tokens`, tronquant parfois la réponse JSON en plein milieu (fuite de
   JSON brut à l'utilisateur). Fix : `thinking_config=ThinkingConfig(thinking_budget=0)`
   dans `src/coach_intelligence/llm/gemini_client.py`.
2. **Troncature des messages du simulateur QA** pour personas verbeux (`max_tokens=300`
   trop court). Fix : porté à 700 dans `src/qa_agent/simulation/simulated_runner.py`.
3. **IntentClassifier** routait en `FEEDBACK` un message de correction de profil contenant
   une question sans "?" littéral → réponse générique "Noté", tour de conversation perdu.
   Fix : prompt système du fallback LLM renforcé dans `src/coach_agent/intent/classifier.py`.

## Gaps produit connus (priorité V2 Coach Intelligence)

1. **Règles KE non décrites** — substantiellement amélioré : plus de code brut
   "RULE-009" observé ; le coach cite la description texte de la règle (parfois encore
   entre guillemets de façon un peu technique). Impact résiduel faible sur `pedagogical_quality`.

2. **Profil biographique vs charge récente** — **non résolu, confirmé récurrent**. Le KE
   classe un coureur "débutant" selon sa charge d'activité récente, même si le coureur
   déclare une forte expérience en cours de conversation. Le coach reconnaît honnêtement
   la discordance mais ne peut pas corriger la classification. C'est la cause principale
   des scores encore sous le seuil (ambitious_marathoner, injured_runner). Fix complet :
   mécanisme de correction profil in-conversation.

3. **Données brutes non exposées** — profils data-driven demandent HRV, score sommeil
   Garmin. Non testable de façon concluante avec le jeu de données Strava actuel (pas de
   HRV/sommeil dans l'export).

## Immediate next steps

1. Mécanisme de correction profil in-conversation (gap #2) — priorité n°1, seul gap
   connu qui reste un vrai risque de score sur plusieurs profils
2. Lancer un nouveau pipe QA de 5-10 conversations pour vérifier la stabilité du score
   moyen ≥7.5 (variance actuelle élevée)
3. Alimenter la Runner Memory — renseigner les actual_outcome sur décisions passées
4. Envisager d'assouplir la détection de question sans "?" dans la passe regex de
   l'IntentClassifier (`src/coach_agent/intent/classifier.py`)

---

# Documentation

Read the relevant documentation before making architectural decisions.

General vision:
docs/PROJECT_VISION.md

System architecture:
docs/ARCHITECTURE.md

Current phase:
docs/DATA_ENGINE.md

Past decisions:
docs/DECISIONS.md

---

# Engineering Rules

## Python

Use:

- Python type hints
- dataclasses or Pydantic for domain objects
- explicit transformations
- modular architecture

Avoid:

- giant classes
- hidden logic
- premature abstractions

## Testing

Important calculations must have tests.

Especially:

- pace calculations
- distance calculations
- metric aggregation
- parsing behavior

## General rule

Before coding, understand why the feature exists.

Prefer a simple correct system over premature complexity.

### Project updates

After a milestone is reached, you should update CLAUDE.md and README.md files, if necessary.
