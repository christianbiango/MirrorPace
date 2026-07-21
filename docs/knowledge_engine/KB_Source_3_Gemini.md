# KB Source 3 — Gemini : Cartographie bibliographique des connaissances

> Rôle : inventaire des sources scientifiques et pratiques pour alimenter le coach marathon IA.
> Statut : ingérée, en attente de fusion avec Source 1 et Source 2.
> Note importante : contrairement à ce que le format laissait attendre, cette source est une **bibliographie structurée** (21 références), non un dataset de variables coureur. L'analyse est adaptée en conséquence.

---

## 1. Inventaire des colonnes du CSV

| Nom original | Nom normalisé | Description | Type | Fréquence | Qualité |
|---|---|---|---|---|---|
| `domaine` | `domain` | Domaine de connaissance (5 valeurs) | Catégorielle | Ponctuelle | Fiable |
| `sous_theme` | `sub_theme` | Sous-thème précis dans le domaine | Catégorielle | Ponctuelle | Fiable |
| `auteur_reference` | `author` | Auteur principal de la source | Texte | Ponctuelle | Fiable |
| `titre_source` | `source_title` | Titre complet de la publication | Texte | Ponctuelle | Fiable |
| `type_source` | `source_type` | article scientifique / livre / podcast / conférence | Catégorielle | Ponctuelle | Fiable |
| `lien_url_si_disponible` | `url` | URL de la source (N/A si absent) | Texte/URL | Ponctuelle | Fiable (1 manquant : Banister) |
| `pourquoi_cette_source_est_importante` | `importance_rationale` | Justification de l'intérêt pour le coach IA | Texte | Ponctuelle | Dépendante de l'auteur |
| `niveau_autorite_estime` | `authority_level` | Score d'autorité scientifique 1–5 | Numérique | Ponctuelle | Fiable |
| `priorite_pour_un_coach_marathon_IA` | `ia_priority` | Priorité d'intégration dans le moteur IA 1–5 | Numérique | Ponctuelle | Fiable |

---

## 2. Classification des 21 sources par domaine

### 2.1. Physiologie & Allures — 4 sources

| Auteur | Sous-thème | Autorité | Priorité IA | Concepts clés extraits |
|--------|-----------|----------|-------------|------------------------|
| Stephen Seiler | Distribution d'intensité | 5 | **5** | Modèle polarisé 80/20 — 80 % basse intensité, 20 % haute intensité. |
| Stephen Seiler | Zones d'entraînement | 5 | **5** | Modèle 3 zones (Z1/Z2/Z3) vs 5–7 zones ; gestion du premier seuil ventilatoire (VT1). |
| Véronique Billat | Seuil Lactique & VVO2max | 5 | 4 | Temps passé à VO2max (T@VMA) ; allures cibles VMA et VT2. |
| Marco Altini | HRV | 4 | 4 | Utilisation quotidienne de la HRV pour ajuster les zones et l'intensité. |

**Variables nouvelles introduites :**
- `zone_1_pct`, `zone_2_pct`, `zone_3_pct` — distribution du temps par zone
- `VT1_pace` (km/h ou min/km) — premier seuil ventilatoire
- `VT2_pace` — deuxième seuil ventilatoire / seuil lactique
- `VMA` (vitesse maximale aérobie, km/h) — indispensable MVP
- `T_at_VMA_min` — durée de travail à VMA par séance
- `HRV_daily` / `HRV_baseline` / `HRV_trend` — récupération objective (V2)

---

### 2.2. Charge & Fatigue — 4 sources

| Auteur | Sous-thème | Autorité | Priorité IA | Concepts clés extraits |
|--------|-----------|----------|-------------|------------------------|
| Tim Gabbett | ACWR | 5 | **5** | Standard de prédiction du risque de blessure via ratio charge aiguë/chronique. |
| Carl Foster | sRPE (charge interne) | 5 | **5** | Charge interne = RPE × durée (session-RPE) ; méthode validée chez les coureurs loisir. |
| Eric Banister | Modèle Fitness-Fatigue | 5 | 4 | Modèle Impulse-Response → CTL (fitness), ATL (fatigue), TSB (forme = CTL − ATL). |
| Iñigo Mujika | Surmenage | 5 | **5** | Distinction fatigue fonctionnelle / surmenage non fonctionnel / syndrome de surentraînement. |

**Variables nouvelles introduites :**
- `acute_load_7d` (km ou UA charge interne) — charge des 7 derniers jours
- `chronic_load_28d` — charge des 28 derniers jours (moyenne) → **confirme fenêtre 4 semaines de Source 2**
- `ACWR` = acute_load / chronic_load → **confirme seuils Source 2 (1.5 / 2.0)**
- `session_RPE` (0–10) × `session_duration_min` → `internal_load_session`
- `CTL` (Chronic Training Load / fitness) — V2
- `ATL` (Acute Training Load / fatigue) — V2
- `TSB` (Training Stress Balance = CTL − ATL) — V2
- `overreaching_flag` (booléen) — indicateur surmenage non fonctionnel

---

### 2.3. Périodisation & Affûtage — 4 sources

| Auteur | Sous-thème | Autorité | Priorité IA | Concepts clés extraits |
|--------|-----------|----------|-------------|------------------------|
| Iñigo Mujika | Tapering | 5 | **5** | Réduction volume −40–60%, maintien intensité, durée 2–3 semaines avant course. |
| Renato Canova | Endurance spécifique marathon | 5 | **5** | Funnel System (spécificité croissante) ; Special Blocks (blocs intensifs pré-marathon). |
| Marius Bakken | Double Threshold / Modèle norvégien | 4 | **5** | 2 séances seuil/jour, contrôle par lactate sanguin. |
| Vladimir Issurin | Périodisation par blocs | 4 | 3 | Séquence accumulation → transformation → réalisation. |

**Variables nouvelles introduites :**
- `taper_week_flag` (booléen) — phase d'affûtage actif
- `taper_volume_reduction_pct` — objectif de réduction volume pendant l'affûtage
- `marathon_pace_sessions_per_week` — fréquence des séances à allure marathon (Canova)
- `special_block_flag` (booléen) — bloc spécifique intensif en cours
- `block_type` = "accumulation" / "transformation" / "realization" (Issurin)
- `lactate_mmol` — lactate sanguin (requis par modèle Bakken — avancé V2+)

---

### 2.4. Biomécanique & Blessures — 3 sources

| Auteur | Sous-thème | Autorité | Priorité IA | Concepts clés extraits |
|--------|-----------|----------|-------------|------------------------|
| Blaise Dubois | Stress mécanique | 5 | 4 | Quantification du stress mécanique ; temps d'adaptation tissulaire. |
| Jill Cook | Tendinopathies | 5 | 4 | Gestion progressive de la charge sur tendons (Achille, fascia plantaire). |
| Isabel Moore | Économie de course & cadence | 4 | 3 | Cadence optimale 170–180 spm ; oscillation verticale. |

**Variables nouvelles introduites :**
- `weekly_elevation_gain_m` — déjà dans Source 2 (non utilisé en V1)
- `terrain_type` = "road" / "trail" / "track" — stress mécanique différencié
- `tendon_load_protocol` — protocole de charge progressive (Cook) — V2
- `running_cadence_spm` — cadence en pas/minute — V2/optionnel
- `vertical_oscillation_cm` — biomécanique — V2/optionnel
- `shoe_type` / `shoe_km` — facteur mécanique — optionnel

---

### 2.5. Nutrition & Hydratation — 3 sources

| Auteur | Sous-thème | Autorité | Priorité IA | Concepts clés extraits |
|--------|-----------|----------|-------------|------------------------|
| Asker Jeukendrup | Glucides & Ravitaillement | 5 | **5** | 60–90 g CHO/h en course (mix glucose/fructose) ; protocole "Training the Gut". |
| Trent Stellingwerff | Disponibilité énergétique | 5 | 4 | Périodisation nutritionnelle : Train-Low / Compete-High. |
| Louise Burke | Hydratation | 5 | 4 | Prévention déshydratation et hyponatrémie sur marathon. |

**Variables nouvelles introduites :**
- `CHO_intake_g_per_hour` — apport glucidique en course (g/h)
- `race_duration_estimated_min` — durée estimée de la course (conditionne le besoin nutritionnel)
- `glycogen_status` = "loaded" / "depleted" — disponibilité énergétique (Train-Low)
- `sweat_rate_ml_per_hour` — taux de sudation (V2, nécessite test)
- `hydration_protocol` — plan de ravitaillement (optionnel)

---

### 2.6. Pacing & Tactique — 3 sources

| Auteur | Sous-thème | Autorité | Priorité IA | Concepts clés extraits |
|--------|-----------|----------|-------------|------------------------|
| Carl Foster | Stratégies d'allure | 5 | **5** | Negative split / even split = meilleures stratégies empiriquement sur 42,195 km. |
| Samuele Marcora | RPE & Modèle psychobiologique | 5 | 4 | RPE et fatigue mentale comme régulateurs primaires de l'allure en course. |
| Ross Tucker | Ajustement thermique | 5 | 4 | Régulation anticipée de l'allure selon température ambiante ; risque hyperthermie. |

**Variables nouvelles introduites :**
- `target_marathon_pace_min_km` — allure cible marathon (essentiel MVP)
- `pace_first_half` / `pace_second_half` — analyse du pacing en course
- `split_ratio` = pace_first / pace_second — indicateur de gestion de l'effort
- `RPE_during_race` — RPE mesuré pendant la course
- `mental_fatigue_pre_race` — fatigue cognitive pré-course (Marcora)
- `ambient_temperature_C` — température ambiante jour de course
- `pace_adjustment_heat_pct` — facteur de correction allure en chaleur (Tucker)

---

## 3. Relations entre variables (nouvelles de Source 3)

```
VMA + temps_semi → target_marathon_pace (prédiction allure)
VT1_pace / VT2_pace + zone_distribution → session intensity prescription
zone_2_pct élevé + fatigue croissante → redistribuer vers Z1 + Z3 (Seiler)

session_RPE × session_duration → internal_load_session
Σ(internal_load_session sur 7j) / Σ(internal_load sur 28j) → ACWR_internal

CTL + ATL → TSB (forme du jour) [Banister, V2]
TSB bas + fatigue élevée → réduire charge
TSB positif élevé + compétition proche → signal de pic de forme

taper_week_flag == True → block_increase interdit (confirme RULE_TAPER Source 2)
special_block_flag == True → augmentation charge tolérée temporairement (Canova)

ambient_temperature_C > 20°C → pace_adjustment_heat_pct (−4 à −8%)
race_duration_estimated_min > 90min → CHO_intake_protocol requis
pace_first_half > target + 5% → risque de blow-up (Foster)
```

---

## 4. Correspondances avec Sources 1 & 2

| Variables Source 3 | Nœud Source 1 | Règle Source 2 | Apport de Source 3 |
|---------------------|---------------|----------------|-------------------|
| ACWR (Gabbett) | K7 | RULE_ACWR_DANGER, RULE_ACWR_HIGH | **Confirme** les seuils 1.5 / 2.0 — source primaire |
| sRPE / internal_load (Foster) | K7, K12 | `weekly_internal_load` field | **Confirme** la méthode de calcul de charge interne |
| Zone distribution (Seiler) | K11 | — | **Opérationnalise** K11 : ratios Z1/Z2/Z3 définis |
| Tapering (Mujika) | K1 | RULE_TAPER_NO_INCREASE | **Précise** : −40–60% volume, 2–3 semaines |
| HRV (Altini) | K6 | `HRV_index` (V2) | **Confirme** pertinence V2, baseline nécessaire |
| CTL/ATL/TSB (Banister) | K7 | V2 extension ACWR | **Extension V2** du modèle de charge |
| Overreaching (Mujika) | K6, K12 | RULE_FATIGUE_SLEEP_RED | **Élargit** : distinction fonctionnel / non-fonctionnel |
| Pacing (Foster) | K13 | — | **Précise** K13 : negative/even split comme stratégie optimale |
| VMA / allures seuil (Billat) | K2, K4 | — | **Remplit gap Source 1** : prédiction allure marathon |
| CHO racing (Jeukendrup) | — | — | **Nouveau domaine** : non couvert par Sources 1 & 2 |
| Thermique / météo (Tucker) | K13 | — | **Enrichit** K13 : ajustement allure par température |

> Note : **K15** (référencé dans Source 1, jamais défini) reste introuvable dans Source 3. Probablement une référence à un nœud de connaissance sur les pathologies connues / contre-indications médicales.

---

## 5. Variables manquantes importantes

### Indispensables MVP

| Variable | Justification | Source couvrant ce besoin |
|----------|--------------|--------------------------|
| `VMA` (vitesse maximale aérobie) | Base de tout calcul d'allure d'entraînement | Billat (Source 3) |
| `target_marathon_pace_min_km` | Sans allure cible, aucune prescription de séance n'est possible | Foster Pacing (Source 3) |
| `recent_race_time_10k` / `recent_race_time_half` | Prédiction de performance et calibration des zones | Sources 1 & 3 (gap confirmé) |
| `zone_distribution_weekly` | Vérifier que l'athlète ne passe pas trop de temps en Z2 | Seiler (Source 3) |

### Utiles V2

| Variable | Justification |
|----------|--------------|
| `CTL` / `ATL` / `TSB` | Modèle Banister plus fin que ACWR simple |
| `HRV_baseline` + `HRV_daily` | Récupération objective sans questionnaire |
| `lactate_mmol` | Modèle norvégien (Bakken) — précision seuils |
| `race_time_marathon_previous` | Historique performance marathons passés |
| `ambient_temperature_race_day` | Ajustement allure (Tucker) |

### Intéressants mais non nécessaires

| Variable | Justification |
|----------|--------------|
| `running_cadence_spm` | Économie de course (Moore, priorité 3) |
| `vertical_oscillation_cm` | Biomécanique — données montre requises |
| `CHO_intake_g_per_hour` | Nutrition en course — hors moteur de charge |
| `sweat_rate_ml_per_hour` | Test de sudation nécessaire |
| `mental_fatigue_pre_race` | Marcora — difficile à mesurer objectivement |

---

## 6. Limites des données

| Variable / domaine | Limite | Risque |
|-------------------|--------|--------|
| `VMA` | Requiert test effort maximal (terrain ou labo) — non auto-déclarable | Valeur estimée incorrecte → toutes les zones fausses |
| `zone_distribution` | Nécessite montre avec capteur FC ou pace — pas toujours disponible | Distribution inestimable sans données GPS/FC |
| `lactate_mmol` (Bakken) | Test sanguin invasif, inaccessible au grand public | Modèle inapplicable sans équipement spécialisé |
| `CTL/ATL/TSB` (Banister) | Nécessite historique long et charge correctement mesurée | Modèle instable si historique < 6 semaines |
| `HRV_daily` | Montre compatible requise + protocole de mesure standardisé | Baseline faussée si mesure irrégulière |
| `CHO_intake` / `sweat_rate` | Très difficile à mesurer en conditions réelles sans protocole dédié | Conseil nutritionnel générique seulement |
| `ambient_temperature` / pacing | Ajustement possible en course seulement — pas en planification | Pertinent J-day, pas en amont |
| Sources podcast / conférence (Seiler, Canova) | Moins reproductibles que les articles peer-reviewed | Concepts validés mais protocoles moins formalisés |
| `performance_trend` (Source 2) | "declining" / "improving" — comment calculé ? Pas défini | Source 3 confirme ce gap : aucune formule fournie |

---

## 7. Priorité d'intégration — synthèse

### Priorité 5/5 (intégrer MVP ou V1)

| Source | Concept central | Action recommandée |
|--------|----------------|-------------------|
| Seiler (distribution) | 80/20 rule + Z1/Z2/Z3 | Ajouter `zone_distribution` dans le monitoring |
| Seiler (zones) | Modèle 3 zones, VT1 | Définir les seuils par zone dans le profil athlète |
| Gabbett (ACWR) | ACWR 1.5 / 2.0 | **Déjà dans Source 2** — confirmer les seuils |
| Foster (sRPE) | internal_load = RPE × durée | **Déjà dans Source 2** — confirmer la méthode |
| Mujika (surmenage) | Overreaching fonctionnel vs non-fonctionnel | Ajouter flag `overreaching_suspected` |
| Mujika (tapering) | −40–60% volume, 2–3 semaines | Préciser les règles RULE_TAPER |
| Canova (marathon spécificité) | Funnel System, Special Blocks | Ajouter `marathon_pace_sessions_per_week` |
| Bakken (double threshold) | Norwegian model — avancé | V1 si profil intermédiaire/avancé |
| Jeukendrup (CHO) | 60–90 g/h, mix glucose/fructose | Nouveau module : nutrition course |
| Foster (pacing) | Negative split optimal | Règle pacing K13 : ajouter seuil first-half |

### Priorité 4/5 (intégrer V2)

Billat (VMA), Altini (HRV), Banister (CTL/ATL), Dubois (stress mécanique), Cook (tendinopathies), Stellingwerff (nutrition périodisée), Burke (hydratation), Marcora (RPE modèle psychobiologique), Tucker (ajustement thermique).

### Priorité 3/5 (optionnel ou V3)

Issurin (block periodization), Moore (économie de course / cadence).
