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
SimulatedRunner (DeepSeek-V3, temp=0.8)
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
        └── ConversationJudge (DeepSeek-V3, temp=0.2)
                │  reçoit transcript + profil + envelopes + résultats hard checks
                ▼
        EvaluationReport
                │
                ▼
        ReportGenerator → AggregateReport
```

---

## Lancer le QA Agent

### Prérequis

```bash
# Variables d'environnement (dans .env)
GEMINI_API_KEY=...      # pour CoachAgent (déjà utilisé)
DEEPSEEK_API_KEY=...    # pour SimulatedRunner et ConversationJudge
```

### Commandes

```bash
# Run minimal (3 conversations, 5 tours max, tous les profils)
python scripts/run_qa.py

# Run avec un profil spécifique
python scripts/run_qa.py --profile anxious_beginner --conversations 5

# Run plus large
python scripts/run_qa.py --conversations 20

# Augmenter le budget pour un gros batch
python scripts/run_qa.py --conversations 50 --budget 1.0

# Plus de tours par conversation
python scripts/run_qa.py --max-turns 8
```

### Garde-fou coût

Le script calcule le coût estimé avant tout appel API.
Si le coût estimé dépasse le budget (défaut : **$0.50**), le script plante avec une erreur explicite.

```
ERROR: Estimated cost ~$0.99 exceeds budget $0.50. Use --budget 1.0 to override.
```

Coûts de référence :

| Conversations | Coût estimé |
|---|---|
| 3 | ~$0.02 |
| 10 | ~$0.07 |
| 20 | ~$0.14 |
| 50 | ~$0.35 |
| 100 | ~$0.70 |

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

[1/5] Débutant anxieux... score=7.2/10 | satisfied
[2/5] Marathonien ambitieux... score=6.8/10 | max_turns | ⚠ 1 violation(s)
...

RAPPORT QA MIRRORPACE — 2026-07-22
5 conversation(s) analysée(s)
================================================================

Score moyen   : 7.0/10  (σ = 0.8)

SCORES PAR DIMENSION :
  empathy                    [███░░] 3.2/5
  conversation_coherence     [████░] 4.0/5
  ...

MÉTRIQUES QUALITÉ :
  Contradictions KE        : 20%
  Alerte médicale manquée  : 0%
  Mémoire non référencée   : 40%
```

### Fichiers générés

```
data/qa_runs/
  20260722_143000/
    conversations/
      conv_qa-abc123.json     ← transcript complet + envelopes
    evaluations/
      eval_qa-abc123.json     ← scores + justifications + forces/faiblesses
    aggregate.json            ← rapport global du batch
```

---

## Interpréter les scores

### Score global (0–10)

| Score | Interprétation |
|---|---|
| 0–3 | Conversation problématique — bloquer avant release |
| 4–5 | Sous le seuil — améliorer avant utilisation en production |
| 6–7 | Acceptable — améliorations identifiées |
| 8–9 | Bonne qualité — itérations mineures |
| 9–10 | Excellent |

**Attention** : une contradiction KE (coach dit "augmenter" quand KE dit "deload") plafonne automatiquement le score à 5, quelle que soit la qualité du reste.

### Violations objectives (hard checks)

Les violations sont non-négociables — elles indiquent un bug fonctionnel, pas une question de style :

- `ke_contradiction` : le coach contredit la décision du Knowledge Engine
- `medical_flag_missed` : une alerte médicale n'a pas été communiquée
- `memory_not_utilized` : la Runner Memory est ignorée alors que des décisions passées existent

---

## Profils disponibles

| ID | Persona |
|---|---|
| `anxious_beginner` | Débutant anxieux, besoin de réassurance |
| `ambitious_marathoner` | Marathonienne, veut toujours augmenter |
| `injured_runner` | Reprise de blessure, surveille son corps |
| `cautious_runner` | Très prudent, suit les règles à la lettre |
| `busy_parent` | Parent pressé, séances courtes, contraintes de temps |
| `performance_obsessed` | Compétiteur obsédé par les données, conteste le coach |

Voir `docs/qa/PROFILES.md` pour le détail et la vision d'évolution.

---

## Utilisation dans le cycle de développement

Le QA Agent sert à :

1. **Valider une évolution du Coach Agent** avant de merger
2. **Tester un nouveau prompt** dans Coach Intelligence
3. **Mesurer l'impact d'un changement de Runner Memory** sur les conversations
4. **Identifier les profils pour lesquels le coach performe mal**

Usage recommandé : lancer 10 conversations après chaque évolution significative du Coach Agent ou de Coach Intelligence, comparer avec le run précédent.
