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
