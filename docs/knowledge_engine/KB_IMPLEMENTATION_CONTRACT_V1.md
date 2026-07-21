# Contrat d'implémentation — Knowledge Engine V1

> Statut : GEL DE SPEC — ne pas modifier sans PR dédiée
> Scope : définit la source de vérité exacte pour l'implémentation du moteur V1

---

## Source de vérité

La spec finale est composée de trois documents, à lire dans cet ordre :

| Priorité | Document | Rôle | Lignes |
|----------|----------|------|--------|
| 3 (base) | `KB_CANONICAL_v1.2.md` | Spec complète — schémas, règles, formules, seuils, orchestration, garde-fous, décisions D-01 à D-20 | ~1500 |
| 2 | `KB_CANONICAL_v1.3.md` | Patch correctif Red Team — 11 corrections, remplace les sections listées dans son §1 | ~400 |
| 1 (prime) | `KB_CANONICAL_v1.3.1.md` | Patch de clarification pré-implémentation — 4 définitions machine, aucun changement métier | ~250 |

**En cas de conflit entre versions : la plus récente prime.**

```
v1.3.1 > v1.3 > v1.2
```

---

## Ce que couvre chaque document

### KB_CANONICAL_v1.2.md — lire en entier

- §1 : Schéma `RunnerState` (meta, profile, week, context, computed)
- §2 : Formules `ComputedVariables` (chronic_load, acwr, delta_volume, readiness, confidence, pace, experience_level)
- §3 : Règles RULE-001 à RULE-026 (conditions exactes, outputs, tests_expected)
- §3.99 : Orchestration — pipeline complet (validate → compute → fire → aggregate → P3 → P4 → envelope)
- §4 : Arborescence projet + `thresholds.yaml` exhaustif
- §5 : Corrections v1.2 (confidence score, renamed internal load, pain_trend, computed experience_level)
- §6 : Catalogue d'actions + `DecisionEnvelope` + garde-fous GF-01 à GF-10
- §7 : Décisions produit D-01 à D-20

### KB_CANONICAL_v1.3.md — appliquer les overrides

Les sections suivantes de v1.2 sont **remplacées** par v1.3 :

| Correction | Section v1.2 remplacée |
|-----------|----------------------|
| C-01 — RULE-011 + guard acwr_reliable | §3 RULE-011 |
| C-02 — confidence à l'étape 2 | §3.99 + §2.4 |
| C-03 — medical_referral depuis pathologies_connues | §6.2 + §1.8 |
| C-04 — fatigue_score_history dans WeekInput | §1.4 |
| C-05 — GF-07 reformulé | §6.3 GF-07 |
| C-06 — validation vitesse implicite | §1.8 |
| C-07 — RULE-020 condition fatigue_trend | §3 RULE-020 |
| C-08 — warning missing_injury_context | §1.8 |
| C-09 — min_absolute_weekly_km_on_maintain | §6.1 + §4.2 |
| C-10 — tests_expected RULE-011 | §3 RULE-011 |
| C-11 — race_target_date dans le passé | §1.8 |

Tout ce qui n'est pas listé ici reste inchangé depuis v1.2.

### KB_CANONICAL_v1.3.1.md — appliquer les clarifications

Les éléments suivants **complètent** v1.2 et v1.3 sans les contredire :

| Clarification | Ajoute |
|--------------|--------|
| C-12 — `compute_fatigue_trend()` | Algorithme déterministe + 8 tests |
| C-13 — `min_restrictive()` | Définition normative + table de vérité |
| C-14 — `resolve_medical_referral()` | Priorité + 7 cas de test |
| C-15 — GF-06/GF-07 interaction P0 | 6 property tests normatifs |

---

## Prompt d'implémentation

Lorsqu'on demande à un développeur ou un LLM d'implémenter le moteur, la formulation correcte est :

> "Implémente le moteur V1 conformément à `KB_IMPLEMENTATION_CONTRACT_V1.md` :
> lire `KB_CANONICAL_v1.2.md` en intégralité, puis appliquer les overrides de `KB_CANONICAL_v1.3.md`,
> puis appliquer les clarifications de `KB_CANONICAL_v1.3.1.md`."

---

## Ce qui reste ouvert

| Item | Statut | Bloque quoi |
|------|--------|------------|
| D-05 — table RULE-017 (experience × chronic → plan_level) | ⚠️ À trancher | RULE-017 uniquement (P4 hint, non décisionnel) |
| Risques acceptés V1 (A-06, A-14, A-20) | ✅ Documentés | Rien — portés en V2 |

---

## Gel de spec

À partir de ce document, toute modification de la spec nécessite :

1. Une PR dédiée sur `docs/knowledge_engine/`
2. Un incrément de version (`v1.3.2`, `v1.4`, etc.)
3. Une mise à jour de ce fichier

**Aucune modification informelle (verbale, en commentaire de code, en PR description) ne fait partie du contrat.**
