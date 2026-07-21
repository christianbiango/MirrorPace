# Source 1 — Perplexity : Cartographie des connaissances coach marathon IA

> Rôle : base de connaissances scientifiques et pratiques pour la prise de décision du coach.
> Statut : ingérée, en attente de fusion avec Source 2 et Source 3.

---

## 1. Concepts clés

| ID | Titre | Domaine | Importance décisionnelle |
|----|-------|---------|--------------------------|
| K1 | Périodisation macro-plan (Vollmer, Pfitzinger) | périodisation | Haute — structure tout le plan de préparation |
| K2 | Adéquation objectif / profil | profilage | Haute — valide ou recadre l'objectif du coureur |
| K3 | Progressivité pour débutants | progressivité | Haute — sécurité et efficacité du plan débutant |
| K4 | Sélection de plan par volume et niveau | périodisation | Haute — évite le sur-dosage ou sous-dosage de charge |
| K5 | Cycles pré-marathon orientés vitesse/seuil | planification | Moyenne — pertinent si marathon lointain + manque de vitesse |
| K6 | Individualisation par état de récupération | charge/récupération | Haute — adaptation continue du plan |
| K7 | Gestion de la progression de charge | charge/progression | Haute — prévention surentraînement et blessures |
| K8 | Cadre evidence-informed pour la prescription | processus prescription | Haute — structure l'agent lui-même |
| K9 | Check-up initial multi-dimensionnel | profilage santé/fitness | Haute — sécurité au démarrage |
| K10 | Adaptation aux aléas du quotidien | flexibilité plan | Moyenne — gestion des imprévus |
| K11 | Distribution d'intensité et zones intermédiaires | distribution intensité | Moyenne — optimisation long terme |
| K12 | Monitoring subjectif fatigue/douleur/motivation | monitoring subjectif | Haute — signal d'ajustement quotidien |
| K13 | Stratégie d'allure en course | gestion course | Moyenne — pertinent à J-X avant le marathon |
| K14 | UX & pédagogie pour l'adhésion | communication | Basse — couche de présentation, pas de décision |

---

## 2. Variables utiles

### Variables directement exploitables

| Variable | Nœuds concernés |
|----------|-----------------|
| `semaines_avant_marathon` | K1, K5 |
| `volume_hebdomadaire_habituel` | K1, K3, K4, K7 |
| `experience_annees_course` | K1, K2, K3 |
| `nombre_marathons_ou_semis` | K1, K2 |
| `temps_10k` / `temps_semi` / `temps_5k` | K2, K4, K5, K13 |
| `seances_par_semaine_possibles` | K1, K10 |
| `age` | K2 |
| `score_fatigue` / `score_douleur` / `score_motivation` | K12, K6 |
| `RPE_moyen` | K7 |
| `nombre_seances_manquees` | K10 |
| `profil_parcours` | K13 |

### Variables nécessitant transformation/calcul

| Variable brute | Transformation nécessaire |
|----------------|--------------------------|
| `historique_volume` | → calcul ACWR (charge aiguë/chronique) |
| `duree_dans_zone_*` | → % distribution intensité par zone |
| `variation_hebdomadaire_charge` | → % d'augmentation semaine/semaine |
| `performances_recentes_*` | → prédiction allure marathon (formules Riegel ou équivalent) |
| `historique_scores_questionnaires` | → tendance (dégradation / amélioration) |

### Variables uniquement contextuelles

| Variable | Usage |
|----------|-------|
| `pathologies_connues` | filtre de sécurité, pas d'optimisation |
| `preferences_style_communication` | adaptation UX seulement |
| `conditions_meteo_prevues` | contextualise K13 uniquement |
| `feedback_qualitatif` | enrichit K8, non quantifiable |

---

## 3. Relations entre variables

```
volume_hebdomadaire_habituel   → sélection du plan (K4)
variation_hebdomadaire_charge  → risque surentraînement (K7)
score_fatigue / score_douleur  → réduction de charge (K6, K12)
historique_volume              → capacité à absorber une progression (K3, K7)
experience_annees_course       → tolérance à la progression et au volume (K2, K3)
phase_marathon                 → stratégie de charge et intensité (K1, K11)
semaines_avant_marathon        → choix phase (pré-marathon vs spécifique) (K5)
nombre_seances_manquees        → ajustement semaine suivante (K10)
temps_semi / temps_10k         → prédiction allure marathon cible (K13)
```

---

## 4. Règles métier (format SI → ALORS)

| ID | Condition | Conséquence | Confiance |
|----|-----------|-------------|-----------|
| R-K1 | SI coureur dispose de plusieurs mois ET volume régulier | ALORS planifier phases générale → spécifique → affûtage | Forte |
| R-K2 | SI niveau pratique et volume très faibles vs objectif | ALORS recommander objectif plus progressif (semi ou marathon sans chrono) | Forte |
| R-K3 | SI coureur débutant avec faible volume régulier | ALORS proposer cycle préparatoire général avant spécifique marathon | Forte |
| R-K4 | SI historique volume modéré et peu d'expérience | ALORS éviter plans très haut volume, privilégier volume modéré | Moyenne |
| R-K5 | SI marathon lointain ET performances 5–10 km en retard vs potentiel | ALORS prévoir cycle vitesse/seuil avant cycle spécifique | Moyenne |
| R-K6 | SI indicateurs de récupération se dégradent notablement | ALORS limiter ou réduire la charge plutôt qu'appliquer le plan standard | Forte |
| R-K7 | SI charge augmente trop rapidement vs niveau habituel | ALORS limiter progression ET/OU insérer semaine de décharge | Forte |
| R-K8 | SI objectifs initiaux ne sont plus cohérents (changement contraintes ou stagnation) | ALORS revisiter les objectifs et ajuster la prescription | Forte |
| R-K9 | SI check-up révèle limitations importantes (santé ou fitness) | ALORS restreindre intensité/volume ET/OU recommander avis médical | Moyenne |
| R-K10 | SI plusieurs séances clés manquées dans une semaine | ALORS ajuster la semaine suivante, ne pas cumuler les rattrapages | Moyenne |
| R-K11 | SI grande proportion de temps en zone intermédiaire avec fatigue croissante | ALORS rééquilibrer vers plus de basse intensité + sessions haute intensité ciblées | Moyenne |
| R-K12 | SI scores fatigue/douleur augmentent nettement et se maintiennent | ALORS réduire charge ET/OU adapter type de séance (plus courte/facile) | Moyenne |
| R-K13 | SI allure premiers km nettement plus rapide que cible | ALORS recommander ralentissement pour réalignement stratégie | Moyenne |
| R-K14 | SI utilisateur signale incompréhension de termes | ALORS reformuler avec explication simple ou analogie | Faible |

---

## 5. Niveaux de confiance

| Niveau | Nœuds | Justification |
|--------|-------|---------------|
| **Forte** (score 5) | K1, K2, K3, K6, K7, K8 | Base scientifique solide ou consensus pratique large |
| **Moyenne** (score 4) | K4, K5, K9, K10, K11, K12, K13 | Expérience terrain validée, variabilité individuelle notable |
| **Faible** (score 3) | K14 | Heuristique communicationnelle, non standardisée |

---

## 6. Informations insuffisantes / ambiguïtés à résoudre

| Élément | Gap identifié | À valider dans |
|---------|--------------|----------------|
| Seuil de progression de charge | "trop rapidement" non défini (% ?) — règle des 10% évoquée ailleurs mais non confirmée ici | Source 2, Source 3 |
| Seuils ACWR | Ratios aiguë/chronique non précisés | Source 2, Source 3 |
| Critères de sélection plan faible/modéré/élevé | Volumes seuils non chiffrés (ex. < 40 km/sem = faible ?) | Source 3 (CSV Gemini) |
| Durée de cycle général pour débutants | Nombre de semaines non précisé | Source 2 |
| Définition des zones d'intensité | Aucune échelle normalisée citée (FC, VMA, RPE ?) | Source 2, Source 3 |
| Score de récupération subjectif | Aucun outil standardisé nommé (TQR ? HRV4T ?) | Source 2 |
| Gestion post-marathon | Aucune règle de récupération après une course | Source 2, Source 3 |
| Allure marathon depuis temps semi/10k | Formule de prédiction non précisée | Source 3 |

---

## 7. Graphe de dépendances inter-nœuds

```
K1 ←→ K2, K3, K4, K5, K7, K8
K2 ←→ K3, K9, K15 (K15 non défini dans cette source)
K3 ←→ K4, K5
K6 ←→ K7, K12
K7 ←→ K6, K12
K8 ←→ K6, K7, K12
K9 ←→ K2, K3
K10 ←→ K6, K7, K12
K11 ←→ K6, K7
K12 ←→ K6, K7, K10
K13 ←→ K1, K2
K14 ←→ K2, K8
```

> Note : K15 est référencé par K2 et K9 mais absent de cette source — à identifier dans Source 2 ou Source 3.
