# Red Team Report — Moteur de décision Knowledge Engine V1

> Version : 1.0
> Basé sur : `KB_CANONICAL_v1.2.md` + `IMPLEMENTATION_BLUEPRINT_V1.md`
> Rôle : ingénieur sécurité + médecin du sport sceptique + utilisateur adversarial
> Priorité absolue : identifier chaque situation où le moteur autorise une progression à tort ou rate un signal de danger

---

## Structure

- [1. Profils adversariaux — 20 scénarios](#1-profils-adversariaux--20-scénarios)
- [2. Contradictions entre règles](#2-contradictions-entre-règles)
- [3. Audit des invariants GF-01 à GF-10](#3-audit-des-invariants-gf-01-à-gf-10)
- [4. Trous dans les données](#4-trous-dans-les-données)
- [5. Analyse des décisions produit D-01 à D-20](#5-analyse-des-décisions-produit-d-01-à-d-20)
- [6. Stratégie de tests — 30 tests indispensables](#6-stratégie-de-tests--30-tests-indispensables-avant-production)
- [7. Verdict final](#7-verdict-final)

---

## 1. Profils adversariaux — 20 scénarios

| # | Scénario | Inputs clés | Règles attendues | Décision attendue | Risque si moteur se trompe |
|---|----------|-------------|-----------------|-------------------|---------------------------|
| A-01 | **ACWR null par chronic trop faible** — history=[2,3,2,3], weekly=25 km → chronic=2.5 < 5 km | chronic < 5 → acwr=null → RULE-003 ne peut pas tirer | Aucune P0/P1 | `increase` possible | Charge explosive (+1000%) invisible au moteur car acwr=null. Aucune règle ne protège. |
| A-02 | **Contournement RULE-005 par manipulation prev_week** — prev=19.9 km, weekly=35 km (+76%) | delta_volume_reliable=false (prev < 20) | RULE-005 désarmée | `increase` libre | Un coureur peut sauter de 20 à 35 km sans blocage en gardant prev juste sous le seuil. |
| A-03 | **Pathologie cardiaque déclarée, aucune douleur** — pathologies_connues=["arythmie_cardiaque"], pain_regions=[], ACWR=1.2 | Validation: warnings+=medical_referral_recommended MAIS medical_referral=false dans DecisionEnvelope | Aucune P0 | `increase` + warning texte | medical_referral=false dans la sortie JSON. Le LLM peut ignorer le warning. Coureur avec pathologie grave reçoit `increase`. |
| A-04 | **Taper involontaire + blessure non déclarée** — days_since_last_run=22, current_phase="general", weekly=5, pain_regions=[] | RULE-026 P1 → maintain | maintain + plan_hint reprise | `maintain` | Arrêt de 22 jours probablement causé par une blessure. Le moteur ne questionne pas la cause de l'arrêt. |
| A-05 | **Saut de semaine basse → semaine haute, seuil prev=20** — history=[20, 65, 68, 70], prev=20, weekly=55 km | delta=+175%, delta_reliable=true (prev=20 ≥ 20) | RULE-005 P1 → maintain | `maintain` ✓ | Si prev était 19.9 → delta_reliable=false → `increase`. Le seuil exact de 20 km est un point de contournement trivial. |
| A-06 | **Douleur déclarée en session_notes mais pain_regions=[]** — session_notes="genou douloureux depuis 5 jours", pain_regions=[] | Aucune règle de douleur ne peut s'activer | Aucune P0 | `increase` possible | La seule trace de la douleur est dans le champ LLM. Le moteur de règles est aveugle. Progression autorisée. |
| A-07 | **Limite exacte RULE-001 — intensity=4, days=1** — douleur forte mais très récente | intensity=4 ≥ 4 MAIS days=1 < 2 → RULE-001 non déclenchée | RULE-001 ✗ | `increase` possible | Douleur intense (4/5) depuis 1 jour non protégée. Fenêtre de 24h sans protection. |
| A-08 | **Limite exacte RULE-002 — achilles, intensity=3, days=2** — sous le seuil tendon | intensity=3 ≥ 3 MAIS days=2 < 3 → RULE-002 ✗ | RULE-002 ✗ | `increase` possible | Tendinopathie achille évolutive non protégée pendant les 2 premiers jours. |
| A-09 | **ACWR exactement à 1.5 — limite stricte RULE-004** — history=[33,33,33,33], weekly=50 | acwr=1.515 → RULE-004 déclenchée. acwr=1.500 → NOT triggered (strict >) | RULE-004 P1 si >1.5 | `maintain` si >1.5 sinon `increase` | Sensibilité au flottant sur le seuil exact. Comportement binaire autour de 1.5. |
| A-10 | **Retour blessure semaine 4 — limite exacte RULE-008** — weeks_since_last_injury=4 | RULE-008: `< 4` strict → 4 semaines = not triggered | Aucune P2 de blessure | `increase` libre | À 3 semaines: cap +5%. À 4 semaines: augmentation libre (+10% pour avancé). Saut brutal en une semaine. |
| A-11 | **Semaine zéro + décision maintain = cible 0 km** — weekly=0, fatigue=5 (RULE-006 P1) | RULE-006 → maintain → absolute_next_week_target = 0×1.0 = 0 km | maintain avec cible **0 km** | **Cible 0 km recommandée** | La décision `maintain` sur 0 km recommande littéralement de rester à 0 km la semaine suivante. Contre-indiqué pour une reprise. |
| A-12 | **Profil avec VMA=25 km/h déclaré beginner** — VMA=25 (élite mondial), chronic=15 km | experience_level="beginner" (chronic < 30). Allure marathon = 3.2 min/km | RULE-010 P2 | `slight_increase` | Données contradictoires ingérées sans alerte. VMA=25 km/h est biologiquement impossible pour 99.99% des coureurs. Aucune validation de plausibilité. |
| A-13 | **RULE-011 feu vert sur acwr fallback = 1.0** — history=[], chronic=current_week, acwr=1.0, fatigue=2, sleep=4 | acwr_reliable=false MAIS acwr_distance=1.0 ∈ [0.8, 1.3] → **RULE-011 tire sur donnée fictive** | RULE-011 P3 → +10 pts score | score gonflé, potentiellement `increase` | Feu vert multi-critères basé sur un ACWR fictif (1.0 fallback). Score de readiness artificiellement élevé. |
| A-14 | **Coureur age=14 avec volume 150 km/semaine** — age=14 (autorisé par schéma), chronic=140 | Aucune règle de protection liée à l'âge | RULE-003/004/005 selon ACWR/delta | `increase` possible | Un adolescent de 14 ans reçoit exactement les mêmes règles qu'un adulte de 35 ans. Aucune contrainte de volume liée à l'âge. |
| A-15 | **Chute massive de volume sans protection** — weekly=5, prev=80, delta=-93.75%, fatigue=1, sleep=5 | delta < 0 → RULE-005 ne tire pas (vérifie delta > cap). RULE-020 P4 hint uniquement | Aucune P0/P1 | `increase` possible | Effondrement de -93% avec signaux positifs = seulement un hint P4. L'effondrement lui-même (indicateur probable de blessure) n'est pas une alerte de sécurité. |
| A-16 | **`submitted_at` retardé de 15 jours** — données de S1 soumises à S1+15j | Pénalité confidence -10 (stale). Si autres données OK: confidence=90 | Décision normale avec confidence ~90 | `increase` normale | Des données vieilles de 15 jours traitées comme quasi-fraiches. Pénalité de 10 pts insuffisante. |
| A-17 | **race_target_date dans le passé** — race_target_date="2020-01-01", weeks_to_race non fourni | weeks_to_race recalculé = valeur négative | Comportement non spécifié | Indéterminé | RULE-015, RULE-016, RULE-018 pourraient recevoir weeks_to_race < 0. Comportement non documenté. |
| A-18 | **Incohérence fatigue/RPE non détectée** — fatigue=5, avg_weekly_RPE=1.0 | Les deux champs traités indépendamment. RULE-006 tire sur fatigue=5 | `maintain` via RULE-006 ✓ | `maintain` ✓ | Décision correcte mais incohérence flagrante non signalée. RPE=1.0 + fatigue=5 = contradictoire physiologiquement. Aucun warning. |
| A-19 | **phase="return_from_injury" sans weeks_since_last_injury** — phase déclare retour mais champ=null | RULE-008: null → not triggered. Aucune règle de blessure active | Selon autres signaux | `increase` possible | Coureur en retour de blessure (via current_phase) sans protection d'aucune règle. Double source d'information sans priorité définie. |
| A-20 | **Aggravation cachée via pain_trend="worsening" + intensity=2** — achilles, intensity=2, days=5, trend="worsening" | intensity=2 < 3 → RULE-002 ✗. intensity=2 < 4 → RULE-001 ✗. pain_trend ignoré V1 | Aucune P0 | `increase` possible | Signal d'aggravation clair ignoré. Dans 2-3 jours: intensity atteindra le seuil. En attendant, l'entraînement continue sans alerte. |

---

## 2. Contradictions entre règles

### Conf-01 — RULE-007 (force_decrease P1) + RULE-004 (block_increase P1) simultanées

```
Règles    : RULE-007 (taper → force_decrease P1) + RULE-004 (acwr élevé → block_increase P1)
Priorité  : Les deux P1
Spec      : §3.99 "IF any P1 forced 'decrease' → decision = decrease" → RULE-007 gagne
Ambiguïté : Faible. Mais RULE-004 est "perdante" invisiblement si pas documentée
            dans ignored_rules_due_to_priority
Correction: Documenter explicitement la hiérarchie interne P1 (force_decrease > block_increase)
            dans §3.99 et dans DecisionEnvelope
```

### Conf-02 — RULE-011 sans guard `acwr_reliable` [BUG DE SPEC]

```
Règles    : RULE-011 (feu vert P3), RULE-003/004 (guards sur acwr_reliable)
Spec      : RULE-003/004 ont guard explicite acwr_reliable == true
            RULE-011 vérifie uniquement acwr_distance != null
Problème  : history=[], chronic=current_week, acwr_distance=1.0 (fallback) ∈ [0.8, 1.3]
            → RULE-011 donne +10 pts score sur une donnée fictive
            → readiness_score artificiellement gonflé
Correction: Ajouter `AND acwr_reliable == true` dans la condition de RULE-011
            (documenté dans P-14 du Blueprint mais pas corrigé dans la spec)
```

### Conf-03 — GF-07 libellé sans condition explicite "pas de P0"

```
Règles    : GF-07 "taper → always decrease", RULE-003 P0 (deload)
Spec      : P0 court-circuite P1 → deload. GF-07 formulé de façon absolue
Ambiguïté : Un implémenteur qui applique GF-07 avant P0 pourrait forcer "decrease"
            là où "deload" est correct
Correction: Reformuler GF-07 : "Si current_phase == taper ET aucun P0 déclenché
            → action == decrease"
```

### Conf-04 — `pathologies_connues` → warning ≠ `medical_referral = true` [FAILLE SÉMANTIQUE]

```
Règles    : Validator §1.8 → warnings += "medical_referral_recommended"
            RULE-001/002 → medical_referral = true dans DecisionEnvelope
Problème  : pathologies_connues = ["arythmie_cardiaque"] + pain_regions = []
            → DecisionEnvelope.medical_referral = false
            → decision.action = "increase" possible
            Confusion entre le warning textuel et le champ booléen
Correction: Si pathologies_connues non vide → medical_referral = true dans DecisionEnvelope
            (sans modifier decision.action si aucun P0 déclenché — mais le champ est correct)
```

### Conf-05 — RULE-020 satisfaite quand `fatigue_trend = "unknown"`

```
Règles    : RULE-020 condition : delta < -20% AND fatigue_trend != "worsening"
Problème  : "unknown" != "worsening" → condition satisfaite
            Chute de -50% avec état de fatigue inconnu → hint "no_catchup"
            alors que la chute était peut-être due à un épuisement sévère non documenté
Correction: Modifier la condition : fatigue_trend ∈ {"improving", "stable"}
            (exclure explicitement "unknown")
```

### Conf-06 — GF-06 calculé APRÈS l'agrégation [TIMING ARCHITECTURAL]

```
Règles    : GF-06 (confidence < 50 → cap maintain), §3.99 étape 7 (calcul confidence)
Spec      : §3.99 étape 4 = agrégation, étape 7 = calcul confidence
            GF-06 s'applique sur la décision finale mais confidence n'existe pas encore à l'étape 4
Problème  : GF-06 doit être un post-processing après l'étape 7, pas intégré à l'étape 4
            Si le développeur implémente §3.99 à la lettre et oublie le post-processing
            → GF-06 jamais appliqué
Correction: Déplacer le calcul de readiness_confidence_score à l'étape 2
            (avec les autres ComputedVariables), puis l'utiliser dans l'agrégation à l'étape 4
            OU documenter explicitement que GF-06 = post-processing à l'étape 8
```

### Conf-07 — RULE-008 cap +5% inefficace sur une décision de decrease

```
Règles    : RULE-007 force_decrease P1 (-50%), RULE-008 cap +5% P2
Contexte  : Coureur en taper + blessure récente (3 semaines)
Spec      : P1 > P2 → RULE-008 ignorée. Résultat : decrease -50%
Paradoxe  : RULE-008 protège uniquement les augmentations. Elle n'a aucun effet plancher
            sur les réductions. Un coureur post-blessure subit la même réduction de taper
            qu'un coureur sain.
Correction: Documenter ce comportement dans §3.99. RULE-008 ne peut pas protéger
            contre un decrease forcé — c'est voulu mais non explicite.
```

### Conf-08 — `current_phase = "return_from_injury"` sans lien avec `weeks_since_last_injury`

```
Règles    : current_phase (source de vérité planification), weeks_since_last_injury (RULE-008)
Problème  : Les deux champs sont indépendants. Un coureur peut avoir
            current_phase="return_from_injury" ET weeks_since_last_injury=null
            → RULE-008 ne déclenche pas → aucun cap de progression
Correction: Ajouter validation croisée WARNING : si current_phase == "return_from_injury"
            ET weeks_since_last_injury == null → warning "missing_injury_context"
```

---

## 3. Audit des invariants GF-01 à GF-10

### GF-01 — Sécurité toujours prioritaire

```
Objectif  : medical_referral == true → action == "deload"
Risque    : pathologies_connues non vide → warning textuel MAIS medical_referral = false
            Un coureur avec cardiopathie connue, pain_regions=[], ACWR=1.2
            → medical_referral = false + action = "increase"
            La confusion vient du double usage : "recommended" dans warnings vs champ booléen
Property  : ∀ input : (RULE-001.triggered OR RULE-002.triggered)
            → (medical_referral == true AND action == "deload")
Fail      : pathologies_connues = ["stenose_aortique"] + pain_regions = []
            → medical_referral = false + action = "increase" — légalement inacceptable
```

### GF-02 — Jamais d'augmentation si P1 déclenché

```
Objectif  : ∃ rule P1 triggered → action ∈ {deload, decrease, maintain}
Risque    : Bug d'implémentation dans l'agrégateur (itération dans le mauvais ordre)
            ou condition triggered mal évaluée
Property  : ∀ input valide : (∃ rule ∈ triggered_rules : rule.priority == "P1")
            → action ∈ {"deload", "decrease", "maintain"}
Fail      : Peu probable si l'agrégateur est correct. Vérifier que "triggered" est évalué
            avant d'itérer sur la liste des outcomes
```

### GF-03 — Volume cible jamais négatif

```
Objectif  : absolute_next_week_target_km >= 0
Risque    : weekly=0, action=maintain → cible = 0 km (techniquement valide mais absurde)
Property  : ∀ input valide : absolute_next_week_target_km >= 0
Fail      : Faible sur la valeur négative. Mais maintain sur weekly=0 = 0 km recommandé
            pour une reprise — cas A-11 ci-dessus. Ajouter params.min_absolute_weekly_km
            comme plancher configurable (actuellement défini à 0 dans la spec)
```

### GF-04 — LLM en lecture seule

```
Objectif  : La couche LLM ne peut pas modifier decision.action
Risque    : Payload transmis au LLM = référence mutable → modification possible si
            le code aval réutilise le même objet
Property  : Test d'architecture — mock LLM qui tente de modifier decision.action
            → vérifier que DecisionEnvelope.decision.action est inchangé après appel LLM
Fail      : Si envelope_builder.py transmet decision par référence (dict Python)
            au lieu d'une copie profonde (copy.deepcopy)
```

### GF-05 — Config immuable pendant une exécution

```
Objectif  : config_hash capturé au démarrage, stable pendant toute l'exécution
Risque    : Config lue en lazy loading → modification du fichier entre deux règles
            → incohérence silencieuse (RULE-001 avec seuil=4, RULE-006 avec seuil=3 modifié)
Property  : Modifier thresholds.yaml pendant l'exécution → erreur "config_mutation"
Fail      : Contexte asyncio ou multi-process avec reload automatique du fichier YAML
```

### GF-06 — Confidence < seuil médium → cap maintain

```
Objectif  : readiness_confidence_score < 50 → action ∈ {deload, decrease, maintain}
Risque    : CRITIQUE — la confidence est calculée à l'étape 7 (§3.99) APRÈS
            l'agrégation (étape 4). GF-06 doit donc s'appliquer en post-processing
            à l'étape 7 ou 8. Si oubli → GF-06 jamais appliqué
Property  : ∀ input : readiness_confidence_score < 50
            → action ∈ {"deload", "decrease", "maintain"}
Fail      : Implémentation naïve de §3.99 à la lettre sans post-processing GF-06
            → profil P-14 (fatigue=1, sleep=5, history=[]) → slight_increase autorisée
```

### GF-07 — Taper toujours en decrease

```
Objectif  : current_phase == "taper" ET pas de P0 → action == "decrease"
Risque    : Libellé actuel "taper → always decrease" sans condition explicite "pas de P0"
            Un implémenteur peut appliquer GF-07 avant P0 → conflit avec GF-01
Property  : ∀ input avec current_phase == "taper" :
            (aucun P0 déclenché → action == "decrease")
            AND (P0 déclenché → action == "deload")
Fail      : GF-07 appliqué avant P0 → force "decrease" quand "deload" est correct
```

### GF-08 — Deload minimum

```
Objectif  : action == "deload" → delta_pct <= -20%
Risque    : Bug de convention de signe (delta positif au lieu de négatif)
            ou clamp mal implémenté (clamp[-40, -20] vs clamp[-40, 0])
Property  : ∀ input : action == "deload" → delta_pct <= -20.0
Fail      : Faible si bounds sont correctement implémentés. Vérifier cohérence
            entre delta_pct signé et absolute_next_week_target_km calculé
```

### GF-09 — Une seule action finale

```
Objectif  : decision.action est un scalar ∈ VALID_ACTIONS
Risque    : Agrégateur qui concatène plusieurs actions si plusieurs P0 simultanés
            (P-13 : 3 règles P0 → potentiellement "deload|deload|deload")
Property  : ∀ input : isinstance(decision.action, str)
            AND decision.action ∈ {"deload","decrease","maintain","slight_increase","increase"}
Fail      : P-13 (3 P0 simultanés) est le cas le plus exposé. Test obligatoire.
```

### GF-10 — Version du contrat

```
Objectif  : Toute modification de DecisionEnvelope ou RunnerState → incrément schema_version
Risque    : Oubli humain — modification non documentée sans incrément de version
Property  : Test CI — hash de la définition des schémas Pydantic → doit correspondre
            au schema_version déclaré dans le code
Fail      : Très probable si non automatisé. Quasi-universel dans les projets initiaux.
```

---

## 4. Trous dans les données

### 4.1 Champs présents mais utilisés nulle part

| Champ | Collecté | Utilisé V1 | Risque |
|-------|----------|-----------|--------|
| `sessions_per_week_available` | ✅ requis MVP | ❌ aucune règle | +10% recommandé a un sens très différent pour 1 séance/semaine vs 7 séances |
| `mood_motivation_score` | ⭕ optionnel | ❌ LLM uniquement | Score 1/5 + fatigue=4 = surcharge psychologique ignorée par le moteur de règles |
| `pain_trend` | ✅ requis (PainRegion) | ❌ informatif uniquement | trend="worsening" à intensity=2 → intensity=4 dans 2-3 jours. Signal collecté, ignoré |
| `terrain_type` | ⭕ optionnel | ❌ contextuel V1 | Trail = charge réelle 20-40% plus élevée à volume identique. Non corrigé |

### 4.2 Champs absents du schéma mais requis par des formules

| Besoin | Formule | Manque | Impact |
|--------|---------|--------|--------|
| `fatigue_score_history` | §2.5 `fatigue_trend` | Non défini dans RunnerState §1 | `fatigue_trend` sera toujours "unknown" → RULE-020 mal déclenchée (voir Conf-05) |
| `longest_race_km_history` | §5.4 `experience_level` | "dérivé de recent_race_time_*" — pas un champ explicite | Coureur sans temps de course récent → longest_race_km=0 → "beginner" même pour un marathonien |

### 4.3 Incohérences entre champs non validées

| Incohérence | Validée ? | Risque |
|-------------|-----------|--------|
| `avg_weekly_RPE = 1.0` + `fatigue_score = 5` | ❌ | Contradiction flagrante, aucun warning |
| `race_target_date` + `weeks_to_race` incohérents | ❌ | Source de vérité non définie si les deux sont fournis |
| `current_phase = "return_from_injury"` + `weeks_since_last_injury = null` | ❌ | Phase déclare retour mais aucune règle de protection active |
| `current_phase = "taper"` + `weeks_to_race = 20` | ❌ | Taper à 20 semaines = physiologiquement absurde. Aucun warning |
| `weekly_distance_km = 200` + `weekly_duration_min = 120` | ❌ | 200 km en 2h → vitesse 100 km/h. Impossible, non détecté |

### 4.4 Valeurs extrêmes non couvertes

| Cas | Comportement actuel | Risque |
|-----|---------------------|--------|
| `previous_week_distance_km = 0` | `max(prev, 1)` → delta = weekly × 100% affiché | Delta fictif (+5000%) trompeur dans les logs et l'UI |
| `weekly_distance_history = [0, 0, 0, 0]` | chronic = 0 → acwr = null (chronic < 5) | Charge historique nulle = protection ACWR inexistante |
| `race_target_date` dans le passé | weeks_to_race recalculé = valeur négative | RULE-015/018 comportement non défini pour weeks_to_race < 0 |
| `action = maintain` sur `weekly_distance_km = 0` | cible absolue = 0 km | Recommander 0 km pour une reprise est contra-indiqué |

### 4.5 Hypothèses non explicites

| Hypothèse | Conséquence si fausse |
|-----------|----------------------|
| weekly_distance_history ordonné du plus récent au plus ancien | Si inversé → chronic calculé sur données futures → ACWR erroné |
| Le caller fournit fatigue_score_history si disponible | Champ non défini dans le schéma → tout caller l'omet → fatigue_trend=unknown |
| longest_race_km dérivé de recent_race_time_* | Coureur avec VMA seulement, aucune course récente → longest_race_km=0 → beginner par défaut |

---

## 5. Analyse des décisions produit D-01 à D-20

| ID | Décision | Classe | Risque caché | Bloquer avant codage ? |
|----|----------|--------|-------------|----------------------|
| **D-01** | simple_mean vs ewma | **C** | 3 semaines à 70 km + 1 semaine à 0 → chronic=52.5. Reprise à 40 km → acwr=0.76 (sous-estimé). ewma serait plus réactif sur les semaines atypiques. | Non |
| **D-02** | Fenêtre 4 semaines | **B** | Maladie de 3 semaines (3×0 km) → chronic=17.5. Reprise à 30 km → acwr=1.71 → RULE-004 → maintain. Correct mais très sensible à la composition de la fenêtre. | Non |
| **D-03** | Critères experience_level | **B** | chronic ≥ 60 pour "advanced" ignore les traileurs (volume km < route). Un traileur expert à 40 km/sem = "intermediate". | Non |
| **D-04** | years_running optionnel | **C** | Sans ce champ, un coureur de 6 mois intense (chronic=50 km) = "intermediate". Acceptable V1. | Non |
| **D-05** | Table RULE-017 | **A** | Bloque uniquement RULE-017. Impact safety = nul (P4 hints). Impact UX : beginner avec chronic=15 km pourrait recevoir "plan haut volume" si table mal calibrée. | **Oui** |
| **D-06** | off_season → maintain | **B** | "maintain volume bas" ambigu. Quel volume de référence si le coureur fait 0 km en off_season ? | Non |
| **D-07** | Cap unique 4 semaines post-blessure | **B** | Fracture de fatigue et entorse légère ont le même cap (+5% pendant 4 semaines). Trop permissif pour les fractures mais V1 acceptable. | Non |
| **D-08** | long_run → hint P4 | **B** | Non bloquant = sortie longue de 20 à 35 km (+75%) en une semaine sans blocage si le total hebdo est +8%. RULE-005 ne vérifie pas la sortie longue séparément. | Non (risque sous-estimé) |
| **D-09** | Échelle fatigue 1-5 maison | **C** | Pas de validation scientifique mais UX simple. Comparaison inter-coureurs impossible. | Non |
| **D-10** | Ne pas forcer taper sur weeks_to_race < 3 | **B** | Coureur à 2 semaines de course en phase "general" peut recevoir `increase`. Qui met à jour current_phase ? Si personne, le moteur pousse à l'entraînement à J-14. | Non (trou de responsabilité) |
| **D-11** | Bornes actions | **B** | Deload plage [-40%, -20%], défaut -25%. Qui choisit dans cette plage ? Un deload à -20% pour ACWR=2.5 est insuffisant. | Non |
| **D-12** | Riegel 1.06 | **C** | 1.06 prédit des temps plus rapides que 1.15. Semi 2h → Riegel 1.06 = 4h14, Riegel 1.15 = 4h36. Sous-estimer le temps cible → allure d'entraînement trop élevée. | Non |
| **D-13** | region="other" → RULE-001 oui, RULE-002 non | **B** | Douleur "other" intensity=3, days=5 : intensity < 4 → RULE-001 ✗, "other" ∉ CRITICAL → RULE-002 ✗. Zone non protégée. | Non |
| **D-14** | stale_input seuil 10 jours | **B** | 10 jours très permissif. Données de fatigue, sommeil, douleur vieilles de 10 jours = périmées. Pénalité -10 pts insuffisante. | Non |
| **D-15** | Moteur stateless, caller passe l'historique | **B** | fatigue_score_history non défini dans le schéma RunnerState. Tout caller l'omet par défaut → fatigue_trend=unknown systématiquement. | Non |
| **D-16** | RULE-013/014 désactivées | **C** | Correct sans les variables correspondantes. | Non |
| **D-17** | pain_trend informatif uniquement | **B** | Signal "worsening" collecté mais ignoré = risque médical. À V1.5 minimum : pénaliser confidence si pain_trend="worsening". | Non (délai risqué) |
| **D-18** | K15 → pathologies_connues | **C** | Cohérence de graphe. Aucun impact sur les règles. | Non |
| **D-19** | mood_motivation_score → LLM only | **C** | Acceptable V1. | Non |
| **D-20** | Arrondi 0.5 km | **C** | Cohérence UX. Aucun impact safety. | Non |

**Synthèse :**
- **Classe A** (bloque le moteur) : D-05 uniquement
- **Classe B** (important avant release) : D-02, D-03, D-06, D-07, D-08, D-10, D-11, D-12, D-13, D-14, D-15, D-17
- **Classe C** (peut attendre) : D-01, D-04, D-09, D-16, D-18, D-19, D-20

---

## 6. Stratégie de tests — 30 tests indispensables avant production

### Tests unitaires — formules

| # | Test | Fichier | Assertion clé |
|---|------|---------|--------------|
| T-01 | chronic_load: history=[] → fallback=current_week, acwr_reliable=false | test_acwr.py | `chronic == weekly_distance_km AND acwr_reliable == False` |
| T-02 | chronic_load: history=[10,10,10,10] → mean=10.0 | test_acwr.py | `chronic == 10.0` |
| T-03 | acwr: chronic < 5 → acwr_distance=null, reliable=false | test_acwr.py | `acwr_distance is None` |
| T-04 | delta_volume: prev=19.9 → delta_reliable=false | test_acwr.py | `delta_volume_reliable == False` |
| T-05 | delta_volume: prev=20.0 → delta_reliable=true | test_acwr.py | `delta_volume_reliable == True` |
| T-06 | confidence: history=[], RPE=null, days=20 → score ≤ 50 | test_readiness.py | `confidence_score <= 50` |
| T-07 | confidence: profil complet, 8 semaines → score ≥ 80 | test_readiness.py | `confidence_score >= 80` |
| T-08 | experience_level: declared="advanced", chronic=25 → "beginner", source="calculated" | test_experience.py | `level == "beginner" AND source == "calculated"` |
| T-09 | experience_level: declared="beginner", critères → "intermediate" → respecter déclaration prudente | test_experience.py | `level == "beginner" AND source == "declared"` |
| T-10 | Riegel: semi=6600s → marathon_time ≈ 13748s | test_pace.py | `abs(predicted - 13748) < 10` |

### Tests unitaires — règles

| # | Test | Règle | Input clé | Assertion |
|---|------|-------|-----------|-----------|
| T-11 | Seuil exact RULE-001 | RULE-001 | intensity=4, days=2 | triggered=true |
| T-12 | Sous le seuil RULE-001 (days=1) | RULE-001 | intensity=4, days=1 | triggered=false |
| T-13 | RULE-002 seuil exact | RULE-002 | achilles, intensity=3, days=3 | triggered=true |
| T-14 | RULE-002 region="other" | RULE-002 | other, intensity=5, days=10 | triggered=false |
| T-15 | RULE-003 guard acwr_reliable | RULE-003 | acwr=2.5, reliable=false | triggered=false |
| T-16 | RULE-005 guard delta_reliable | RULE-005 | delta=50%, prev=15 km | triggered=false |
| T-17 | RULE-006 branche OR (fatigue=5) | RULE-006 | fatigue=5, sleep=5 | triggered=true |
| T-18 | RULE-006 branche AND (fatigue=4, sleep=2) | RULE-006 | fatigue=4, sleep=2 | triggered=true |
| T-19 | RULE-006 négative (fatigue=4, sleep=3) | RULE-006 | fatigue=4, sleep=3 | triggered=false |
| T-20 | **RULE-011 avec acwr_reliable=false** [guard manquant] | RULE-011 | history=[], acwr=1.0 fallback, reliable=false | **triggered=false** |

### Tests d'intégration (bout en bout)

| # | Test | Entrée | Assertion |
|---|------|--------|-----------|
| T-21 | P0 short-circuit + ignored_rules reportées | intensity=5, days=3, knee | `action=="deload" AND medical_referral==true AND len(ignored_rules) > 0` |
| T-22 | P1 multiples convergents | fatigue=5, delta=+50% | `action=="maintain"` |
| T-23 | Taper sans P0 | phase=taper, tous signaux verts | `action=="decrease"` |
| T-24 | GF-06: confidence=30 → maintain forcé | history=[], days=25, RPE=null | `action=="maintain" AND confidence_score==30` |
| T-25 | Profil avancé stable → increase autorisé | chronic=70km, acwr=1.1, 8 semaines | `action=="increase"` |

### Tests de propriété (invariants GF)

| # | Invariant | Garde-fou | Outil |
|---|-----------|-----------|-------|
| T-26 | `medical_referral==true → action=="deload"` | GF-01 | Hypothesis |
| T-27 | `P1_triggered → action ∈ {deload,decrease,maintain}` | GF-02 | Hypothesis |
| T-28 | `confidence_score < 50 → action ∈ {deload,decrease,maintain}` | GF-06 | Hypothesis |
| T-29 | `phase==taper AND no_P0 → action=="decrease"` | GF-07 | Hypothesis |
| T-30 | `action=="deload" → delta_pct <= -20.0` | GF-08 | Hypothesis |

---

## 7. Verdict final

### 7.1 Les 10 risques techniques les plus importants

| Priorité | Risque | Criticité médicale |
|----------|--------|-------------------|
| R-01 | `RULE-011` sans guard `acwr_reliable` — feu vert basé sur acwr=1.0 fictif | **Élevée** — autorise augmentation sur données inexistantes |
| R-02 | `GF-06` calculé après l'agrégation — timing architectural ambigu | **Élevée** — GF-06 peut ne jamais s'appliquer si mal implémenté |
| R-03 | `pathologies_connues` → warning textuel ≠ `medical_referral=true` | **Élevée** — cardiopathie connue + `increase` possible |
| R-04 | `fatigue_score_history` absent du schéma RunnerState | **Moyenne** — `fatigue_trend` systématiquement "unknown" |
| R-05 | `pain_trend="worsening"` ignoré en V1 — fenêtre de 2-3 jours sans protection | **Moyenne-haute** — blessure détectée trop tard |
| R-06 | `RULE-020` satisfaite quand `fatigue_trend="unknown"` | **Faible** — hint incorrect mais non décisionnel |
| R-07 | `sessions_per_week_available` non utilisé — delta volume sans lien avec la densité d'entraînement | **Moyenne** — +10% pour 1 séance/sem ≠ +10% pour 7 séances/sem |
| R-08 | `action=maintain` sur `weekly_distance_km=0` → cible 0 km | **Moyenne** — recommandation absurde pour une reprise |
| R-09 | Seuil `prev_week = 20 km` — contournement trivial de RULE-005 à 19.9 km | **Moyenne** — progression +76% possible sans blocage |
| R-10 | `current_phase="taper"` + `weeks_to_race=20` — incohérence non détectée | **Faible** — taper à 20 semaines du marathon, moteur obéit sans alerter |

### 7.2 Les 10 modifications recommandées avant codage

| # | Modification | Urgence | Effort estimé |
|---|-------------|---------|--------------|
| **M-01** | **Ajouter `acwr_reliable == true` dans RULE-011** | Critique | 1 ligne dans la spec |
| **M-02** | **Déplacer le calcul de `readiness_confidence_score` à l'étape 2** (avec ComputedVariables, avant l'agrégation à l'étape 4) | Critique | Restructuration §3.99 |
| **M-03** | **Définir `fatigue_score_history` dans RunnerState §1** (champ optionnel, array[int], longueur 0..8) | Critique | Ajout de schéma |
| **M-04** | **Clarifier la sémantique de `medical_referral`** : pathologies_connues non vide → `medical_referral=true` dans DecisionEnvelope (sans modifier decision.action si aucun P0) | Important | Logique validator |
| **M-05** | **Reformuler GF-07** : "Si current_phase == taper ET aucun P0 déclenché → action == decrease" | Important | Documentation |
| **M-06** | **Ajouter validation croisée** : `weekly_duration_min` incohérent avec `weekly_distance_km` (vitesse implicite > 50 km/h → error) | Important | Validator §1.8 |
| **M-07** | **Ajouter le cas `acwr_reliable=false` dans tests_expected de RULE-011** | Important | Documentation |
| **M-08** | **Modifier RULE-020** : condition `fatigue_trend ∈ {"improving", "stable"}` au lieu de `!= "worsening"` | Important | 1 ligne dans la spec |
| **M-09** | **Ajouter validation croisée** : `current_phase="return_from_injury"` + `weeks_since_last_injury=null` → warning "missing_injury_context" | Souhaitable | Validator §1.8 |
| **M-10** | **Documenter le traitement de `action=maintain` sur `weekly_distance_km=0`** : définir `params.min_absolute_weekly_km_on_maintain` (proposé: 5 km) | Souhaitable | Config + logique |

### 7.3 Ce qui peut rester inchangé

- La hiérarchie P0 → P4 : solide et cohérente
- RULE-001, RULE-002, RULE-003 : conditions précises, guards corrects
- RULE-004, RULE-005, RULE-006, RULE-007, RULE-026 : logique correcte
- La structure DecisionEnvelope avec `ignored_rules_due_to_short_circuit` : exhaustive pour l'audit
- La séparation config / domaine / règles / moteur : architecture saine
- Les 15 profils adversariaux du Blueprint : corrects comme fixtures de régression
- GF-03, GF-04, GF-05, GF-09, GF-10 : bien formulés, implémentation straightforward

### 7.4 Verdict

**Peut-on coder maintenant ?**

Presque. Deux blocages architecturaux doivent être résolus dans la spec avant le premier commit :

1. **M-01** (RULE-011 + guard acwr_reliable) — bug de spec, 1 ligne à corriger
2. **M-02** (confidence calculée avant l'agrégation) — ambiguïté dans §3.99 créant un risque fort d'implémentation incorrecte de GF-06

Ces deux items prennent moins d'une heure à corriger dans KB_CANONICAL. Ensuite le codage peut démarrer.

**Faut-il modifier l'architecture ?**

Non. L'architecture est solide. Les problèmes identifiés sont :
- 2 bugs de spec (M-01, M-02) → corriger dans KB_CANONICAL → v1.2.1
- 3 ajouts de schéma bénins (M-03, M-04, M-06)
- 3 clarifications de documentation (M-05, M-07, M-08)
- 2 décisions produit mineures (M-09, M-10)

**Étapes suivantes recommandées :**

```
1. Corriger M-01 et M-02 dans KB_CANONICAL_v1.2.md → passer en v1.2.1
2. Ajouter M-03 (schéma fatigue_score_history) et M-04 (sémantique medical_referral)
3. Encoder les 20 profils de ce rapport comme fixtures JSON dans /tests/fixtures/adversarial/
4. Phase B — coder le moteur sur toutes les règles sauf RULE-017 (bloquée par D-05)
```

**Résumé en une phrase :** le moteur est bien conçu et la priorité de sécurité est correctement hiérarchisée — les 3 risques critiques (RULE-011 sans guard, GF-06 timing, medical_referral sémantique) se corrigent en moins d'une heure sur la spec, pas sur le code.
