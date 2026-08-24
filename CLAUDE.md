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
- **Knowledge Engine** — ACWR, readiness score, règles P0–P4, DecisionEnvelope — gelé v1.3.2
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

## État QA (2026-08-24)

Pipe de validation du fix gap #2 (correction de profil in-conversation + KE v1.3.2),
8 conversations, toutes personas couvertes (`data/qa_runs/20260824_211205`). Score moyen
Gemini : **8.7/10** (σ≈1.6, en baisse par rapport à 1.99) — jugé aussi avec Groq + Mistral
(`scripts/rejudge_multi_llm.py`) pour éviter de confondre effet du fix et bruit de juge
(voir "Biais de juge QA" ci-dessous).

**Vote à la majorité (2 juges sur 3 ≥ seuil) : 7/8 conversations passent.**

- anxious_beginner ×2 : 10.0/10 — **PASS 3/3**
- ambitious_marathoner : 9.24/10 — **PASS 3/3** ; deuxième conv 7.50/10 — PASS 2/3
- injured_runner : 10.0/10 — **PASS 3/3** (Groq 9.10, Mistral 10.0)
- cautious_runner : 10.0/10 — PASS 3/3
- busy_parent : 7.04/10 — PASS 2/3 (Gemini juste sous le seuil, Groq/Mistral au-dessus)
- performance_obsessed : 5.90/10 — **FAIL 0/3, unanime** (nouveau gap identifié, voir #4
  ci-dessous)

**Gap #2 confirmé résolu** : `ambitious_marathoner` et `injured_runner` — les deux
profils qui faisaient échouer le pipe du 30/07 à cause du gap #2 — passent maintenant à
la majorité de juges indépendants, pas seulement selon Gemini. C'est un signal robuste,
pas un artefact de juge unique (contrairement à ce qu'un seul juge alternatif aurait pu
suggérer — voir constat ci-dessous).

Ancien pipe (2026-07-30, avant le fix) : score moyen 8.11/10, σ≈1.99,
`ambitious_marathoner` 4.66 ❌ et `injured_runner` 7.4 ❌. Détail :
`data/qa_pipe/mvp_progress.md`, `data/qa_pipe/pipe_20260730_183347.md`.

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

### Biais de juge QA — constat du 2026-08-24 (affiné à 3 juges)

Le pipeline QA note les conversations avec `ConversationJudge`, jusqu'ici toujours sur
Gemini 2.5 Flash — le même modèle qui génère la réponse du coach ET simule le persona
coureur. Risque classique de LLM-as-judge : un modèle a tendance à sur/sous-noter sa
propre famille. `ConversationJudge` accepte maintenant un `client` injecté (au lieu de
forcer `QAGeminiClient`), et `src/qa_agent/llm.py` ajoute `QAGroqClient` (Groq, modèle
`openai/gpt-oss-120b`) et `QAMistralClient` (Mistral, `mistral-large-latest`), toutes deux
via l'API OpenAI-compatible (base `_OpenAICompatibleClient` commune). Script
`scripts/rejudge_multi_llm.py` : rejuge les conversations déjà enregistrées sous
`data/qa_runs/*/conversations/` avec Groq + Mistral, réutilise la note Gemini déjà
enregistrée (pas de rappel), et affiche un vote à la majorité (2 juges sur 3 ≥ seuil MVP).

**Premier passage à 2 juges (Gemini vs Groq seul)** laissait penser que Gemini était trop
sévère sur `ambitious_marathoner`/`injured_runner` (Groq remontait ces conversations
nettement au-dessus du seuil). **Le passage à 3 juges renverse cette lecture** : sur les
8 conversations du pipe du 30/07, le vote à la majorité confirme le diagnostic original de
Gemini sur les cas limites — `ambitious_marathoner` (4.66) et les deux `injured_runner`
(7.06, 7.36) restent en échec à la majorité (1/3, Gemini + Mistral d'accord), et c'est
**Groq qui apparaît comme l'outlier optimiste** sur ces conversations précises (jusqu'à
9.10-10.00 quand Gemini et Mistral s'accordent autour de 6.7-7.4). Seuls
`anxious_beginner`, `cautious_runner` et un `performance_obsessed` obtiennent un 3/3 net ;
l'autre `performance_obsessed` (2.46) est un échec confirmé à l'unanimité (0/3).
**Conclusion pratique : le gap #2 (profil biographique vs charge récente) était
probablement un vrai problème produit, pas un artefact du juge Gemini.** Le fix implémenté
cette session reste donc à valider sur ses propres mérites — mais juger le prochain pipe
avec les 3 modèles (majorité, pas Gemini seul) reste la bonne pratique : un seul juge
alternatif (Groq seul) aurait ici mené à une fausse conclusion de "faux positif".

## Gaps produit connus (priorité V2 Coach Intelligence)

1. **Règles KE non décrites** — substantiellement amélioré : plus de code brut
   "RULE-009" observé ; le coach cite la description texte de la règle (parfois encore
   entre guillemets de façon un peu technique). Impact résiduel faible sur `pedagogical_quality`.

2. **Profil biographique vs charge récente** — **✅ résolu et validé (2026-08-24)**. Le KE
   classe un coureur "débutant" selon sa charge d'activité récente ; ce comportement est
   volontaire (`compute_experience_level`, garde-fou anti-surestimation) et le calcul
   lui-même n'a pas changé. Ce qui manquait : (a) `experience_level_declared`/
   `years_running` n'étaient jamais mis à jour depuis la conversation — ajouté
   `RunnerProfileStore.save()`, détection d'une correction candidate par le
   `FollowupHandler` (confirmation explicite requise avant écriture —
   `ProfileCorrectionHandler`), état `pending_profile_correction` sur la session ; (b)
   `experience_level_source` (declared|calculated|reconciled) était calculé puis jeté par
   l'orchestrator, donc le coach ne pouvait jamais citer la vraie raison — **KE étendu en
   v1.3.2** (`docs/knowledge_engine/KB_CANONICAL_v1.3.2.md`) : `experience_level`/
   `experience_level_source` exposés sur `DecisionEnvelope` et injectés dans le prompt du
   `FollowupHandler`. Validé par le pipe du 24/08 : `ambitious_marathoner` et
   `injured_runner` passent maintenant à la majorité de 3 juges indépendants (voir
   "État QA" ci-dessus).

3. **Données brutes non exposées** — profils data-driven demandent HRV, score sommeil
   Garmin. Non testable de façon concluante avec le jeu de données Strava actuel (pas de
   HRV/sommeil dans l'export).

4. **Explication ACWR insuffisante pour profil data-driven (nouveau, 2026-08-24)** —
   `performance_obsessed` échoue à l'unanimité des 3 juges (5.90/7.44/5.34, seul échec du
   pipe du 24/08). Le coach ne sait pas expliquer comment l'ACWR sera géré après une
   reprise à volume réduit (ex: 5km) pour un coureur expérimenté — celui-ci se sent
   "ignoré et infantilisé" par une recommandation qui ignore son passif. Contrairement au
   gap #2, ce n'est pas un problème de données manquantes mais de pédagogie/explication :
   le coach devrait pouvoir projeter/expliquer la trajectoire de charge à venir, pas
   seulement la semaine courante.

## Immediate next steps

1. **Gap #4** — améliorer l'explication de la trajectoire ACWR pour les profils
   data-driven/expérimentés (`performance_obsessed` échoue à l'unanimité, voir gap #4
   ci-dessus). Probablement un chantier Coach Intelligence (prompt/contexte), pas KE.
2. Alimenter la Runner Memory — renseigner les actual_outcome sur décisions passées
3. Envisager d'assouplir la détection de question sans "?" dans la passe regex de
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
