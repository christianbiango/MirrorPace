# Data Engine

Current project phase.

## Objective

Transform raw activity files into reliable normalized activity objects.

The Data Engine creates facts.

It does not create intelligence.

---

# Supported inputs

Currently:

- FIT
- GPX

Future:

- Garmin API
- Coros
- Polar
- Suunto

---

# Data flow

FIT / GPX
|
v
Parser
|
v
Normalized Activity
|
v
Database

---

# Parser rules

Parsers must:

- read source files
- extract available information
- normalize formats

Parsers must not:

- calculate training concepts
- evaluate session quality
- make recommendations

---

# Data principles

Raw information must always remain accessible.

Never destroy information by simplifying too early.

Example:

Keep:

- elapsed time
- moving time
- timer time

Do not immediately merge them into one duration.

---

# Current goal

At the end of Phase 1:

The system should reliably import the complete Strava archive
and represent every activity in a consistent format.
