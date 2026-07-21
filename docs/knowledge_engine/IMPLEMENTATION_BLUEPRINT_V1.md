# Implementation Blueprint V1 — Knowledge Engine

> Version : 1.0
> Basé sur : `KB_CANONICAL_v1.2.md`
> Statut : document de préparation à l'implémentation — ne modifie pas la spec moteur
> Objectif : valider l'architecture existante avant le premier commit de code

---

## Structure

- [Phase A — Validation avant code](#phase-a)
- [Phase B — Implémentation moteur V1](#phase-b)
- [Phase C — Tests automatisés](#phase-c)
- [Phase D — Simulation comportementale](#phase-d)
- [Annexe — Extreme Profiles & Adversarial Test Suite](#adversarial)

---

## Phase A — Validation avant code {#phase-a}

### A.1. Spec gelée

Avant d'écrire la première ligne de code :

- [ ] `KB_CANONICAL_v1.2.md` est le contrat d'implémentation. Aucune modification sans PR dédiée.
- [ ] `thresholds.yaml` (§ 4.2) est extrait dans `/config/` et versionné séparément du code.
- [ ] `rules_status.yaml` liste l'état de chaque règle (enabled/disabled). RULE-013 et RULE-014 sont `disabled`.
- [ ] Toute constante numérique dans le code déclenche un échec de linting : seules les références à `config.*` sont autorisées.

### A.2. Décisions produit à trancher avant kickoff

Les 20 décisions de la section 7 de la spec doivent être arbitrées. Statut recommandé :

| ID | Statut | Valeur choisie |
|----|--------|---------------|
| D-01 | ✅ tranché | `simple_mean` V1 |
| D-02 | ✅ tranché | 4 semaines |
| D-03 | ✅ tranché | seuils par défaut config §4.2 |
| D-04 | ✅ tranché | `years_running` optionnel, null si absent |
| D-05 | ⚠️ bloquant | table 3×3 `experience × chronic_load → plan_level` à figer |
| D-06 | ✅ tranché | `off_season` → maintain + hint cross-training |
| D-07 | ✅ tranché | cap unique 4 semaines V1 |
| D-08 | ✅ tranché | hint P4 (non bloquant) |
| D-09 | ✅ tranché | conserver 1–5 maison |
| D-10 | ✅ tranché | non — `current_phase` reste source de vérité |
| D-11 | ✅ tranché | défauts audit −25/−10/0/+3/+7/+10 |
| D-12 | ✅ tranché | exposant Riegel = 1.06 |
| D-13 | ✅ tranché | `other` → RULE-001 oui, RULE-002 non |
| D-14 | ✅ tranché | 10 jours |
| D-15 | ✅ tranché | historique passé par le caller, moteur stateless |
| D-16 | ✅ tranché | RULE-013/014 restent désactivées |
| D-17 | ✅ tranché | `pain_trend` informatif V1 uniquement |
| D-18 | ✅ tranché | mapper K15 → `pathologies_connues` |
| D-19 | ✅ tranché | `mood_motivation_score` → UI LLM uniquement |
| D-20 | ✅ tranché | arrondi 0.5 km |

**Seul D-05 bloque strictement RULE-017. Toutes les autres règles peuvent être codées.**

### A.3. Adversarial Test Suite

Les 15 profils sont définis en [Annexe](#adversarial). Ils doivent être exécutés manuellement (simulation papier) avant le kickoff pour confirmer que l'architecture produit les décisions attendues. L'implémentation commence après cette validation.

---

## Phase B — Implémentation moteur V1 {#phase-b}

### B.1. Ordre d'implémentation

L'ordre garantit que chaque couche est testable indépendamment.

```
1. /config/                         — charger et valider la config YAML
2. /domain/schemas/runner_state.py  — RunnerState + validation §1.8
3. /domain/schemas/computed.py      — ComputedVariables (structure)
4. /domain/schemas/decision.py      — DecisionEnvelope (structure)
5. /domain/formulas/acwr.py         — §2.2 chronic_load + acwr
6. /domain/formulas/readiness.py    — §2.3 readiness_score + §2.4 confidence
7. /domain/formulas/pace.py         — §2.6 hiérarchie target_marathon_pace
8. /domain/formulas/experience_level.py — §5.4
9. /engine/validator.py             — §1.8 (errors + warnings)
10. /rules/safety_rules.py          — RULE-001, 002, 003
11. /rules/progression_rules.py     — RULE-004, 005, 006, 007, 008, 009, 010, 026
12. /rules/planning_rules.py        — RULE-011, 012, 015–022, 025
13. /engine/aggregator.py           — §3.99 étape 4
14. /engine/orchestrator.py         — §3.99 pipeline complet
15. /engine/envelope_builder.py     — DecisionEnvelope final
```

### B.2. Arborescence cible

```
knowledge_engine/
├── config/
│   ├── thresholds.yaml
│   ├── rules_status.yaml
│   └── enums.yaml
├── domain/
│   ├── concepts.py
│   └── schemas/
│       ├── runner_state.py
│       ├── computed.py
│       └── decision.py
│   └── formulas/
│       ├── acwr.py
│       ├── readiness.py
│       ├── pace.py
│       └── experience_level.py
├── rules/
│   ├── safety_rules.py
│   ├── progression_rules.py
│   ├── planning_rules.py
│   └── disabled/
│       ├── rule_013_perf_declining.py
│       └── rule_014_grey_zone.py
├── engine/
│   ├── orchestrator.py
│   ├── validator.py
│   ├── aggregator.py
│   └── envelope_builder.py
└── tests/
    ├── unit/
    ├── fixtures/
    └── property/
```

### B.3. Contrats d'interface critiques

**Chaque règle est une fonction pure :**
```python
def rule_XXX(state: RunnerState, computed: ComputedVariables, config: Config) -> RuleOutcome:
    ...
```

**Aucun accès IO, base de données, ou état global dans les règles.**

**Le `config_hash` est capturé au démarrage de l'orchestrateur et transmis à chaque appel.**

---

## Phase C — Tests automatisés {#phase-c}

### C.1. Tests unitaires

Un fichier de test par règle et par formule. Couvrir au minimum les cas `tests_expected` listés dans chaque règle de la spec.

Priorité : P0 → P1 → formules → P2 → P3 → P4.

### C.2. Tests d'intégration

Scénarios de bout en bout (RunnerState → DecisionEnvelope) couvrant :
- Chaque action possible (`deload`, `decrease`, `maintain`, `slight_increase`, `increase`)
- Chaque priorité de règle dominante (P0 seul, P1 seul, P2 seul, aucune règle)
- Court-circuit (P0 + règles P1/P2 en attente)

### C.3. Tests de propriété (property-based)

Invariants à vérifier sur tout input valide :

| Invariant | Garde-fou | Test |
|-----------|-----------|------|
| `medical_referral == true` ⇒ `action == "deload"` | GF-01 | property |
| P1 déclenché ⇒ `action ∈ {deload, decrease, maintain}` | GF-02 | property |
| `absolute_next_week_target_km >= 0` | GF-03 | property |
| `action == "deload"` ⇒ `delta_pct <= -20%` | GF-08 | property |
| Un seul `action` dans `decision` | GF-09 | property |
| `current_phase == "taper"` ET aucun P0 ⇒ `action == "decrease"` | GF-07 | property |
| `readiness_confidence_score < 50` ⇒ `action ∈ {deload, decrease, maintain}` | GF-06 | property |

### C.4. Exécution des profils adversariaux

Après les tests unitaires et d'intégration : encoder chaque profil de l'Annexe en fixture JSON et vérifier automatiquement les assertions critiques listées. Ces fixtures sont des tests de régression permanents.

---

## Phase D — Simulation comportementale {#phase-d}

**Cette phase commence APRÈS que la Phase C est complète et verte.**

### D.1. Objectif

Valider le comportement du moteur à l'échelle sur des milliers de profils synthétiques, sans modifier les règles ni les seuils.

### D.2. Générateur de profils synthétiques

Produire N = 10 000 `RunnerState` aléatoires valides (respectant les contraintes de validation §1.8) couvrant les distributions réalistes de :
- `acwr_distance` : distribution log-normale centrée sur 1.0
- `fatigue_score`, `sleep_quality_score` : distribution uniforme sur {1..5}
- `experience_level_declared` : 50% beginner, 35% intermediate, 15% advanced
- `current_phase` : pondéré (general 60%, specific 25%, taper 5%, off_season 10%)

### D.3. Analyse des distributions de décisions

Métriques à calculer :
- Distribution des actions : `{deload: X%, decrease: Y%, maintain: Z%, slight_increase: A%, increase: B%}`
- Taux de déclenchement par règle (% des inputs qui la triggent)
- Distribution de `readiness_score` et `readiness_confidence_score`
- Corrélation entre `acwr_distance` et action finale

### D.4. Détection d'anomalies

Alertes si :
- `deload` < 1% ou > 15% (calibration des seuils P0)
- `increase` > 60% (moteur trop permissif)
- `readiness_confidence_score` < 50 sur > 40% des profils (seuils trop stricts)

### D.5. Calibration des paramètres

Si des anomalies sont détectées, ajuster les valeurs dans `thresholds.yaml` uniquement. Aucune modification des règles elles-mêmes.

---

## Annexe — Extreme Profiles & Adversarial Test Suite {#adversarial}

### Vue d'ensemble

Ces 15 profils sont conçus pour valider que l'architecture existante (priorités P0→P4, agrégation §3.99, garde-fous GF-01→GF-10) produit des décisions cohérentes dans des situations limites.

**Contrainte stricte : aucun de ces profils ne justifie l'ajout d'une nouvelle règle.** S'ils échouent, c'est l'implémentation qui est incorrecte, pas la spec.

**Structure de chaque profil :**

```
Objectif de test  — ce que le profil cherche à prouver
Scénario          — description du cas limite
Input             — extrait RunnerState pertinent (JSON)
Computed          — variables calculées attendues
Règles            — quelles règles se déclenchent et pourquoi
Décision          — action + delta attendus
Hints / Warnings  — sorties non décisionnelles attendues
Garde-fous        — invariants GF-XX vérifiés
Assertion         — la propriété clé du test
```

---

### P-01 — Surcharge invisible

**Objectif :** L'ACWR acceptable + progression raisonnable NE DOIVENT PAS conduire à une augmentation quand la récupération est mauvaise.

**Scénario :** Coureur dont la charge externe semble sous contrôle (ACWR 1.14, Δvolume +8.3%) mais dont les signaux de récupération sont mauvais (fatigue=4, sommeil=2). Situation typique de surentraînement masqué.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 52,
    "previous_week_distance_km": 48,
    "weekly_distance_history": [48, 46, 45, 44],
    "weekly_duration_min": 280,
    "long_run_km_last_week": 22,
    "long_run_km_previous_week": 20,
    "avg_weekly_RPE": 6.5,
    "fatigue_score": 4,
    "sleep_quality_score": 2,
    "pain_regions": [],
    "days_since_last_run": 0
  },
  "context": { "current_phase": "general", "weeks_to_race": null }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 45.75 km |
| `acwr_distance` | 1.137 |
| `acwr_reliable` | true |
| `delta_volume_pct` | +8.33% |
| `delta_volume_reliable` | true |
| `delta_long_run_pct` | +10.0% |
| `estimated_internal_load` | 1820 |

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| RULE-001 | P0 | ✗ | Aucune douleur |
| RULE-003 | P0 | ✗ | acwr 1.14 < 2.0 |
| RULE-004 | P1 | ✗ | acwr 1.14 pas dans (1.5, 2.0) |
| RULE-005 | P1 | ✗ | Δvolume 8.3% < 10% |
| **RULE-006** | **P1** | **✓** | **fatigue=4 ≥ 4 ET sleep=2 ≤ 2** |
| RULE-011 | P3 | ✗ | Condition RULE-006 active — score ajustement ignoré |

**Décision attendue :** `maintain` (0%)

**Warnings :** aucun

**Plan hints :** aucun

**Garde-fous vérifiés :** GF-02 (P1 déclenché → action ∈ {deload, decrease, maintain})

**Assertion critique :** Un ACWR de 1.14 (sweet spot) et une progression de +8.3% (sous le cap) n'autorisent PAS une augmentation dès lors que RULE-006 P1 est déclenchée par fatigue=4 + sommeil=2. Le moteur ne se laisse pas tromper par de bons signaux de charge externe.

---

### P-02 — Douleur critique

**Objectif :** Une douleur de haute intensité persistante doit déclencher une priorité médicale absolue, indépendamment de tous les autres signaux.

**Scénario :** Coureur avec genou fortement douloureux (5/5 depuis 3 jours, tendance aggravante). Tous les autres signaux sont neutres.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 45,
    "previous_week_distance_km": 42,
    "weekly_distance_history": [42, 40, 38, 36],
    "weekly_duration_min": 240,
    "long_run_km_last_week": 18,
    "long_run_km_previous_week": 16,
    "fatigue_score": 3,
    "sleep_quality_score": 3,
    "pain_regions": [
      {
        "region": "knee",
        "intensity": 5,
        "days_persistent": 3,
        "pain_trend": "worsening"
      }
    ],
    "days_since_last_run": 1
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 39.0 km |
| `acwr_distance` | 1.154 |
| `acwr_reliable` | true |

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| **RULE-001** | **P0** | **✓** | intensity=5 ≥ 4, days=3 ≥ 2 → deload forcé + short_circuit |
| **RULE-002** | **P0** | **✓** | knee ∈ CRITICAL_PAIN_REGIONS, intensity=5 ≥ 3, days=3 ≥ 3 |
| RULE-006 | P1 | ignorée | short_circuit P0 actif |

**Décision attendue :** `deload` (−25%)
**`medical_referral`** : `true`

**Warnings :** `["medical_referral_recommended"]`

**Garde-fous vérifiés :** GF-01 (medical_referral → deload), GF-08 (deload → delta ≤ −20%), GF-09 (action unique)

**Assertion critique :** Une douleur genou 5/5 depuis 3 jours active RULE-001 et RULE-002 simultanément (P0). Tous les signaux favorables (ACWR sain, fatigue neutre) sont court-circuités. La décision est `deload` avec renvoi médical, sans exception.

---

### P-03 — Expérimenté fragile

**Objectif :** L'expérience avancée NE DOIT PAS annuler une douleur chronique en zone critique.

**Scénario :** Coureur de haut niveau (70 km/semaine chronique, semi en 1h35) avec tendinopathie d'Achille persistante (3/5 depuis 4 jours). Se sent bien par ailleurs.

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "experience_level_declared": "advanced",
    "recent_race_time_half": 5700
  },
  "week": {
    "weekly_distance_km": 72,
    "previous_week_distance_km": 75,
    "weekly_distance_history": [75, 72, 70, 68, 66, 65, 65, 64],
    "weekly_duration_min": 390,
    "long_run_km_last_week": 28,
    "long_run_km_previous_week": 30,
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [
      {
        "region": "achilles",
        "intensity": 3,
        "days_persistent": 4,
        "pain_trend": "stable"
      }
    ],
    "days_since_last_run": 0
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 71.25 km |
| `acwr_distance` | 1.011 |
| `acwr_reliable` | true |
| `computed.experience_level` | `"advanced"` |
| `experience_level_source` | `"reconciled"` |
| `readiness_confidence_score` | ~90 (pénalité active_pain −5) |

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| RULE-001 | P0 | ✗ | intensity=3 < 4 (seuil pain_critical_intensity) |
| **RULE-002** | **P0** | **✓** | achilles ∈ CRITICAL_PAIN_REGIONS, intensity=3 ≥ 3, days=4 ≥ 3 |
| RULE-012 | P3 | ignorée | short_circuit P0 actif |

**Décision attendue :** `deload` (−25%)
**`medical_referral`** : `true`

**Garde-fous vérifiés :** GF-01, GF-08, GF-09

**Assertion critique :** Malgré 8 semaines d'historique, un niveau "advanced" calculé et confirmé, et une récupération correcte, RULE-002 P0 s'applique sans aucune exception liée au profil. L'expérience ne protège pas contre les risques de blessure structurelle.

---

### P-04 — Retour après interruption longue (retour prudent)

**Objectif :** RULE-026 doit se déclencher pour toute interruption > 14 jours, même si les signaux de forme sont bons et le volume de retour est modeste.

**Scénario :** Coureur reprenant après 30 jours d'arrêt complet (maladie). Reprend à volume faible (10 km). Se sent bien.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 10,
    "previous_week_distance_km": 0,
    "weekly_distance_history": [0, 0, 75, 70],
    "weekly_duration_min": 60,
    "long_run_km_last_week": 10,
    "long_run_km_previous_week": null,
    "avg_weekly_RPE": 4.0,
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 30
  },
  "context": { "current_phase": "general", "weeks_to_race": null }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 36.25 km |
| `acwr_distance` | 0.276 |
| `acwr_reliable` | true |
| `delta_volume_pct` | +900% (approx) |
| `delta_volume_reliable` | false (prev=0 < 20 km) |
| `readiness_confidence_score` | ~55 (pénalité interruption −20, long_run_prev −5) |

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| RULE-003 | P0 | ✗ | acwr 0.276 < 2.0 |
| RULE-005 | P1 | ✗ | delta_volume_reliable = false (guard) |
| **RULE-026** | **P1** | **✓** | days_since_last_run=30 > 14 |

**Décision attendue :** `maintain` (0%)

**Plan hints :** `["return_from_interruption_progressive"]`

**Garde-fous vérifiés :** GF-02 (P1 → pas d'augmentation), GF-06 (confidence ~55 ≥ 50 : décision avec caveat)

**Assertion critique :** RULE-026 se déclenche correctement sur 30 jours d'interruption. La règle du 10% (RULE-005) ne s'applique pas car le delta est non fiable (semaine précédente = 0). La décision est `maintain` avec guide de reprise progressive.

---

### P-05 — Reprise trop ambitieuse

**Objectif :** Une tentative de reprise à l'ancien volume après 30 jours d'arrêt doit être bloquée, même si les signaux subjectifs sont excellents.

**Scénario :** Même coureur qu'en P-04, mais qui essaie de reprendre directement à 50 km (ancien volume). Fatigue=2, sommeil=5.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 50,
    "previous_week_distance_km": 0,
    "weekly_distance_history": [0, 0, 65, 62],
    "weekly_duration_min": 280,
    "long_run_km_last_week": 20,
    "long_run_km_previous_week": null,
    "fatigue_score": 2,
    "sleep_quality_score": 5,
    "pain_regions": [],
    "days_since_last_run": 30
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 31.75 km |
| `acwr_distance` | 1.575 |
| `acwr_reliable` | true |
| `delta_volume_reliable` | false (prev=0 < 20) |

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| RULE-003 | P0 | ✗ | acwr 1.575 < 2.0 |
| **RULE-004** | **P1** | **✓** | 1.5 < acwr=1.575 < 2.0 → block_increase |
| RULE-005 | P1 | ✗ | delta_volume_reliable = false |
| **RULE-026** | **P1** | **✓** | days=30 > 14 → block_increase |

**Décision attendue :** `maintain` (deux P1 concordants)

**Garde-fous vérifiés :** GF-02

**Assertion critique :** Malgré fatigue=2 et sommeil=5 (signaux subjectifs parfaits), la tentative de reprendre à 50 km génère un ACWR de 1.575 (RULE-004) et une interruption de 30 jours (RULE-026). Deux règles P1 convergent vers `maintain`. L'absence de signal de souffrance ne suffit pas à autoriser une reprise brutale.

---

### P-06 — Débutant trop ambitieux

**Objectif :** La déclaration `experience_level = "advanced"` doit être écrasée par le calcul objectif si les critères ne sont pas remplis.

**Scénario :** Coureur se déclarant "advanced". Son historique révèle un chronic_load de 23.75 km (< 30 km, seuil intermediate) et un 10k en 55 min. Aucun semi-marathon complété.

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "experience_level_declared": "advanced",
    "recent_race_time_10k": 3300,
    "recent_race_time_half": null,
    "VMA_kmh": null
  },
  "week": {
    "weekly_distance_km": 30,
    "previous_week_distance_km": 28,
    "weekly_distance_history": [28, 25, 22, 20],
    "weekly_duration_min": 180,
    "long_run_km_last_week": 12,
    "long_run_km_previous_week": 10,
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 0
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 23.75 km |
| `acwr_distance` | 1.263 |
| `acwr_reliable` | true |
| `delta_volume_pct` | +7.14% |
| `computed.experience_level` | `"beginner"` |
| `experience_level_source` | `"calculated"` (déclaration ignorée) |

**Calcul experience_level :**
- `intermediate` : chronic ≥ 30 km → 23.75 < 30 → ✗
- `candidate = "beginner"`
- `declared = "advanced"` > `candidate = "beginner"` → **computed = "beginner", source = "calculated"**

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| RULE-003/004/005/006 | P0/P1 | ✗ | Signaux sains |
| **RULE-010** | **P2** | **✓** | `experience_level == "beginner"` → cap +5% |
| RULE-011 | P3 | ✓ | acwr 1.263 ∈ [0.8, 1.3], fatigue=2, sleep=4, no pain → +10 pts |
| RULE-012 | P3 | ✗ | experience_level ≠ "advanced" |

**Décision attendue :** `slight_increase` (+3%, capé à +5%)

**Garde-fous vérifiés :** GF-09

**Assertion critique :** La déclaration "advanced" est écrasée. `computed.experience_level = "beginner"` (source = "calculated"). RULE-010 cap la progression à +5%. RULE-012 (bonus avancé) ne se déclenche pas. Le coureur n'obtient pas les droits de progression d'un athlète avancé par simple déclaration.

---

### P-07 — Objectif marathon irréaliste

**Objectif :** RULE-019 doit signaler un objectif chronométrique incohérent avec les performances réelles, sans bloquer l'entraînement.

**Scénario :** Coureur intermédiaire (semi en 1h50 = 6600s) visant un marathon en 3h (10800s). La prédiction Riegel donne 3h49 (13 748s). Écart de 27.3%, très au-delà du seuil de 15%.

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "experience_level_declared": "intermediate",
    "recent_race_time_half": 6600,
    "race_target_time": 10800
  },
  "week": {
    "weekly_distance_km": 55,
    "previous_week_distance_km": 52,
    "weekly_distance_history": [52, 50, 48, 46],
    "weekly_duration_min": 300,
    "long_run_km_last_week": 22,
    "long_run_km_previous_week": 20,
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 0
  },
  "context": {
    "current_phase": "specific_marathon",
    "weeks_to_race": 20
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 49.0 km |
| `acwr_distance` | 1.122 |
| `target_marathon_pace_min_km` | 4.27 min/km |
| `target_marathon_pace_source` | `"race_target_time"` |
| Riegel depuis semi | 13 748s ≈ 3h49 |
| Écart objectif vs Riegel | 27.3% > 20% → warning validation §1.3 |

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| Aucune P0/P1/P2 | — | ✗ | Profil sain |
| RULE-011 | P3 | ✓ | Feu vert multi-critères → +10 pts |
| **RULE-019** | **P4** | **✓** | Écart 27.3% > 15% → plan_hint "revise_objectives" |

**Décision attendue :** `increase` (+7%, intermédiaire)

**Warnings :** `["race_target_unrealistic"]`

**Plan hints :** `["revise_objectives"]`

**Assertion critique :** L'objectif irréaliste ne bloque PAS l'entraînement (P4 = hints uniquement). La décision est `increase` normale. Mais le warning de validation (§1.3, écart > 20%) ET le plan hint (RULE-019, écart > 15%) sont générés. Le moteur distingue "s'entraîner bien" de "avoir un objectif cohérent".

---

### P-08 — Taper correct

**Objectif :** La phase taper doit systématiquement forcer une réduction, indépendamment de tous les autres signaux.

**Scénario :** Coureur avancé en phase taper, 2 semaines avant la course. Tout va bien par ailleurs.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 50,
    "previous_week_distance_km": 70,
    "weekly_distance_history": [70, 68, 65, 62],
    "weekly_duration_min": 280,
    "long_run_km_last_week": 18,
    "long_run_km_previous_week": 28,
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 0
  },
  "context": {
    "current_phase": "taper",
    "weeks_to_race": 2
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 66.25 km |
| `acwr_distance` | 0.755 |
| `delta_volume_pct` | −28.6% |

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| **RULE-007** | **P1** | **✓** | `current_phase == "taper"` → force_decrease |
| RULE-021 | P4 | ✓ | hint structure taper |

**Décision attendue :** `decrease` (−50% cible, plage [−60%, −40%])

**Garde-fous vérifiés :** GF-07 (taper → toujours decrease)

**Assertion critique :** La phase taper force `decrease` via RULE-007 P1. L'ACWR en dessous du sweet spot (0.755) et la bonne récupération ne créent aucune ambiguïté. Le moteur n'interprète pas la réduction comme un problème.

---

### P-09 — Taper contradictoire

**Objectif :** GF-07 doit bloquer toute augmentation pendant le taper, même si tous les signaux subjectifs sont parfaits.

**Scénario :** Phase taper, mais le coureur se sent exceptionnellement bien (fatigue=1, sommeil=5, aucune douleur). Test que le moteur n'est pas séduit par les bons signaux.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 45,
    "previous_week_distance_km": 75,
    "weekly_distance_history": [75, 72, 70, 68],
    "weekly_duration_min": 240,
    "long_run_km_last_week": 16,
    "long_run_km_previous_week": 30,
    "avg_weekly_RPE": 4.0,
    "fatigue_score": 1,
    "sleep_quality_score": 5,
    "pain_regions": [],
    "days_since_last_run": 0
  },
  "context": {
    "current_phase": "taper",
    "weeks_to_race": 2
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 71.25 km |
| `acwr_distance` | 0.632 |
| `acwr_reliable` | true |

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| **RULE-007** | **P1** | **✓** | taper → force_decrease |
| RULE-011 | P3 | ✗ | acwr=0.632 ∉ [0.8, 1.3] → condition non remplie |
| RULE-012 | P3 | ✗ | acwr hors sweet spot |

**Décision attendue :** `decrease` (−50%)

**Garde-fous vérifiés :** GF-07

**Assertion critique :** Fatigue=1, sommeil=5, aucune douleur : tous les signaux subjectifs sont au maximum. Pourtant RULE-007 P1 force `decrease`. RULE-011 ne se déclenche pas (ACWR hors sweet spot en taper). GF-07 garantit qu'aucune augmentation n'est possible en phase taper.

---

### P-10 — Préparation marathon insuffisante

**Objectif :** Un coureur débutant avec base faible à quelques semaines d'un marathon doit générer une faible confiance et des hints forts, sans toutefois dépasser `maintain`.

**Scénario :** Coureur débutant, 4 semaines avant marathon, chronic_load de 18.75 km. Historique limité (1 semaine seulement). Pas de RPE, pas d'info sortie longue précédente.

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "experience_level_declared": "beginner",
    "recent_race_time_10k": 2700
  },
  "week": {
    "weekly_distance_km": 25,
    "previous_week_distance_km": 22,
    "weekly_distance_history": [22],
    "weekly_duration_min": 150,
    "long_run_km_last_week": 10,
    "long_run_km_previous_week": null,
    "avg_weekly_RPE": null,
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 0
  },
  "context": {
    "current_phase": "specific_marathon",
    "weeks_to_race": 4
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 22.0 km (1 semaine history → window=1) |
| `acwr_distance` | 1.136 |
| `acwr_reliable` | false (< 4 semaines) |
| `delta_volume_pct` | +13.6% |
| `delta_volume_reliable` | true (prev=22 ≥ 20) |
| `estimated_internal_load` | null |

**Calcul readiness_confidence_score :**
```
acwr_unreliable:        −15
missing_rpe:            −10
missing_long_run_prev:   −5
per_missing_week (×3):  −15
Total penalties:         −45
confidence_score:         55  (medium — entre 50 et 75)
```

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| RULE-003/004 | P0/P1 | ✗ | acwr_reliable = false (guard) |
| **RULE-005** | **P1** | **✓** | Δvolume 13.6% > 10%, delta_reliable=true |
| RULE-016 | P4 | ✓ | beginner + chronic=22 < 25 km → hint "preparatory_cycle" |

**Décision attendue :** `maintain` (P1 — RULE-005)

**Plan hints :** `["preparatory_cycle_before_marathon_specific"]`

**`llm_context.confidence_caveat`** : `"medium"` → caveata LLM `"low_confidence_advice"`

**Garde-fous vérifiés :** GF-02, GF-06 (confidence=55 ≥ 50 : décision proposée avec caveat)

**Assertion critique :** Avec 4 semaines avant le marathon, un chronic_load de 22 km, et des données insuffisantes (historique court, pas de RPE), le moteur génère confidence=55 (medium) et bloque toute augmentation via RULE-005. RULE-016 signale que l'athlète n'est pas prêt pour une phase spécifique marathon. La décision est `maintain` avec un caveat LLM obligatoire.

---

### P-11 — Profil minimal (données insuffisantes)

**Objectif :** Un profil avec données très pauvres doit générer un `readiness_confidence_score` très bas (< 50) et déclencher GF-06.

**Scénario :** Coureur ayant repris après 20 jours d'arrêt. Aucun historique, aucun RPE, aucun temps de course, aucune VMA. Seuls les champs requis MVP sont renseignés.

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "experience_level_declared": "beginner",
    "recent_race_time_10k": null,
    "recent_race_time_half": null,
    "VMA_kmh": null
  },
  "week": {
    "weekly_distance_km": 30,
    "previous_week_distance_km": 28,
    "weekly_distance_history": [],
    "weekly_duration_min": 180,
    "long_run_km_last_week": 10,
    "long_run_km_previous_week": null,
    "avg_weekly_RPE": null,
    "fatigue_score": 3,
    "sleep_quality_score": 3,
    "pain_regions": [],
    "days_since_last_run": 20
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 30.0 km (fallback = current week) |
| `acwr_distance` | 1.0 |
| `acwr_reliable` | false (history vide) |
| `estimated_internal_load` | null |
| `target_marathon_pace_min_km` | null |
| `target_marathon_pace_source` | `"unavailable"` |

**Calcul readiness_confidence_score :**
```
acwr_unreliable:          −15
missing_rpe:              −10
missing_long_run_prev:     −5
long_interruption:        −20   (days=20 > 14)
per_missing_week (×4):    −20
Total penalties:           −70
confidence_score:           30  (< 50 → GF-06 actif)
```

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| RULE-003/004 | P0/P1 | ✗ | acwr_reliable = false |
| RULE-005 | P1 | ✗ | Δvolume 7.1% < 10% |
| **RULE-026** | **P1** | **✓** | days=20 > 14 |
| RULE-009 | P2 | ✓ | fatigue=3 == 3 → cap +5% (ignoré : P1 actif) |
| RULE-010 | P2 | ✓ | beginner → cap +5% (ignoré : P1 actif) |

**Décision attendue :** `maintain` — dual enforcement :
1. RULE-026 P1 (interruption)
2. GF-06 (confidence=30 < 50)

**`llm_context.confidence_caveat`** : `"low"`

**Garde-fous vérifiés :** GF-02, GF-06

**Assertion critique :** Un profil à données minimales génère confidence=30/100. RULE-026 et GF-06 convergent indépendamment vers `maintain`. Le moteur exige plus de données avant de proposer quoi que ce soit au-delà du statu quo. L'absence de signal négatif n'est pas traitée comme un feu vert.

---

### P-12 — Profil incohérent

**Objectif :** Un profil avec déclaration flatteuse et signaux objectifs contradictoires doit être recalé : experience_level override + détection du saut de volume anormal.

**Scénario :** Coureur se déclarant "advanced". La semaine précédente était anormalement basse (20 km, récupération probable), semaines before = 65+ km. Le coureur reprend à 55 km cette semaine. Ressent très bien (fatigue=1, sommeil=5). Son chronic_load de 55.75 km ne remplit pas les critères "advanced" (< 60 km).

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "experience_level_declared": "advanced",
    "recent_race_time_10k": 3900,
    "recent_race_time_half": null
  },
  "week": {
    "weekly_distance_km": 55,
    "previous_week_distance_km": 20,
    "weekly_distance_history": [20, 65, 68, 70],
    "weekly_duration_min": 310,
    "long_run_km_last_week": 22,
    "long_run_km_previous_week": 8,
    "avg_weekly_RPE": 4.0,
    "fatigue_score": 1,
    "sleep_quality_score": 5,
    "pain_regions": [],
    "days_since_last_run": 0
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 55.75 km |
| `acwr_distance` | 0.987 |
| `delta_volume_pct` | +175% |
| `delta_volume_reliable` | true (prev=20 ≥ 20, limite exacte — strict <, donc reliable) |
| `computed.experience_level` | `"intermediate"` |
| `experience_level_source` | `"calculated"` |

**Calcul experience_level :**
- `advanced` : chronic ≥ 60 → 55.75 < 60 → ✗
- `intermediate` : chronic ≥ 30 ✓, longest_race = 10 km ✓ → candidate = "intermediate"
- declared = "advanced" > candidate = "intermediate" → **computed = "intermediate", source = "calculated"**

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| **RULE-005** | **P1** | **✓** | Δvolume=175% > 10%, reliable=true → block_increase |
| RULE-011 | P3 | ✓ | acwr ∈ sweet spot, fatigue=1, sleep=5, no pain → +10 pts |
| RULE-012 | P3 | ✗ | experience = "intermediate" ≠ "advanced" |

**Décision attendue :** `maintain` (P1 — RULE-005)

**Assertion critique :** Fatigue=1 et sommeil=5 sont parfaits, mais RULE-005 détecte un saut de +175% (semaine basse suivie de reprise forte) et impose `maintain`. De plus, la déclaration "advanced" est recalée (`computed = "intermediate"`) — RULE-012 (bonus avancé) ne se déclenche pas. Le moteur ne se laisse pas tromper par les bons signaux subjectifs ni par la déclaration flatteuse.

---

### P-13 — Conflit maximal sécurité

**Objectif :** En présence de multiples déclencheurs P0, le moteur doit produire une UNIQUE décision `deload`, tous les autres déclencheurs P1/P4 étant reportés (non ignorés silencieusement).

**Scénario :** Profil catastrophique intentionnel — combine douleur critique multiple, ACWR dangereux, fatigue extrême, interruption longue, objectif irréaliste.

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "recent_race_time_half": 6000,
    "race_target_time": 10800
  },
  "week": {
    "weekly_distance_km": 115,
    "previous_week_distance_km": 60,
    "weekly_distance_history": [60, 55, 52, 50],
    "weekly_duration_min": 620,
    "long_run_km_last_week": 35,
    "long_run_km_previous_week": 22,
    "fatigue_score": 4,
    "sleep_quality_score": 2,
    "pain_regions": [
      { "region": "knee",    "intensity": 5, "days_persistent": 3, "pain_trend": "worsening" },
      { "region": "achilles","intensity": 4, "days_persistent": 4, "pain_trend": "worsening" }
    ],
    "days_since_last_run": 20
  },
  "context": {
    "current_phase": "specific_marathon",
    "weeks_to_race": 3
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 54.25 km |
| `acwr_distance` | 2.12 |
| `acwr_reliable` | true |
| `delta_volume_pct` | +91.7% |

**Règles P0 (toutes déclenchées + short_circuit) :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| **RULE-001** | **P0** | **✓** | knee: intensity=5 ≥ 4, days=3 ≥ 2 |
| **RULE-002** | **P0** | **✓** | achilles: intensity=4 ≥ 3, days=4 ≥ 3 — aussi knee ✓ |
| **RULE-003** | **P0** | **✓** | acwr=2.12 ≥ 2.0 |

**Règles auraient dû déclencher (short-circuitées) :**

| Règle | Priorité | Aurait déclenché | Reportée dans `ignored_rules_due_to_short_circuit` |
|-------|----------|-----------------|--------------------------------------------------|
| RULE-005 | P1 | ✓ (+91.7%) | ✓ |
| RULE-006 | P1 | ✓ (fatigue=4, sleep=2) | ✓ |
| RULE-026 | P1 | ✓ (days=20 > 14) | ✓ |
| RULE-019 | P4 | ✓ (objectif irréaliste) | ✓ |

**Décision attendue :** `deload` (−25%)
**`medical_referral`** : `true`

**Sortie attendue dans DecisionEnvelope :**
```json
{
  "decision": { "action": "deload", "delta_pct": -25.0 },
  "triggered_rules": ["RULE-001", "RULE-002", "RULE-003"],
  "ignored_rules_due_to_short_circuit": ["RULE-005", "RULE-006", "RULE-026", "RULE-019"],
  "medical_referral": true
}
```

**Garde-fous vérifiés :** GF-01, GF-08, GF-09

**Assertion critique :** Trois règles P0 déclenchées simultanément → une seule décision `deload`. Les règles P1/P4 qui auraient tiré sont répertoriées dans `ignored_rules_due_to_short_circuit` (pas silencieusement abandonnées). GF-09 garantit qu'une seule action est émise. L'audit complet reste possible malgré le court-circuit.

---

### P-14 — Faux profil vert

**Objectif :** L'absence de signal négatif ne doit pas être interprétée comme une certitude. GF-06 doit bloquer toute augmentation quand les données sont insuffisantes.

**Scénario :** Tous les signaux subjectifs sont positifs (fatigue=1, sommeil=5, aucune douleur). Mais les données objectives manquent totalement : aucun historique, aucune perf, aucun RPE. Seule VMA déclarée.

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "experience_level_declared": "intermediate",
    "recent_race_time_10k": null,
    "recent_race_time_half": null,
    "VMA_kmh": 12.0
  },
  "week": {
    "weekly_distance_km": 30,
    "previous_week_distance_km": 28,
    "weekly_distance_history": [],
    "weekly_duration_min": 180,
    "long_run_km_last_week": 12,
    "long_run_km_previous_week": null,
    "avg_weekly_RPE": null,
    "fatigue_score": 1,
    "sleep_quality_score": 5,
    "pain_regions": [],
    "days_since_last_run": 0
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 30.0 km (fallback) |
| `acwr_distance` | 1.0 |
| `acwr_reliable` | false |
| `target_marathon_pace_source` | `"vma_only"` |
| `computed.experience_level` | `"beginner"` (longest_race = 0 < 10 km) |
| `experience_level_source` | `"calculated"` |

**Calcul readiness_confidence_score :**
```
acwr_unreliable:          −15
missing_rpe:              −10
missing_long_run_prev:     −5
per_missing_week (×4):    −20
pace_vma_only:            −10
Total penalties:           −60
confidence_score:           40  (< 50 → GF-06 actif)
```

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| Aucune P0/P1 | — | ✗ | Signaux subjectifs parfaits |
| **RULE-010** | **P2** | **✓** | experience_level = "beginner" → cap +5% |
| RULE-011 | P3 | ✗ | acwr_reliable=false → condition non fiable (impl. doit vérifier) |

**Sans GF-06 :** P2 → `slight_increase` (+3%, capé à +5%)

**Avec GF-06 :** confidence=40 < 50 → cap forcé à `maintain`

**Décision attendue :** `maintain` (GF-06 écrase la décision P2)

**`llm_context.confidence_caveat`** : `"low"`

**Garde-fous vérifiés :** GF-06, GF-09

**Note d'implémentation :** RULE-011 doit vérifier `acwr_reliable` (comme RULE-003 et RULE-004) pour éviter un faux feu vert sur acwr fallback = 1.0. Ce profil expose ce risque.

**Assertion critique :** Fatigue=1, sommeil=5, aucune douleur — tous les signaux disponibles sont verts. Pourtant confidence=40 < 50. GF-06 interdit toute proposition au-delà de `maintain`, écrasant même la décision P2 (slight_increase). L'absence de signal négatif n'est PAS une preuve de sécurité.

---

### P-15 — Profil avancé stable

**Objectif :** Le moteur ne doit pas être sur-prudent pour un coureur avancé avec des données solides et une récupération excellente. Une augmentation normale doit rester possible.

**Scénario :** Coureur expérimenté, historique long et régulier (chronic=64 km), semi en 1h30, objectif marathon 3h30 (cohérent), ACWR dans le sweet spot, signaux de récupération excellents.

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "experience_level_declared": "advanced",
    "recent_race_time_half": 5400,
    "race_target_time": 12600
  },
  "week": {
    "weekly_distance_km": 74,
    "previous_week_distance_km": 68,
    "weekly_distance_history": [68, 65, 63, 60, 62, 64, 66, 68],
    "weekly_duration_min": 380,
    "long_run_km_last_week": 26,
    "long_run_km_previous_week": 24,
    "avg_weekly_RPE": 5.5,
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 0
  },
  "context": {
    "current_phase": "specific_marathon",
    "weeks_to_race": 14
  }
}
```

**Variables calculées attendues :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 64.0 km (mean 4 semaines) |
| `acwr_distance` | 1.156 |
| `acwr_reliable` | true (8 semaines) |
| `delta_volume_pct` | +8.8% |
| `delta_long_run_pct` | +8.3% |
| `computed.experience_level` | `"advanced"` |
| `experience_level_source` | `"reconciled"` |
| `target_marathon_pace_source` | `"race_target_time"` |
| `readiness_confidence_score` | ~95 (pénalités quasi nulles) |

**Vérification Riegel (cohérence objectif) :**
- Riegel depuis semi 5400s : 5400 × 2^1.06 = 11 248s ≈ 3h07
- Objectif : 12 600s = 3h30
- Écart : |11 248 − 12 600| / 12 600 = 10.7% < 15% → pas de RULE-019, pas de warning

**Règles :**

| Règle | Priorité | Déclenchée | Raison |
|-------|----------|-----------|--------|
| Aucune P0/P1/P2 | — | ✗ | Profil sain et données solides |
| **RULE-011** | **P3** | **✓** | acwr ∈ [0.8, 1.3], fatigue=2, sleep=4, no pain → +10 pts |
| **RULE-012** | **P3** | **✓** | experience="advanced", acwr ∈ sweet spot → +5 pts |

**Décision attendue :** `increase` (+10%, avancé)

**`readiness_score`** : élevé (tous composants bien remplis + P3 +15 pts)

**Garde-fous vérifiés :**
- GF-01 : pas de medical_referral → action ≠ deload (cohérent) ✓
- GF-02 : aucun P1 → increase autorisé ✓
- GF-07 : pas en taper → pas de force_decrease ✓
- GF-09 : action unique ✓

**Assertion critique :** Un coureur avancé avec 8 semaines d'historique solide, récupération excellente, et ACWR contrôlé (1.156) doit recevoir une décision `increase` (+10%). Le moteur n'est PAS sur-prudent : RULE-011 et RULE-012 accordent des bonus de score. L'objectif marathon 3h30 est cohérent avec le semi 1h30 (Riegel 3h07, écart 10.7%). Aucun frein actif.

---

### Vue d'ensemble des 15 profils

| # | Profil | Règle dominante | Décision | Garde-fou clé |
|---|--------|-----------------|----------|---------------|
| P-01 | Surcharge invisible | RULE-006 P1 | `maintain` | GF-02 |
| P-02 | Douleur critique | RULE-001/002 P0 | `deload` | GF-01, GF-08 |
| P-03 | Expérimenté fragile | RULE-002 P0 | `deload` | GF-01 |
| P-04 | Retour prudent | RULE-026 P1 | `maintain` | GF-02 |
| P-05 | Reprise ambitieuse | RULE-004 + RULE-026 P1 | `maintain` | GF-02 |
| P-06 | Débutant ambitieux | RULE-010 P2 + override exp. | `slight_increase` | GF-09 |
| P-07 | Objectif irréaliste | RULE-019 P4 | `increase` | GF-09 |
| P-08 | Taper correct | RULE-007 P1 | `decrease` | GF-07 |
| P-09 | Taper contradictoire | RULE-007 P1 | `decrease` | GF-07 |
| P-10 | Prépa insuffisante | RULE-005 P1 + confidence medium | `maintain` | GF-02, GF-06 |
| P-11 | Profil minimal | RULE-026 P1 + confidence=30 | `maintain` | GF-06 |
| P-12 | Profil incohérent | RULE-005 P1 + exp. override | `maintain` | GF-02 |
| P-13 | Conflit maximal | RULE-001/002/003 P0 | `deload` | GF-01, GF-08, GF-09 |
| P-14 | Faux profil vert | GF-06 (confidence=40) | `maintain` | GF-06 |
| P-15 | Avancé stable | RULE-011/012 P3 bonus | `increase` | GF-02, GF-07 |

**Couverture des garde-fous :**

| Garde-fou | Profils couverts |
|-----------|-----------------|
| GF-01 | P-02, P-03, P-13 |
| GF-02 | P-01, P-04, P-05, P-10, P-12, P-15 |
| GF-03 | (invariant property test — volume ≥ 0) |
| GF-04 | (test d'architecture — LLM read-only) |
| GF-05 | (test d'architecture — config hash) |
| GF-06 | P-11, P-14 (+ P-10 medium) |
| GF-07 | P-08, P-09 |
| GF-08 | P-02, P-13 |
| GF-09 | P-02, P-06, P-13, P-14, P-15 |
| GF-10 | (schema version — test CI) |
