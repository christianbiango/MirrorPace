# Architecture

## Stack actuelle (Phase 6 — pre-Coach Agent)

```
Raw Data (FIT / GPX / CSV Strava)
        |
        v
  Data Engine
  (parsing, normalisation, ActivityRepository → SQLite)
        |
        v
  Structured Database
  data/mirrorpace.db
        |
        v
  Activity Intelligence      Analytics
  (classifier intensité,      (weekly stats, pace trends,
   pace trends, PBs)          personal bests)
        |                          |
        +----------+---------------+
                   |
                   v
            Runner Model
     (RunnerSnapshot + WeekInputBuilder
      + RunnerProfileStore + RunnerStateBuilder)
                   |
                   v
         Knowledge Engine
      (règles P0–P4, ACWR, readiness score)
                   |
                   v
          DecisionEnvelope
                   |
        +----------+----------+
        |                     |
        v                     v
  MemoryWriter          Coach Intelligence
  (Runner Memory)       (RAG + LLM → CoachResponse)
        |                     |
        v                     v
  data/memory/         CoachResponse
  decisions.yaml       (decision_summary, main_message,
  events.yaml           scientific_context, plan_hints, …)
        |
        v
  RunnerContextRetriever
  (indexe la mémoire → nourrit CI au prochain run)

        ↓ (futur)
   Coach Agent
   (conversation, mémoire session, actions)
```

---

## Layer responsibilities

### Data Engine

Question : "Que s'est-il passé ?"

- Parsing FIT / GPX
- Normalisation en objets `Activity`
- Stockage dans `ActivityRepository` (SQLite)

Ne fait pas : interprétation, coaching.

---

### Analytics

Question : "Que peut-on calculer ?"

- Volume hebdomadaire
- Tendances de pace
- Records personnels
- Statistiques de progression

Ne fait pas : décisions.

---

### Activity Intelligence

Question : "Que signifie cette séance ?"

- Classification d'intensité (easy / moderate / hard)
- Extraction de contexte athlète (`AthleteContext`)

---

### Runner Model

Question : "Qui est cet athlète aujourd'hui ?"

Composants :
- `RunnerSnapshot` — état historique agrégé (fitness trend, volume moyen, PBs)
- `RunnerProfileStore` — profil statique YAML (âge, VMA, objectifs, pathologies)
- `WeekInputBuilder` — métriques objectives de la semaine courante
- `RunnerStateBuilder` — assemble `RunnerState` complet à partir des activités + profil

---

### Knowledge Engine

Question : "Quelle est la décision pour cette semaine ?"

- Calculs déterministes : ACWR, fatigue trend, readiness score, experience level
- Règles P0–P4 (safety, progression, planning, race day)
- Produit un `DecisionEnvelope` : action, readiness, règles déclenchées, plan hints

Gelé en v1.3.1. Ne change pas sans révision du spec.

---

### Runner Memory

Question : "Qu'est-ce qui s'est déjà passé avec CE coureur ?"

Composants :
- `CoachingDecision` — une entrée par run pipeline, avec contexte complet
  (decision_ref, dominant_rules, key_metrics_snapshot, expected_outcome, actual_outcome)
- `RunnerEvent` — événements manuels (blessures, courses, arrêts)
- `MemoryStore` — persistence YAML, déduplication par id déterministe
- `MemoryWriter` — branché sur `DecisionEnvelope` (pas sur `CoachResponse`)
- `build_runner_context_store` — indexe la mémoire en `InMemoryVectorStore` (Jaccard)

Alimenté automatiquement à chaque run. `RunnerEvent` en saisie manuelle (V1).

---

### Coach Intelligence

Question : "Comment expliquer et personnaliser cette décision pour ce coureur ?"

Composants :
- `EnvelopeInterpreter` — traduit `DecisionEnvelope` en `InterpretedDecision`
- `RunnerPersonalizer` — construit le contexte de personnalisation depuis `RunnerSnapshot`
- `ScientificRetriever` — RAG Jaccard sur 13 entrées KB scientifique
- `RunnerContextRetriever` — RAG Jaccard sur la mémoire coureur
- `ReasoningContextBuilder` — assemble le contexte complet pour le LLM
- `PromptBuilder` — construit le prompt (system + user) avec les vraies valeurs chiffrées
- `ResponseAssembler` — appel LLM via protocole `LLMClient`
- `SafetyGuard` — injection déterministe des alertes médicales, parsing JSON, response_ref

Clients LLM disponibles : `GeminiLLMClient`, `OpenAILLMClient`, `AnthropicLLMClient`.

Ne prend pas de décisions. Ne calcule pas de métriques. Le LLM génère uniquement le texte.

---

### Coach Agent (futur)

Question : "Que faire et comment dialoguer avec le coureur ?"

- Conversation multi-tour
- Mémoire de session
- Interprétation des follow-ups ("pourquoi ?", "détaille", "adapte")
- Déclenchement d'actions (mise à jour profil, ajout RunnerEvent, etc.)

---

## Règles d'or

- La DB est la source de vérité pour les données quantitatives.
- Le LLM est un moteur de génération de texte, pas un moteur de décision.
- La décision vient du Knowledge Engine (déterministe, testable, reproductible).
- La mémoire enregistre la décision du KE, pas la formulation du LLM.
- Les alertes médicales sont injectées par `SafetyGuard`, jamais générées par le LLM.
- Le RAG (scientifique + mémoire) nourrit le raisonnement, ne le remplace pas.
