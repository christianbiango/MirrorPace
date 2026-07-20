# Ingestion Module

This module belongs to:

Phase 1 — Data Engine

## Responsibility

Convert raw activity files into normalized domain objects.

Supported formats:

- FIT
- GPX

## Rules

This module must:

- read files
- extract information
- normalize formats

This module must NOT:

- calculate training intelligence
- classify sessions
- call LLMs
- make coaching decisions

## Design principles

Keep parsers simple.

Prefer:

Raw file
↓
Parser
↓
Normalized object

Avoid putting business logic inside parsers.
