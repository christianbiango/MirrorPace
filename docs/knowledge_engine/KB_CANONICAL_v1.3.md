# Knowledge Base Canonique — Coach Marathon IA — v1.3

> Version : 1.3 — patch de robustesse post Red Team
> Version parente : v1.2 (docs/knowledge_engine/KB_CANONICAL_v1.2.md)
> Statut : contrat d'implémentation — delta uniquement vs v1.2
> Scope : corrections des failles identifiées dans RED_TEAM_REPORT_V1.md
> Contrainte : aucune nouvelle fonctionnalité produit, aucune nouvelle règle sans justification Red Team

**Lecture :** ce document ne se substitue pas à v1.2. Il la complète.
Lire d'abord v1.2 en intégralité, puis appliquer les modifications listées ici.

---

## 1. Changements appliqués

| ID | Problème Red Team | Section v1.2 | Modification appliquée | Impact sur le moteur |
|----|-------------------|-------------|----------------------|---------------------|
| **C-01** | RULE-011 sans guard `acwr_reliable` — feux vert sur ACWR=1.0 fictif (R-01, A-13) | §3 RULE-011 | Ajout `computed.acwr_reliable == true` dans la condition | Élimine le +10 pts score sur données inexistantes |
| **C-02** | GF-06 calculé après l'agrégation — invariant possiblement jamais appliqué (R-02, Conf-06) | §3.99 + §2.4 | Déplacement de `readiness_confidence_score` à l'étape 2 (ComputedVariables) | GF-06 opérationnel dans l'agrégation à l'étape 4 |
| **C-03** | `pathologies_connues` → warning textuel ≠ `medical_referral=true` (R-03, A-03) | §6.2 + §1.8 | `medical_referral=true` dans DecisionEnvelope si pathologies_connues non vide | Cohérence sémantique du champ boolean — sans changer decision.action |
| **C-04** | `fatigue_score_history` absent du schéma RunnerState (R-04) | §1.4 | Nouveau champ optionnel `fatigue_score_history` dans WeekInput | `fatigue_trend` calculable — sort de "unknown" permanent |
| **C-05** | GF-07 libellé sans condition explicite "pas de P0" (Conf-03) | §6.3 GF-07 | Reformulation avec condition explicite | Clarté d'implémentation, évite conflit GF-01/GF-07 |
| **C-06** | Validation vitesse implicite absurde — 200 km en 2h accepté (A-12, §4.3) | §1.8 | Validation croisée distance/durée — erreur si vitesse > 50 km/h | Filtre les données physiologiquement impossibles |
| **C-07** | RULE-020 satisfaite quand `fatigue_trend="unknown"` (Conf-05, R-06) | §3 RULE-020 | Condition `fatigue_trend ∈ {"improving","stable"}` au lieu de `!= "worsening"` | Évite hint incorrect sur état de fatigue inconnu |
| **C-08** | `current_phase="return_from_injury"` + `weeks_since_last_injury=null` sans alerte (Conf-08, A-19) | §1.8 | Warning "missing_injury_context" | Incohérence visible dans DecisionEnvelope.warnings |
| **C-09** | `action=maintain` sur `weekly_distance_km=0` → cible 0 km recommandée (A-11) | §6.1 + §4.2 | Nouveau paramètre `min_absolute_weekly_km_on_maintain` (défaut 5) | Plancher configurable sur la cible absolue en maintain |
| **C-10** | `tests_expected` de RULE-011 ne couvre pas `acwr_reliable=false` (M-07) | §3 RULE-011 | Ajout cas dans tests_expected | Couverture de test exhaustive |
| **C-11** | `race_target_date` dans le passé — weeks_to_race négatif non géré (A-17) | §1.8 | Warning "race_target_date_in_past" + weeks_to_race forcé à null | Comportement déterminé pour RULE-015/016/018 |

---

## 2. Modifications de règles

### RULE-011 — Feu vert multi-critères [MODIFIÉE]

**Ancienne logique (v1.2) :**
```
IF  computed.acwr_distance != null
    AND params.acwr_sweet_spot_min <= computed.acwr_distance <= params.acwr_sweet_spot_max
    AND fatigue_score <= params.fatigue_low_threshold
    AND sleep_quality_score >= params.sleep_high_threshold
    AND max([r.intensity for r in pain_regions], default=0) <= params.pain_ok_threshold
THEN score_delta = +params.green_light_bonus_pts
```

**Nouvelle logique (v1.3) :**
```
IF  computed.acwr_reliable == true                          // NOUVEAU — guard identique à RULE-003/004
    AND computed.acwr_distance != null
    AND params.acwr_sweet_spot_min <= computed.acwr_distance <= params.acwr_sweet_spot_max
    AND fatigue_score <= params.fatigue_low_threshold
    AND sleep_quality_score >= params.sleep_high_threshold
    AND max([r.intensity for r in pain_regions], default=0) <= params.pain_ok_threshold
THEN score_delta = +params.green_light_bonus_pts
```

**Raison :** Sans ce guard, `history=[]` → `chronic_load=current_week` → `acwr_distance=1.0` (fallback) ∈ [0.8, 1.3] → RULE-011 donnait +10 pts score basés sur une donnée fictive. RULE-003 et RULE-004 ont le même guard depuis v1.2 — RULE-011 était la seule exception (bug de spec).

**`tests_expected` mis à jour :**
```
- all_green_reliable        → acwr_reliable=true, acwr=1.0, fat=1, sleep=5, no pain → triggered
- all_green_unreliable      → acwr_reliable=false, acwr=1.0 (fallback) → not_triggered  // NOUVEAU
- acwr_unreliable_history_empty → history=[], fat=1, sleep=5               → not_triggered  // NOUVEAU
- one_pain_3                → pain=3                                        → not_triggered
- acwr_1_5_exact            → acwr=1.5, reliable=true                      → not_triggered (hors sweet spot)
```

---

### RULE-020 — Séances manquées [MODIFIÉE]

**Ancienne logique (v1.2) :**
```
IF  delta_volume_pct != null
    AND delta_volume_pct < -params.missed_sessions_neg_delta_pct
    AND fatigue_trend != "worsening"
THEN plan_hint = "adjust_next_week_no_catchup"
```

**Nouvelle logique (v1.3) :**
```
IF  delta_volume_pct != null
    AND delta_volume_pct < -params.missed_sessions_neg_delta_pct
    AND fatigue_trend in {"improving", "stable"}             // MODIFIÉ — exclut "unknown"
THEN plan_hint = "adjust_next_week_no_catchup"
```

**Raison :** `fatigue_trend = "unknown"` satisfaisait l'ancienne condition (`!= "worsening"`), ce qui déclenchait le hint "pas de rattrapage" même lorsque l'état de fatigue était inconnu. Un coureur épuisé mais sans historique recevait le message "ne rattrape pas les séances" — interprétation d'un manque de données comme absence de fatigue. La nouvelle condition exige une information positive et fiable sur l'état de fatigue.

---

## 3. Modifications des garde-fous

### GF-06 — Confidence < seuil médium → cap maintain [ORCHESTRATION MODIFIÉE]

**Problème détecté :** §3.99 calculait `readiness_confidence_score` à l'étape 7, après l'agrégation (étape 4). GF-06 ne pouvait donc pas s'appliquer pendant l'agrégation — il devait être un post-processing non documenté. Risque fort d'omission à l'implémentation.

**Nouveau comportement attendu :**
- `readiness_confidence_score` est calculé à l'étape 2 (avec les autres ComputedVariables) — voir §3.99 v1.3
- À l'étape 4, l'agrégateur dispose de la confidence pour appliquer GF-06 directement
- L'étape 7 de v1.2 est supprimée — la confidence est déjà dans `computed`

**Test associé :**
```python
# property test
def test_gf06_cap_maintain(state, computed, config):
    envelope = run_engine(state, computed, config)
    if computed.readiness_confidence_score < config.confidence_min_medium:
        assert envelope.decision.action in {"deload", "decrease", "maintain"}
```

---

### GF-07 — Taper toujours en decrease [LIBELLÉ MODIFIÉ]

**Problème détecté :** Le libellé "taper → always decrease" était absolu. Un implémenteur qui applique GF-07 avant P0 pourrait forcer "decrease" là où "deload" est correct, créant un conflit avec GF-01.

**Ancien libellé (v1.2) :**
> Si `current_phase == "taper"`, `decision.action == "decrease"`. Interdit `maintain` ou augmentation en taper.

**Nouveau libellé (v1.3) :**
> Si `current_phase == "taper"` **ET aucune règle P0 n'est déclenchée**, `decision.action == "decrease"`. Si une règle P0 est déclenchée, GF-01 prend le dessus : `decision.action == "deload"`. Il est impossible d'avoir `increase` ou `maintain` en taper sans P0.

**Test associé :**
```python
# property test — deux branches
def test_gf07_taper(state, computed, config):
    envelope = run_engine(state, computed, config)
    if state.context.current_phase == "taper":
        p0_triggered = any(r.priority == "P0" and r.triggered for r in envelope.triggered_rules)
        if p0_triggered:
            assert envelope.decision.action == "deload"
        else:
            assert envelope.decision.action == "decrease"
```

---

## 4. Modifications du schéma RunnerState / ComputedVariables

### 4.1. Nouveau champ — `WeekInput.fatigue_score_history`

| Champ | Type | Unité | Requis MVP | Défaut | Validation | Notes |
|-------|------|-------|-----------|--------|-----------|-------|
| `fatigue_score_history` | array[int] | — | ⭕ optionnel | `[]` | Longueur 0..8 ; chaque val ∈ {1,2,3,4,5} | Ordre : plus récent → plus ancien. Nécessaire pour `fatigue_trend` (§2.5). Fourni par le caller (moteur stateless — décision D-15). |

**Justification :** La formule `fatigue_trend` (§2.5 v1.2) nécessite un historique des fatigue_scores. Ce champ existait dans la logique mais était absent du schéma RunnerState, rendant `fatigue_trend` systématiquement "unknown" pour tout caller implémentant le schéma §1.

**Impact sur `fatigue_trend` (§2.5) :** la formule est inchangée — elle utilise maintenant `fatigue_score_history` comme champ explicite du schéma au lieu d'un champ implicite passé hors-contrat.

---

### 4.2. Nouveau paramètre — `min_absolute_weekly_km_on_maintain`

À ajouter dans `thresholds.yaml` (§4.2 v1.2) :

```yaml
# ==== ACTIONS (complément) ====
min_absolute_weekly_km_on_maintain:  5     # C-09 — plancher sur la cible absolue en maintain
                                           # Si weekly_distance_km < 5 et action=maintain,
                                           # absolute_next_week_target_km = max(weekly * 1.0, 5)
                                           # Évite de recommander 0 km en reprise
```

**Règle d'application (dans `envelope_builder.py`) :**
```
IF decision.action == "maintain":
    absolute_next_week_target_km = max(
        weekly_distance_km * (1 + delta_pct / 100),
        params.min_absolute_weekly_km_on_maintain
    )
ELSE:
    absolute_next_week_target_km = max(
        weekly_distance_km * (1 + delta_pct / 100),
        0
    )
```

---

### 4.3. Nouvelles validations §1.8

**Niveau `ERROR` (refus d'exécution) — ajouté en v1.3 :**

- **Vitesse implicite incohérente :** `weekly_duration_min > 0 AND (weekly_distance_km / (weekly_duration_min / 60)) > 50.0` → erreur `"invalid_speed_ratio"` (50 km/h est impossible en course à pied).

**Niveau `WARNING` — ajouté en v1.3 :**

- **Retour blessure sans contexte :** `current_phase == "return_from_injury" AND weeks_since_last_injury == null` → warning `"missing_injury_context"`. RULE-008 ne peut pas se déclencher dans ce cas ; le coureur est non protégé.
- **Objectif passé :** `race_target_date != null AND race_target_date < week_start_date` → warning `"race_target_date_in_past"`. `weeks_to_race` est forcé à `null` pour cette exécution. RULE-015, RULE-018 seront inactives.

---

### 4.4. Modification de `medical_referral` dans DecisionEnvelope

**Ancienne règle (v1.2) :** `medical_referral = true` uniquement si RULE-001 ou RULE-002 déclenchée.

**Nouvelle règle (v1.3) :** `medical_referral = true` si :
- RULE-001 déclenchée, **OU**
- RULE-002 déclenchée, **OU**
- `pathologies_connues` non vide (depuis le validator §1.8)

**Comportement important :** `medical_referral = true` issu de `pathologies_connues` **ne modifie pas** `decision.action`. Il indique au LLM et à l'UI qu'une supervision médicale est recommandée, sans passer en `deload` forcé (aucun P0 actif). Seules RULE-001/002 déclenchent `deload` via GF-01.

**Distinction explicite dans DecisionEnvelope :**
```
medical_referral:         bool          // true si RULE-001/002 OU pathologies_connues non vide
medical_referral_reason:  enum          // "pain_critical" | "pain_tendon" | "known_pathology" | null
```

**Implémentation :** `envelope_builder.py` consulte `validator_output.pathologies_flagged` et les `triggered_rules`.

---

### 4.5. Modification de l'orchestration §3.99 — ordre des étapes

**Ancienne version (v1.2) :**
```
1. Validate(RunnerState)
2. Compute(ComputedVariables)   // sans confidence
3. Fire all rules
4. Aggregate
5. Apply P3
6. Collect P4
7. Compute readiness_confidence_score   // ← ici en v1.2
8. Return DecisionEnvelope
```

**Nouvelle version (v1.3) :**
```
1. Validate(RunnerState) → errors/warnings
   IF errors: refuse execution.

2. Compute(ComputedVariables) using §2 formulas,
   INCLUDING readiness_confidence_score (§2.4)    // ← déplacé ici
   // La confidence est maintenant disponible à l'étape 4

3. Fire all rules in priority order [P0..P4]

4. Aggregate:
   IF any P0 triggered:          decision = "deload", short_circuit
   ELIF any P1 triggered:        decision = intersection P1
   ELIF any P2 triggered:        decision = "capped_increase"
   ELSE:                         decision = "increase"
   // Application de GF-06 ici, confidence déjà disponible :
   IF computed.readiness_confidence_score < params.confidence_min_medium:
       decision = min_restrictive(decision, "maintain")
       // "min_restrictive" : si decision était "increase"/"slight_increase" → "maintain"
       //                     si "decrease" ou "deload" → inchangé

5. Apply P3 score adjustments

6. Collect P4 plan hints

7. Build DecisionEnvelope (medical_referral, warnings, llm_context)

8. Return DecisionEnvelope
```

**Note :** `min_restrictive(a, b)` retourne l'action la plus restrictive dans l'ordre : `deload > decrease > maintain > slight_increase > increase`. GF-06 ne peut que réduire la décision, jamais l'augmenter.

---

## 5. Modifications des décisions produit D-01 à D-20

### Décisions affectées par v1.3

| ID | Statut v1.2 | Statut v1.3 | Changement |
|----|-------------|-------------|-----------|
| D-15 | ✅ tranché (historique passé par caller, stateless) | ✅ **renforcé** | `fatigue_score_history` est maintenant un champ explicite du schéma §1 — le contrat entre le caller et le moteur est formalisé |
| D-17 | ✅ tranché (pain_trend informatif V1) | ✅ **maintenu** | Décision conservée. Mais documenté comme risque médical accepté V1 — pain_trend="worsening" ne déclenche aucune règle |

### Décisions inchangées

D-01, D-02, D-03, D-04, D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-12, D-13, D-14, D-16, D-18, D-19, D-20 : **statut inchangé vs v1.2**. Se référer au tableau §7 de KB_CANONICAL_v1.2.md.

### Nouvelle décision produit

| ID | Décision | Valeur choisie |
|----|----------|---------------|
| **D-21** | Plancher sur `absolute_next_week_target_km` en `action=maintain` quand `weekly_distance_km` est très bas (< 5 km) | `min_absolute_weekly_km_on_maintain = 5 km` (configurable dans thresholds.yaml) |

---

## 6. Nouveaux profils adversariaux

Ces 4 profils couvrent les failles corrigées par v1.3 et servent de tests de régression permanents. Ils s'ajoutent aux 15 profils de l'Implementation Blueprint V1.

---

### P-16 — Faux feu vert RULE-011 sur ACWR fictif [couvre C-01]

**Objectif :** RULE-011 NE DOIT PAS se déclencher quand l'ACWR est un fallback fictif (acwr_reliable=false).

**Scénario :** Coureur sans historique (première semaine), tous les signaux subjectifs verts. L'ACWR calculé est 1.0 (fallback chronic=current_week). En v1.2, RULE-011 aurait donné +10 pts score. En v1.3, elle ne doit pas se déclencher.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 30,
    "previous_week_distance_km": 28,
    "weekly_distance_history": [],
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 0
  }
}
```

**Variables calculées :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 30.0 km (fallback) |
| `acwr_distance` | 1.0 (fallback) |
| `acwr_reliable` | false (history vide) |

**Règles :**

| Règle | Déclenchée | Raison |
|-------|-----------|--------|
| RULE-011 | ✗ | `acwr_reliable=false` — guard v1.3 |
| RULE-010 | Selon experience_level | — |

**Décision attendue :** Selon règles actives. RULE-011 ne contribue pas au score.

**Assertion critique :** `RULE-011.triggered == false` malgré `acwr_distance=1.0 ∈ [0.8, 1.3]`.

**Régression v1.2 → v1.3 :** En v1.2, RULE-011 aurait tiré → score +10 pts → potentiellement `slight_increase` ou `increase` au lieu de `maintain` (GF-06 confidence < 50).

---

### P-17 — Pathologie connue + aucune douleur [couvre C-03]

**Objectif :** `pathologies_connues` non vide doit positionner `medical_referral=true` dans DecisionEnvelope même sans douleur déclarée.

**Scénario :** Coureur avec pathologie cardiaque connue, tous les signaux normaux, aucune douleur. En v1.2, `medical_referral=false`. En v1.3, `medical_referral=true` avec raison "known_pathology".

**Input RunnerState (extrait) :**
```json
{
  "profile": {
    "pathologies_connues": ["arythmie_cardiaque_bénigne"],
    "experience_level_declared": "intermediate"
  },
  "week": {
    "weekly_distance_km": 45,
    "previous_week_distance_km": 42,
    "weekly_distance_history": [42, 40, 38, 36],
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 0
  }
}
```

**Décision attendue :** `increase` (aucun P0/P1/P2 actif)

**Sortie attendue dans DecisionEnvelope :**
```json
{
  "decision": { "action": "increase", "delta_pct": 7.0 },
  "medical_referral": true,
  "medical_referral_reason": "known_pathology",
  "warnings": ["medical_referral_recommended"]
}
```

**Assertion critique :** `medical_referral=true` ET `action="increase"` peuvent coexister. Le champ `medical_referral` est informatif, pas décisionnel, sauf quand combiné avec GF-01 (P0).

---

### P-18 — Maintain sur semaine à volume nul [couvre C-09]

**Objectif :** `action=maintain` sur `weekly_distance_km=0` ne doit pas recommander 0 km la semaine suivante.

**Scénario :** Coureur avec semaine blanche (maladie, weekly=0), fatigue=5. RULE-006 P1 → maintain. En v1.2, cible absolue = 0 km. En v1.3, cible = max(0, min_absolute_weekly_km_on_maintain) = 5 km.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 0,
    "previous_week_distance_km": 40,
    "weekly_distance_history": [40, 38, 36, 34],
    "fatigue_score": 5,
    "sleep_quality_score": 2,
    "pain_regions": [],
    "days_since_last_run": 3
  }
}
```

**Variables calculées :**

| Variable | Valeur |
|----------|--------|
| `chronic_load_distance` | 37.0 km |
| `acwr_distance` | 0.0 |
| `delta_volume_pct` | -100% |
| `delta_volume_reliable` | true (prev=40 ≥ 20) |

**Règles :**

| Règle | Déclenchée | Raison |
|-------|-----------|--------|
| RULE-006 | ✓ | fatigue=5 ≥ 5 → P1 |

**Décision attendue :**
```json
{
  "decision": {
    "action": "maintain",
    "delta_pct": 0.0,
    "absolute_next_week_target_km": 5.0   // min_absolute_weekly_km_on_maintain
  }
}
```

**Assertion critique :** `absolute_next_week_target_km == params.min_absolute_weekly_km_on_maintain` (5 km par défaut) et non 0 km.

---

### P-19 — Retour de blessure sans contexte [couvre C-08]

**Objectif :** `current_phase="return_from_injury"` sans `weeks_since_last_injury` doit générer un warning visible.

**Scénario :** Coureur qui reprend après une blessure mais n'a pas renseigné `weeks_since_last_injury`. RULE-008 est aveugle. Le warning signale ce trou.

**Input RunnerState (extrait) :**
```json
{
  "week": {
    "weekly_distance_km": 20,
    "previous_week_distance_km": 18,
    "weekly_distance_history": [18, 15, 0, 0],
    "fatigue_score": 2,
    "sleep_quality_score": 4,
    "pain_regions": [],
    "days_since_last_run": 0
  },
  "context": {
    "current_phase": "return_from_injury",
    "weeks_since_last_injury": null
  }
}
```

**Décision attendue :** Selon autres règles (ici possiblement `increase` ou `maintain`)

**Sortie attendue :**
```json
{
  "warnings": ["missing_injury_context"],
  "triggered_rules": []   // RULE-008 non déclenchée (weeks_since_last_injury=null)
}
```

**Assertion critique :** `"missing_injury_context" ∈ warnings` ET `RULE-008.triggered == false`.

---

## 7. Impact sur l'implémentation

### 7.1. Fichiers à modifier

| Fichier | Modification | Correction |
|---------|-------------|-----------|
| `domain/schemas/runner_state.py` | Ajout `fatigue_score_history: list[int] = []` dans WeekInput | C-04 |
| `domain/schemas/computed.py` | `readiness_confidence_score` devient un champ de ComputedVariables | C-02 |
| `domain/schemas/decision.py` | Ajout `medical_referral_reason: str \| None` dans DecisionEnvelope | C-03 |
| `domain/formulas/readiness.py` | Déplacer le calcul de `readiness_confidence_score` depuis orchestrator | C-02 |
| `engine/validator.py` | Ajout 3 nouvelles règles de validation §4.3 | C-06, C-08, C-11 |
| `engine/orchestrator.py` | Supprimer l'étape 7 (confidence), appliquer GF-06 à l'étape 4 | C-02 |
| `engine/aggregator.py` | Intégrer GF-06 dans l'agrégation avec `min_restrictive()` | C-02 |
| `engine/envelope_builder.py` | Logique `medical_referral_reason`, plancher `min_absolute_weekly_km_on_maintain` | C-03, C-09 |
| `rules/progression_rules.py` | RULE-011 + guard acwr_reliable, RULE-020 + condition fatigue_trend | C-01, C-07 |
| `config/thresholds.yaml` | Ajout `min_absolute_weekly_km_on_maintain: 5` | C-09 |

### 7.2. Ordre d'implémentation modifié

L'ordre B.1 de l'Implementation Blueprint V1 reste valide avec un ajustement :

- **Étape 6** (`readiness.py`) : inclure désormais le calcul de `readiness_confidence_score` (déplacé de l'étape 14)
- **Étape 9** (`validator.py`) : ajouter les 3 nouvelles règles de validation
- **Étape 14** (`orchestrator.py`) : supprimer l'ancien step 7 de calcul confidence

### 7.3. Tests à créer ou mettre à jour

| Test | Type | Action |
|------|------|--------|
| T-20 (Blueprint) | Unitaire | **Mettre à jour** : RULE-011 avec acwr_reliable=false → not_triggered |
| T-24 (Blueprint) | Intégration | **Vérifier** : GF-06 toujours valide avec la confidence à l'étape 2 |
| P-16 | Fixture adversariale | **Créer** |
| P-17 | Fixture adversariale | **Créer** |
| P-18 | Fixture adversariale | **Créer** |
| P-19 | Fixture adversariale | **Créer** |
| `test_gf06_confidence_before_aggregation` | Property | **Créer** — vérifie que GF-06 s'applique à l'étape 4 |
| `test_gf07_with_p0` | Property | **Créer** — taper + P0 → deload (pas decrease) |
| `test_medical_referral_from_pathologies` | Intégration | **Créer** |
| `test_maintain_on_zero_volume` | Unitaire | **Créer** |

### 7.4. Risques restants acceptés en V1 (non corrigés)

Ces risques sont documentés comme acceptés — ils ne bloquent pas l'implémentation V1.

| Risque | Raison de l'acceptation |
|--------|------------------------|
| A-06 — douleur dans `session_notes` mais `pain_regions=[]` | Require NLP/LLM pour parser. Hors scope moteur de règles. Documenté dans llm_context |
| A-14 — age=14, mêmes règles qu'adulte | Règles physiologiques spécifiques à l'âge = V2. Alerte médicale si age < 18 possible en V1.5 |
| A-20 — pain_trend="worsening" ignoré | Décision D-17 maintenue. Signal collecté, confiance pénalisée, règle décisionnelle V2 |
| R-07 — sessions_per_week_available non utilisé | Utilisation dans le calcul du delta suggéré = V2. Champ collecté pour la rétrocompatibilité |
| A-09 — sensibilité flottant seuil ACWR=1.5 | Acceptable. Seuils configurables dans thresholds.yaml. Utiliser comparaison à epsilon en implémentation |

---

## 8. Verdict V1.3

### La spec est-elle maintenant suffisamment stable pour coder ?

**Oui.**

Les deux blocages architecturaux identifiés dans le Red Team ont été résolus :

1. **C-01** (RULE-011 guard acwr_reliable) — corrigé dans §3
2. **C-02** (confidence avant l'agrégation) — corrigé dans §3.99

Les 9 autres corrections sont des améliorations de robustesse qui peuvent être implémentées en parallèle du développement sans modifier l'architecture.

### Points restants bloquants

**Aucun bloquant architectural.**

D-05 (table RULE-017) reste le seul bloquant fonctionnel — il concerne une règle P4 (hint uniquement, non décisionnel) et peut être résolu indépendamment.

### Statut des règles

| Statut | Règles |
|--------|--------|
| ✅ Prêtes à coder (v1.3) | RULE-001, 002, 003, 004, 005, 006, 007, 008, 009, 010, **011** (modifiée), 012, 015, 016, 018, 019, **020** (modifiée), 021, 022, 023, 025, 026 |
| ⚠️ Dépend de D-05 | RULE-017 |
| ⛔ Désactivées V1 | RULE-013, 014, 024 |

### Résumé des changements v1.2 → v1.3

```
Règles modifiées        : 2 (RULE-011, RULE-020)
Garde-fous reformulés   : 2 (GF-06 orchestration, GF-07 libellé)
Champs ajoutés          : 1 (fatigue_score_history) + 1 (medical_referral_reason)
Validations ajoutées    : 3 (vitesse, injury_context, race_date_past)
Paramètres config       : 1 (min_absolute_weekly_km_on_maintain)
Profils adversariaux    : 4 nouveaux (P-16 à P-19)
Décisions produit       : 1 nouvelle (D-21)
```
