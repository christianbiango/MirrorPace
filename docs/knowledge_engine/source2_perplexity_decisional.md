# Source 2 — Perplexity : Analyse décisionnelle — Charge hebdomadaire

> Rôle : moteur de décision déterministe pour décider si un coureur doit augmenter, maintenir ou réduire sa charge.
> Statut : ingérée, en attente de fusion avec Source 1 et Source 3.

---

## 1. Critères décisionnels clés

| Critère | Description | Impact potentiel |
|---------|-------------|-----------------|
| **ACWR distance** | Ratio charge aiguë / charge chronique sur volume km | ≥2.0 → deload forcé ; >1.5 → blocage augmentation ; 0.8–1.3 → feu vert |
| **Douleur (intensité + durée)** | Score 0–5 par région anatomique × jours persistants | ≥4 et ≥2j → deload forcé ; zone tendon ≥3 et ≥3j → deload forcé |
| **Fatigue perçue + qualité sommeil** | Scores 1–5 auto-déclarés | ≥4 combinés → blocage augmentation ; ==3 → cap à +5% |
| **Augmentation volume hebdo %** | (sem_actuelle − sem_précédente) / sem_précédente × 100 | >10% → blocage augmentation |
| **Niveau d'expérience** | beginner / intermediate / advanced | beginner → cap à +5% ; advanced → bonus +5 pts si ACWR OK |
| **Phase d'entraînement** | general / specific_marathon / taper / return_from_injury / off_season | taper → blocage augmentation ; return_from_injury → score contexte bas |
| **Semaines depuis blessure** | Entier ≥ 0 | <4 semaines → cap à +5% |
| **Tendance de performance** | improving / stable / declining / unknown | declining + ACWR ≥ 1.0 → pénalité −10 pts |

---

## 2. Variables utiles

### Directement exploitables (champs bruts)

| Nom normalisé | Définition | Rôle décisionnel | Relations |
|---------------|-----------|-----------------|-----------|
| `weekly_distance_km` | Distance totale de la semaine courante (km) | Numérateur ACWR, delta volume | → ACWR, Δvolume% |
| `previous_week_distance_km` | Distance semaine précédente (km) | Calcul Δvolume | → Δvolume% |
| `weekly_distance_history` | Liste de 1–8 semaines passées (km) | Calcul charge chronique | → chronic_load, ACWR |
| `fatigue_score` | Score fatigue 1–5 (auto-déclaré) | Règles récupération | → RULE_FATIGUE_* |
| `sleep_quality_score` | Score sommeil 1–5 (auto-déclaré) | Règles récupération | → RULE_FATIGUE_* |
| `pain_regions` | Tableau [{region, intensity 0–5, days_persistent}] | Règles douleur (hard rules) | → RULE_PAIN_* |
| `experience_level` | beginner / intermediate / advanced | Cap et bonus profil | → RULE_BEGINNER, RULE_ADVANCED |
| `current_phase` | Phase entraînement (enum 5 valeurs) | Contexte décisionnel | → RULE_TAPER, score contexte |
| `weeks_since_last_injury` | Semaines écoulées depuis dernière blessure | Sécurité reprise | → RULE_RECENT_INJURY_CAP |
| `performance_trend` | improving / stable / declining / unknown | Score performance (V2) | → RULE_PERF_DECLINING |

### Nécessitant transformation / calcul

| Variable brute | Calcul | Résultat | Rôle |
|----------------|--------|----------|------|
| `weekly_distance_history` (4 sem.) | Moyenne simple | `chronic_load_distance` | Dénominateur ACWR |
| `weekly_distance_km` / `chronic_load_distance` | Division | `ACWR_distance` | Règles surcharge |
| (`weekly_distance_km` − `previous_week_distance_km`) / `previous_week_distance_km` × 100 | Pourcentage | `delta_volume_pct` | Règle >10% |
| `avg_weekly_RPE` × `weekly_duration_min` | Multiplication | `weekly_internal_load` | Charge interne (session-RPE) |

### Uniquement contextuelles

| Variable | Usage |
|----------|-------|
| `weeks_to_race` | Contexte temporel, pas de règle directe V1 (influencé via `current_phase`) |
| `resting_HR_morning` / `resting_HR_baseline` | V2 uniquement — récupération objective |
| `HRV_index` | V2 uniquement — récupération objective |
| `weekly_elevation_gain_m` | Non utilisé dans les règles V1 |
| `mood_motivation_score` | Non utilisé dans les règles V1 (présent dans le schéma mais absent des règles YAML) |
| `soreness_score_global` | Score global — les règles utilisent `pain_regions` à la place |

---

## 3. Relations décisionnelles entre variables

```
ACWR_distance >= 2.0                                    → force_deload
ACWR_distance in (1.5, 2.0)                             → block_increase
ACWR_distance in (0.8, 1.3) + fatigue ≤ 2 + sleep ≤ 2 + no pain > 2 → score_bonus (feu vert)

delta_volume_pct > 10%                                  → block_increase
weeks_since_last_injury < 4                             → cap_increase_pct:5

fatigue_score ≥ 4 + sleep_quality_score ≥ 4            → block_increase
fatigue_score == 3 OR sleep_quality_score == 3          → cap_increase_pct:5

pain.intensity ≥ 4 + pain.days_persistent ≥ 2          → force_deload (priorité max)
tendon/joint pain ≥ 3 + days_persistent ≥ 3            → force_deload

experience_level == "beginner"                          → cap_increase_pct:5
experience_level == "advanced" + ACWR in (0.8, 1.3)    → score_bonus:5
current_phase == "taper"                                → block_increase

performance_trend == "declining" + ACWR ≥ 1.0          → score_penalty:10

readiness_score_final ≥ 75 + no block_increase         → decision: increase
readiness_score_final in [50, 74] + no block_increase  → decision: increase (slight)
readiness_score_final in [30, 49]                       → decision: maintain
readiness_score_final < 30                              → decision: decrease
any force_deload triggered                              → decision: deload (override tout)
```

---

## 4. Règles métier (format SI → ALORS)

| ID règle | Condition | Conséquence | Action système | Confiance | Limites |
|----------|-----------|-------------|----------------|-----------|---------|
| RULE_PAIN_CRITICAL | SI douleur intensité ≥ 4 ET persistante ≥ 2j | ALORS décharge forcée | force_deload | Forte | Dépend de la fiabilité de l'auto-déclaration |
| RULE_PAIN_TENDON_JOINT | SI douleur région tendon/articulaire ≥ 3 ET persistante ≥ 3j | ALORS décharge forcée | force_deload | Forte | Zones définies en enum, "other" moins précis |
| RULE_RECENT_INJURY_CAP | SI semaines depuis blessure < 4 | ALORS cap augmentation à +5% max | cap_increase_pct:5 | Forte | Seuil de 4 semaines arbitraire |
| RULE_FATIGUE_SLEEP_RED | SI fatigue ≥ 4 ET sommeil ≥ 4 | ALORS blocage augmentation | block_increase | Forte | Scores auto-déclarés non standardisés |
| RULE_FATIGUE_MODERATE | SI fatigue == 3 OU sommeil == 3 | ALORS cap à +5% | cap_increase_pct:5 | Moyenne | Seuil de 3 sur 5 à valider |
| RULE_ACWR_DANGER | SI ACWR ≥ 2.0 | ALORS décharge forcée | force_deload | Forte | ACWR calculé sur moyenne simple 4 sem. |
| RULE_ACWR_HIGH | SI 1.5 < ACWR < 2.0 | ALORS blocage augmentation | block_increase | Forte | Idem |
| RULE_WEEKLY_INCREASE_GT10 | SI Δvolume > 10% vs semaine précédente | ALORS blocage augmentation | block_increase | Forte | Règle des 10% — consensus large |
| RULE_GREEN_LIGHT | SI 0.8 ≤ ACWR ≤ 1.3 ET fatigue ≤ 2 ET sommeil ≤ 2 ET pas de douleur > 2 | ALORS bonus score | score_bonus:10 | Forte | Feu vert multi-critères |
| RULE_BEGINNER_LIMIT | SI experience_level == "beginner" | ALORS cap à +5% | cap_increase_pct:5 | Moyenne | Pas de critère de transition beginner → intermediate |
| RULE_ADVANCED_TOLERANCE | SI experience_level == "advanced" ET 0.8 ≤ ACWR ≤ 1.3 | ALORS bonus score | score_bonus:5 | Moyenne | Définition "advanced" non précisée |
| RULE_TAPER_NO_INCREASE | SI current_phase == "taper" | ALORS blocage augmentation | block_increase | Forte | Pas de règle pour off_season |
| RULE_PERF_DECLINING | SI performance_trend == "declining" ET ACWR ≥ 1.0 | ALORS pénalité score | score_penalty:10 | Moyenne | performance_trend = V2, souvent "unknown" en V1 |

---

## 5. Hiérarchie des facteurs décisionnels

La source définit explicitement un ordre de priorité à deux niveaux :

### Niveau 1 — Hard rules (override absolu)
```
1. force_deload  (PAIN_CRITICAL, PAIN_TENDON, ACWR >= 2.0)
   └── Override toutes les autres règles, décision = "deload"
```

### Niveau 2 — Blocages (interdisent l'augmentation)
```
2. block_increase  (FATIGUE_SLEEP_RED, ACWR_HIGH, WEEKLY_INCREASE_GT10, TAPER)
   └── Décision max = "maintain" ou "decrease"
```

### Niveau 3 — Caps (limitent le % d'augmentation)
```
3. cap_increase_pct  (RECENT_INJURY, FATIGUE_MODERATE, BEGINNER)
   └── Prend le minimum de tous les caps déclenchés
```

### Niveau 4 — Ajustements de score (influence le readiness_score)
```
4. score_bonus / score_penalty  (GREEN_LIGHT, ADVANCED, PERF_DECLINING)
   └── Modifie le score final, pas la décision brute
```

**Principe général confirmé :** blessure/douleur > ACWR > récupération > progression > profil > performance.

---

## 6. Seuils et valeurs numériques

| Seuil | Valeur | Contexte | Niveau de preuve | Risque d'abus |
|-------|--------|----------|-----------------|---------------|
| ACWR danger | ≥ 2.0 → force_deload | Ratio charge aiguë/chronique | Forte (littérature endurance) | Sur-réaction si historique < 4 semaines |
| ACWR élevé | > 1.5 → block_increase | Idem | Forte | Idem |
| ACWR zone verte | 0.8–1.3 | Feu vert progression | Forte | Peut masquer une fatigue accumulée |
| ACWR zone basse | < 0.6 → danger aussi | Déconditionnement | Moyenne | Rare en pratique |
| Augmentation hebdo max | > 10% → block | Règle des 10% | Forte (consensus large) | Peut être trop restrictif sur petits volumes |
| Fenêtre historique ACWR | 4 semaines (MVP) | Moyenne simple | Moyenne (EWMA non utilisé) | Sensible aux semaines atypiques |
| Fatigue critique | ≥ 4/5 | Combiné avec sommeil | Moyenne (auto-déclaré) | Subjectivité |
| Fatigue modérée | == 3/5 | Seul ou combiné | Faible (seuil arbitraire) | Frontière floue 3/4 |
| Douleur critique | intensité ≥ 4 + ≥ 2j | N'importe quelle région | Forte | Dépend de l'honnêteté déclarative |
| Douleur tendon/joint | intensité ≥ 3 + ≥ 3j | Régions spécifiques (enum) | Forte | Région "other" moins discriminante |
| Reprise blessure | < 4 semaines → cap 5% | Post-blessure | Forte | Seuil de 4 sem. non justifié scientifiquement |
| Readiness → increase | ≥ 75/100 | + no block | Moyenne (calibration empirique) | Seuils de score à valider sur données réelles |
| Readiness → slight increase | 50–74/100 | + no block | Moyenne | Idem |
| Readiness → maintain | 30–49/100 | — | Moyenne | Idem |
| Readiness → decrease | < 30/100 | — | Moyenne | Idem |
| Augmentation recommandée max | +10% (advanced) | Bon score + no cap | Moyenne | |
| Augmentation recommandée std | +5–8% | Standard | Moyenne | |
| Décharge recommandée | −20 à −40% | deload | Moyenne | Plage large |

---

## 7. Pondération du readiness_score

| Composante | Poids | Sous-scores |
|-----------|-------|-------------|
| Charge & ratios | 35% (0–35 pts) | ACWR_score (0–20) + Δvolume_score (0–10) + chronic_load_score (0–5) |
| Récupération / fatigue / douleurs | 35% (0–35 pts) | fatigue_component (0–15) + sleep_component (0–10) + pain_component (0–10) |
| Performance | 10% (0–10 pts) | performance_component — V2, défaut = 5 (unknown) |
| Contexte / profil | 20% (0–20 pts) | experience_component (0–8) + injury_history_component (0–8) + phase_component (0–4) |

---

## 8. Gaps identifiés / contradictions / arbitrages nécessaires

| Gap | Description | Source potentielle |
|-----|-------------|-------------------|
| K15 (Source 1) | Toujours non défini dans cette source | Source 3 ou absent |
| Calcul charge chronique | Moyenne simple vs EWMA — pas de formule précise fournie | Source 3 |
| Outils de mesure fatigue/sommeil | Aucun questionnaire standardisé nommé (TQR ? POMS ? Echelle maison ?) | À définir |
| Définition `experience_level` | Aucun critère de classification beginner/intermediate/advanced (années ? volume ?) | Source 3 |
| Règle `off_season` | Phase présente dans l'enum mais aucune règle associée | À arbitrer |
| `mood_motivation_score` | Présent dans le schéma, absent de toutes les règles YAML | À décider V1 ou V2 |
| `weeks_to_race` | Présent dans le schéma, aucune règle directe — uniquement via `current_phase` | À arbitrer |
| `HRV_index` échelle 0–2 | Échelle non standard (habituellement en ms ou rMSSD) — à clarifier | — |
| Transition `beginner → intermediate` | Aucun critère de franchissement du palier | Source 3 potentiellement |
| Seuil des 4 semaines post-blessure | Arbitraire — pas de justification scientifique citée | Littérature |
| `chronic_load_score` seuil "30–40 km" | Seuil de volume "phase spécifique marathon" non chiffré précisément | Source 3 |
| Résolution conflits `cap_increase` + `block_increase` | Si une règle cap ET une règle block coexistent → block gagne, cap ignoré ? Pas explicite | À définir |
| Scores de récupération objectifs (HR, HRV) | Totalement absents du V1, décision dépend 100% de l'auto-déclaration | V2 |

---

## 9. Ponts avec Source 1

| Règle Source 2 | Nœud Source 1 correspondant | Apport de Source 2 |
|----------------|----------------------------|--------------------|
| RULE_ACWR_DANGER / RULE_ACWR_HIGH | K7 (progression charge) | **Remplit gap** : seuils ACWR 1.5 et 2.0 désormais définis |
| RULE_WEEKLY_INCREASE_GT10 | K7 | **Remplit gap** : seuil de 10% confirmé |
| RULE_FATIGUE_SLEEP_RED | K6, K12 | **Précise** : combinaison fatigue + sommeil ≥ 4 sur 5 |
| RULE_PAIN_CRITICAL / TENDON | K9 (check-up initial) | **Étend** : régions anatomiques avec enum + seuils |
| RULE_BEGINNER_LIMIT | K3 (progressivité débutants) | **Quantifie** : cap à +5% pour beginner |
| RULE_TAPER_NO_INCREASE | K1 (périodisation macro) | **Opérationnalise** : phase taper = blocage |
| readiness_score structure | K8 (cadre evidence-informed) | **Implémente** le cadre conceptuel en score numérique |
