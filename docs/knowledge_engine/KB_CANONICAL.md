# Knowledge Base Canonique — Coach Marathon IA

> Version : 1.0
> Statut : fondation — à ne pas modifier sans arbitrage explicite
> Sources fusionnées : Source 1 (Perplexity cartographie), Source 2 (Perplexity décisionnel), Source 3 (Gemini bibliographie)
> Scope : modélisation des connaissances — aucun code, aucune API, aucun algorithme final

---

## 1. Concepts métier fondamentaux

| ID | Nom normalisé | Définition | Domaine | Rôle dans le coach IA | Importance décisionnelle | Sources |
|----|--------------|-----------|---------|----------------------|--------------------------|---------|
| C-001 | **Charge d'entraînement** | Quantité de travail produite par un coureur, mesurée en volume externe (km, durée, dénivelé) et en charge interne (RPE × durée = session-RPE). | Charge | Entrée centrale du moteur décisionnel ; détermine si augmentation, maintien ou réduction. | Critique | S1:K7, S2:schema, S3:Foster/Gabbett |
| C-002 | **ACWR** (Acute:Chronic Workload Ratio) | Ratio entre la charge des 7 derniers jours (aiguë) et la charge moyenne des 28 derniers jours (chronique). Indicateur de surcharge ou de déconditionnement. | Charge | Règle principale de décision de volume (seuils 1.5 et 2.0). | Critique | S1:K7, S2:RULE_ACWR_*, S3:Gabbett |
| C-003 | **Récupération** | Capacité du coureur à absorber la charge d'entraînement, évaluée via fatigue perçue, sommeil, douleurs et (V2) HRV. Dimension multifactorielle. | Récupération | Conditionne les règles de blocage et de cap d'augmentation. | Critique | S1:K6, K12, S2:RULE_FATIGUE_*, S3:Mujika/Altini |
| C-004 | **Périodisation** | Organisation du cycle d'entraînement en phases successives (générale → spécifique → affûtage) avec volume et intensité adaptés à l'objectif. | Planification | Structure la prescription sur plusieurs semaines ; détermine la phase courante. | Haute | S1:K1, K3, S2:current_phase, S3:Mujika/Canova/Issurin |
| C-005 | **Distribution d'intensité** | Répartition du temps d'entraînement entre les zones physiologiques. Modèle de référence : Z1 (basse intensité) / Z2 (zone intermédiaire) / Z3 (haute intensité). | Intensité | Qualité de la charge au-delà du volume — éviter la zone grise. | Haute | S1:K11, S3:Seiler |
| C-006 | **Profilage coureur** | Caractérisation du niveau, de l'expérience, de l'objectif et de l'état de santé du coureur. Conditionne toutes les décisions de planification. | Profilage | Point d'entrée de toute prescription ; calibre les seuils et caps. | Haute | S1:K2, K9, S2:experience_level, S3:— |
| C-007 | **Progressivité** | Principe d'augmentation contrôlée et graduelle de la charge. Seuil empirique : +10% par semaine maximum. | Progression | Règle fondamentale de sécurité pour la progression de volume. | Critique | S1:K3, K7, S2:RULE_WEEKLY_INCREASE_GT10 |
| C-008 | **Risque de blessure** | Probabilité d'une lésion musculo-squelettique en fonction de la charge, des douleurs, de l'historique de blessure et du stress mécanique. | Sécurité | Déclencheur des hard rules (deload forcé). | Critique | S1:K9, S2:RULE_PAIN_*, S3:Gabbett/Dubois/Cook |
| C-009 | **Performance** | Capacité de course mesurée via des temps sur distances de référence (5k, 10k, semi, marathon) ou via VMA. Indicateur de progression. | Performance | Calibre l'objectif, valide les zones d'intensité et prédit l'allure marathon. | Haute | S1:K2, K4, K13, S2:performance_trend, S3:Billat/Foster |
| C-010 | **Affûtage (Tapering)** | Phase finale de préparation avec réduction du volume (−40–60%) et maintien de l'intensité sur 2–3 semaines avant la course. | Planification | Déclencheur de la règle de blocage d'augmentation en phase taper. | Haute | S1:K1, S2:RULE_TAPER, S3:Mujika |
| C-011 | **Allure marathon / Pacing** | Vitesse cible au marathon, dérivée des performances récentes. Stratégie de course : negative split ou even split recommandés. | Performance | Ancre toute la prescription de séances spécifiques. | Haute | S1:K13, S3:Foster/Billat |
| C-012 | **Readiness** | Capacité globale du coureur à absorber une charge supplémentaire dans la semaine à venir. Score composite 0–100. | Décision | Sortie centrale du moteur décisionnel — détermine la décision finale. | Critique | S1:K6, K8, S2:readiness_score |

---

## 2. Dictionnaire canonique des variables

### 2.1. Variables MVP — entrée directe utilisateur

| Nom canonique | Définition | Type | Unité | Origine | Rôle | Concepts associés |
|---------------|-----------|------|-------|---------|------|------------------|
| `weekly_distance_km` | Distance totale de la semaine courante | Numérique | km | S2 | Entrée | C-001, C-002 |
| `previous_week_distance_km` | Distance de la semaine précédente | Numérique | km | S2 | Entrée | C-002, C-007 |
| `weekly_distance_history` | Tableau des 1–8 semaines précédentes | Array[float] | km/sem | S2 | Entrée | C-002 |
| `weekly_duration_min` | Durée totale d'entraînement de la semaine | Numérique | min | S2 | Entrée | C-001 |
| `avg_weekly_RPE` | RPE moyen pondéré de la semaine (0–10) | Numérique | — | S1/S2 | Entrée | C-001 |
| `fatigue_score` | Fatigue perçue auto-déclarée (1=très faible, 5=extrême) | Numérique | 1–5 | S2 | Entrée | C-003, C-012 |
| `sleep_quality_score` | Qualité du sommeil auto-déclarée (1=excellente, 5=très mauvaise) | Numérique | 1–5 | S2 | Entrée | C-003, C-012 |
| `pain_regions` | Tableau de douleurs [{region, intensity 0–5, days_persistent}] | Array[object] | — | S2 | Entrée | C-008 |
| `experience_level` | Niveau du coureur : "beginner" / "intermediate" / "advanced" | Catégorielle | enum | S2 | Entrée | C-006, C-007 |
| `current_phase` | Phase d'entraînement : "general" / "specific_marathon" / "taper" / "return_from_injury" / "off_season" | Catégorielle | enum | S2 | Entrée | C-004, C-010 |
| `weeks_since_last_injury` | Nombre de semaines depuis la dernière blessure | Entier | sem | S2 | Entrée | C-008 |
| `weeks_to_race` | Semaines restantes avant la course cible (null si pas de course) | Entier / null | sem | S1/S2 | Contextuelle | C-004, C-010 |
| `sessions_per_week_available` | Nombre de séances possibles par semaine (contrainte calendrier) | Entier | — | S1 | Entrée | C-004 |
| `recent_race_time_10k` | Temps récent sur 10 km (format mm:ss) | Numérique | sec | S1/S3 | Entrée | C-009, C-011 |
| `recent_race_time_half` | Temps récent sur semi-marathon (format mm:ss) | Numérique | sec | S1/S3 | Entrée | C-009, C-011 |
| `VMA_kmh` | Vitesse maximale aérobie estimée ou testée | Numérique | km/h | S3:Billat | Entrée (ou calculée) | C-005, C-009, C-011 |

### 2.2. Variables calculées (dérivées des entrées)

| Nom canonique | Calcul | Type | Unité | Concepts associés |
|---------------|--------|------|-------|------------------|
| `chronic_load_distance` | Moyenne de `weekly_distance_history` (fenêtre 4 semaines) | Numérique | km | C-001, C-002 |
| `ACWR_distance` | `weekly_distance_km` / `chronic_load_distance` | Numérique | ratio | C-002, C-008 |
| `delta_volume_pct` | (`weekly_distance_km` − `previous_week_distance_km`) / `previous_week_distance_km` × 100 | Numérique | % | C-007 |
| `weekly_internal_load` | `avg_weekly_RPE` × `weekly_duration_min` | Numérique | UA | C-001 |
| `readiness_score` | Score composite 0–100 (voir Section 3) | Numérique | 0–100 | C-012 |
| `target_marathon_pace_min_km` | Dérivé de `recent_race_time_half` ou `VMA_kmh` (formule à définir) | Numérique | min/km | C-011 |
| `zone_distribution` | % temps en Z1 / Z2 / Z3 sur la semaine | Object | % | C-005 |
| `fatigue_trend` | Tendance des `fatigue_score` sur les 3–4 dernières semaines | Catégorielle | improving/stable/worsening | C-003 |

### 2.3. Variables V2 (nécessitent capteurs, historique long ou tests spécialisés)

| Nom canonique | Justification du report | Source scientifique |
|---------------|------------------------|---------------------|
| `HRV_daily` / `HRV_baseline` / `HRV_trend` | Montre compatible + protocole standardisé requis | S3:Altini |
| `resting_HR_morning` / `resting_HR_baseline` | Données montre quotidiennes | S2:schema |
| `CTL` / `ATL` / `TSB` | Historique ≥ 6 semaines + charge précise requise | S3:Banister |
| `performance_trend` | Formule de calcul non définie — nécessite arbitrage | S2:schema |
| `lactate_mmol` | Test sanguin invasif — inaccessible grand public | S3:Bakken |
| `ambient_temperature_C` | Pertinent J-day uniquement, pas en planification | S3:Tucker |
| `marathon_pace_sessions_per_week` | Suivi granulaire des séances spécifiques | S3:Canova |
| `mental_fatigue_pre_race` | Mesure objective difficile | S3:Marcora |

### 2.4. Variables contextuelles (non utilisées dans les règles)

| Nom canonique | Usage | Concepts associés |
|---------------|-------|------------------|
| `age` | Filtre de sécurité profil | C-006 |
| `pathologies_connues` | Contre-indication — déclenche recommandation médicale | C-008 |
| `terrain_type` | Modifie le stress mécanique (trail > route) | C-008 |
| `preferences_communication` | Couche UX uniquement | — |
| `feedback_qualitatif` | Enrichit l'évaluation sans décision directe | C-003 |

---

## 3. États internes du coureur

Le coach évalue en permanence 5 états. Chaque état est calculé à partir d'un sous-ensemble de variables.

---

### ÉTAT-1 : Récupération

**Définition :** Capacité du coureur à absorber le prochain stimulus d'entraînement.

| Variables contributrices | Poids dans readiness_score | Méthode |
|--------------------------|--------------------------|---------|
| `fatigue_score` | 15/100 | Linéaire inverse (1→15 pts, 5→0 pts) |
| `sleep_quality_score` | 10/100 | Linéaire inverse |
| `pain_regions` | 10/100 | Inverse de l'intensité maximale des douleurs actives |

**V2 :** `HRV_trend`, `resting_HR_morning`

**Niveau de confiance :** Moyenne — dépend de l'auto-déclaration sincère et régulière.

---

### ÉTAT-2 : Charge

**Définition :** Niveau de charge actuel par rapport à la charge habituelle du coureur.

| Variables contributrices | Poids dans readiness_score | Méthode |
|--------------------------|--------------------------|---------|
| `ACWR_distance` | 20/100 | Courbe en cloche (optimum 0.8–1.3) |
| `delta_volume_pct` | 10/100 | Pénalité si >10% |
| `chronic_load_distance` | 5/100 | Bonus si volume suffisant pour la phase |

**Niveau de confiance :** Forte — basé sur la littérature ACWR (Gabbett, autorité 5/5).

---

### ÉTAT-3 : Progression

**Définition :** Tendance de l'évolution de la charge et de la performance sur les dernières semaines.

| Variables contributrices | Méthode |
|--------------------------|---------|
| `weekly_distance_history` | Pente de régression linéaire |
| `delta_volume_pct` | Variation semaine/semaine |
| `performance_trend` (V2) | Catégorie : improving / stable / declining |

**Niveau de confiance :** Moyenne — `performance_trend` non défini en V1.

---

### ÉTAT-4 : Risque blessure

**Définition :** Probabilité d'une lésion si la charge actuelle est maintenue ou augmentée.

| Variables contributrices | Signal |
|--------------------------|--------|
| `pain_regions[].intensity` + `pain_regions[].days_persistent` | Hard rule → deload |
| `weeks_since_last_injury` | Cap d'augmentation si < 4 semaines |
| `ACWR_distance` | Risque élevé si > 1.5 |
| `delta_volume_pct` | Risque si > 10% |

**Niveau de confiance :** Forte pour les douleurs (objective) / Forte pour l'ACWR (Gabbett) / Arbitraire pour le seuil 4 semaines.

---

### ÉTAT-5 : Préparation marathon

**Définition :** Adéquation entre l'état du coureur et les exigences de la prochaine compétition.

| Variables contributrices | Signal |
|--------------------------|--------|
| `current_phase` | Phase cohérente avec `weeks_to_race` ? |
| `weeks_to_race` | Proximité de la course |
| `readiness_score` | Score global |
| `zone_distribution` (V1 si disponible) | Proportion de travail spécifique |
| `target_marathon_pace_min_km` | Allure cible validée ? |

**Niveau de confiance :** Moyenne — dépend de la qualité du profilage initial.

---

## 4. Règles métier canonisées

> Convention de priorité :
> - **P0 — Override absolu** : s'applique en premier, annule toutes les autres décisions.
> - **P1 — Blocage** : interdit l'augmentation de charge.
> - **P2 — Cap** : plafonne le % d'augmentation (prend le minimum si plusieurs caps).
> - **P3 — Score** : ajuste le readiness_score sans changer la décision brute.
> - **P4 — Planification** : oriente la structure du plan sur plusieurs semaines.

---

### P0 — Override absolu (deload forcé)

| ID | SI condition | ALORS conséquence | Sources | Confiance | Seuils à surveiller |
|----|-------------|-------------------|---------|-----------|---------------------|
| RULE-001 | `pain_regions` contient intensity ≥ 4 ET days_persistent ≥ 2 (toute région) | Décharge forcée. Conseil consultation médicale. | S2 + S3:Cook/Dubois | **Forte** | Seuil auto-déclaré — subjectivité |
| RULE-002 | `pain_regions` contient region ∈ {achilles, knee, shin, hip, foot} ET intensity ≥ 3 ET days_persistent ≥ 3 | Décharge forcée. Risque tendinopathie/stress fracture. | S2 + S3:Cook | **Forte** | Région "other" moins discriminante |
| RULE-003 | `ACWR_distance` ≥ 2.0 | Décharge forcée. Charge aiguë 2× la normale. | S2 + S3:Gabbett | **Forte** | ACWR sur moyenne simple — voir CONF-001 |

---

### P1 — Blocage (interdiction d'augmentation)

| ID | SI condition | ALORS conséquence | Sources | Confiance | Seuils à surveiller |
|----|-------------|-------------------|---------|-----------|---------------------|
| RULE-004 | `ACWR_distance` > 1.5 ET < 2.0 | Bloquer l'augmentation. Décision max = maintain. | S2 + S3:Gabbett | **Forte** | Idem RULE-003 |
| RULE-005 | `delta_volume_pct` > 10% | Bloquer l'augmentation. Règle des 10%. | S1:K7 + S2 | **Forte** | Peut être trop restrictif sur très petits volumes (<15 km) |
| RULE-006 | `fatigue_score` ≥ 4 ET `sleep_quality_score` ≥ 4 | Bloquer l'augmentation. Récupération insuffisante. | S1:K6,K12 + S2 | **Forte** | Scores non standardisés — voir CONF-003 |
| RULE-007 | `current_phase` == "taper" | Bloquer l'augmentation. Phase d'affûtage : réduire le volume. | S1:K1 + S2 + S3:Mujika | **Forte** | Phase taper = −40–60% volume, 2–3 sem (Mujika) |

---

### P2 — Cap (plafonnement de l'augmentation)

| ID | SI condition | ALORS conséquence | Sources | Confiance | Seuils à surveiller |
|----|-------------|-------------------|---------|-----------|---------------------|
| RULE-008 | `weeks_since_last_injury` < 4 | Plafonner l'augmentation à +5% max | S2 | **Forte** | Seuil 4 semaines arbitraire — voir CONF-005 |
| RULE-009 | `fatigue_score` == 3 OU `sleep_quality_score` == 3 | Plafonner l'augmentation à +5% max | S2 | **Moyenne** | Frontière 3/4 floue |
| RULE-010 | `experience_level` == "beginner" | Plafonner l'augmentation à +5% max | S1:K3 + S2 | **Moyenne** | Critères "beginner" non définis — voir CONF-002 |

> **Résolution des conflits cap + blocage :** si une règle P1 et une règle P2 sont toutes deux déclenchées, P1 prend la priorité. Le cap est ignoré (la décision est block, pas capped-increase). ← *Décision d'arbitrage à confirmer.*

---

### P3 — Ajustements de score (readiness_score)

| ID | SI condition | ALORS conséquence | Sources | Confiance |
|----|-------------|-------------------|---------|-----------|
| RULE-011 | 0.8 ≤ `ACWR_distance` ≤ 1.3 ET `fatigue_score` ≤ 2 ET `sleep_quality_score` ≤ 2 ET pas de douleur > 2 | +10 pts readiness (feu vert multi-critères) | S2 | **Forte** |
| RULE-012 | `experience_level` == "advanced" ET 0.8 ≤ `ACWR_distance` ≤ 1.3 | +5 pts readiness (tolérance avancée) | S2 | **Moyenne** |
| RULE-013 | `performance_trend` == "declining" ET `ACWR_distance` ≥ 1.0 | −10 pts readiness | S2 | **Faible** (V2 — performance_trend souvent "unknown") |
| RULE-014 | `zone_distribution.Z2_pct` élevé ET `fatigue_trend` == "worsening" | −5 pts readiness (heuristique zone grise) | S3:Seiler | **Moyenne** (heuristique) |

---

### P4 — Règles de planification (structure du plan sur plusieurs semaines)

| ID | SI condition | ALORS conséquence | Sources | Confiance |
|----|-------------|-------------------|---------|-----------|
| RULE-015 | `weeks_to_race` ≥ 16 ET `weekly_distance_km` régulier (non spécifié) | Planifier phases générale → spécifique → taper | S1:K1 + S3:Canova | **Forte** |
| RULE-016 | `experience_level` == "beginner" ET `weekly_distance_km` faible | Proposer cycle préparatoire général AVANT cycle spécifique marathon | S1:K3 | **Forte** |
| RULE-017 | `experience_level` + historique volume → détermine plan faible/modéré/élevé | Sélectionner le plan de volume adapté au profil | S1:K4 | **Moyenne** |
| RULE-018 | `weeks_to_race` éloigné ET performances 5–10k en retard vs potentiel estimé | Prévoir cycle vitesse/seuil avant cycle spécifique marathon | S1:K5 | **Moyenne** |
| RULE-019 | Objectifs initiaux incohérents avec la situation actuelle (stagnation, blessure, changement contraintes) | Revisiter les objectifs et ajuster la prescription | S1:K8 | **Forte** |
| RULE-020 | Plusieurs séances clés manquées dans une semaine | Ajuster la semaine suivante — ne pas rattraper en cumulant | S1:K10 | **Moyenne** |
| RULE-021 | `current_phase` == "taper" | Réduire volume de 40–60%, maintenir l'intensité, durée 2–3 semaines | S3:Mujika | **Forte** |
| RULE-022 | `recent_race_time_half` ou `VMA_kmh` disponibles ET `target_marathon_pace` non défini | Calculer `target_marathon_pace_min_km` | S1:K13 + S3:Billat/Foster | **Forte** |

---

### P4 — Règles de gestion de course (jour J)

| ID | SI condition | ALORS conséquence | Sources | Confiance |
|----|-------------|-------------------|---------|-----------|
| RULE-023 | `pace_first_half` > `target_marathon_pace` + 5% | Signal de risque blow-up — recommander ralentissement | S1:K13 + S3:Foster | **Forte** |
| RULE-024 | `ambient_temperature_C` > 20°C | Ajuster `target_marathon_pace` à la baisse (−4 à −8%) | S3:Tucker | **Forte** (V2) |
| RULE-025 | Durée estimée course > 90 min | Protocole de ravitaillement glucidique requis (60–90 g CHO/h) | S3:Jeukendrup | **Forte** (module nutrition) |

---

## 5. Hiérarchie décisionnelle officielle

```
NIVEAU 1 — SÉCURITÉ (Blessure / Douleur critique)
├── RULE-001 : douleur ≥ 4/5 pendant ≥ 2 jours → deload forcé
├── RULE-002 : douleur tendon/articulaire ≥ 3/5 pendant ≥ 3 jours → deload forcé
└── RULE-003 : ACWR ≥ 2.0 → deload forcé
    ↓ OVERRIDE ABSOLU — si déclenché, ignorer niveaux 2–5

NIVEAU 2 — SURCHARGE (ACWR / Progression excessive)
├── RULE-004 : ACWR > 1.5 → block_increase
├── RULE-005 : Δvolume > 10% → block_increase
└── RULE-007 : phase taper → block_increase
    ↓ Si déclenché → décision max = "maintain" ou "decrease"

NIVEAU 3 — RÉCUPÉRATION (Fatigue / Sommeil)
├── RULE-006 : fatigue ≥ 4 ET sommeil ≥ 4 → block_increase
├── RULE-009 : fatigue = 3 OU sommeil = 3 → cap +5%
└── RULE-008 : blessure récente < 4 sem → cap +5%
    ↓ Si déclenché → décision max = "slight_increase" (cappée)

NIVEAU 4 — ADAPTATION INDIVIDUELLE (Profil / Phase / Historique)
├── RULE-010 : beginner → cap +5%
├── RULE-011 : feu vert multi-critères → +10 pts
├── RULE-012 : advanced + ACWR OK → +5 pts
├── RULE-013 : performance_trend declining → −10 pts
├── RULE-014 : zone grise + fatigue worsening → −5 pts
└── RULE-020 : séances manquées → ajuster plan

NIVEAU 5 — OPTIMISATION PERFORMANCE (Intensité / Allure / Spécificité)
├── RULE-015 : structurer phases macro-plan
├── RULE-018 : cycle vitesse/seuil pré-marathon
├── RULE-022 : calculer allure marathon cible
├── RULE-023 : pacing jour J
└── RULE-025 : nutrition course
```

**Règles d'override :**
1. Si au moins une règle P0 est déclenchée → décision = "deload", niveaux 2–5 ignorés.
2. Si au moins une règle P1 est déclenchée → décision max = "maintain", caps ignorés.
3. Si plusieurs caps P2 → prendre le minimum.
4. Les ajustements P3 n'overrident jamais P0, P1 ou P2.

---

## 6. Modèles scientifiques associés

| Modèle | Auteur | Concept apporté | Utilisation dans le coach | Niveau de preuve | Priorité IA |
|--------|--------|----------------|--------------------------|-----------------|-------------|
| **ACWR** | Tim Gabbett (2016) | Ratio aiguë/chronique pour prédire le risque de blessure | Seuils 1.5 (blocage) et 2.0 (deload) dans RULE-003/004 | ★★★★★ | 5/5 |
| **Session-RPE** | Carl Foster (1998) | Charge interne = RPE × durée | Calcul de `weekly_internal_load` | ★★★★★ | 5/5 |
| **Polarized Training / 80-20** | Stephen Seiler (2010) | 80% basse intensité / 20% haute ; modèle 3 zones | RULE-014 ; variable `zone_distribution` | ★★★★★ | 5/5 |
| **Tapering** | Iñigo Mujika (2009) | −40–60% volume, maintien intensité, 2–3 semaines avant course | RULE-007 + RULE-021 | ★★★★★ | 5/5 |
| **Surmenage / Overreaching** | Iñigo Mujika (2018) | Distinction fatigue fonctionnelle / non-fonctionnelle / surentraînement | Interprétation de `fatigue_trend` ; RULE-006 | ★★★★★ | 5/5 |
| **Spécificité marathon (Funnel)** | Renato Canova | Spécificité croissante ; Special Blocks | RULE-015 ; variable `marathon_pace_sessions_per_week` | ★★★★★ (expérientiel) | 5/5 |
| **Double Threshold / Norvégien** | Marius Bakken | 2 séances seuil/jour contrôlées au lactate | V1 si intermédiaire/avancé ; V2 complet | ★★★★ | 5/5 |
| **VVO2max / VMA** | Véronique Billat (1999) | Temps à VO2max ; allures VMA et VT2 | Calcul `target_marathon_pace` ; zones d'intensité | ★★★★★ | 4/5 |
| **Pacing marathon** | Carl Foster (2004) | Negative/even split → meilleures stratégies | RULE-023 ; calcul `split_ratio` | ★★★★★ | 5/5 |
| **Fitness-Fatigue (CTL/ATL/TSB)** | Eric Banister (1975) | Modèle Impulse-Response → forme du jour | V2 — extension du modèle ACWR | ★★★★★ | 4/5 |
| **HRV** | Marco Altini | Variabilité FC pour ajustement quotidien | V2 — récupération objective | ★★★★ | 4/5 |
| **Stress mécanique** | Blaise Dubois | Quantification du stress tissulaire ; adaptation | Enrichit RULE-001/002 ; variable `terrain_type` | ★★★★★ | 4/5 |
| **Tendinopathies** | Jill Cook (2001) | Charge progressive sur tendons | Régions anatomiques dans `pain_regions` enum | ★★★★★ | 4/5 |
| **CHO en course** | Asker Jeukendrup (2014) | 60–90 g CHO/h ; glucose+fructose | RULE-025 ; module nutrition | ★★★★★ | 5/5 |
| **Ajustement thermique** | Ross Tucker (2006) | Régulation anticipée de l'allure par la chaleur | RULE-024 (V2) | ★★★★★ | 4/5 |

---

## 7. Variables MVP vs V2

### MVP — Nécessaires au premier coach fonctionnel

```
PROFIL COUREUR (collecte unique + mise à jour ponctuelle)
├── experience_level
├── age
├── pathologies_connues
├── recent_race_time_10k
├── recent_race_time_half
├── VMA_kmh  (estimée depuis les temps de course ou testée)
└── sessions_per_week_available

SEMAINE COURANTE (collecte hebdomadaire)
├── weekly_distance_km
├── previous_week_distance_km
├── weekly_distance_history  (min. 4 entrées pour ACWR fiable)
├── weekly_duration_min
├── avg_weekly_RPE
├── fatigue_score
├── sleep_quality_score
└── pain_regions  [{region, intensity, days_persistent}]

CONTEXTE PLAN
├── current_phase
├── weeks_to_race
└── weeks_since_last_injury

VARIABLES CALCULÉES AUTOMATIQUEMENT
├── ACWR_distance
├── chronic_load_distance
├── delta_volume_pct
├── weekly_internal_load
├── readiness_score
└── target_marathon_pace_min_km
```

### V2 — Nécessitent capteurs / historique long / validation

```
RÉCUPÉRATION OBJECTIVE
├── HRV_daily
├── HRV_baseline
├── HRV_trend
├── resting_HR_morning
└── resting_HR_baseline

MODÈLE FITNESS-FATIGUE
├── CTL  (Chronic Training Load)
├── ATL  (Acute Training Load)
└── TSB  (Training Stress Balance)

PERFORMANCE
├── performance_trend  (formule de calcul à définir)
└── lactate_mmol  (test sanguin — avancé)

DISTRIBUTION D'INTENSITÉ
└── zone_distribution  {Z1_pct, Z2_pct, Z3_pct}  (données GPS/FC)

CONTEXTE COURSE
├── ambient_temperature_C
└── marathon_pace_sessions_per_week
```

---

## 8. Conflits, ambiguïtés et décisions nécessaires

> Ces éléments nécessitent un **arbitrage humain explicite** avant implémentation.
> Aucune résolution arbitraire n'a été appliquée dans ce document.

| ID | Type | Description | Impact | Décision requise |
|----|------|-------------|--------|-----------------|
| CONF-001 | Seuil arbitraire | Fenêtre ACWR = 4 semaines (moyenne simple). EWMA plus robuste mais non implémenté. Sensible aux semaines atypiques (vacances, maladie). | RULE-003/004 | Choisir entre moyenne simple (MVP simple) et EWMA (V1+ robuste) |
| CONF-002 | Critères non définis | `experience_level` (beginner/intermediate/advanced) : aucun critère de classification fourni. Par années ? Volume ? Temps sur marathon ? | RULE-010/012/016 | Définir les critères de segmentation (ex. : beginner < 1 an ou < 30 km/sem) |
| CONF-003 | Outils non standardisés | `fatigue_score` et `sleep_quality_score` : échelle 1–5 maison, non validée scientifiquement. TQR, POMS ou Hooper Index seraient plus robustes. | RULE-006/009 | Choisir et documenter l'échelle utilisée |
| CONF-004 | Règle manquante | Phase `off_season` présente dans l'enum de `current_phase` mais aucune règle associée dans aucune source. | Décision sans règle | Définir le comportement en off_season (maintien, récupération active ?) |
| CONF-005 | Seuil arbitraire | Seuil de 4 semaines post-blessure pour le cap à +5% : aucune justification scientifique. | RULE-008 | Valider ou remplacer par une règle basée sur la sévérité de la blessure |
| CONF-006 | Variable orpheline | `mood_motivation_score` présent dans le schéma Source 2, absent de toutes les règles. Lié à K14 (UX) et au modèle Marcora (S3). | Aucun (V1) | Décider : ignore en V1, ou intégrer comme pénalité légère en V2 |
| CONF-007 | Variable orpheline | `weeks_to_race` présent dans le schéma, aucune règle directe — uniquement implicite via `current_phase`. | Décision sans règle | Faut-il une règle directe (ex. : si weeks_to_race < 3 → taper forcé) ? |
| CONF-008 | Définition ambiguë | `performance_trend` (improving/stable/declining) : aucune formule de calcul. Sur combien de semaines ? Quel indicateur ? | RULE-013 | Définir la formule avant V2 |
| CONF-009 | Conflit de résolution | Si une règle P2 (cap) et une règle P1 (block) sont simultanément déclenchées : le block gagne-t-il ? Ce document dit oui, mais ce n'est pas explicite dans les sources. | RULE-005 + RULE-010 (ex.) | Confirmer la règle de résolution cap vs block |
| CONF-010 | Zone d'intensité | Définition des zones Z1/Z2/Z3 : basée sur %FC max ? %VMA ? RPE ? Seiler utilise les seuils ventilatoires — difficile à mesurer en auto. | RULE-014 + zone_distribution | Choisir l'indicateur proxy accessible (RPE préféré pour MVP) |
| CONF-011 | Transition niveau | Critères de passage beginner → intermediate → advanced : absents de toutes les sources. | RULE-010/012 | Définir les critères de transition (ex. : intermediate si >1 an ET >40 km/sem habituel) |
| CONF-012 | K15 introuvable | Le nœud K15 est référencé par K2 et K9 dans Source 1 mais absent des trois sources. Probablement : "contre-indications médicales" ou "consultation médicale préalable". | Graphe de dépendances | Identifier ou supprimer la référence à K15 |
| CONF-013 | Règle des 10% petits volumes | RULE-005 (Δvolume > 10% = block) peut être trop restrictif pour un coureur à 15 km/sem : +2 km déclenche la règle. | RULE-005 | Envisager un seuil absolu minimum (ex. : block si Δ > 10% ET semaine précédente > 20 km) |

---

## 9. Graphe de dépendances global

```
┌─────────────────────────────────────────────────────────┐
│                    ENTRÉES UTILISATEUR                  │
│  weekly_distance_km  ·  fatigue_score  ·  pain_regions  │
│  experience_level  ·  current_phase  ·  weeks_to_race   │
│  recent_race_times  ·  VMA  ·  sessions_available       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    VARIABLES CALCULÉES                  │
│  ACWR_distance  ·  delta_volume_pct  ·  readiness_score │
│  chronic_load_distance  ·  weekly_internal_load          │
│  target_marathon_pace  ·  zone_distribution (V2)         │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    ÉTATS COUREUR                        │
│                                                         │
│  ÉTAT-1 Récupération  ──────────┐                       │
│  ÉTAT-2 Charge        ──────────┤                       │
│  ÉTAT-3 Progression   ──────────┤──► readiness_score    │
│  ÉTAT-4 Risque blessure ────────┤                       │
│  ÉTAT-5 Préparation marathon ───┘                       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  RÈGLES DÉCISIONNELLES                  │
│                                                         │
│  P0 — Override (RULE-001/002/003)                        │
│    ↓                                                    │
│  P1 — Blocage (RULE-004/005/006/007)                    │
│    ↓                                                    │
│  P2 — Cap (RULE-008/009/010)                            │
│    ↓                                                    │
│  P3 — Score (RULE-011/012/013/014)                      │
│    ↓                                                    │
│  P4 — Planification (RULE-015 à 025)                    │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  ACTIONS DU COACH                       │
│                                                         │
│  deload         → réduire −20 à −40%                   │
│  decrease       → réduire −5 à −20%                    │
│  maintain       → ±0%                                  │
│  slight_increase → +3 à +5%                            │
│  increase       → +5 à +10% (selon profil)             │
│                                                         │
│  + Règles planification :                               │
│    · ajuster la phase courante                          │
│    · réviser l'objectif                                 │
│    · structurer le prochain cycle                       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              EXPLICATIONS UTILISATEUR (LLM)             │
│                                                         │
│  Input :  Decision JSON (scellé, non modifiable)        │
│           + rules_triggered[]                           │
│           + readiness_score + confidence_score          │
│           + historique qualitatif coureur               │
│                                                         │
│  Output : coach_message (langage naturel)               │
│           + suggestions séances hebdomadaires           │
│           + pédagogie adaptée au niveau                 │
│                                                         │
│  Contrainte absolue : le LLM ne peut PAS modifier       │
│  la décision ni assouplir un deload.                    │
└─────────────────────────────────────────────────────────┘
```

---

## Annexe — Index de traçabilité des règles

| ID règle | Origine Source 1 | Origine Source 2 | Origine Source 3 (auteur) |
|----------|-----------------|-----------------|---------------------------|
| RULE-001 | K9 | RULE_PAIN_CRITICAL | Cook, Dubois |
| RULE-002 | K9 | RULE_PAIN_TENDON_JOINT | Cook |
| RULE-003 | K7 | RULE_ACWR_DANGER | Gabbett |
| RULE-004 | K7 | RULE_ACWR_HIGH | Gabbett |
| RULE-005 | K7 | RULE_WEEKLY_INCREASE_GT10 | Gabbett |
| RULE-006 | K6, K12 | RULE_FATIGUE_SLEEP_RED | Mujika (surmenage) |
| RULE-007 | K1 | RULE_TAPER_NO_INCREASE | Mujika (tapering) |
| RULE-008 | K9 | RULE_RECENT_INJURY_CAP | Dubois |
| RULE-009 | K12 | RULE_FATIGUE_MODERATE | — |
| RULE-010 | K3 | RULE_BEGINNER_LIMIT | — |
| RULE-011 | K6 | RULE_GREEN_LIGHT | Gabbett |
| RULE-012 | K1, K4 | RULE_ADVANCED_TOLERANCE | — |
| RULE-013 | — | RULE_PERF_DECLINING | — |
| RULE-014 | K11 | — | Seiler |
| RULE-015 | K1 | — | Canova |
| RULE-016 | K3 | — | — |
| RULE-017 | K4 | — | — |
| RULE-018 | K5 | — | — |
| RULE-019 | K8 | — | — |
| RULE-020 | K10 | — | — |
| RULE-021 | K1 | RULE_TAPER (détail) | Mujika (tapering) |
| RULE-022 | K13 | — | Billat, Foster |
| RULE-023 | K13 | — | Foster (pacing) |
| RULE-024 | K13 | — | Tucker |
| RULE-025 | — | — | Jeukendrup |
