# Knowledge Base Canonique — Coach Marathon IA — v1.2 (Implementation Ready)

> Version : 1.2 — spec d'exécution du moteur décisionnel
> Version parente : v1.1 (docs/knowledge_engine/KB_CANONICAL_v1.1.md)
> Statut : contrat d'implémentation — aucune nouvelle connaissance métier, formalisation stricte de la v1.1
> Scope : schémas de données, moteur de règles, séparation config, actions du coach
> Contrainte de lecture : ce document doit être suffisant pour développer le moteur sans interprétation humaine

---

## 0. Portée et lecture

Cette v1.2 **ne fait qu'un travail de spécification** :
- La v1.1 dit *quoi* le moteur doit faire.
- La v1.2 dit *comment* il doit être structuré pour le faire.

**Ce qui change vs v1.1 (autorisé par l'utilisateur, en dehors des renommages) :**

1. Ajout de `readiness_confidence_score` (score de confiance du moteur dans sa propre sortie)
2. Renommage `weekly_internal_load` → `estimated_internal_load` (éviter l'amalgame avec le session-RPE Foster)
3. Ajout de `pain_regions[].pain_trend` (évolution de la douleur)
4. `experience_level` devient **calculé** par critères, avec `experience_level_declared` comme signal auxiliaire
5. Hiérarchie explicite pour `target_marathon_pace_min_km` : `race_target_time` > semi récent > 10k récent > VMA

**Ce qui n'est pas dans ce document :** algorithmes de calcul finaux (formules livrées mais paramètres pouvant être ajustés), UI, endpoints API, base de données.

---

## 1. Schéma canonique du coureur — `RunnerState`

### 1.1. Structure JSON de haut niveau

```
RunnerState {
  meta:      RunnerStateMeta
  profile:   RunnerProfile
  week:      WeekInput
  context:   PlanContext
  computed:  ComputedVariables   // rempli par le moteur, jamais par l'utilisateur
}
```

### 1.2. `RunnerStateMeta` — traçabilité de l'entrée

| Champ | Type | Unité | Requis MVP | Défaut | Validation | Notes |
|-------|------|-------|-----------|--------|-----------|-------|
| `runner_id` | string (uuid) | — | ✅ | — | UUID v4 | Identifiant stable du coureur |
| `submitted_at` | string (ISO-8601) | — | ✅ | `now()` | ISO-8601 UTC | Timestamp de soumission |
| `week_start_date` | string (ISO-8601 date) | — | ✅ | — | Doit être un lundi (ou paramètre `week_start_day`) | Semaine à laquelle se réfère `WeekInput` |
| `schema_version` | string (semver) | — | ✅ | `"1.2.0"` | Regex `^\d+\.\d+\.\d+$` | Permet la migration future |

### 1.3. `RunnerProfile` — collecte unique + mise à jour ponctuelle

| Champ | Type | Unité | Requis MVP | Défaut | Validation | Notes |
|-------|------|-------|-----------|--------|-----------|-------|
| `age` | int | années | ✅ | — | 14 ≤ age ≤ 90 | < 14 ou > 90 → alerte médicale, refuse la prescription |
| `sex` | enum | — | ⭕ optionnel | `"unspecified"` | ∈ `{"male","female","unspecified"}` | Non utilisé V1, réservé V2 |
| `experience_level_declared` | enum | — | ✅ | — | ∈ `{"beginner","intermediate","advanced"}` | **Signal auxiliaire** — le vrai `experience_level` est calculé (§ 5.4) |
| `pathologies_connues` | array[string] | — | ⭕ | `[]` | Chaîne libre, max 200 char | Alerte médicale si non vide |
| `recent_race_time_10k` | int / null | secondes | ⭕ (mais ≥ 1 requis parmi 10k/semi/VMA) | `null` | 1200 ≤ v ≤ 7200 (20–120 min) | Format d'entrée UI : `mm:ss` |
| `recent_race_time_half` | int / null | secondes | ⭕ (idem) | `null` | 2700 ≤ v ≤ 18000 (45–300 min) | |
| `recent_race_time_marathon` | int / null | secondes | ⭕ | `null` | 7200 ≤ v ≤ 36000 (2–10 h) | Utile V2 pour prédiction |
| `VMA_kmh` | float / null | km/h | ⭕ (idem) | `null` | 8 ≤ v ≤ 25 | Testée ou estimée |
| `sessions_per_week_available` | int | — | ✅ | — | 1 ≤ v ≤ 14 | Contrainte calendrier |
| `race_target_time` | int / null | secondes | ⭕ | `null` | 7200 ≤ v ≤ 36000 (2–10 h) | Objectif marathon. Feed la hiérarchie de pace (§ 5.5). |
| `race_target_date` | string / null | ISO-8601 date | ⭕ | `null` | ≥ `week_start_date` | Sert à recalculer `weeks_to_race` |

**Règle de cohérence croisée** (validation) :
- Au moins l'un parmi `recent_race_time_10k`, `recent_race_time_half`, `VMA_kmh` doit être renseigné, sinon `target_marathon_pace_min_km = null` et le moteur passe en mode "sans allure cible".
- Si `race_target_time` incohérent (> 20% plus rapide que ce que prédisent les temps récents via Riegel) → warning `"race_target_unrealistic"`, la valeur est acceptée mais annotée.

### 1.4. `WeekInput` — collecte hebdomadaire

| Champ | Type | Unité | Requis MVP | Défaut | Validation | Notes |
|-------|------|-------|-----------|--------|-----------|-------|
| `weekly_distance_km` | float | km | ✅ | — | 0 ≤ v ≤ 300 | 0 accepté (semaine off) |
| `previous_week_distance_km` | float | km | ✅ | — | 0 ≤ v ≤ 300 | Peut être 0 |
| `weekly_distance_history` | array[float] | km | ✅ | `[]` | Longueur 0..8 ; chaque val 0..300 | Ordre : plus récent → plus ancien. Utilisé pour ACWR et pente. |
| `weekly_duration_min` | float | minutes | ✅ | — | 0 ≤ v ≤ 1800 (30h max) | |
| `long_run_km_last_week` | float | km | ✅ | — | 0 ≤ v ≤ `weekly_distance_km` | Doit être ≤ total. Sinon → `"invalid_long_run"` erreur. |
| `long_run_km_previous_week` | float / null | km | ⭕ | `null` | 0 ≤ v ≤ 300 | Nécessaire pour `delta_long_run_pct` |
| `avg_weekly_RPE` | float / null | 0–10 | ⭕ | `null` | 0 ≤ v ≤ 10 | Auto-déclaré. `low_confidence = true` — voir § 2.5 |
| `fatigue_score` | int | 1–5 | ✅ | — | ∈ {1,2,3,4,5} | **1 = très faible, 5 = extrême** |
| `sleep_quality_score` | int | 1–5 | ✅ | — | ∈ {1,2,3,4,5} | **[v1.2 confirmé]** 1 = très mauvaise, 5 = excellente (inversé vs v1.0) |
| `pain_regions` | array[PainRegion] | — | ✅ | `[]` | Longueur 0..10 | Voir schéma § 1.4.1 |
| `days_since_last_run` | int | jours | ✅ | — | 0 ≤ v ≤ 365 | 0 = a couru aujourd'hui |
| `session_notes` | string | — | ⭕ | `""` | Max 2000 char | Alimente la couche LLM uniquement |

#### 1.4.1. Sous-schéma `PainRegion`

| Champ | Type | Unité | Requis | Défaut | Validation | Notes |
|-------|------|-------|--------|--------|-----------|-------|
| `region` | enum | — | ✅ | — | ∈ `PAIN_REGION_ENUM` (voir § 1.7) | |
| `intensity` | int | 0–5 | ✅ | — | ∈ {0,1,2,3,4,5} | 0 = pas de douleur (mais l'entrée existe) |
| `days_persistent` | int | jours | ✅ | — | 0 ≤ v ≤ 365 | Nb de jours consécutifs |
| `pain_trend` | enum | — | ✅ | `"unknown"` | ∈ `{"improving","stable","worsening","unknown"}` | **[NOUVEAU v1.2]** Évolution ressentie sur les 3 derniers jours |
| `mechanism` | enum | — | ⭕ | `"unknown"` | ∈ `{"acute","chronic","mechanical","overuse","unknown"}` | V2 — réservé |

**Règle** : si `intensity == 0`, `days_persistent` et `pain_trend` sont ignorés par les règles (mais conservés en donnée brute).

### 1.5. `PlanContext` — contexte de planification

| Champ | Type | Unité | Requis MVP | Défaut | Validation | Notes |
|-------|------|-------|-----------|--------|-----------|-------|
| `current_phase` | enum | — | ✅ | `"general"` | ∈ `PHASE_ENUM` | Voir § 1.7 |
| `weeks_to_race` | int / null | semaines | ⭕ | `null` | 0 ≤ v ≤ 52 | Recalculable depuis `race_target_date` |
| `weeks_since_last_injury` | int / null | semaines | ⭕ | `null` | 0 ≤ v ≤ 520 | `null` = aucune blessure récente ou inconnue |
| `terrain_type` | enum | — | ⭕ | `"road"` | ∈ `{"road","trail","track","treadmill","mixed"}` | Contextuel, non décisionnel V1 |
| `mood_motivation_score` | int / null | 1–5 | ⭕ | `null` | ∈ {1..5} | UX-only V1 |

### 1.6. `ComputedVariables` — sortie du moteur

Cette section n'est **jamais fournie par l'utilisateur**. Elle est calculée par le moteur (§ 2).

### 1.7. Enums canoniques

```
PAIN_REGION_ENUM = [
  "achilles",        // tendon d'Achille
  "knee",            // genou
  "shin",            // tibia (périostite)
  "hip",             // hanche
  "foot",            // pied (voûte, orteils)
  "calf",            // mollet
  "hamstring",       // ischio-jambiers
  "quadriceps",      // quadriceps
  "lower_back",      // lombaires
  "glute",           // fessier
  "it_band",         // bandelette ilio-tibiale
  "ankle",           // cheville
  "other"            // autre
]

PHASE_ENUM = [
  "general",              // phase générale (base)
  "specific_marathon",    // phase spécifique marathon
  "taper",                // affûtage
  "return_from_injury",   // retour de blessure
  "off_season"            // hors saison
]

CRITICAL_PAIN_REGIONS = subset of PAIN_REGION_ENUM = [
  "achilles", "knee", "shin", "hip", "foot"
]
```

### 1.8. Validation globale des entrées

**Niveau `ERROR` (refus d'exécution du moteur) :**
- Un champ requis MVP est absent
- Un enum est hors valeurs autorisées
- Un intervalle numérique est violé (age < 14, distance > 300, etc.)
- `long_run_km_last_week > weekly_distance_km`
- `weekly_distance_history` contient une valeur négative
- `week_start_date` postérieur à `submitted_at`

**Niveau `WARNING` (exécution avec annotations) :**
- `weekly_distance_history` a < 4 entrées → `computed.acwr_reliable = false`
- `avg_weekly_RPE` absent → `estimated_internal_load = null`, `readiness_confidence_score` pénalisé
- Race target incohérent (voir § 1.3) → `warnings += "race_target_unrealistic"`
- `pathologies_connues` non vide → `warnings += "medical_referral_recommended"`
- Fatigue et sommeil incohérents entre eux N semaines de suite → V2

**Niveau `INFO` (annotation informative) :**
- Semaine à volume 0 → `computed.zero_volume_week = true`

---

## 2. Schéma des variables calculées

### 2.1. `ComputedVariables` — structure

```
ComputedVariables {
  chronic_load_distance:            float
  acwr_distance:                    float | null
  acwr_reliable:                    bool
  delta_volume_pct:                 float | null   // null si prev_week ~ 0
  delta_volume_reliable:            bool
  delta_long_run_pct:               float | null
  estimated_internal_load:          float | null   // renommé de weekly_internal_load
  estimated_internal_load_notice:   string         // toujours "aggregated_RPE_estimate"
  target_marathon_pace_min_km:      float | null
  target_marathon_pace_source:      enum           // voir § 2.6
  experience_level:                 enum           // voir § 5.4
  experience_level_source:          enum           // "declared" | "calculated" | "reconciled"
  readiness_score:                  int (0..100)
  readiness_confidence_score:       int (0..100)   // NOUVEAU v1.2
  readiness_component_scores: {
    recovery:                       int (0..35)
    load:                           int (0..35)
    progression:                    int (0..15)
    marathon_prep:                  int (0..15)
    p3_adjustments:                 int (-10..+10)
  }
  fatigue_trend:                    enum ("improving"|"stable"|"worsening"|"unknown")
  progression_slope_km_per_week:    float          // pente régression linéaire
  zero_volume_week:                 bool
}
```

### 2.2. Formules canoniques

**`chronic_load_distance`** (km) :
```
IF len(weekly_distance_history) == 0:
    chronic_load_distance = weekly_distance_km   // fallback conservateur
    acwr_reliable = false
ELSE:
    window = min(len(weekly_distance_history), params.chronic_load_window_weeks)  // default 4
    IF params.chronic_load_method == "simple_mean":
        chronic_load_distance = mean(weekly_distance_history[:window])
    ELIF params.chronic_load_method == "ewma":
        chronic_load_distance = EWMA(weekly_distance_history, alpha=params.ewma_alpha)  // default 0.13
    acwr_reliable = (len(weekly_distance_history) >= params.acwr_min_history_weeks)  // default 4
```

**`acwr_distance`** (ratio sans unité) :
```
IF chronic_load_distance <= params.chronic_load_min_km:  // default 5 km
    acwr_distance = null   // rapport non significatif si chronique trop faible
    acwr_reliable = false
ELSE:
    acwr_distance = weekly_distance_km / chronic_load_distance
```

**`delta_volume_pct`** (%) :
```
IF previous_week_distance_km < params.small_volume_threshold_km:  // default 20 km
    delta_volume_pct = (weekly_distance_km - previous_week_distance_km) / max(previous_week_distance_km, 1) * 100
    delta_volume_reliable = false   // signal existe mais RULE-005 ignorée (voir § 3)
ELSE:
    delta_volume_pct = (weekly_distance_km - previous_week_distance_km) / previous_week_distance_km * 100
    delta_volume_reliable = true
```

**`delta_long_run_pct`** (%) :
```
IF long_run_km_previous_week == null OR long_run_km_previous_week <= 0:
    delta_long_run_pct = null
ELSE:
    delta_long_run_pct = (long_run_km_last_week - long_run_km_previous_week) / long_run_km_previous_week * 100
```

**`estimated_internal_load`** (unités arbitraires) — renommé et clarifié :
```
IF avg_weekly_RPE == null:
    estimated_internal_load = null
ELSE:
    estimated_internal_load = avg_weekly_RPE * weekly_duration_min

estimated_internal_load_notice = "aggregated_RPE_estimate"
// Rappel : ce n'est PAS un session-RPE Foster (qui exige un RPE par séance).
// Nom explicite pour éviter toute confusion en aval.
```

### 2.3. `readiness_score` (0..100) — composition

Toutes les fonctions sont bornées **[0, poids_max]** et clampées.

```
recovery_component (0..35) =
    fatigue_component (0..15)     // 15 pts si fatigue==1, 0 pt si fatigue==5, linéaire
  + sleep_component (0..10)       // sens direct : 10 pts si sleep==5, 0 pt si sleep==1
  + pain_component (0..10)        // 10 - 2 * max_pain_intensity, clampé [0..10]

load_component (0..35) =
    acwr_component (0..20)        // courbe en cloche centrée sur [0.8..1.3], 0 si acwr manquant/non fiable
  + delta_volume_component (0..10)  // 10 si delta<=0, 0 si delta>=15%, linéaire décroissant
  + chronic_baseline_component (0..5)  // bonus si chronic_load couvre la phase (règle produit § 5)

progression_component (0..15) =
    slope_component (0..10)       // + si pente positive contrôlée, - si régressive
  + long_run_component (0..5)     // dépend de delta_long_run_pct et phase

marathon_prep_component (0..15) =
    phase_coherence_component (0..8)    // cohérence current_phase vs weeks_to_race
  + pace_readiness_component (0..7)     // target_marathon_pace défini et cohérent ?

p3_adjustments (-10..+10) =
    sum de RULE-011, RULE-012 (RULE-013, RULE-014 désactivées V1)
    clampé dans [-10, +10]

readiness_score = clamp(
    recovery_component + load_component + progression_component + marathon_prep_component + p3_adjustments,
    0, 100
)
```

**Toutes les constantes 35/35/15/15/10 sont dans `thresholds.yaml` (§ 4).**

### 2.4. `readiness_confidence_score` (0..100) — NOUVEAU v1.2

Mesure **la confiance du moteur dans sa propre sortie**, indépendamment du niveau de forme du coureur.

```
readiness_confidence_score = 100 - penalties

penalties = 0
IF acwr_reliable == false:                       penalties += params.penalty_acwr_unreliable   (default 15)
IF avg_weekly_RPE == null:                       penalties += params.penalty_missing_rpe       (default 10)
IF long_run_km_previous_week == null:            penalties += params.penalty_missing_long_run  (default 5)
IF days_since_last_run > 14:                     penalties += params.penalty_long_interruption (default 20)
IF len(weekly_distance_history) < 4:             penalties += (4 - len) * params.penalty_per_missing_week  (default 5)
IF target_marathon_pace_source == "vma_only":    penalties += params.penalty_pace_vma_only     (default 10)
IF experience_level_source == "declared":        penalties += params.penalty_experience_declared_only (default 5)
IF max(pain_regions[].intensity) > 0:            penalties += params.penalty_active_pain       (default 5)
IF submitted_at > week_start_date + 10 days:     penalties += params.penalty_stale_input       (default 10)

readiness_confidence_score = clamp(100 - penalties, 0, 100)
```

**Contrat de sortie** :
- `readiness_confidence_score >= params.confidence_min_high` (default 75) → le moteur propose une décision.
- `params.confidence_min_medium` (default 50) ≤ score < `confidence_min_high` → décision proposée mais accompagnée d'un caveat LLM `"low_confidence_advice"`.
- `readiness_confidence_score < params.confidence_min_medium` → le moteur refuse de dépasser `maintain` et exige des données supplémentaires.

### 2.5. `fatigue_trend` — méthode

```
IF len(fatigue_score_history) < 3:
    fatigue_trend = "unknown"
ELSE:
    diff = fatigue_score_history[recent] - fatigue_score_history[oldest]
    IF diff <= -1: fatigue_trend = "improving"
    ELIF diff >= +1: fatigue_trend = "worsening"
    ELSE: fatigue_trend = "stable"
```
(Nécessite un stockage inter-semaine — hors périmètre stateless du moteur mais listé pour complétude.)

### 2.6. `target_marathon_pace_min_km` — hiérarchie [NOUVELLE v1.2]

**Ordre de priorité** (arrêter au premier disponible) :

```
1. IF race_target_time != null:
      target_pace = race_target_time / 42.195
      target_marathon_pace_source = "race_target_time"
      // Validation : si écart > 20% vs Riegel(recent_race_time_half) → warning "race_target_unrealistic"
      // mais la valeur reste utilisée.

2. ELIF recent_race_time_half != null:
      // Riegel : t2 = t1 * (d2 / d1)^1.06
      predicted_marathon_time = recent_race_time_half * (42.195 / 21.0975) ^ params.riegel_exponent  // default 1.06
      target_pace = predicted_marathon_time / 42.195
      target_marathon_pace_source = "riegel_from_half"

3. ELIF recent_race_time_10k != null:
      predicted_marathon_time = recent_race_time_10k * (42.195 / 10.0) ^ params.riegel_exponent
      target_pace = predicted_marathon_time / 42.195
      target_marathon_pace_source = "riegel_from_10k"

4. ELIF VMA_kmh != null:
      // Formule produit : allure marathon ≈ 75–85% de VMA (Billat-inspiré, calibré par experience_level)
      marathon_speed_kmh = VMA_kmh * params.vma_marathon_fraction[experience_level]
        // beginner: 0.75, intermediate: 0.80, advanced: 0.83 (paramètres [PROD])
      target_pace = 60.0 / marathon_speed_kmh  // min/km
      target_marathon_pace_source = "vma_only"

5. ELSE:
      target_marathon_pace_min_km = null
      target_marathon_pace_source = "unavailable"
```

**Unité de sortie** : minutes/km (float).
**Cohérence** : si sources 1 et 2 disponibles et écart > 20% → priorité à `race_target_time` mais `warnings += "race_target_unrealistic"`.

---

## 3. Moteur de règles — spécification exacte

**Convention format :**
```
RULE-XXX — nom court
  priority:            P0 | P1 | P2 | P3 | P4
  action_type:         deload_forced | force_decrease | block_increase | cap_increase | score_adjust | plan_hint
  short_circuit:       true | false  (true = ignore les priorités inférieures)

  IF <condition logique exacte, en pseudo-code>
  THEN <sortie machine>
  ELSE <no-op sauf mention>
  OUTPUT <schéma JSON>

  variables_used:      [liste]
  configurable_params: [liste avec valeurs par défaut]
  justification:       [source refs + tag preuve/signal]
  tests_expected:      [liste des cas à couvrir]
```

**Contrat de sortie par règle** :
```json
{
  "rule_id": "RULE-XXX",
  "triggered": true|false,
  "action": "deload"|"force_decrease"|"block_increase"|"cap_increase"|"score_adjust"|"plan_hint"|null,
  "priority": "P0"|"P1"|"P2"|"P3"|"P4",
  "cap_pct": float|null,
  "score_delta": int|null,
  "reason": "string lisible humain",
  "params_used": {...},
  "variables_snapshot": {...}
}
```

---

### RULE-001 — Douleur critique

```
priority:            P0
action_type:         deload_forced
short_circuit:       true

IF  exists r in pain_regions such that
      r.intensity >= params.pain_critical_intensity     // default 4
      AND r.days_persistent >= params.pain_critical_days  // default 2
THEN
      action = "deload"
      medical_referral = true
      short_circuit_downstream = true
ELSE  no-op

OUTPUT
  { rule_id: "RULE-001", triggered, action: "deload"|null,
    priority: "P0",
    reason: "Douleur intensité {r.intensity} pendant {r.days_persistent}j sur {r.region}",
    medical_referral: bool }

variables_used:      pain_regions[].intensity, pain_regions[].days_persistent, pain_regions[].region
configurable_params: pain_critical_intensity (int, default 4, range 3..5)
                     pain_critical_days       (int, default 2, range 1..7)
justification:       S2 + S3:Cook/Dubois, [SCI] concept, [PROD] seuils, signal Moyen
tests_expected:
  - no_pain              → pain_regions = []                                 → not_triggered
  - below_intensity      → intensity=3, days=5                               → not_triggered
  - below_days           → intensity=4, days=1                               → not_triggered
  - exact_threshold      → intensity=4, days=2                               → triggered
  - extreme_short        → intensity=5, days=1                               → not_triggered
  - multiple_regions_one_meets → r1 ok, r2 not → triggered_reason cites r1
  - zero_intensity_entry → intensity=0, days=10                              → not_triggered
```

---

### RULE-002 — Douleur tendon/articulation

```
priority:            P0
action_type:         deload_forced
short_circuit:       true

IF  exists r in pain_regions such that
      r.region in CRITICAL_PAIN_REGIONS                             // achilles, knee, shin, hip, foot
      AND r.intensity >= params.pain_tendon_intensity               // default 3
      AND r.days_persistent >= params.pain_tendon_days              // default 3
THEN
      action = "deload"
      medical_referral = true
      short_circuit_downstream = true
ELSE  no-op

OUTPUT { rule_id, triggered, action, priority, reason: "Zone critique {r.region} — risque tendinopathie" }

variables_used:      pain_regions[].region, pain_regions[].intensity, pain_regions[].days_persistent
configurable_params: pain_tendon_intensity (int, default 3, range 2..5)
                     pain_tendon_days      (int, default 3, range 2..7)
                     CRITICAL_PAIN_REGIONS (set, default {achilles,knee,shin,hip,foot})
justification:       S2 + S3:Cook, [SCI], signal Moyen
tests_expected:
  - other_region_high  → region="other", int=5, days=10                → not_triggered (RULE-001 possible)
  - knee_exact         → region="knee", int=3, days=3                  → triggered
  - achilles_below     → region="achilles", int=2, days=5              → not_triggered
  - pain_trend_worsening_shortcut → V2 : envisager déclenchement anticipé si trend="worsening"
```

**Note pour v1.2** : `pain_trend` n'entre PAS dans RULE-002 en V1 (par prudence pour ne pas overrider sans preuve). Mais il alimente l'explication LLM et pourra abaisser les seuils en V2.

---

### RULE-003 — ACWR danger

```
priority:            P0
action_type:         deload_forced
short_circuit:       true

IF  computed.acwr_reliable == true
    AND computed.acwr_distance != null
    AND computed.acwr_distance >= params.acwr_deload_threshold   // default 2.0
THEN
      action = "deload"
      short_circuit_downstream = true
ELSE  no-op

OUTPUT { rule_id, triggered, action, priority, reason: "ACWR {value} ≥ {threshold} — charge aiguë 2× la normale" }

variables_used:      computed.acwr_distance, computed.acwr_reliable
configurable_params: acwr_deload_threshold (float, default 2.0, range 1.7..2.5)
justification:       S2 + S3:Gabbett, [PRAT] (voir caveat modèle ACWR § 6 v1.1), signal Fort
tests_expected:
  - acwr_unreliable_high_ratio → history<4 sem, ratio=2.5 → not_triggered (guard)
  - acwr_reliable_below        → ratio=1.9                → not_triggered
  - acwr_reliable_exact        → ratio=2.0                → triggered
  - acwr_null                  → chronic_load < min       → not_triggered
```

---

### RULE-004 — ACWR élevé

```
priority:            P1
action_type:         block_increase   // décision max = maintain
short_circuit:       false

IF  computed.acwr_reliable == true
    AND computed.acwr_distance != null
    AND params.acwr_block_threshold < computed.acwr_distance < params.acwr_deload_threshold
    // default 1.5 < acwr < 2.0
THEN
      decision_cap = "maintain"
ELSE  no-op

OUTPUT { rule_id, triggered, action: "block_increase"|null, priority: "P1",
         reason: "ACWR {value} — zone à risque" }

variables_used:      computed.acwr_distance, computed.acwr_reliable
configurable_params: acwr_block_threshold  (float, default 1.5, range 1.3..1.8)
                     acwr_deload_threshold (float, default 2.0, range 1.7..2.5)
justification:       S2 + S3:Gabbett, [PRAT], signal Fort
tests_expected:
  - acwr_1_4  → not_triggered
  - acwr_1_5_exact → not_triggered (strict >)
  - acwr_1_6  → triggered
  - acwr_2_0  → not_triggered here (RULE-003 handles ≥ 2.0)
```

---

### RULE-005 — Progression volume > 10%

```
priority:            P1
action_type:         block_increase
short_circuit:       false

IF  computed.delta_volume_reliable == true
    AND computed.delta_volume_pct != null
    AND computed.delta_volume_pct > params.weekly_increase_cap_pct   // default 10
THEN
      decision_cap = "maintain"
ELSE  no-op

OUTPUT { rule_id, triggered, action, priority: "P1", reason: "Δvolume {pct}% > {cap}%" }

variables_used:      computed.delta_volume_pct, computed.delta_volume_reliable
configurable_params: weekly_increase_cap_pct    (float, default 10, range 5..15)
                     small_volume_threshold_km  (float, default 20, range 10..30)
justification:       S1:K7 + S2, [PRAT] (règle non validée par RCT — v1.1 § 6), signal Fort
tests_expected:
  - small_prev_week_10km_delta_50 → not_triggered (guard : delta_reliable=false)
  - big_prev_week_delta_9         → not_triggered
  - big_prev_week_delta_11        → triggered
  - big_prev_week_delta_negative  → not_triggered (delta < cap)
```

---

### RULE-006 — Récupération insuffisante (logique corrigée v1.1)

```
priority:            P1
action_type:         block_increase
short_circuit:       false

IF  (fatigue_score >= params.fatigue_high_threshold             // default 4
     AND sleep_quality_score <= params.sleep_low_threshold      // default 2  (rappel : 1=mauvaise)
    )
    OR fatigue_score >= params.fatigue_extreme_threshold        // default 5
THEN
      decision_cap = "maintain"
ELSE  no-op

OUTPUT { rule_id, triggered, action, priority: "P1", reason: "Fatigue/sommeil insuffisants" }

variables_used:      fatigue_score, sleep_quality_score
configurable_params: fatigue_high_threshold     (int, default 4, range 3..5)
                     fatigue_extreme_threshold  (int, default 5, range 4..5)
                     sleep_low_threshold        (int, default 2, range 1..3)
justification:       S1:K6,K12 + S2 + S3:Mujika, [SCI] concept, [PROD] seuils, signal Moyen
tests_expected:
  - fatigue_5_sleep_5           → triggered (fatigue==5 OR branch)
  - fatigue_4_sleep_5           → not_triggered (sleep bon)
  - fatigue_4_sleep_2           → triggered
  - fatigue_3_sleep_1           → not_triggered here (RULE-009 P2 s'en occupe)
  - fatigue_5_sleep_1           → triggered
```

---

### RULE-007 — Phase taper : décrément forcé (corrigée v1.1)

```
priority:            P1
action_type:         force_decrease
short_circuit:       false

IF  current_phase == "taper"
THEN
      decision_forced = "decrease"
      target_delta_pct_range = [-params.taper_volume_reduction_max, -params.taper_volume_reduction_min]
      // default [-60, -40]
ELSE  no-op

OUTPUT { rule_id, triggered, action: "force_decrease"|null, priority: "P1",
         target_delta_pct: float within range,
         reason: "Phase taper : −{X}% volume, intensité maintenue" }

variables_used:      current_phase
configurable_params: taper_volume_reduction_min (float, default 40, range 20..50)
                     taper_volume_reduction_max (float, default 60, range 50..80)
justification:       S1:K1 + S2 + S3:Mujika, [SCI], signal Fort
tests_expected:
  - phase_general                → not_triggered
  - phase_specific_marathon      → not_triggered
  - phase_taper                  → triggered, delta in [-60, -40]
  - phase_taper_but_p0_pain      → RULE-001 short_circuits, RULE-007 ignored
```

---

### RULE-008 — Blessure récente

```
priority:            P2
action_type:         cap_increase
short_circuit:       false

IF  weeks_since_last_injury != null
    AND weeks_since_last_injury < params.recent_injury_cap_weeks   // default 4
THEN
      cap_pct = params.recent_injury_max_increase_pct              // default 5
ELSE  no-op

OUTPUT { rule_id, triggered, action: "cap_increase"|null, cap_pct, priority: "P2",
         reason: "Blessure il y a {n} semaines — cap +{cap}%" }

variables_used:      weeks_since_last_injury
configurable_params: recent_injury_cap_weeks         (int, default 4, range 2..8)
                     recent_injury_max_increase_pct  (float, default 5, range 3..7)
justification:       S2, [PROD] seuil arbitraire (CONF-005), signal Fort
tests_expected:
  - null_injury      → not_triggered
  - 2_weeks_ago      → triggered, cap=5
  - 4_weeks_ago      → not_triggered (strict <)
  - 6_weeks_ago      → not_triggered
```

---

### RULE-009 — Fatigue/sommeil modéré

```
priority:            P2
action_type:         cap_increase
short_circuit:       false

IF  fatigue_score == params.fatigue_moderate_value           // default 3
    OR sleep_quality_score == params.sleep_moderate_value    // default 3
THEN
      cap_pct = params.moderate_fatigue_cap_pct              // default 5
ELSE  no-op

OUTPUT { rule_id, triggered, action, cap_pct, priority: "P2", reason }

variables_used:      fatigue_score, sleep_quality_score
configurable_params: fatigue_moderate_value    (int, default 3)
                     sleep_moderate_value      (int, default 3)
                     moderate_fatigue_cap_pct  (float, default 5, range 3..7)
justification:       S2, [PROD], signal Moyen
tests_expected:
  - fatigue_3_sleep_5      → triggered
  - fatigue_5_sleep_3      → triggered (mais RULE-006 P1 gagne — voir orchestration § 3.99)
  - fatigue_2_sleep_2      → not_triggered
```

---

### RULE-010 — Beginner cap

```
priority:            P2
action_type:         cap_increase
short_circuit:       false

IF  computed.experience_level == "beginner"
THEN
      cap_pct = params.beginner_max_increase_pct   // default 5
ELSE  no-op

OUTPUT { rule_id, triggered, cap_pct, priority: "P2" }

variables_used:      computed.experience_level   (voir § 5.4 calcul)
configurable_params: beginner_max_increase_pct   (float, default 5, range 3..7)
justification:       S1:K3 + S2, [PROD], signal Fort (dépend qualité calcul experience_level)
tests_expected:
  - beginner   → triggered, cap=5
  - intermediate → not_triggered
  - advanced  → not_triggered
```

---

### RULE-011 — Feu vert multi-critères (clarifiée v1.1)

```
priority:            P3
action_type:         score_adjust
short_circuit:       false

IF  computed.acwr_distance != null
    AND params.acwr_sweet_spot_min <= computed.acwr_distance <= params.acwr_sweet_spot_max
    AND fatigue_score <= params.fatigue_low_threshold                // default 2
    AND sleep_quality_score >= params.sleep_high_threshold           // default 4
    AND max([r.intensity for r in pain_regions], default=0) <= params.pain_ok_threshold  // default 2
THEN
      score_delta = +params.green_light_bonus_pts                    // default +10
ELSE  no-op

OUTPUT { rule_id, triggered, score_delta, priority: "P3", reason }

variables_used:      computed.acwr_distance, fatigue_score, sleep_quality_score, pain_regions[].intensity
configurable_params: acwr_sweet_spot_min       (float, default 0.8, range 0.7..0.9)
                     acwr_sweet_spot_max       (float, default 1.3, range 1.2..1.5)
                     fatigue_low_threshold     (int, default 2, range 1..3)
                     sleep_high_threshold      (int, default 4, range 3..5)
                     pain_ok_threshold         (int, default 2, range 1..3)
                     green_light_bonus_pts     (int, default 10, range 5..15)
justification:       S2, [PROD] composition, signal Moyen
tests_expected:
  - all_green   → triggered
  - one_pain_3  → not_triggered
  - acwr_1_5    → not_triggered
```

---

### RULE-012 — Tolérance avancée

```
priority:            P3
action_type:         score_adjust
short_circuit:       false

IF  computed.experience_level == "advanced"
    AND computed.acwr_distance != null
    AND params.acwr_sweet_spot_min <= computed.acwr_distance <= params.acwr_sweet_spot_max
THEN
      score_delta = +params.advanced_tolerance_bonus_pts   // default +5
ELSE  no-op

OUTPUT { rule_id, triggered, score_delta, priority: "P3" }

variables_used:      computed.experience_level, computed.acwr_distance
configurable_params: advanced_tolerance_bonus_pts (int, default 5, range 3..8)
justification:       S2, [PROD], signal Fort
tests_expected:
  - advanced_acwr_1  → triggered
  - beginner_acwr_1  → not_triggered
```

---

### RULE-013 — Performance déclinante  [DÉSACTIVÉE V1]

```
priority:            P3
status:              disabled_v1
reason_disabled:     "performance_trend requires V2 formula (CONF-008)"

// Spec conservée pour V2 :
IF  performance_trend == "declining" AND acwr_distance >= 1.0
THEN score_delta = -params.perf_declining_penalty_pts   // proposé -10
```

---

### RULE-014 — Zone grise + fatigue croissante  [DÉSACTIVÉE V1]

```
priority:            P3
status:              disabled_v1
reason_disabled:     "zone_distribution requires V2 (CONF-010)"

IF  zone_distribution.Z2_pct >= params.z2_grey_zone_threshold  (proposed 30%)
    AND fatigue_trend == "worsening"
THEN score_delta = -params.grey_zone_penalty_pts  (proposed -5)
```

---

### RULE-015 — Structuration macro-plan

```
priority:            P4
action_type:         plan_hint
short_circuit:       false

IF  weeks_to_race >= params.macro_plan_min_weeks    // default 16
    AND weekly_distance_history sufficient (≥ 4 entries, coefficient de variation < params.cv_max_regular)  // default 0.35
THEN
      plan_hint = "structure_macroplan"
      phases = compute_phase_boundaries(weeks_to_race)
ELSE  no-op

OUTPUT { rule_id, triggered, action: "plan_hint", plan_type: "macro", suggested_phases: {...} }

variables_used:      weeks_to_race, weekly_distance_history
configurable_params: macro_plan_min_weeks (int, default 16)
                     cv_max_regular       (float, default 0.35)
justification:       S1:K1 + S3:Canova, [SCI], signal Fort
tests_expected:
  - weeks_20_regular → triggered
  - weeks_8         → not_triggered
```

---

### RULE-016 — Beginner : cycle préparatoire d'abord

```
priority:            P4
action_type:         plan_hint

IF  computed.experience_level == "beginner"
    AND chronic_load_distance < params.beginner_base_min_km   // default 25
THEN
      plan_hint = "preparatory_cycle_before_marathon_specific"
ELSE  no-op

variables_used:      computed.experience_level, computed.chronic_load_distance
configurable_params: beginner_base_min_km  (float, default 25, range 15..35)
justification:       S1:K3, [SCI]
```

---

### RULE-017 — Sélection plan volume

```
priority:            P4
action_type:         plan_hint

IF  input suffisant pour classifier volume habituel
THEN
      plan_level = pick_from({low, moderate, high}) using experience_level + chronic_load
ELSE  no-op

// Décision produit : mapping exact du triangle experience × chronic_load → plan_level
// À figer avant implémentation — voir § 7 décision restante D-05.
```

---

### RULE-018 — Cycle vitesse/seuil pré-marathon

```
priority:            P4
action_type:         plan_hint

IF  weeks_to_race >= params.speed_cycle_min_weeks_out    // default 12
    AND performances_10k_below_potential(target_marathon_pace, recent_race_time_10k)
THEN
      plan_hint = "speed_threshold_cycle_recommended"
ELSE  no-op

// La fonction performances_10k_below_potential est [PROD] :
// compare recent_race_time_10k vs Riegel-inversé depuis target_marathon_pace
// avec tolérance params.speed_gap_tolerance_pct (default 5%)
```

---

### RULE-019 — Objectifs incohérents

```
priority:            P4
action_type:         plan_hint

IF  race_target_time != null
    AND ABS(riegel_predict(recent_race_time_half, 42.195) - race_target_time) / race_target_time
        > params.target_realism_gap_pct   // default 15%
THEN
      plan_hint = "revise_objectives"
ELSE  no-op
```

---

### RULE-020 — Séances manquées

```
priority:            P4
action_type:         plan_hint

// V1 MVP : détecté via delta_volume_pct fortement négatif ET fatigue_trend != "worsening"
IF  delta_volume_pct != null
    AND delta_volume_pct < -params.missed_sessions_neg_delta_pct   // default -20
    AND fatigue_trend != "worsening"
THEN
      plan_hint = "adjust_next_week_no_catchup"
ELSE  no-op
```

---

### RULE-021 — Détail taper (planification)

```
priority:            P4
action_type:         plan_hint

IF  current_phase == "taper"
THEN
      plan_hint = "taper_structure"
      volume_reduction_pct = mean(params.taper_volume_reduction_min, params.taper_volume_reduction_max)  // default 50
      taper_duration_weeks = params.taper_duration_weeks   // default 3
      keep_intensity = true
```

---

### RULE-022 — Calculer allure marathon cible

```
priority:            P4
action_type:         plan_hint

IF  target_marathon_pace_min_km == null
    AND (recent_race_time_half OR recent_race_time_10k OR VMA_kmh OR race_target_time is not null)
THEN
      trigger the hierarchy in § 2.6 to fill computed.target_marathon_pace_min_km
ELSE  no-op
```

---

### RULE-023 — Pacing jour J

```
priority:            P4
action_type:         plan_hint
context:             race_day

IF  pace_first_half != null
    AND target_marathon_pace_min_km != null
    AND pace_first_half > target_marathon_pace_min_km * (1 + params.blowup_pace_tolerance_pct)  // default 5%
THEN
      plan_hint = "slow_down_now"
      blowup_risk = true
ELSE  no-op

variables_used:      pace_first_half (V2 : intra-race), target_marathon_pace_min_km
configurable_params: blowup_pace_tolerance_pct (float, default 5, range 3..7)
justification:       S1:K13 + S3:Foster, [SCI]
```

---

### RULE-024 — Ajustement thermique  [V2]

```
priority:            P4
action_type:         plan_hint
status:              v2

IF  ambient_temperature_C > params.heat_threshold_C     // default 20
THEN
      target_marathon_pace_adjustment_pct = params.heat_pace_penalty_pct  // default -6 (fourchette -4..-8)
```

---

### RULE-025 — Nutrition course

```
priority:            P4
action_type:         plan_hint

IF  estimated_race_duration_min > params.cho_protocol_min_duration_min   // default 90
THEN
      plan_hint = "cho_protocol_60_90g_per_hour"
      cho_min_g_per_hour = params.cho_min_g_per_hour   // default 60
      cho_max_g_per_hour = params.cho_max_g_per_hour   // default 90
```

---

### RULE-026 — Retour d'interruption [NOUVELLE v1.1]

```
priority:            P1
action_type:         block_increase
short_circuit:       false

IF  days_since_last_run > params.interruption_threshold_days   // default 14
THEN
      decision_cap = "maintain"
      plan_hint_secondary = "return_from_interruption_progressive"
ELSE  no-op

variables_used:      days_since_last_run
configurable_params: interruption_threshold_days (int, default 14, range 7..21)
justification:       Ajout audit v1.1, [PROD], signal Fort
tests_expected:
  - 10_days   → not_triggered
  - 14_days   → not_triggered (strict >)
  - 15_days   → triggered
  - 30_days   → triggered, plan_hint added
```

---

### 3.99. Orchestration — l'ordre officiel du moteur

```
1. Validate(RunnerState) → errors/warnings   (§ 1.8)
   IF errors: refuse execution, return error report.

2. Compute(ComputedVariables) using § 2 formulas.

3. Fire all rules in priority order:
   for priority in [P0, P1, P2, P3, P4]:
       for rule in rules[priority]:
           evaluate(rule) → RuleOutcome

4. Aggregate:
   IF any P0 triggered:
       decision = "deload"
       delta_pct = action_bounds["deload"]["default"]
       all_lower_priority_outcomes = ignored_but_reported
   ELIF any P1 triggered:
       decision = intersection_of_P1_actions:
           IF any P1 forced "decrease": decision = "decrease"
           ELSE:                        decision = "maintain"
       delta_pct = action_bounds[decision]["default"]
       P2 caps = ignored (resolution v1.1 CONF-009, [PROD])
   ELIF any P2 triggered:
       decision = "capped_increase"
       cap_pct = min(all triggered P2 caps)
       delta_pct = min(cap_pct, action_bounds["slight_increase"]["default"])
   ELSE:
       decision = "increase"
       delta_pct = action_bounds["increase"]["default_by_experience_level"]

5. Apply P3 score adjustments (never override decision):
   readiness_score += clamp(sum(P3 deltas), -10, +10)

6. Collect P4 plan hints as suggestions (never affect decision).

7. Compute readiness_confidence_score (§ 2.4).

8. Return DecisionEnvelope (§ 6.2).
```

---

## 4. Séparation stricte — structure de projet

### 4.1. Arborescence proposée

```
/config/
    thresholds.yaml               # [PROD] tous les paramètres numériques (§ 4.2)
    rules_status.yaml             # [PROD] activation/désactivation par règle
    enums.yaml                    # [PROD] listes énumérées (PAIN_REGION_ENUM, PHASE_ENUM, etc.)

/domain/
    concepts.py                   # [SCI] constantes scientifiques immuables (§ 4.3)
    schemas/
        runner_state.py           # RunnerState + sous-schémas (§ 1)
        computed.py               # ComputedVariables (§ 2)
        decision.py               # DecisionEnvelope (§ 6.2)
    formulas/
        acwr.py                   # § 2.2
        readiness.py              # § 2.3, 2.4
        pace.py                   # § 2.6 (hiérarchie target_marathon_pace)
        experience_level.py       # § 5.4

/rules/
    safety_rules.py               # RULE-001, RULE-002, RULE-003
    progression_rules.py          # RULE-004, RULE-005, RULE-006, RULE-007, RULE-008,
                                  # RULE-009, RULE-010, RULE-011, RULE-012, RULE-026
    planning_rules.py             # RULE-015 à RULE-022, RULE-026 plan_hint secondaire
    race_day_rules.py             # RULE-023, RULE-024, RULE-025
    disabled/
        rule_013_perf_declining.py  # spec conservée, non chargée
        rule_014_grey_zone.py

/engine/
    orchestrator.py               # § 3.99
    validator.py                  # § 1.8
    aggregator.py                 # étape 4 (P0/P1/P2/P3/P4)
    envelope_builder.py           # sortie finale

/tests/
    unit/                         # un fichier par règle et par formule
    fixtures/                     # RunnerState échantillons
    property/                     # tests de propriété (invariants)
```

### 4.2. `/config/thresholds.yaml` — inventaire exhaustif

```yaml
# ==== SEUILS ACWR ====
acwr_deload_threshold:        2.0        # RULE-003
acwr_block_threshold:         1.5        # RULE-004
acwr_sweet_spot_min:          0.8        # RULE-011, RULE-012
acwr_sweet_spot_max:          1.3        # RULE-011, RULE-012
acwr_min_history_weeks:       4          # gating de acwr_reliable
chronic_load_window_weeks:    4          # § 2.2
chronic_load_method:          "simple_mean"   # ou "ewma"
ewma_alpha:                   0.13       # si method=ewma
chronic_load_min_km:          5          # § 2.2 (rejet ACWR si base trop faible)

# ==== PROGRESSION ====
weekly_increase_cap_pct:      10         # RULE-005
small_volume_threshold_km:    20         # RULE-005 guard
long_run_max_increase_km:     2          # future rule (voir décision D-08)

# ==== RÉCUPÉRATION ====
fatigue_high_threshold:       4          # RULE-006
fatigue_extreme_threshold:    5          # RULE-006
fatigue_moderate_value:       3          # RULE-009
fatigue_low_threshold:        2          # RULE-011
sleep_low_threshold:          2          # RULE-006 (sens : ≤2 = mauvais)
sleep_moderate_value:         3          # RULE-009
sleep_high_threshold:         4          # RULE-011 (sens : ≥4 = bon)
moderate_fatigue_cap_pct:     5          # RULE-009

# ==== BLESSURE ====
pain_critical_intensity:      4          # RULE-001
pain_critical_days:           2          # RULE-001
pain_tendon_intensity:        3          # RULE-002
pain_tendon_days:             3          # RULE-002
pain_ok_threshold:            2          # RULE-011
recent_injury_cap_weeks:      4          # RULE-008
recent_injury_max_increase_pct: 5        # RULE-008
interruption_threshold_days:  14         # RULE-026

# ==== PROFIL ====
beginner_max_increase_pct:    5          # RULE-010
beginner_base_min_km:         25         # RULE-016

# Critères experience_level (§ 5.4)
experience_level_criteria:
  intermediate:
    min_years_running:        1
    min_chronic_load_km:      30
    min_longest_race_km:      10
  advanced:
    min_years_running:        3
    min_chronic_load_km:      60
    min_longest_race_km:      21.0975    # semi ou plus

# ==== PACE MARATHON ====
riegel_exponent:              1.06
vma_marathon_fraction:
  beginner:                   0.75
  intermediate:               0.80
  advanced:                   0.83
target_realism_gap_pct:       15         # RULE-019
speed_gap_tolerance_pct:      5          # RULE-018
speed_cycle_min_weeks_out:    12         # RULE-018

# ==== TAPER ====
taper_volume_reduction_min:   40         # RULE-007, RULE-021
taper_volume_reduction_max:   60
taper_duration_weeks:         3

# ==== READINESS COMPOSITION ====
readiness_weights:
  recovery:                   35
  load:                       35
  progression:                15
  marathon_prep:              15
readiness_p3_bounds:          10          # ±10

# ==== READINESS CONFIDENCE ====
confidence_penalty:
  acwr_unreliable:            15
  missing_rpe:                10
  missing_long_run:           5
  long_interruption:          20
  per_missing_week:           5
  pace_vma_only:              10
  experience_declared_only:   5
  active_pain:                5
  stale_input:                10
confidence_min_high:          75
confidence_min_medium:        50

# ==== ACTIONS ====
action_bounds:
  deload:
    min: -40
    default: -25
    max: -20
  decrease:
    min: -20
    default: -10
    max: -5
  maintain:
    min: 0
    default: 0
    max: 0
  slight_increase:
    min: 2
    default: 3
    max: 5
  increase:
    min: 5
    default_by_experience_level:
      beginner:               5
      intermediate:           7
      advanced:               10
    max: 10

# ==== RACE DAY ====
blowup_pace_tolerance_pct:    5           # RULE-023
heat_threshold_C:             20          # RULE-024
heat_pace_penalty_pct:        -6          # RULE-024
cho_protocol_min_duration_min: 90         # RULE-025
cho_min_g_per_hour:           60          # RULE-025
cho_max_g_per_hour:           90          # RULE-025

# ==== PLAN ====
macro_plan_min_weeks:         16          # RULE-015
cv_max_regular:               0.35        # RULE-015
missed_sessions_neg_delta_pct: 20         # RULE-020

# ==== GREEN LIGHT / TOLÉRANCE ====
green_light_bonus_pts:        10          # RULE-011
advanced_tolerance_bonus_pts: 5           # RULE-012
```

### 4.3. `/domain/concepts.py` — constantes scientifiques (fait, jamais modifié en config)

```
MARATHON_DISTANCE_KM        = 42.195         # [SCI] fait olympique
HALF_MARATHON_DISTANCE_KM   = 21.0975        # [SCI]
TEN_K_DISTANCE_KM           = 10.0           # [SCI]
FIVE_K_DISTANCE_KM          = 5.0            # [SCI]
MINUTES_PER_HOUR            = 60.0
SECONDS_PER_MINUTE          = 60.0

# Fenêtres physiologiques canoniques (Gabbett terminologie)
ACWR_ACUTE_WINDOW_DAYS      = 7              # [SCI] définition ACWR
ACWR_CHRONIC_WINDOW_DAYS    = 28             # [SCI] définition ACWR

# Formule Riegel (1981)
RIEGEL_DEFAULT_EXPONENT     = 1.06           # [SCI] convention littérature
                                             # (le paramètre config peut le surcharger, mais ce fichier
                                             #  définit la valeur canonique)

# Session-RPE de Foster : nécessite RPE PAR séance × durée PAR séance
# → NOT computable in MVP with weekly aggregation.
FOSTER_SESSION_RPE_REQUIRES_PER_SESSION_RPE = True   # marqueur documentaire
```

### 4.4. Règles d'or de la séparation

1. Aucun `if pain_intensity >= 4:` en dur dans le code. Toujours `if pain_intensity >= config.pain_critical_intensity:`.
2. `concepts.py` ne dépend d'aucune config ; c'est le fondement scientifique.
3. `rules/*.py` importe **uniquement** `concepts` + `schemas` + `config` (aucun accès BDD, aucun IO).
4. Chaque règle est une fonction pure `(RunnerState, ComputedVariables, Config) -> RuleOutcome`.
5. Le fichier de config est chargé une fois au démarrage, hashé, et son hash apparaît dans chaque `DecisionEnvelope` (traçabilité).

---

## 5. Corrections spécifiques ajoutées en v1.2

### 5.1. `readiness_confidence_score` — voir § 2.4

Ajouté. Composition explicite, seuils configurables, contrat d'usage (`refuse > maintain` si confiance basse).

### 5.2. Renommage `weekly_internal_load` → `estimated_internal_load`

Justification : Foster définit session-RPE = **RPE de la séance × durée de la séance**, agrégé sur la semaine. Un `avg_weekly_RPE × duration_min` n'est pas ça — c'est un estimateur agrégé, biaisé par nature.

**Changement de nommage :**
- `weekly_internal_load` → `estimated_internal_load`
- Nouveau champ compagnon : `estimated_internal_load_notice = "aggregated_RPE_estimate"` (constante)
- Toute règle utilisant `estimated_internal_load` doit lire l'annotation.
- Le vrai session-RPE Foster arrivera en V2 avec `session_rpe_per_workout[]`.

### 5.3. `pain_trend` — ajouté dans `PainRegion`

Voir schéma § 1.4.1. Champ `pain_trend ∈ {improving, stable, worsening, unknown}`.

**Utilisation V1 :** enrichit l'explication LLM et le `readiness_confidence_score` (pas encore de règle décisionnelle qui s'en sert — prudence sur signal auto-déclaré subjectif).
**Piste V2 :** RULE-002 peut abaisser ses seuils si `pain_trend == "worsening"` (à valider).

### 5.4. `experience_level` calculé

**Nouveau contrat v1.2 :** le champ `experience_level_declared` est un signal auxiliaire ; `computed.experience_level` est **calculé** par le moteur.

```
Inputs:
  - experience_level_declared             (user)
  - profile.years_running                 (optional new field V2 — see D-04)
  - computed.chronic_load_distance
  - longest_race_km_history               (dérivé de recent_race_time_*)
  - race_target_time                      (optional)

Algorithm (pseudo-code, uses params.experience_level_criteria):

candidate = "beginner"
IF chronic_load_distance >= criteria.intermediate.min_chronic_load_km
   AND (years_running is null OR years_running >= criteria.intermediate.min_years_running)
   AND longest_race_km >= criteria.intermediate.min_longest_race_km:
    candidate = "intermediate"
IF chronic_load_distance >= criteria.advanced.min_chronic_load_km
   AND (years_running is null OR years_running >= criteria.advanced.min_years_running)
   AND longest_race_km >= criteria.advanced.min_longest_race_km:
    candidate = "advanced"

// Reconciliation avec la déclaration
IF experience_level_declared == candidate:
    computed.experience_level = candidate
    computed.experience_level_source = "reconciled"
ELIF declared is "harder" than candidate  (advanced > intermediate > beginner):
    // Ne jamais faire confiance à une déclaration flatteuse non étayée
    computed.experience_level = candidate
    computed.experience_level_source = "calculated"
ELSE:  // declared plus prudent que ce que les critères permettent
    // Respecter la prudence du coureur
    computed.experience_level = experience_level_declared
    computed.experience_level_source = "declared"
```

**Effet de bord** : `readiness_confidence_score` pénalise `experience_level_source == "declared"` uniquement (§ 2.4) — reflète le fait qu'on n'a pas pu croiser.

### 5.5. Hiérarchie `target_marathon_pace_min_km` — voir § 2.6

Ordre : `race_target_time` > semi > 10k > VMA > null. Formalisé avec `target_marathon_pace_source` en sortie. Warning `race_target_unrealistic` si divergence > 20% vs Riegel.

---

## 6. Actions du moteur — catalogue et garde-fous

### 6.1. Catalogue d'actions

| Action | Description | Fourchette autorisée | Défaut V1 | Signal |
|--------|-------------|---------------------|-----------|--------|
| `deload` | Réduction forcée de la charge (blessure, ACWR danger) | −40% à −20% | −25% | Utilisateur reçoit consigne stricte |
| `decrease` | Réduction planifiée (taper, fatigue) | −20% à −5% | −10% | Baisse volontaire |
| `maintain` | Aucun changement de volume | 0% (strict) | 0% | Statu quo |
| `slight_increase` | Progression prudente (cap actif) | +2% à +5% | +3% | Progression sous contrainte |
| `increase` | Progression standard | +5% à +10% | +5%/+7%/+10% par experience_level | Progression libre |

Toutes les bornes sont dans `thresholds.yaml § 4.2` sous `action_bounds`.

### 6.2. `DecisionEnvelope` — sortie finale du moteur

```
DecisionEnvelope {
  meta: {
    engine_version:              "1.2.0"
    config_hash:                 string (sha256)
    computed_at:                 ISO-8601
    schema_version:              "1.2.0"
  }
  decision: {
    action:                      "deload"|"decrease"|"maintain"|"slight_increase"|"increase"
    delta_pct:                   float               // valeur signée (ex: -25.0, +3.0)
    delta_pct_range:             [float, float]      // fourchette autorisée
    absolute_next_week_target_km: float              // = weekly_distance_km * (1 + delta_pct/100)
    // Toujours ≥ 0
  }
  readiness: {
    score:                       int (0..100)
    confidence_score:            int (0..100)         // NOUVEAU v1.2
    components: {...}                                 // recovery/load/progression/marathon_prep/p3
  }
  triggered_rules: [
    RuleOutcome, RuleOutcome, ...    // toutes les règles déclenchées (P0..P4)
  ]
  ignored_rules_due_to_short_circuit: [rule_id, ...]  // pour audit
  warnings: [string]                                   // ex: "medical_referral_recommended"
  plan_hints: [
    { rule_id, hint, params }
  ]
  medical_referral:              bool
  llm_context: {
    // Payload structuré à destination de la couche explication LLM
    // Le LLM n'a AUCUN droit d'écriture sur decision.
    reasons_human_readable:      [string]
    confidence_caveat:           "high"|"medium"|"low"
  }
}
```

### 6.3. Garde-fous absolus (invariants d'implémentation)

**GF-01 — Sécurité toujours prioritaire.** Si `medical_referral == true`, `decision.action` doit être `deload`.
Test : property test — quel que soit l'input avec RULE-001 ou RULE-002 déclenchée, la sortie est `deload`.

**GF-02 — Jamais d'augmentation si P1 est déclenchée.** Si un `RuleOutcome` de priorité P1 est `triggered = true`, `decision.action ∈ {"deload","decrease","maintain"}`.
Test : property test.

**GF-03 — Volume cible jamais négatif.** `absolute_next_week_target_km >= 0`, borné inférieurement par `params.min_absolute_weekly_km` (default 0, ajustable par profil).

**GF-04 — LLM en lecture seule.** La couche explication reçoit `DecisionEnvelope`, n'a aucun droit d'écriture. Toute réponse LLM qui contient une action différente de `decision.action` doit être bloquée par un filtre en sortie.

**GF-05 — Config immuable pendant une exécution.** `config_hash` capturé au début, réutilisé pour le logging. Si config change en cours d'exécution → erreur `"config_mutation_during_execution"`.

**GF-06 — Confidence < seuil médium → cap `maintain`.** Si `readiness_confidence_score < params.confidence_min_medium`, `decision.action ∈ {"deload","decrease","maintain"}` (même en l'absence de P0/P1).

**GF-07 — Taper toujours en `decrease`.** Si `current_phase == "taper"` et pas de P0 déclenchée, `decision.action == "decrease"` (RULE-007 force). Interdit `maintain` ou augmentation en taper.

**GF-08 — Deload minimum.** `decision.action == "deload"` ⇒ `delta_pct ≤ params.action_bounds.deload.max` (default −20%). Un deload à −5% n'est pas un deload.

**GF-09 — Une seule action finale.** Le moteur n'émet qu'**un** `decision.action`. Les autres règles sont reportées mais non exécutoires.

**GF-10 — Version du contrat.** Toute modification de `DecisionEnvelope` ou `RunnerState` incrémente `schema_version`.

---

## 7. Décisions produit à trancher **avant** codage

Les items ci-dessous **doivent** être arbitrés par le PO/tech lead avant d'écrire la première ligne de code du moteur. Chaque item propose une valeur par défaut audit — à valider explicitement ou modifier.

| ID | Décision | Recommandation audit | Impact si non tranché |
|----|----------|----------------------|-----------------------|
| **D-01** | Méthode `chronic_load` : `"simple_mean"` vs `"ewma"` | `"simple_mean"` V1, `"ewma"` V1.5 | ACWR erratique sur semaines atypiques |
| **D-02** | Fenêtre chronique : 4 vs 6 vs 8 semaines | **4 semaines V1** (min viable) | Signal plus lissé ou plus réactif |
| **D-03** | Critères `experience_level` (§ 5.4) : valider les seuils `intermediate` et `advanced` proposés | Seuils par défaut config § 4.2 | `experience_level_source = "declared"` pour tout le monde → confiance pénalisée systématique |
| **D-04** | Ajouter `profile.years_running` (input MVP) ? | **Oui, optionnel** — améliore le calcul experience_level | Sinon `years_running` toujours null → algo dégradé |
| **D-05** | RULE-017 : mapping `experience × chronic_load → plan_level` | Nécessite une table 3×3 explicite à figer | RULE-017 non exécutable |
| **D-06** | Comportement `current_phase == "off_season"` | `maintain volume bas + cross-training recommandé` | Décision indéterminée en off_season |
| **D-07** | Seuil `recent_injury_cap_weeks = 4` : conserver ou décomposer par sévérité de blessure ? | Conserver V1, prévoir schéma sévérité V2 | Traitement identique pour entorse et fracture |
| **D-08** | Progression sortie longue : `long_run_max_increase_km = 2` : règle dure ou hint ? | **Hint P4** en V1 (pas une règle bloquante) | Sortie longue non protégée |
| **D-09** | Adopter TQR / Hooper (validé) ou conserver `fatigue_score` 1–5 maison ? | **Conserver 1–5 maison V1** — plus simple, à mesurer plus tard | Signal moins validé, mais UX simple |
| **D-10** | Ajouter une règle directe `weeks_to_race < 3 → force taper` ? | **Non** — laisser `current_phase` être la source de vérité | Sinon double source d'autorité |
| **D-11** | Bornes exactes des actions (§ 6.1) : valider les défauts | Défauts audit `-25/-10/0/+3/+7 (par profil pour increase)` | Actions non chiffrables → décision qualitative seule |
| **D-12** | Formule Riegel exposant : `1.06` (littérature) vs `1.15` (Peter Riegel original) ? | **1.06 V1** (plus conservateur pour longs formats) | Prédiction marathon biaisée |
| **D-13** | Mapping `pain_regions[].region == "other"` : autoriser RULE-001 ? RULE-002 ? | RULE-001 oui, RULE-002 non ("other" pas dans CRITICAL_PAIN_REGIONS) | Douleur diffuse mal capturée |
| **D-14** | `stale_input` (délai submission vs week_start) : seuil 10 jours OK ? | **10 jours** V1 | Feedback tardif pris comme frais |
| **D-15** | Persistance de `fatigue_score_history` inter-semaine (nécessaire pour `fatigue_trend`) : où stocker ? Hors moteur ? | **Hors moteur** — le moteur reste stateless, le caller passe l'historique | Sinon architecture couplée BDD |
| **D-16** | RULE-013 et RULE-014 : rester désactivées V1 ou fournir formule V2 dès maintenant ? | **Rester désactivées** en V1, ne pas préparer V2 tant que `performance_trend` et `zone_distribution` ne sont pas définis | Confusion sur la roadmap |
| **D-17** | `pain_trend` (nouveau v1.2) : purement informatif V1, ou pénalise `readiness_confidence_score` si "worsening" ? | **Informatif V1**, effet sur confidence en V1.5 | Signal collecté mais inutilisé |
| **D-18** | Mapping K15 (v1.1 CONF-012) : `pathologies_connues` ou supprimer référence ? | **Mapper à `pathologies_connues`** | Nœud K15 orphelin dans le graphe |
| **D-19** | `mood_motivation_score` : effet sur UI LLM uniquement, ou pénalise `readiness_score` en V1 ? | **UI LLM uniquement V1** | Signal non exploité mais consistant |
| **D-20** | `absolute_next_week_target_km` : arrondir à quelle précision (0.5 km ? 1 km ?) | **0.5 km** V1 | UX incohérente |

---

## 8. Récapitulatif — ce qui est prêt à coder maintenant

**Complet et exécutable sans arbitrage humain supplémentaire :**
- Section 1 : `RunnerState` (validation, enums, defaults, requis MVP)
- Section 2 : `ComputedVariables` (toutes formules)
- Section 3 : toutes les règles P0 (001/002/003), P1 (004/005/006/007/026), P2 (008/009/010), P3 (011/012)
- Section 4 : arborescence + `thresholds.yaml`
- Section 6 : `DecisionEnvelope` + garde-fous GF-01 à GF-10

**Exécutable avec seuils par défaut audit (à confirmer avant release) :**
- RULE-017 dépend de D-05
- Comportement `off_season` dépend de D-06
- Valeurs `experience_level_criteria` dépendent de D-03

**Reste V2 (ne pas coder V1) :**
- RULE-013, RULE-014 (variables absentes)
- RULE-024 (température ambiante)
- Session-RPE Foster par séance
- `zone_distribution`
- HRV / CTL / ATL / TSB

**Décisions produit ouvertes (Section 7) : 20 items — à trancher en une session avant kickoff.**

---

## Annexe A — Matrice règle × variable

Pour audit rapide : quelles règles utilisent quelles variables.

| Variable | RULES qui l'utilisent |
|----------|----------------------|
| `pain_regions[].intensity` | RULE-001, RULE-002, RULE-011 |
| `pain_regions[].days_persistent` | RULE-001, RULE-002 |
| `pain_regions[].region` | RULE-002 |
| `pain_regions[].pain_trend` | Aucune V1 (informatif LLM + confidence si D-17 tranche "oui") |
| `computed.acwr_distance` | RULE-003, RULE-004, RULE-011, RULE-012 |
| `computed.acwr_reliable` | RULE-003, RULE-004 (guards) |
| `computed.delta_volume_pct` | RULE-005 |
| `computed.delta_volume_reliable` | RULE-005 (guard) |
| `fatigue_score` | RULE-006, RULE-009, RULE-011 |
| `sleep_quality_score` | RULE-006, RULE-009, RULE-011 |
| `current_phase` | RULE-007, RULE-021 |
| `weeks_since_last_injury` | RULE-008 |
| `computed.experience_level` | RULE-010, RULE-012, RULE-016, RULE-017 |
| `weeks_to_race` | RULE-015, RULE-018 |
| `days_since_last_run` | RULE-026 |
| `computed.target_marathon_pace_min_km` | RULE-018, RULE-022, RULE-023 |
| `race_target_time` | RULE-019, § 2.6 hiérarchie |
| `computed.chronic_load_distance` | RULE-016, RULE-017 |

---

## Annexe B — Statut par règle (résumé exécutif)

| Règle | Priorité | Statut V1.2 | Bloque codage ? |
|-------|----------|-------------|-----------------|
| RULE-001 | P0 | ✅ prête | Non |
| RULE-002 | P0 | ✅ prête | Non |
| RULE-003 | P0 | ✅ prête | Non |
| RULE-004 | P1 | ✅ prête | Non |
| RULE-005 | P1 | ✅ prête | Non |
| RULE-006 | P1 | ✅ prête | Non |
| RULE-007 | P1 | ✅ prête (corrigée v1.1 : force_decrease) | Non |
| RULE-008 | P2 | ✅ prête | Non |
| RULE-009 | P2 | ✅ prête | Non |
| RULE-010 | P2 | ✅ prête (dépend § 5.4) | Non |
| RULE-011 | P3 | ✅ prête | Non |
| RULE-012 | P3 | ✅ prête | Non |
| RULE-013 | P3 | ⛔ désactivée V1 | Non (out-of-scope) |
| RULE-014 | P3 | ⛔ désactivée V1 | Non |
| RULE-015 | P4 | ✅ prête | Non |
| RULE-016 | P4 | ✅ prête | Non |
| RULE-017 | P4 | ⚠️ dépend D-05 | Oui (table à figer) |
| RULE-018 | P4 | ✅ prête (dépend D-12) | Non (défaut Riegel 1.06) |
| RULE-019 | P4 | ✅ prête | Non |
| RULE-020 | P4 | ✅ prête | Non |
| RULE-021 | P4 | ✅ prête | Non |
| RULE-022 | P4 | ✅ prête (§ 2.6 hiérarchie) | Non |
| RULE-023 | P4 | ✅ prête (V2 pour données intra-race) | Non |
| RULE-024 | P4 | ⛔ V2 (température) | Non |
| RULE-025 | P4 | ✅ prête | Non |
| RULE-026 | P1 | ✅ prête (nouvelle v1.1) | Non |

**Verdict** : le codage du moteur peut démarrer sur toutes les règles ✅. Seul **D-05** (mapping RULE-017) bloque strictement une règle. Les 19 autres décisions produit peuvent être tranchées en parallèle du codage — leurs valeurs par défaut audit sont utilisables comme baseline.
