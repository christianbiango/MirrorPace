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

All layers up to and including Coach Agent V1 are implemented and tested (398 tests).

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

Phase 7 — Coach Agent V1 livré

Completed: toutes les couches jusqu'à Coach Agent V1 (398 tests verts).

Current objective:

Valider les conversations réelles via `scripts/run_agent.py`, puis itérer.

Immediate next steps:

1. Lancer `python scripts/run_agent.py` et tester les 4 intents sur données réelles
2. Itérer sur Coach Intelligence — affiner le prompt sur 5-10 runs réels via eval_coach.py
3. Alimenter la Runner Memory — renseigner les actual_outcome sur décisions passées
4. Implémenter `src/coach_agent/` — couche conversationnelle et agentique

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
