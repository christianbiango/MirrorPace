# QA Agent — MirrorPace

Outil interne d'évaluation automatique du Coach Agent.

Le QA Agent **n'est pas un agent conversationnel du produit**. C'est un microscope : il simule des utilisateurs, observe les conversations réelles avec le CoachAgent, et produit un rapport structuré sur la qualité.

---

## Pourquoi ce système existe

Le Coach Agent V1 fonctionne. Mais :

- Les tests unitaires vérifient des propriétés isolées
- `eval_coach.py` évalue la qualité d'une réponse unique
- **Personne ne teste ce qui se passe sur plusieurs tours**

Le QA Agent couvre ce gap : il teste la qualité conversationnelle — cohérence entre tours, respect des décisions du Knowledge Engine, utilisation de la Runner Memory, ton, pédagogie.

---

## Architecture

```
SimulatedRunner (Gemini 2.5 Flash, temp=0.8)
        │  joue un coureur avec une personnalité et des objectifs
        ▼
CoachAgent.ask()  ← le vrai produit, jamais mocké
        │
        ▼
ConversationLog  (transcript complet + envelopes KE)
        │
        ├── HardChecks (déterministes, sans LLM)
        │       ├── ke_coherence
        │       ├── medical_flag
        │       └── memory_utilization
        │
        └── ConversationJudge (Gemini 2.5 Flash, temp=0.2)
                │  reçoit transcript + profil + envelopes + résultats hard checks
                ▼
        EvaluationReport
                │
                ▼
        ReportGenerator → AggregateReport
```

---

## Prérequis

```bash
# Variables d'environnement (dans .env)
GEMINI_API_KEY=...      # pour CoachAgent, SimulatedRunner et ConversationJudge

# Données runner (gitignored)
data/mirrorpace.db      # base SQLite des activités
data/runner_profile.yaml
```

---

## Lancer le QA Agent

```bash
# Run minimal (3 conversations, 5 tours max, tous les profils)
uv run python scripts/run_qa.py

# Run avec un profil spécifique
uv run python scripts/run_qa.py --profile anxious_beginner --conversations 5

# Run plus large
uv run python scripts/run_qa.py --conversations 20

# Augmenter le budget pour un gros batch
uv run python scripts/run_qa.py --conversations 50 --budget 1.0

# Plus de tours par conversation
uv run python scripts/run_qa.py --max-turns 8
```

### Garde-fou coût

Le script calcule le coût estimé avant tout appel API. Si le coût estimé dépasse le budget (défaut : **$0.50**), le script échoue immédiatement sans rien appeler.

```
ERROR: Estimated cost ~$0.99 exceeds budget $0.50. Use --budget 1.0 to override.
```

Coûts de référence :

| Conversations | Coût estimé |
|---|---|
| 1 | ~$0.007 |
| 5 | ~$0.035 |
| 10 | ~$0.07 |
| 20 | ~$0.14 |
| 50 | ~$0.35 |

---

## Lire les résultats

### Sortie console

```
MirrorPace QA Agent
  Conversations : 5 | Tours max : 5
  Coût estimé   : ~$0.035 (budget : $0.50)
  Profils       : [anxious_beginner, ambitious_marathoner, ...]
  Sortie        : data/qa_runs/20260722_143000
================================================================

[1/5] Débutant anxieux... score=9.6/10 | satisfied
[2/5] Marathonien ambitieux... score=8.0/10 | satisfied
[3/5] Coureur blessé... score=4.4/10 | satisfied | ⚠ 1 violation(s)
...

Score moyen   : 6.96/10  (σ = 1.9)

SCORES PAR DIMENSION :
  pedagogical_quality        [███░░] 3.0/5
  question_answered          [███░░] 3.4/5
  ...
```

### Fichiers générés

```
data/qa_runs/
  20260722_143000/
    conversations/
      conv_qa-abc123.json     ← transcript complet + envelopes KE
    evaluations/
      eval_qa-abc123.json     ← scores + justifications + forces/faiblesses
    aggregate.json            ← rapport global du batch
```

---

## Interpréter les scores

### Score global (0–10)

| Score | Interprétation |
|---|---|
| 0–3 | Conversation problématique — bug fonctionnel |
| 4–5 | Sous le seuil — améliorer avant utilisation en production |
| 6–7 | Acceptable — axes d'amélioration identifiés |
| 8–9 | Bonne qualité — itérations mineures |
| 9–10 | Excellent |

Une contradiction KE (coach dit "augmenter" quand KE dit "deload") plafonne automatiquement le score à 5.

### Violations objectives (hard checks)

Les violations indiquent un bug fonctionnel, pas une question de style :

- `ke_contradiction` : le coach contredit la décision du Knowledge Engine
- `medical_flag_missed` : une alerte médicale n'a pas été communiquée
- `memory_not_utilized` : la Runner Memory est ignorée alors que des décisions passées existent

---

## Profils disponibles

| ID | Persona |
|---|---|
| `anxious_beginner` | Débutant anxieux, besoin de réassurance |
| `ambitious_marathoner` | Marathonienne expérimentée, veut toujours augmenter |
| `injured_runner` | Reprise après tendinite, surveille son corps |
| `cautious_runner` | Très prudent, suit les règles à la lettre |
| `busy_parent` | Parent pressé, contraintes de temps |
| `performance_obsessed` | Compétiteur data-driven, conteste le coach |

Voir `docs/qa/PROFILES.md` pour le détail et la vision d'évolution.

---

## État actuel (2026-07-23)

### Résultats du pipe du 2026-07-22

| Profil | Score | Statut |
|---|---|---|
| anxious_beginner | 9.60/10 | ✅ MVP |
| ambitious_marathoner | 8.04/10 | ✅ MVP |
| injured_runner | 4.42/10 | ❌ |
| cautious_runner | 7.58/10 | ✅ MVP |
| performance_obsessed | 5.18/10 | ❌ |
| **Moyenne** | **6.96/10** | ❌ seuil 7.5 |

Transcripts + analyse : `data/qa_pipe/pipe_20260722_231435.md`  
Progression MVP : `data/qa_pipe/mvp_progress.md`

### Bugs fixés lors du pipe

| Bug | Fix | Fichier |
|---|---|---|
| Substring "rest" matchait mots français → faux positif ke_contradiction | Regex `\b{word}\b` | `src/qa_agent/evaluation/hard_checks.py` |
| ANALYSIS_REQUEST répété → même réponse KE en boucle | Route vers FollowupHandler après 1er tour | `src/coach_agent/agent.py` |
| FollowupHandler ne reconnaissait pas corrections biographiques | Ajout règle dans system prompt | `src/coach_agent/handlers/followup_handler.py` |

### Gaps connus (non fixés)

1. **Règles KE citées sans description lisible** — le coach dit "RULE-009" au lieu d'expliquer en français
2. **Classification "débutant" vs expérience déclarée** — KE utilise la charge récente, pas l'historique biographique
3. **Données brutes non exposées** — profils data-driven veulent HRV, score sommeil brut

---

## Utilisation dans le cycle de développement

Usage recommandé : lancer 5–10 conversations après chaque évolution significative du Coach Agent ou de Coach Intelligence, comparer avec le run précédent via le tableau `data/qa_pipe/mvp_progress.md`.

```bash
# Pipe complet avec sauvegarde du rapport
# (voir docs/qa/QA_PIPE_PROMPT.md pour le prompt Claude Code)
uv run python scripts/run_qa.py --conversations 5
```
