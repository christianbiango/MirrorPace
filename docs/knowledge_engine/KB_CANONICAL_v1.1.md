# Knowledge Base Canonique — Coach Marathon IA — v1.1

> Version : 1.1 (audit + corrections)
> Statut : fondation révisée, prête à être transformée en moteur décisionnel
> Version parente : v1.0 (docs/knowledge_engine/KB_CANONICAL.md)
> Sources fusionnées : Source 1 (Perplexity cartographie), Source 2 (Perplexity décisionnel), Source 3 (Gemini bibliographie)
> Scope : modélisation des connaissances — aucun code, aucune API, aucun algorithme final
> Nature des changements v1.0 → v1.1 : voir Section 11 (Changelog)

---

## 0. Cadre d'audit — méthodologie de classification

Cette section est nouvelle en v1.1. Elle définit **comment lire** la KB pour éviter que la couche implémentation confonde un fait scientifique, un paramètre configurable et une décision produit.

### 0.1. Classification épistémique (niveau de preuve)

Chaque concept, variable, règle et modèle est étiqueté avec l'un des trois niveaux suivants :

| Étiquette | Signification | Comportement attendu dans le moteur |
|-----------|--------------|-------------------------------------|
| **[SCI]** Preuve scientifique solide | Méta-analyses, RCT, consensus international documenté. | Peut être présenté à l'utilisateur comme un fait. Modifiable uniquement par revue de littérature. |
| **[PRAT]** Consensus pratique / expert | Utilisé par la profession, mais preuve limitée ou controversée. | À traiter comme une **heuristique de sécurité** — pas comme une vérité. Modifiable avec justification. |
| **[PROD]** Décision produit / heuristique MVP | Choix de design du coach IA, absent des sources ou non validé. | **Paramétrable en config**. Doit être révisable sans toucher au code métier. |

### 0.2. Séparation science / paramètre / décision produit

| Nature | Exemple | Où le stocker |
|--------|---------|--------------|
| **Fait scientifique** | "L'ACWR est le ratio charge aiguë 7j / charge chronique 28j" | Constante métier (`concepts.py`) |
| **Paramètre configurable** | Seuil ACWR de blocage = 1.5 | Fichier de config (`thresholds.yaml`) — révisable sans redéploiement |
| **Règle métier choisie pour le MVP** | "Cap +5% pour beginner" | Règle explicite, taguée `[PROD]`, dans le rules engine |

**Principe directeur (nouveau v1.1) :** aucune règle du moteur décisionnel ne doit contenir de constante numérique en dur. Tous les seuils (1.5, 2.0, 10%, 4 semaines, +5%, +10%) sont des **paramètres**, pas des faits.

### 0.3. Niveau de confiance opérationnelle (nouveau)

Distinct du niveau de preuve. Mesure la fiabilité du **signal d'entrée** en pratique (auto-déclaration, données manquantes, etc.).

| Niveau | Signification |
|--------|--------------|
| **Fort** | Donnée objective ou dérivée mécanique (distance GPS, temps de course). |
| **Moyen** | Auto-déclaration avec échelle bien définie, biais connus. |
| **Faible** | Auto-déclaration subjective non standardisée, ou variable V2 non-mesurée en V1. |

Chaque règle en Section 4 porte désormais **deux annotations** : `preuve = [SCI|PRAT|PROD]` et `signal = [Fort|Moyen|Faible]`. Une règle P0 (override absolu) ne devrait jamais reposer sur un signal Faible — c'est un des critères d'audit appliqués.

---

## 1. Concepts métier fondamentaux

Colonnes ajoutées v1.1 : **Type** (science/produit) et **Niveau de preuve**.

| ID | Nom normalisé | Définition | Domaine | Rôle | Type | Preuve | Sources |
|----|--------------|-----------|---------|------|------|--------|---------|
| C-001 | **Charge d'entraînement** | Quantité de travail : volume externe (km, durée, dénivelé) + charge interne (session-RPE = RPE × durée). | Charge | Entrée centrale du moteur. | Science | [SCI] | S1:K7, S2, S3:Foster/Gabbett |
| C-002 | **ACWR** (Acute:Chronic Workload Ratio) | Ratio charge 7 derniers jours / moyenne 28 derniers jours. **Note critique v1.1** : le modèle a été contesté (Impellizzeri 2019, Wang 2020) pour colinéarité num/dénom et taux élevé de faux positifs. Reste utile comme **garde-fou heuristique**, pas comme prédicteur unique. | Charge | Règle de décision de volume. | Science + heuristique | [PRAT] (nuancé — voir modèles) | S1:K7, S2, S3:Gabbett |
| C-003 | **Récupération** | Capacité à absorber la charge, évaluée via fatigue perçue, sommeil, douleurs et (V2) HRV. Dimension multifactorielle. | Récupération | Blocage et cap d'augmentation. | Science | [SCI] | S1:K6, K12, S2, S3:Mujika/Altini |
| C-004 | **Périodisation** | Organisation en phases (générale → spécifique → affûtage). | Planification | Structure la prescription. | Science | [SCI] | S1:K1, K3, S2, S3:Mujika/Canova/Issurin |
| C-005 | **Distribution d'intensité** | Répartition du temps entre zones physiologiques (Z1/Z2/Z3). | Intensité | Qualité de la charge. | Science + choix produit (proxy zones) | [SCI] modèle / [PROD] proxy | S1:K11, S3:Seiler |
| C-006 | **Profilage coureur** | Caractérisation niveau, expérience, objectif, santé. | Profilage | Calibre seuils et caps. | Produit (segmentation) | [PROD] | S1:K2, K9, S2 |
| C-007 | **Progressivité** | Augmentation contrôlée. Seuil empirique +10%/sem. | Progression | Sécurité de progression. | Heuristique historique | [PRAT] (voir modèles) | S1:K3, K7, S2 |
| C-008 | **Risque de blessure** | Probabilité d'une lésion en fonction de charge, douleurs, historique, stress mécanique. | Sécurité | Déclencheur des hard rules. | Science + heuristique | [SCI] (concept) / [PRAT] (opérationnalisation) | S1:K9, S2, S3:Gabbett/Dubois/Cook |
| C-009 | **Performance** | Capacité de course (temps références 5/10k/semi/marathon, VMA). | Performance | Calibre objectif, zones, prédiction. | Science | [SCI] | S1:K2, K4, K13, S2, S3:Billat/Foster |
| C-010 | **Affûtage (Tapering)** | Réduction volume −40–60%, maintien intensité, 2–3 sem avant course. | Planification | Déclenche règle de décharge en taper. | Science | [SCI] (méta-analyses Mujika) | S1:K1, S2, S3:Mujika |
| C-011 | **Allure marathon / Pacing** | Vitesse cible marathon, négative/even split. | Performance | Ancre les séances spécifiques. | Science | [SCI] | S1:K13, S3:Foster/Billat |
| C-012 | **Readiness** | Capacité globale à absorber une charge supplémentaire. **Score composite 0–100.** | Décision | Sortie centrale du moteur. | Produit (composition) | [PROD] (composition) — les composants sont [SCI]/[PRAT] | S1:K6, K8, S2 |

**Concept ajouté v1.1 :**

| ID | Nom normalisé | Définition | Domaine | Rôle | Type | Preuve | Sources |
|----|--------------|-----------|---------|------|------|--------|---------|
| C-013 | **Sortie longue (Long Run)** | Séance hebdomadaire de plus longue durée, distincte du volume total. Signal marathon-spécifique. | Charge / spécificité marathon | Suivi d'adaptation aux longues distances ; jamais bloquée par la règle des 10% seule. | Science | [SCI] | S1:K1, S3:Canova/Daniels (à documenter) |

**Justification C-013 :** la KB v1.0 traite `weekly_distance_km` comme unique métrique de volume, ce qui masque totalement la progression de la sortie longue (fondamentale en préparation marathon). Deux coureurs à 40 km/sem n'ont pas le même risque si l'un fait 4×10 km et l'autre 1×25 km + 3×5 km.

---

## 2. Dictionnaire canonique des variables

### 2.1. Variables MVP — entrée directe utilisateur

| Nom canonique | Définition | Type | Unité | Origine | Rôle | Signal | Concepts | Statut v1.1 |
|---------------|-----------|------|-------|---------|------|--------|----------|-------------|
| `weekly_distance_km` | Distance totale semaine courante | Numérique | km | S2 | Entrée | Fort | C-001, C-002 | inchangé |
| `previous_week_distance_km` | Distance semaine précédente | Numérique | km | S2 | Entrée | Fort | C-002, C-007 | inchangé |
| `weekly_distance_history` | Tableau 1–8 semaines précédentes | Array[float] | km/sem | S2 | Entrée | Fort | C-002 | **Précision** : minimum 4 entrées requis pour ACWR fiable, sinon marquer `acwr_reliable = false` |
| `weekly_duration_min` | Durée totale semaine | Numérique | min | S2 | Entrée | Fort | C-001 | inchangé |
| `long_run_km_last_week` | **[NOUVEAU v1.1]** Distance de la plus longue sortie de la semaine | Numérique | km | Ajout audit | Entrée | Fort | C-001, C-013 | **Ajouté** |
| `avg_weekly_RPE` | RPE moyen pondéré 0–10 | Numérique | — | S1/S2 | Entrée | Moyen | C-001 | **Signal dégradé** : auto-déclaration agrégée peu fiable |
| `fatigue_score` | Fatigue perçue **1=très faible → 5=extrême** | Numérique | 1–5 | S2 | Entrée | Moyen | C-003, C-012 | **Sens conservé** |
| `sleep_quality_score` | **[CORRIGÉ v1.1]** Qualité sommeil **1=très mauvaise → 5=excellente** (sens inversé par rapport à v1.0 pour cohérence avec `fatigue_score`) | Numérique | 1–5 | S2 | Entrée | Moyen | C-003, C-012 | **CHANGEMENT BREAKING** — voir Section 11 |
| `pain_regions` | Tableau `[{region, intensity 0–5, days_persistent}]` | Array[object] | — | S2 | Entrée | Moyen | C-008 | **Précision** : voir enum ci-dessous |
| `pain_regions[].region` | **[NOUVEAU v1.1]** Enum explicite : `achilles / knee / shin / hip / foot / calf / hamstring / lower_back / other` | Enum | — | Ajout audit | Entrée | Moyen | C-008 | **Ajouté** (référencé par RULE-002 mais jamais défini en v1.0) |
| `experience_level` | `beginner / intermediate / advanced` | Catégorielle | enum | S2 | Entrée | Fort (déclaratif) | C-006 | **Critères à définir** — voir CONF-002 |
| `current_phase` | `general / specific_marathon / taper / return_from_injury / off_season` | Catégorielle | enum | S2 | Entrée | Fort (déclaratif) | C-004, C-010 | inchangé |
| `weeks_since_last_injury` | Semaines depuis dernière blessure | Entier | sem | S2 | Entrée | Fort | C-008 | inchangé |
| `days_since_last_run` | **[NOUVEAU v1.1]** Jours depuis la dernière séance courue | Entier | jours | Ajout audit | Entrée | Fort | C-007, C-008 | **Ajouté** — détecte interruptions non déclarées |
| `weeks_to_race` | Semaines avant course cible (null si aucune) | Entier / null | sem | S1/S2 | Contextuelle | Fort | C-004, C-010 | inchangé |
| `sessions_per_week_available` | Contrainte calendrier | Entier | — | S1 | Entrée | Fort | C-004 | inchangé |
| `recent_race_time_10k` | Temps 10 km récent | Numérique | sec | S1/S3 | Entrée | Fort | C-009, C-011 | inchangé |
| `recent_race_time_half` | Temps semi récent | Numérique | sec | S1/S3 | Entrée | Fort | C-009, C-011 | inchangé |
| `VMA_kmh` | VMA estimée/testée | Numérique | km/h | S3:Billat | Entrée ou calculée | Moyen | C-005, C-009, C-011 | inchangé |
| `race_target_time` | **[NOUVEAU v1.1]** Objectif chrono marathon (null si aucun) | Numérique / null | sec | Ajout audit | Entrée | Fort | C-011 | **Ajouté** — nourrit `target_marathon_pace` |

### 2.2. Variables calculées (dérivées des entrées)

| Nom canonique | Calcul | Type | Unité | Concepts | Statut v1.1 |
|---------------|--------|------|-------|----------|-------------|
| `chronic_load_distance` | Moyenne `weekly_distance_history` (fenêtre 4 sem) | Numérique | km | C-001, C-002 | **Décision produit à confirmer** : moyenne simple vs EWMA (CONF-001) |
| `ACWR_distance` | `weekly_distance_km / chronic_load_distance` | Numérique | ratio | C-002, C-008 | **Ajout** : marquer `acwr_reliable = (len(history) >= 4)` |
| `delta_volume_pct` | (`weekly_distance_km` − `previous_week_distance_km`) / `previous_week_distance_km` × 100 | Numérique | % | C-007 | **Garde nouveau** : ignorer si `previous_week_distance_km < seuil_min_pertinence` (voir CONF-013) |
| `delta_long_run_pct` | **[NOUVEAU v1.1]** (long_run cette sem − long_run sem précédente) / long_run sem précédente × 100 | Numérique | % | C-013 | **Ajouté** — progression sortie longue |
| `weekly_internal_load` | `avg_weekly_RPE` × `weekly_duration_min` | Numérique | UA | C-001 | **⚠️ Faible fiabilité** — RPE agrégé hebdo n'est pas un session-RPE au sens Foster. À réévaluer en V2 avec RPE par séance. |
| `readiness_score` | Score composite 0–100 (voir Section 3) | Numérique | 0–100 | C-012 | **Décision produit** — voir Section 3 mise à jour |
| `target_marathon_pace_min_km` | Dérivé de `recent_race_time_half`, `VMA_kmh` ou `race_target_time` (formule Section 8, arbitrage requis) | Numérique | min/km | C-011 | Formule à figer |
| `zone_distribution` | % temps Z1/Z2/Z3 sur la semaine | Object | % | C-005 | **RECLASSÉ V2** (voir Section 7) — nécessite proxy fiable |
| `fatigue_trend` | Tendance `fatigue_score` sur 3–4 dernières semaines | Catégorielle | improving/stable/worsening | C-003 | inchangé |

### 2.3. Variables V2 (nécessitent capteurs, historique long ou tests spécialisés)

| Nom canonique | Justification du report | Source scientifique |
|---------------|------------------------|---------------------|
| `HRV_daily` / `HRV_baseline` / `HRV_trend` | Montre compatible + protocole standardisé | S3:Altini |
| `resting_HR_morning` / `resting_HR_baseline` | Données montre quotidiennes | S2 |
| `CTL` / `ATL` / `TSB` | Historique ≥ 6 sem + charge précise | S3:Banister |
| `performance_trend` | Formule non définie — nécessite arbitrage (CONF-008) | S2 |
| `lactate_mmol` | Test sanguin invasif — inaccessible grand public | S3:Bakken |
| `ambient_temperature_C` | Pertinent J-day uniquement | S3:Tucker |
| `marathon_pace_sessions_per_week` | Suivi granulaire des séances spécifiques | S3:Canova |
| `mental_fatigue_pre_race` | Mesure objective difficile | S3:Marcora |
| `zone_distribution` | **[RECLASSÉ V2 v1.1]** Nécessite données FC/GPS par séance + proxy zones défini (RPE ou %VMA — CONF-010) | S3:Seiler |
| `session_rpe_per_workout` | **[NOUVEAU V2 v1.1]** RPE par séance individuelle — permet vrai session-RPE Foster | S3:Foster |

### 2.4. Variables contextuelles (non utilisées dans les règles)

| Nom canonique | Usage | Concepts |
|---------------|-------|----------|
| `age` | Filtre de sécurité profil | C-006 |
| `pathologies_connues` | Contre-indication — recommandation médicale | C-008 |
| `terrain_type` | Modifie stress mécanique (trail > route) | C-008 |
| `preferences_communication` | Couche UX | — |
| `feedback_qualitatif` | Enrichit évaluation sans décision directe | C-003 |
| `mood_motivation_score` | **[NOUVEAU v1.1 — CONF-006 résolu]** Reclassé en contextuelle V1 (non-décisionnel). Peut moduler le ton de l'explication LLM. | C-003, C-012 |

### 2.5. Variables retirées du MVP (nouveau v1.1)

Aucune suppression brutale. Les variables ci-dessous, présentes ou implicites en v1.0, sont **explicitement décalées** :

| Variable | Statut v1.0 | Statut v1.1 | Raison |
|----------|-------------|-------------|--------|
| `weekly_internal_load` | MVP calculée | **MVP dégradée** (annoter `low_confidence = true`) | RPE hebdo agrégé ≠ session-RPE Foster |
| `zone_distribution` | MVP calculée + utilisée en RULE-014 et ÉTAT-5 | **V2** | Nécessite proxy zones défini (CONF-010) |
| `performance_trend` | V2 mais utilisée en RULE-013 | **V2, RULE-013 désactivée en V1** | Formule non définie (CONF-008) |

---

## 3. États internes du coureur

**Correction v1.1 majeure** : les poids du `readiness_score` doivent sommer à 100 explicitement. En v1.0 les poids déclarés ne totalisent que 70 (Récupération 35 + Charge 35), sans indication de la répartition des 30 restants. La v1.1 fixe la somme.

### 3.0. Composition du `readiness_score` (0–100)

| État | Poids v1.1 | Justification |
|------|-----------|--------------|
| ÉTAT-1 Récupération | 35 | Réactivité rapide, signal direct de l'utilisateur |
| ÉTAT-2 Charge | 35 | Base scientifique la plus solide (charge externe objective) |
| ÉTAT-3 Progression | 15 | Signal moyen terme |
| ÉTAT-4 Risque blessure | (n'entre pas dans le score — override P0) | Voir note ci-dessous |
| ÉTAT-5 Préparation marathon | 15 | Contexte de planification |
| **Ajustements P3** | ±10 max (bornés) | RULE-011/012/013/014 |

**Note sur ÉTAT-4** : le risque blessure ne doit pas être dilué dans un score continu. En cas de signal fort (douleur ≥ seuil), il déclenche P0 et court-circuite le score. Le score `readiness_score` ne reflète donc pas le risque blessure — il reflète la marge disponible **une fois la sécurité validée**.

### ÉTAT-1 : Récupération (poids 35)

| Variables | Poids intra-état | Méthode |
|-----------|------------------|---------|
| `fatigue_score` | 15/35 | Linéaire inverse (1→15 pts, 5→0 pts) |
| `sleep_quality_score` | 10/35 | Linéaire **directe** (1→0 pts, 5→10 pts) — **cohérent avec le nouveau sens 1=mauvaise, 5=excellente** |
| `pain_regions` | 10/35 | Inverse de l'intensité maximale (0→10 pts, 5→0 pts) |

**V2 :** `HRV_trend`, `resting_HR_morning`
**Signal :** Moyen (auto-déclaration).
**Type :** [PROD] pour la composition, [SCI] pour les variables.

### ÉTAT-2 : Charge (poids 35)

| Variables | Poids intra-état | Méthode |
|-----------|------------------|---------|
| `ACWR_distance` | 20/35 | Courbe en cloche (optimum 0.8–1.3) — **[PROD]** paramétrable |
| `delta_volume_pct` | 10/35 | Pénalité si >10% |
| `chronic_load_distance` | 5/35 | Bonus si volume suffisant pour la phase |

**Signal :** Fort.
**Type :** [PRAT] — voir modèle ACWR contesté.
**Précaution v1.1 :** si `acwr_reliable = false` (< 4 semaines d'historique), retomber sur `delta_volume_pct` seul et abaisser le poids ACWR à 0.

### ÉTAT-3 : Progression (poids 15)

| Variables | Méthode |
|-----------|---------|
| `weekly_distance_history` | Pente de régression linéaire |
| `delta_volume_pct` | Variation semaine/semaine |
| `delta_long_run_pct` **[NOUVEAU v1.1]** | Progression de la sortie longue |
| `performance_trend` (V2) | Désactivé en V1 |

**Signal :** Fort (données objectives).
**Type :** [SCI].

### ÉTAT-4 : Risque blessure (n'entre pas dans le score — déclenche P0)

| Variables | Signal |
|-----------|--------|
| `pain_regions[].intensity` + `.days_persistent` | Hard rule → deload (RULE-001/002) |
| `weeks_since_last_injury` | Cap d'augmentation si < 4 semaines |
| `ACWR_distance` | Risque si > 1.5 (bloc), ≥ 2.0 (deload) |
| `delta_volume_pct` | Risque si > 10% |
| `days_since_last_run` **[NOUVEAU v1.1]** | Si > 14 jours, retour progressif imposé — cap +10% et pas de sortie longue augmentée |

**Signal :** Moyen à Fort selon la variable.
**Type :** [SCI] concepts, [PROD] seuils.

### ÉTAT-5 : Préparation marathon (poids 15)

| Variables | Signal |
|-----------|--------|
| `current_phase` | Phase cohérente avec `weeks_to_race` ? |
| `weeks_to_race` | Proximité de la course |
| `readiness_score` | Score global (référence circulaire à surveiller) |
| `target_marathon_pace_min_km` | Allure cible validée ? |
| `race_target_time` **[NOUVEAU v1.1]** | Cohérence objectif / performances récentes |

**Note v1.1 :** `zone_distribution` retiré de cet état (reclassé V2). En V1, ÉTAT-5 s'appuie sur la cohérence de phase et l'existence d'une allure cible.
**Signal :** Moyen.
**Type :** [PROD] majoritairement.

---

## 4. Règles métier canonisées

### Convention de priorité (inchangée v1.0, clarifiée v1.1)

- **P0 — Override absolu** : deload forcé, ignore tout le reste.
- **P1 — Blocage / Décrément forcé** : décision max = `maintain` (ou `decrease` selon règle).
- **P2 — Cap** : plafonne le % d'augmentation (min des caps si plusieurs).
- **P3 — Score** : ajuste `readiness_score`, jamais la décision brute.
- **P4 — Planification** : structure du plan sur plusieurs semaines.

**Précision v1.1 (résolution CONF-009)** : conflit P1 + P2 → **P1 gagne**. Le cap est ignoré ; la décision devient `maintain`, pas `capped_increase`. Cette règle est marquée **[PROD]**.

---

### P0 — Override absolu (deload forcé)

| ID | SI condition | ALORS | Sources | Preuve | Signal | Confiance globale | Seuils à surveiller |
|----|-------------|-------|---------|--------|--------|-------------------|---------------------|
| RULE-001 | `pain_regions` contient `intensity ≥ 4` ET `days_persistent ≥ 2` (toute région) | Deload forcé. Conseil consultation médicale. | S2 + S3:Cook/Dubois | [SCI] concept / [PROD] seuils exacts | Moyen (auto-déclaré) | **Forte** | Subjectivité — chartre douleur à documenter |
| RULE-002 | `pain_regions.region ∈ {achilles, knee, shin, hip, foot}` ET `intensity ≥ 3` ET `days_persistent ≥ 3` | Deload forcé. Risque tendinopathie / stress fracture. | S2 + S3:Cook | [SCI] concept / [PROD] seuils | Moyen | **Forte** | Voir enum `pain_regions[].region` en Section 2 |
| RULE-003 | `ACWR_distance ≥ 2.0` **ET** `acwr_reliable = true` | Deload forcé. Charge aiguë 2× la normale. | S2 + S3:Gabbett | [PRAT] (voir modèle ACWR contesté) | Fort | **Moyenne-Forte** (dégradée v1.1) | ACWR moyenne simple — voir CONF-001 |

**Changement v1.1 sur RULE-003 :** ajout du garde `acwr_reliable`. Un ACWR sur 2 semaines d'historique n'est pas un ACWR — il ne doit pas forcer un deload.

**Reclassé en P1 (voir ci-dessous) :** aucune règle P0 supplémentaire. Le principe : P0 ne se déclenche que sur signaux **redondants et graves**, jamais sur un signal isolé auto-déclaré faible.

---

### P1 — Blocage / Décrément forcé

| ID | SI condition | ALORS | Sources | Preuve | Signal | Confiance | Seuils |
|----|-------------|-------|---------|--------|--------|-----------|--------|
| RULE-004 | `1.5 < ACWR_distance < 2.0` ET `acwr_reliable = true` | Décision max = `maintain`. | S2 + S3:Gabbett | [PRAT] | Fort | **Moyenne-Forte** | Idem RULE-003 |
| RULE-005 | `delta_volume_pct > 10%` ET `previous_week_distance_km ≥ seuil_min_pertinence` (paramètre, par défaut 20 km — décision produit) | Décision max = `maintain`. Règle des 10%. | S1:K7 + S2 | [PRAT] (règle historique non prouvée par RCT) | Fort | **Moyenne** (dégradée v1.1) | Garde petits volumes ajouté — voir CONF-013 |
| RULE-006 | (`fatigue_score ≥ 4` ET `sleep_quality_score ≤ 2`) **OU** `fatigue_score == 5` | Décision max = `maintain`. Récupération insuffisante. | S1:K6, K12 + S2 | [SCI] concept / [PROD] seuils | Moyen | **Forte** (logique corrigée) | Note v1.1 : sleep échelle inversée + fatigue extrême seule suffit |
| RULE-007 | **[CORRIGÉE v1.1]** `current_phase == "taper"` | **Forcer `decrease`** (pas seulement bloquer l'augmentation). Volume −40 à −60% sur 2–3 semaines. | S1:K1 + S2 + S3:Mujika | [SCI] (Mujika méta-analyses) | Fort | **Forte** | Cohérence avec RULE-021 rétablie |
| RULE-026 | **[NOUVEAU v1.1]** `days_since_last_run > 14` | Décision max = `maintain`. Retour progressif imposé (aucune augmentation autorisée la première semaine). | Ajout audit | [PROD] | Fort | **Moyenne** | Seuil 14 jours paramétrable |

**Changement critique v1.1 sur RULE-007** : en v1.0 elle bloquait juste l'augmentation, ce qui laissait l'utilisateur maintenir un volume complet en taper — contraire à Mujika. Rétablissement du forçage à `decrease`.

**Changement v1.1 sur RULE-006** : le "ET" logique de v1.0 laissait passer une fatigue extrême isolée. Passage à une logique en OR avec un cas de fatigue extrême seule.

---

### P2 — Cap (plafonnement de l'augmentation)

| ID | SI condition | ALORS | Sources | Preuve | Signal | Confiance | Seuils |
|----|-------------|-------|---------|--------|--------|-----------|--------|
| RULE-008 | `weeks_since_last_injury < 4` | Cap +5% max | S2 | [PROD] (seuil arbitraire) | Fort | **Faible-Moyenne** (dégradée v1.1) | Seuil 4 sem arbitraire — CONF-005 |
| RULE-009 | `fatigue_score == 3` OU `sleep_quality_score == 3` | Cap +5% max | S2 | [PROD] | Moyen | **Moyenne** | Frontière 3/4 floue |
| RULE-010 | `experience_level == "beginner"` | Cap +5% max | S1:K3 + S2 | [PROD] | Fort (déclaratif) | **Moyenne** | Critères beginner non définis — CONF-002 |

**Précision résolution des conflits P1+P2** : voir Section 4 en-tête (P1 gagne, cap ignoré). Marquage **[PROD]**.

---

### P3 — Ajustements de score (readiness_score, ± bornés à ±10 en cumul)

| ID | SI condition | ALORS | Sources | Preuve | Signal | Confiance |
|----|-------------|-------|---------|--------|--------|-----------|
| RULE-011 | `0.8 ≤ ACWR_distance ≤ 1.3` ET `fatigue_score ≤ 2` ET `sleep_quality_score ≥ 4` ET `max(pain_regions[].intensity) ≤ 2` | +10 pts readiness | S2 | [PROD] composition | Moyen | **Forte** |
| RULE-012 | `experience_level == "advanced"` ET `0.8 ≤ ACWR_distance ≤ 1.3` | +5 pts readiness | S2 | [PROD] | Fort | **Moyenne** |
| RULE-013 | **[DÉSACTIVÉE V1 v1.1]** `performance_trend == "declining"` ET `ACWR_distance ≥ 1.0` | −10 pts readiness | S2 | [PROD] | Faible (V2) | **N/A en V1** — voir CONF-008 |
| RULE-014 | **[DÉSACTIVÉE V1 v1.1]** `zone_distribution.Z2_pct élevé` ET `fatigue_trend == "worsening"` | −5 pts readiness | S3:Seiler | [PROD] heuristique | Faible (V2) | **N/A en V1** — `zone_distribution` V2 |

**Changement v1.1 sur RULE-011** : la référence `pas de douleur > 2` était floue. Clarifié : `max(pain_regions[].intensity) ≤ 2`. Le sens de `sleep_quality_score` est inversé (≥ 4 = bon sommeil, cohérent avec correction Section 2.1).

**Changement v1.1 sur RULE-013/014** : désactivées explicitement en V1 (au lieu de laisser courir sur des variables non définies). À réactiver quand `performance_trend` et `zone_distribution` seront formalisés en V2.

---

### P4 — Règles de planification (structure du plan)

Aucun changement de fond v1.0 → v1.1, sauf annotations preuve/signal.

| ID | SI condition | ALORS | Sources | Preuve | Signal | Confiance |
|----|-------------|-------|---------|--------|--------|-----------|
| RULE-015 | `weeks_to_race ≥ 16` ET volume régulier | Planifier phases générale → spécifique → taper | S1:K1 + S3:Canova | [SCI] | Fort | **Forte** |
| RULE-016 | `experience_level == "beginner"` ET volume faible | Cycle préparatoire général AVANT spécifique marathon | S1:K3 | [SCI] | Fort | **Forte** |
| RULE-017 | Profil + historique → plan faible/modéré/élevé | Sélectionner plan de volume adapté | S1:K4 | [PROD] segmentation | Fort | **Moyenne** |
| RULE-018 | `weeks_to_race` éloigné ET performances 5–10k en retard | Cycle vitesse/seuil avant spécifique marathon | S1:K5 | [SCI] | Moyen | **Moyenne** |
| RULE-019 | Objectifs incohérents (stagnation, blessure, contraintes) | Revisiter objectifs | S1:K8 | [PROD] | Moyen | **Forte** |
| RULE-020 | Séances clés manquées | Ajuster semaine suivante, ne pas rattraper | S1:K10 | [SCI] | Fort | **Moyenne** |
| RULE-021 | `current_phase == "taper"` | Volume −40–60%, maintien intensité, 2–3 semaines | S3:Mujika | [SCI] | Fort | **Forte** |
| RULE-022 | `recent_race_time_half` ou `VMA_kmh` ou `race_target_time` disponibles ET `target_marathon_pace` non défini | Calculer `target_marathon_pace_min_km` | S1:K13 + S3:Billat/Foster | [SCI] | Fort | **Forte** |

---

### P4 — Règles de gestion de course (jour J)

| ID | SI condition | ALORS | Sources | Preuve | Signal | Confiance |
|----|-------------|-------|---------|--------|--------|-----------|
| RULE-023 | `pace_first_half > target_marathon_pace + 5%` | Signal blow-up — ralentir | S1:K13 + S3:Foster | [SCI] | Fort | **Forte** |
| RULE-024 | `ambient_temperature_C > 20°C` (V2) | Ajuster `target_marathon_pace` (−4 à −8%) | S3:Tucker | [SCI] | Fort | **Forte** (V2) |
| RULE-025 | Durée estimée > 90 min | Protocole ravitaillement CHO (60–90 g/h) | S3:Jeukendrup | [SCI] | Fort | **Forte** |

---

## 5. Hiérarchie décisionnelle officielle (corrigée v1.1)

**Correction majeure v1.1** : le niveau 4 en v1.0 mélangeait règles P2 (caps) et P3 (score). La v1.1 réaligne strictement sur les priorités déclarées.

```
NIVEAU 1 — SÉCURITÉ (Override absolu — P0)
├── RULE-001 : douleur ≥ 4/5 pendant ≥ 2 jours → deload
├── RULE-002 : douleur tendon/articulaire ≥ 3/5 pendant ≥ 3 jours → deload
└── RULE-003 : ACWR ≥ 2.0 (fiable) → deload
    ↓ OVERRIDE ABSOLU — si déclenché, ignorer niveaux 2–5

NIVEAU 2 — BLOCAGE / DÉCRÉMENT (P1)
├── RULE-004 : 1.5 < ACWR < 2.0 → maintain
├── RULE-005 : Δvolume > 10% (volume ≥ seuil pertinence) → maintain
├── RULE-006 : fatigue extrême ou combo fatigue/sommeil → maintain
├── RULE-007 : phase taper → decrease (−40 à −60%)   ← corrigé v1.1
└── RULE-026 : interruption > 14 jours → maintain    ← nouveau v1.1
    ↓ Si déclenché → décision max = "maintain" (ou "decrease" pour RULE-007)

NIVEAU 3 — CAP (P2)
├── RULE-008 : blessure récente < 4 sem → cap +5%
├── RULE-009 : fatigue = 3 OU sommeil = 3 → cap +5%
└── RULE-010 : beginner → cap +5%
    ↓ Si plusieurs caps → min. Si niveau 2 déclenché → cap ignoré (P1 gagne).

NIVEAU 4 — AJUSTEMENT DE SCORE (P3, bornes ±10)
├── RULE-011 : feu vert multi-critères → +10 pts
├── RULE-012 : advanced + ACWR OK → +5 pts
├── RULE-013 : DÉSACTIVÉE V1 (variable V2 manquante)
└── RULE-014 : DÉSACTIVÉE V1 (variable V2 manquante)
    ↓ Ne modifie jamais la décision brute, uniquement le score.

NIVEAU 5 — PLANIFICATION & OPTIMISATION (P4)
├── RULE-015 à 022 : structure macro-plan
├── RULE-023 à 025 : gestion course
└── RULE-020 : gestion séances manquées
```

**Règles d'override (formalisation v1.1) :**
1. P0 déclenché → décision = `deload`, niveaux 2–5 ignorés.
2. P1 déclenché → décision max = `maintain` (ou `decrease` pour RULE-007). Caps P2 ignorés.
3. Plusieurs P2 → prendre le cap minimum.
4. P3 ne modifie jamais la décision brute, uniquement `readiness_score`.
5. P4 travaille sur l'horizon multi-semaines, orthogonal aux niveaux 1–4.

**Décision produit [PROD]** : ces règles d'override sont un choix de design, pas une science. Elles doivent être versionnées.

---

## 6. Modèles scientifiques associés (niveaux de preuve réévalués v1.1)

Colonne **Niveau de preuve** recalibrée. La v1.0 donnait 5/5 à presque tout ; la v1.1 distingue plus finement.

| Modèle | Auteur | Concept | Utilisation | Preuve v1.1 | Note critique v1.1 |
|--------|--------|---------|-------------|-------------|--------------------|
| **ACWR** | Gabbett (2016) | Ratio aiguë/chronique | RULE-003/004 | ★★★ [PRAT] | **Dégradé** — critique Impellizzeri 2019, Wang 2020 (colinéarité mathématique, faux positifs). Reste utile comme garde-fou heuristique, pas comme prédicteur validé. |
| **Session-RPE** | Foster (1998) | Charge interne = RPE × durée | `weekly_internal_load` | ★★★★★ [SCI] | Nécessite RPE **par séance** — pas la moyenne hebdo (correction v1.1) |
| **Polarized Training / 80-20** | Seiler (2010) | 80/20 basse/haute intensité | RULE-014 (V2), `zone_distribution` | ★★★★ [SCI] | Fort chez élites. Transposition amateurs moins claire — Stöggl/Sperlich mitigés. |
| **Tapering** | Mujika (2009, 2018) | −40–60% vol, 2–3 sem | RULE-007, RULE-021 | ★★★★★ [SCI] | Méta-analyses solides |
| **Surmenage / Overreaching** | Mujika (2018) | Fatigue fonctionnelle vs surentraînement | RULE-006, `fatigue_trend` | ★★★★★ [SCI] | Modèle qualitatif solide |
| **Spécificité marathon (Funnel)** | Canova | Special Blocks, spécificité croissante | RULE-015, C-013 | ★★★★ [PRAT] | Expérientiel élite, peu de RCT |
| **Double Threshold / Norvégien** | Bakken | 2 séances seuil/j au lactate | V2 avancé | ★★★★ [PRAT] | Excellent chez élites, non applicable MVP |
| **VVO2max / VMA** | Billat (1999) | Temps à VO2max, allures VMA/VT2 | `target_marathon_pace`, zones | ★★★★★ [SCI] | Solide |
| **Pacing marathon** | Foster (2004) | Negative/even split | RULE-023 | ★★★★★ [SCI] | Solide |
| **Fitness-Fatigue (CTL/ATL/TSB)** | Banister (1975) | Impulse-Response | V2 | ★★★★ [SCI] | Modèle historique solide, calibration individuelle |
| **HRV** | Altini | Variabilité FC | V2 | ★★★★ [SCI] | Validation croissante 2018+ |
| **Stress mécanique** | Dubois | Quantification stress tissulaire | RULE-001/002, `terrain_type` | ★★★★ [PRAT] | Cadre théorique fort, seuils moins précis |
| **Tendinopathies** | Cook (2001) | Charge progressive tendons | `pain_regions` enum | ★★★★★ [SCI] | Solide |
| **CHO en course** | Jeukendrup (2014) | 60–90 g CHO/h, glu+fructose | RULE-025 | ★★★★★ [SCI] | Solide |
| **Ajustement thermique** | Tucker (2006) | Régulation anticipée chaleur | RULE-024 (V2) | ★★★★ [SCI] | Solide |
| **Règle des 10%** | Tradition entraîneurs | +10% max hebdo | RULE-005 | ★★ [PRAT] | **Nouveau caveat** — non validée par RCT (Nielsen 2014). Heuristique historique utile mais surestimée en v1.0. |

---

## 7. Variables MVP vs V2 (recalibré v1.1)

### MVP — Nécessaires au premier coach fonctionnel (v1.1)

```
PROFIL COUREUR
├── experience_level          [PROD critères à définir]
├── age
├── pathologies_connues
├── recent_race_time_10k
├── recent_race_time_half
├── VMA_kmh                    (estimée ou testée)
├── sessions_per_week_available
└── race_target_time           ← NOUVEAU v1.1

SEMAINE COURANTE
├── weekly_distance_km
├── previous_week_distance_km
├── weekly_distance_history    (min. 4 entrées pour ACWR)
├── weekly_duration_min
├── long_run_km_last_week      ← NOUVEAU v1.1
├── avg_weekly_RPE             (signal Moyen — annoter low_confidence)
├── fatigue_score              (1=faible → 5=extrême)
├── sleep_quality_score        (1=mauvaise → 5=excellente ← INVERSÉ v1.1)
└── pain_regions [{region ∈ enum, intensity 0–5, days_persistent}]

CONTEXTE PLAN
├── current_phase
├── weeks_to_race
├── weeks_since_last_injury
└── days_since_last_run        ← NOUVEAU v1.1

VARIABLES CALCULÉES AUTOMATIQUEMENT
├── ACWR_distance              (+ acwr_reliable flag)
├── chronic_load_distance
├── delta_volume_pct           (+ garde petits volumes)
├── delta_long_run_pct         ← NOUVEAU v1.1
├── weekly_internal_load       (⚠ low_confidence)
├── readiness_score
└── target_marathon_pace_min_km
```

### V2 — Nécessitent capteurs / historique long / validation

```
RÉCUPÉRATION OBJECTIVE
├── HRV_daily, HRV_baseline, HRV_trend
├── resting_HR_morning, resting_HR_baseline

MODÈLE FITNESS-FATIGUE
├── CTL, ATL, TSB

PERFORMANCE
├── performance_trend          (formule à définir — CONF-008)
└── lactate_mmol               (avancé)

DISTRIBUTION D'INTENSITÉ         ← RECLASSÉ V2 v1.1
├── zone_distribution {Z1, Z2, Z3}
└── session_rpe_per_workout    ← NOUVEAU V2 v1.1

CONTEXTE COURSE
├── ambient_temperature_C
└── marathon_pace_sessions_per_week
```

---

## 8. Conflits, ambiguïtés et arbitrages humains restants

Statut mis à jour : ✅ résolu v1.1 / 🟡 partiellement résolu / 🔴 encore ouvert.

| ID | Type | Description | Impact | Statut v1.1 |
|----|------|-------------|--------|-------------|
| CONF-001 | Seuil arbitraire | Fenêtre ACWR = 4 sem (moyenne simple) vs EWMA | RULE-003/004 | 🟡 Ajout du flag `acwr_reliable`. **Arbitrage restant** : moyenne simple (MVP) vs EWMA (V1+). |
| CONF-002 | Critères non définis | `experience_level` : sans critères de classification | RULE-010/012/016 | 🔴 **Décision produit requise**. Proposition audit : `beginner = < 1 an ET < 30 km/sem` ; `advanced = > 3 ans ET > 60 km/sem` — à valider. |
| CONF-003 | Outils non standardisés | `fatigue_score` / `sleep_quality_score` 1–5 maison | RULE-006/009 | 🟡 Sens `sleep_quality_score` **inversé v1.1** pour cohérence. **Arbitrage restant** : adopter TQR/Hooper ou conserver 1–5 maison ? |
| CONF-004 | Règle manquante | Phase `off_season` sans règle | Décision sans règle | 🔴 **Décision produit requise**. Proposition audit : en `off_season`, décision par défaut = `maintain` volume bas + recommandation cross-training. |
| CONF-005 | Seuil arbitraire | 4 semaines post-blessure pour cap +5% | RULE-008 | 🔴 Marqué **[PROD]** en v1.1. Arbitrage : conserver, ou décomposer par sévérité (mineure/modérée/majeure) ? |
| CONF-006 | Variable orpheline | `mood_motivation_score` non utilisé | Aucun (V1) | ✅ Résolu : reclassé variable contextuelle V1 (module UX du LLM). |
| CONF-007 | Variable orpheline | `weeks_to_race` sans règle directe | Décision sans règle | 🟡 **Arbitrage restant** : faut-il RULE `weeks_to_race < 3 → taper forcé` ? Aujourd'hui uniquement via `current_phase`. |
| CONF-008 | Définition ambiguë | `performance_trend` sans formule | RULE-013 | ✅ Résolu : RULE-013 **désactivée V1**, à réactiver V2 avec formule définie. |
| CONF-009 | Conflit de résolution | Cap vs Block simultanés | RULE-005 + RULE-010 | ✅ Résolu v1.1 : P1 gagne, cap ignoré. Marqué **[PROD]**. |
| CONF-010 | Zone d'intensité | Définition Z1/Z2/Z3 : FC ? %VMA ? RPE ? | RULE-014, `zone_distribution` | 🟡 **Zone_distribution reclassé V2**. Arbitrage restant : quel proxy pour V2 (RPE recommandé) ? |
| CONF-011 | Transition niveau | Critères beginner→intermediate→advanced | RULE-010/012 | 🔴 Voir CONF-002 (même problème). |
| CONF-012 | K15 introuvable | Nœud K15 référencé mais absent | Graphe dépendances | 🔴 **Arbitrage restant** : mapper K15 à "contre-indications médicales" (= `pathologies_connues`) ou supprimer la référence. |
| CONF-013 | Petits volumes | RULE-005 trop restrictif à faible volume | RULE-005 | ✅ Résolu v1.1 : ajout `previous_week_distance_km ≥ seuil_min_pertinence` (paramètre par défaut 20 km). |
| CONF-014 | **[NOUVEAU v1.1]** | Sens de `sleep_quality_score` opposé à `fatigue_score` en v1.0 | UX + toutes règles sommeil | ✅ Résolu v1.1 : inversion du sens de `sleep_quality_score` (1=mauvaise, 5=excellente). **BREAKING CHANGE** pour l'implémentation. |
| CONF-015 | **[NOUVEAU v1.1]** | Poids `readiness_score` sommaient à 70 en v1.0 sans réparti des 30 restants | Section 3 | ✅ Résolu v1.1 : redistribution explicite 35/35/15/15 + P3 bornés à ±10. |
| CONF-016 | **[NOUVEAU v1.1]** | RULE-007 (taper) bloquait juste l'augmentation, contradictoire avec RULE-021 (−40–60%) | Décisions en phase taper | ✅ Résolu v1.1 : RULE-007 devient `force decrease`. |
| CONF-017 | **[NOUVEAU v1.1]** | RULE-006 (`ET` logique) laissait passer fatigue extrême isolée | Sécurité récupération | ✅ Résolu v1.1 : `OR` étendu avec `fatigue_score == 5` seul. |
| CONF-018 | **[NOUVEAU v1.1]** | Formule de `target_marathon_pace_min_km` non figée | RULE-022 | 🔴 **Arbitrage restant** : Riegel ? Daniels VDOT ? %VMA (Billat) ? Recommandation audit : Riegel comme base, ajusté par `race_target_time` si fourni. |
| CONF-019 | **[NOUVEAU v1.1]** | Actions `deload / decrease / maintain / slight_increase / increase` : bornes % à figer (v1.0 propose des fourchettes) | Sortie du moteur | 🔴 **Décision produit requise**. Proposition audit : deload = −25%, decrease = −10%, maintain = 0%, slight_increase = +3%, increase = +7% (paramétrable). |
| CONF-020 | **[NOUVEAU v1.1]** | Fenêtre chronic_load `weekly_distance_history` : 4 sem vs 6/8 sem | ACWR + chronic_load | 🔴 Lié à CONF-001. Recommandation audit : 4 sem minimum, préférer EWMA α ≈ 0.13 en V1+. |
| CONF-021 | **[NOUVEAU v1.1]** | Sortie longue : quelle règle de progression ? La règle des 10% s'y applique-t-elle ? | C-013, `long_run_km_last_week` | 🔴 **Arbitrage requis**. Recommandation audit : cap +2 km/sem sur la sortie longue, indépendant du volume total. |

**Résumé des arbitrages humains restants (7 items 🔴 + 3 items 🟡) :**

1. 🔴 CONF-002 / CONF-011 — Critères `experience_level`
2. 🔴 CONF-004 — Règle `off_season`
3. 🔴 CONF-005 — Seuil 4 semaines post-blessure
4. 🔴 CONF-012 — Mapping K15
5. 🔴 CONF-018 — Formule `target_marathon_pace`
6. 🔴 CONF-019 — Bornes des actions coach (%)
7. 🔴 CONF-020 — Fenêtre chronique et méthode (simple vs EWMA)
8. 🔴 CONF-021 — Progression sortie longue
9. 🟡 CONF-001 — Choix EWMA vs moyenne simple (lié CONF-020)
10. 🟡 CONF-003 — Adopter TQR/Hooper ou 1–5 maison
11. 🟡 CONF-007 — Règle directe `weeks_to_race < 3` ?
12. 🟡 CONF-010 — Proxy zones d'intensité pour V2

---

## 9. Graphe de dépendances global (mis à jour v1.1)

```
┌─────────────────────────────────────────────────────────┐
│                    ENTRÉES UTILISATEUR                  │
│  weekly_distance_km · fatigue_score · pain_regions      │
│  sleep_quality_score (sens inversé v1.1)                │
│  experience_level · current_phase · weeks_to_race       │
│  recent_race_times · VMA · sessions_available           │
│  long_run_km_last_week · days_since_last_run            │
│  race_target_time                    ← NOUVEAUX v1.1    │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    VARIABLES CALCULÉES                  │
│  ACWR_distance (+ acwr_reliable) · delta_volume_pct     │
│  delta_long_run_pct · readiness_score                   │
│  chronic_load_distance · weekly_internal_load (⚠)       │
│  target_marathon_pace · zone_distribution (V2)          │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    ÉTATS COUREUR                        │
│                                                         │
│  ÉTAT-1 Récupération (35)  ──────────┐                 │
│  ÉTAT-2 Charge (35)         ──────────┤                 │
│  ÉTAT-3 Progression (15)    ──────────┤─► readiness_    │
│  ÉTAT-4 Risque blessure (P0 direct) ──┤   score 0–100  │
│  ÉTAT-5 Préparation marathon (15) ────┘                 │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  RÈGLES DÉCISIONNELLES                  │
│                                                         │
│  P0 — Override    (RULE-001/002/003)                   │
│    ↓                                                    │
│  P1 — Blocage     (RULE-004/005/006/007/026)           │
│    ↓                                                    │
│  P2 — Cap         (RULE-008/009/010)                   │
│    ↓                                                    │
│  P3 — Score       (RULE-011/012 ; 013/014 désactivées) │
│    ↓                                                    │
│  P4 — Planification (RULE-015 à 025)                   │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  ACTIONS DU COACH                       │
│                                                         │
│  deload          → −25%  [PROD, paramétrable CONF-019] │
│  decrease        → −10%  [PROD]                        │
│  maintain        →   0%                                │
│  slight_increase → +3%   [PROD]                        │
│  increase        → +7%   [PROD, module par profil]     │
│                                                         │
│  + Règles planification P4                              │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              EXPLICATIONS UTILISATEUR (LLM)             │
│                                                         │
│  Input :  Decision JSON (scellé)                        │
│           + rules_triggered[]                           │
│           + readiness_score + confidence_score          │
│           + preuve/signal par règle                     │
│           + historique qualitatif coureur               │
│                                                         │
│  Output : coach_message + suggestions séances           │
│                                                         │
│  Contrainte absolue : le LLM ne peut PAS modifier       │
│  la décision ni assouplir un deload.                    │
└─────────────────────────────────────────────────────────┘
```

---

## 10. Séparation science / paramètre / décision produit (nouvelle section v1.1)

Tableau récapitulatif pour transformer la KB en moteur décisionnel proprement stratifié.

### 10.1. Faits scientifiques (immuables sans revue littérature)

- Définition de l'ACWR (ratio 7j/28j)
- Session-RPE = RPE × durée (Foster)
- Tapering réduit −40 à −60% du volume 2–3 semaines (Mujika)
- CHO 60–90 g/h en course > 90 min (Jeukendrup)
- Negative/even split > positive split (Foster)
- Chaleur > 20°C dégrade la performance (Tucker)
- VMA / VVO2max définissent des zones physiologiques (Billat)
- Tendinopathies : progression de charge tissulaire (Cook)

### 10.2. Paramètres configurables (fichier de config, révisables sans redéploiement)

| Paramètre | Valeur v1.1 par défaut | Origine |
|-----------|------------------------|---------|
| `acwr_deload_threshold` | 2.0 | Gabbett |
| `acwr_block_threshold` | 1.5 | Gabbett |
| `acwr_sweet_spot_min` | 0.8 | Gabbett |
| `acwr_sweet_spot_max` | 1.3 | Gabbett |
| `chronic_load_window_weeks` | 4 | [PROD] — CONF-001/020 |
| `chronic_load_method` | "simple_mean" | [PROD] — alternative "ewma" |
| `weekly_increase_cap_pct` | 10 | Tradition [PRAT] |
| `small_volume_threshold_km` | 20 | [PROD] — CONF-013 |
| `recent_injury_cap_weeks` | 4 | [PROD] — CONF-005 |
| `recent_injury_max_increase_pct` | 5 | [PROD] |
| `beginner_max_increase_pct` | 5 | [PROD] |
| `moderate_fatigue_cap_pct` | 5 | [PROD] |
| `pain_critical_intensity` | 4 | [PROD] |
| `pain_critical_days` | 2 | [PROD] |
| `pain_tendon_intensity` | 3 | [PROD] |
| `pain_tendon_days` | 3 | [PROD] |
| `interruption_threshold_days` | 14 | [PROD] — CONF-021 |
| `long_run_max_increase_km` | 2 | [PROD] — CONF-021 |
| `taper_volume_reduction_pct` | 50 (fourchette 40–60) | Mujika |
| `readiness_recovery_weight` | 35 | [PROD] |
| `readiness_load_weight` | 35 | [PROD] |
| `readiness_progression_weight` | 15 | [PROD] |
| `readiness_marathon_prep_weight` | 15 | [PROD] |
| `readiness_p3_bounds_pts` | ±10 | [PROD] |

### 10.3. Règles métier MVP (choix de design du coach, révisables par décision produit)

- Résolution P1 vs P2 : P1 gagne, cap ignoré.
- Bornes actions coach : `-25% / -10% / 0% / +3% / +7%`.
- RULE-013 et RULE-014 désactivées en V1.
- `mood_motivation_score` reclassé UX-only.
- ACWR retombe sur `delta_volume_pct` si `acwr_reliable = false`.
- ÉTAT-4 (risque blessure) ne participe pas au score continu : il court-circuite via P0.

---

## 11. Changelog v1.0 → v1.1

### Changements structurels
- **Nouvelle section 0** : cadre d'audit (niveaux de preuve, séparation science/paramètre/produit, niveaux de confiance opérationnelle).
- **Nouvelle section 10** : séparation formelle science/paramètre/décision produit avec table de config.
- **Section 5 (hiérarchie décisionnelle)** : niveau 4 corrigé — séparation stricte P2 (caps) et P3 (score).

### Changements de contenu — Concepts
- **C-002 (ACWR)** : ajout note critique Impellizzeri 2019 / Wang 2020. Reclassé [PRAT].
- **C-007 (Progressivité)** : reclassé [PRAT] — règle des 10% non validée par RCT.
- **C-013 (Sortie longue)** : **nouveau concept**.

### Changements de contenu — Variables
- **BREAKING** : `sleep_quality_score` sens **inversé** (1=mauvaise → 5=excellente, cohérent avec `fatigue_score`).
- **Ajouts MVP** : `long_run_km_last_week`, `days_since_last_run`, `race_target_time`, enum `pain_regions[].region`, `delta_long_run_pct`.
- **`weekly_internal_load`** annoté low_confidence.
- **`zone_distribution`** reclassé V2 (au lieu de MVP calculée).
- **`mood_motivation_score`** résolu : reclassé variable contextuelle V1.

### Changements de contenu — États
- **Section 3** : poids `readiness_score` explicités et sommant à 100 (35/35/15/15 + P3 ±10).
- **ÉTAT-4** ne participe plus au score continu (court-circuite via P0).
- **ÉTAT-5** : `zone_distribution` retiré (V2).

### Changements de contenu — Règles
- **RULE-003** : ajout garde `acwr_reliable = true`.
- **RULE-005** : ajout garde `previous_week_distance_km ≥ seuil_min_pertinence`.
- **RULE-006** : logique `ET` → `(fatigue ≥ 4 ET sommeil ≤ 2) OU fatigue == 5`.
- **RULE-007** : `block_increase` → **`force decrease`** (cohérence Mujika/RULE-021).
- **RULE-011** : condition douleur clarifiée + inversion sommeil.
- **RULE-013 / RULE-014** : **désactivées en V1**.
- **RULE-026** : **nouvelle** — interruption > 14 jours.

### Changements de contenu — Modèles scientifiques
- **ACWR** : dégradé de ★★★★★ à ★★★ [PRAT] avec caveat.
- **Règle des 10%** : ajoutée comme entrée séparée, ★★ [PRAT].
- **80/20 Seiler** : dégradé à ★★★★ (transposition amateurs incertaine).
- **Canova / Bakken** : classés [PRAT] (expérientiel élite).

### Conflits
- **Résolus v1.1** : CONF-006, CONF-008, CONF-009, CONF-013.
- **Nouveaux v1.1** : CONF-014 à CONF-021 (8 nouveaux items).
- **Encore ouverts** (arbitrages humains requis) : 7 rouges + 3 jaunes.

---

## Annexe A — Index de traçabilité des règles

Colonne "Statut v1.1" ajoutée.

| ID règle | Origine S1 | Origine S2 | Origine S3 | Statut v1.1 |
|----------|-----------|-----------|-----------|-------------|
| RULE-001 | K9 | RULE_PAIN_CRITICAL | Cook, Dubois | inchangée |
| RULE-002 | K9 | RULE_PAIN_TENDON_JOINT | Cook | enum region formalisé |
| RULE-003 | K7 | RULE_ACWR_DANGER | Gabbett | garde `acwr_reliable` |
| RULE-004 | K7 | RULE_ACWR_HIGH | Gabbett | garde `acwr_reliable` |
| RULE-005 | K7 | RULE_WEEKLY_INCREASE_GT10 | Gabbett | garde petits volumes |
| RULE-006 | K6, K12 | RULE_FATIGUE_SLEEP_RED | Mujika | logique corrigée + sommeil inversé |
| RULE-007 | K1 | RULE_TAPER_NO_INCREASE | Mujika | `block` → `force decrease` |
| RULE-008 | K9 | RULE_RECENT_INJURY_CAP | Dubois | tag [PROD] seuil arbitraire |
| RULE-009 | K12 | RULE_FATIGUE_MODERATE | — | inchangée |
| RULE-010 | K3 | RULE_BEGINNER_LIMIT | — | dépend CONF-002 |
| RULE-011 | K6 | RULE_GREEN_LIGHT | Gabbett | condition douleur clarifiée |
| RULE-012 | K1, K4 | RULE_ADVANCED_TOLERANCE | — | inchangée |
| RULE-013 | — | RULE_PERF_DECLINING | — | **DÉSACTIVÉE V1** |
| RULE-014 | K11 | — | Seiler | **DÉSACTIVÉE V1** |
| RULE-015 | K1 | — | Canova | inchangée |
| RULE-016 | K3 | — | — | inchangée |
| RULE-017 | K4 | — | — | inchangée |
| RULE-018 | K5 | — | — | inchangée |
| RULE-019 | K8 | — | — | inchangée |
| RULE-020 | K10 | — | — | inchangée |
| RULE-021 | K1 | RULE_TAPER (détail) | Mujika | inchangée |
| RULE-022 | K13 | — | Billat, Foster | + `race_target_time` (v1.1) |
| RULE-023 | K13 | — | Foster | inchangée |
| RULE-024 | K13 | — | Tucker | inchangée (V2) |
| RULE-025 | — | — | Jeukendrup | inchangée |
| RULE-026 | — | — | — | **NOUVELLE v1.1** — interruption > 14 j |

---

## Annexe B — Checklist de préparation à l'implémentation

Une KB est "prête moteur décisionnel" quand :

- [x] Chaque règle a une priorité explicite (P0–P4)
- [x] Chaque règle a un tag preuve ([SCI]/[PRAT]/[PROD])
- [x] Chaque règle a un tag signal (Fort/Moyen/Faible)
- [x] Aucune règle P0 ne repose sur un signal Faible isolé
- [x] Les résolutions de conflits sont explicites et versionnées
- [x] Aucun seuil numérique n'est un fait — tous sont des paramètres [PROD]
- [x] Les variables V1 utilisées par les règles existent effectivement en V1 (RULE-013/014 désactivées)
- [x] Les échelles de mesure sont cohérentes entre elles (correction sommeil)
- [x] Les états du coureur composent le `readiness_score` avec des poids sommant à 100
- [ ] Les arbitrages humains restants (7 🔴 + 3 🟡) sont tranchés
- [ ] La formule `target_marathon_pace_min_km` est figée (CONF-018)
- [ ] Les critères `experience_level` sont figés (CONF-002/011)
- [ ] Le comportement `off_season` est défini (CONF-004)

**Résumé :** la KB v1.1 est **prête pour l'implémentation du moteur décisionnel**, à condition que les 3 items restants de la checklist soient tranchés au moment de commencer l'implémentation. La couche implémentation peut démarrer sur les Sections 1, 2, 3, 4 (hors RULE-013/014), 5, 10 dès maintenant.
