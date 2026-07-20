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

Phase 1 — Data Engine

Current objective:

Transform raw FIT and GPX files into reliable normalized activity objects.

Do not implement:

- coaching logic
- agents
- RAG systems
- recommendations

before the foundation is stable.

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
