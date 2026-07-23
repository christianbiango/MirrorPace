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

## État QA (2026-07-23)

5 conversations lancées. Score moyen : **6.96/10** (seuil MVP : 7.5).

Résultats par profil :
- anxious_beginner : 9.60/10 ✅
- ambitious_marathoner : 8.04/10 ✅
- injured_runner : 4.42/10 ❌
- cautious_runner : 7.58/10 ✅
- performance_obsessed : 5.18/10 ❌

Détail complet : `data/qa_pipe/mvp_progress.md`
Transcripts + rapports : `data/qa_pipe/pipe_20260722_231435.md`

## Gaps produit connus (priorité V2 Coach Intelligence)

1. **Règles KE non décrites** — le coach cite "RULE-009" sans expliquer son contenu en langage naturel.
   Impacte : `pedagogical_quality` sur tous les profils.

2. **Profil biographique vs charge récente** — le KE classe un coureur "débutant" selon sa charge
   d'activité récente (11km/semaine), même si l'utilisateur déclare 8 ans d'expérience.
   Le FollowupHandler reconnaît maintenant la discordance (fix appliqué) mais ne peut pas corriger
   la classification. Fix complet : mécanisme de correction profil in-conversation.

3. **Données brutes non exposées** — profils data-driven demandent HRV, score sommeil Garmin.
   Le coach ne peut pas les fournir car ils ne remontent pas jusqu'au FollowupHandler.

## Immediate next steps

1. Itérer sur Coach Intelligence — ajouter descriptions lisibles des règles KE dans le prompt
2. Lancer un nouveau pipe QA de 5 conversations pour mesurer l'impact
3. Alimenter la Runner Memory — renseigner les actual_outcome sur décisions passées
4. Mécanisme de correction profil in-conversation (moyen terme)

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
