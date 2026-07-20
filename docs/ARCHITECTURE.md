# Architecture

## High level architecture

Raw Data
(FIT / GPX)
|
v
Data Engine
|
v
Structured Database
|
v
Runner Intelligence
|
v
Runner Model
|
v
Coach Agent

---

# Layer responsibilities

## Data Engine

Question:

"What happened?"

Responsible for:

- parsing files
- normalization
- storing objective facts

Not responsible for:

- interpretation
- coaching

---

## Analytics

Question:

"What can we calculate?"

Responsible for:

- volume
- trends
- comparisons
- performance metrics

Not responsible for:

- decisions

---

## Activity Intelligence

Question:

"What does this session mean?"

Responsible for:

- classifying sessions
- extracting insights
- understanding execution

---

## Runner Model

Question:

"Who is this athlete today?"

Responsible for:

- current fitness
- fatigue
- recovery
- training profile

---

## Coach Agent

Question:

"What should happen next?"

Responsible for:

- recommendations
- explanations
- adaptation proposals
