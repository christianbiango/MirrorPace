# MirrorPace

A personal AI running coach that builds a persistent digital twin of a single athlete over time.

Not a chatbot over Strava data — a model that understands the athlete, follows their evolution, and helps make better training decisions.

---

## Current phase

**Phase 8 — QA conversationnel en cours**

Le Coach Agent V1 est livré et opérationnel. On valide maintenant la qualité des conversations en production via un QA Agent automatisé.

Score QA courant : **6.96/10** moyenne (seuil MVP : 7.5) — voir `data/qa_pipe/mvp_progress.md`.

---

## Architecture

```
Data Engine
    ↓
Runner Intelligence
    ↓
Activity Intelligence
    ↓
Runner Model
    ↓
Knowledge Engine          ← règles déterministes, DecisionEnvelope
    ↓
Coach Intelligence        ← interprétation, personnalisation, génération LLM
    ↓
Coach Agent               ← orchestration conversationnelle
    ↑
QA Agent                  ← évaluation automatisée (hors prod)
```

---

## Setup

### 1. Dépendances

```bash
uv sync
```

### 2. Variables d'environnement

```bash
cp .env.example .env
# Remplir GEMINI_API_KEY dans .env
```

### 3. Vérifier que les tests passent

```bash
uv run pytest
# Attendu : 434 passed, 1 skipped
```

---

## Peupler la base de données

Le répertoire `data/` est gitignored — données personnelles GPS/fitness. Voici comment initialiser depuis zéro.

### 1. Exporter ses activités Strava

Dans Strava : **Paramètres → Mon compte → Télécharger ou supprimer vos données → Demander vos archives**.

Strava envoie un `.zip` contenant un dossier `export_<id>/` avec :
- `activities/` — les fichiers `.fit.gz` et `.gpx`
- `activities.csv` — les métadonnées

Dézipper dans `data/raw/strava/` :

```
data/
  raw/
    strava/
      export_<ton_id_strava>/
        activities/         ← fichiers fit.gz / gpx
        activities.csv      ← métadonnées Strava
```

### 2. Ajuster le chemin dans `import_strava.py`

Le chemin est hardcodé ligne 8 — mettre ton propre ID d'export :

```python
# scripts/import_strava.py, ligne 8
STRAVA_DIR = Path("data/raw/strava/export_<ton_id_strava>/activities")
```

### 3. Importer les activités

```bash
uv run python scripts/import_strava.py
# Génère : data/mirrorpace.db
```

### 4. Créer le profil coureur

Créer `data/runner_profile.yaml` (seuls `runner_id` et `age` sont obligatoires) :

```yaml
runner_id: prenom          # identifiant unique, utilisé par la Runner Memory
age: 30

# Optionnel — améliore la personnalisation du coach
sex: male                  # male | female | unspecified
experience_level_declared: intermediate   # beginner | intermediate | advanced
sessions_per_week_available: 4
years_running: 3.0

# Pathologies connues (liste libre)
pathologies_connues:
  - douleur genou gauche 2024

# Temps de course récents (en secondes)
# recent_race_time_10k: 2700    # 45min
# recent_race_time_half: 6300   # 1h45
# recent_race_time_marathon: 13500  # 3h45

# VMA et objectif course
# VMA_kmh: 14.0
# race_target_date: "2026-10-15"
# race_target_time: 12600   # 3h30 en secondes
```

### 5. Vérifier l'import

```bash
uv run python scripts/run_agent.py
# Doit lancer une conversation avec le coach sur tes données réelles
```

### Structure finale de `data/`

```
data/
  mirrorpace.db         ← base SQLite des activités (généré par import_strava.py)
  runner_profile.yaml   ← profil coureur (créé manuellement)
  runner_memory/        ← décisions de coaching persistées (créé automatiquement)
  qa_runs/              ← résultats QA (créé par run_qa.py)
  qa_pipe/              ← rapports de pipe QA (créé par run_qa.py)
```

---

## Scripts principaux

| Script | Usage |
|---|---|
| `scripts/run_agent.py` | Lancer une conversation interactive avec le CoachAgent |
| `scripts/run_qa.py` | Lancer le QA Agent (simulations + évaluation automatique) |
| `scripts/eval_coach.py` | Évaluer une réponse unique du coach |
| `scripts/import_strava.py` | Importer des activités Strava dans la base |

---

## QA Agent

Le QA Agent simule des coureurs avec des personnalités différentes, teste le CoachAgent en conditions réelles, et produit un rapport structuré.

```bash
# 1 conversation rapide
uv run python scripts/run_qa.py --conversations 1

# 5 conversations sur un profil
uv run python scripts/run_qa.py --profile injured_runner --conversations 5

# Batch complet (tous les profils)
uv run python scripts/run_qa.py --conversations 20
```

Résultats enregistrés dans `data/qa_runs/<timestamp>/`.  
Progression MVP dans `data/qa_pipe/mvp_progress.md`.  
Voir `docs/qa/README.md` pour la doc complète.

---

## Layers implémentées (434 tests)

- **Data Engine** — parsing FIT/GPX, normalisation Activity, SQLite
- **Activity Intelligence** — classifier intensité, pace trends, personal bests
- **Analytics** — weekly stats, progression slope
- **Runner Model** — RunnerSnapshot, WeekInputBuilder, RunnerProfileStore
- **Knowledge Engine** — ACWR, readiness score, règles P0–P4, DecisionEnvelope (gelé v1.3.1)
- **Coach Intelligence v1.0.1** — EnvelopeInterpreter, PersonalizedPromptBuilder, ResponseAssembler, SafetyGuard
- **Runner Memory** — CoachingDecision, MemoryStore YAML, MemoryWriter
- **Coach Agent V1** — IntentClassifier hybride, AnalysisHandler, FollowupHandler, FeedbackHandler
- **QA Agent** — SimulatedRunner, ConversationRunner, HardChecks, ConversationJudge, 6 profils

---

## Documentation

| Fichier | Contenu |
|---|---|
| `docs/PROJECT_VISION.md` | Vision produit et principe directeur |
| `docs/ARCHITECTURE.md` | Architecture détaillée par couche |
| `docs/DECISIONS.md` | Décisions techniques passées et leur justification |
| `docs/qa/README.md` | QA Agent — usage, scores, interprétation |
| `docs/qa/RUBRIC.md` | Grille d'évaluation : 9 dimensions, exemples 1/3/5 |
| `docs/qa/PROFILES.md` | Profils de coureurs simulés |
| `CLAUDE.md` | Instructions pour Claude Code |

The `data/` directory is gitignored to keep personal GPS and fitness data off GitHub.
