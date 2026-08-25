# KB_CANONICAL v1.3.4 — Durée d'affûtage par défaut : 3 → 2 semaines

> Version : 1.3.4
> Version parente : KB_CANONICAL_v1.3.3.md
> Statut : **READY FOR IMPLEMENTATION**
> Scope : changement de valeur d'un seuil de config existant (`taper_duration_weeks`), aucune nouvelle règle, aucun nouveau schéma
> Objectif : aligner la durée d'affûtage par défaut sur la pratique courante (2 semaines), signalée par l'athlète comme plus habituelle que les 3 semaines actuellement codées

**Lecture :** appliquer après v1.3.3. Remplace la valeur documentée en §4.2 et §3.99/RULE-021 de
KB_CANONICAL_v1.2.md (`taper_duration_weeks: 3` → `2`).

---

## Sommaire des corrections

| ID | Problème | Section remplacée | Type |
|----|----------|--------------------|------|
| C-18 | `taper_duration_weeks` par défaut = 3 sem., signalé trop long par l'athlète (2 sem. est la norme habituelle pour un marathon) | §4.2 v1.2 (table `thresholds.yaml`) + §3.99 RULE-021 | Changement de valeur de seuil |

---

## C-18 — `taper_duration_weeks` : 3 → 2

**Remplace :** la valeur par défaut documentée en §4.2 de KB_CANONICAL_v1.2.md
(`taper_duration_weeks: 3`) et référencée dans la définition de RULE-021.

**Décision :** `taper_duration_weeks` passe de `3` à `2` dans `thresholds.py`.

**Impact concret :**
- RULE-021 (détail de l'affûtage) couvre désormais une fenêtre de 2 semaines avant course
  au lieu de 3 — sa réduction de volume (-40% à -60%, inchangée) s'applique sur cette
  fenêtre plus courte.
- RULE-015 (macro-plan) avait sa propre valeur `taper = 3` codée en dur localement,
  indépendamment de `cfg.taper_duration_weeks` — divergence non détectée jusqu'ici.
  Corrigée pour lire `cfg.get("taper_duration_weeks")`, comme RULE-021 : la phase
  d'affûtage suggérée par RULE-015 passe donc aussi de 3 à 2 semaines, et la phase
  "spécifique" récupère la semaine ainsi libérée (le total de semaines ne change pas).
- La dérivation automatique de `current_phase` (Coach Agent, `analysis_handler.py`, ajoutée
  en session du 2026-08-25) considère désormais qu'on entre en phase `"taper"` à
  `weeks_to_race <= 2` au lieu de `<= 3`.
- Aucune autre règle, formule ou seuil n'est modifié. `_phase_coherence_component`
  (`readiness.py`) garde sa fenêtre de tolérance `0 <= weeks_to_race <= 3` pour le calcul
  de cohérence de phase — une phase `"taper"` à 2 semaines reste dans cette fenêtre, donc
  aucune incohérence n'est introduite.

---

## Mise à jour requise du contrat

`KB_IMPLEMENTATION_CONTRACT_V1.md` doit référencer ce document comme priorité 0 (prime
sur v1.3.3) et `ENGINE_VERSION`/`SCHEMA_VERSION` passer à `"1.3.4"`.
