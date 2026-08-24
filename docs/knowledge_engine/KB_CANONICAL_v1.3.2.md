# KB_CANONICAL v1.3.2 — Exposition de `experience_level_source` dans `DecisionEnvelope`

> Version : 1.3.2
> Version parente : KB_CANONICAL_v1.3.1.md
> Statut : **READY FOR IMPLEMENTATION**
> Scope : ajout additif au schéma de sortie uniquement — zéro nouvelle règle, zéro nouveau seuil, zéro changement de comportement de calcul
> Objectif : permettre à la couche Coach Intelligence de citer la vraie raison d'une classification de niveau, au lieu de deviner

**Lecture :** appliquer après v1.3.1. N'introduit aucun conflit avec v1.2/v1.3/v1.3.1 — étend uniquement §6.2.

---

## Sommaire des corrections

| ID | Problème | Section étendue | Type |
|----|----------|------------------|------|
| C-16 | `experience_level` et `experience_level_source` calculés en §2 (`ComputedVariables`, cf. §5 v1.2) mais jamais renvoyés dans `DecisionEnvelope` — la couche Coach Intelligence ne peut pas expliquer pourquoi une expérience déclarée a été ignorée | §6.2 v1.2 (`DecisionEnvelope`) | Extension additive de schéma |

---

## C-16 — `DecisionEnvelope` expose `experience_level` et `experience_level_source`

**Étend :** §6.2 de KB_CANONICAL_v1.2.md (schéma `DecisionEnvelope`)

**Problème :** `compute_experience_level()` (§5 v1.2, formalisé dans `experience_level.py`) produit une provenance (`"declared" | "calculated" | "reconciled"`) qui documente précisément si le niveau déclaré par le coureur a été respecté, ignoré (garde-fou anti-surestimation), ou confirmé par la charge réelle. Cette variable vit dans `ComputedVariables`, une structure interne à l'étape 2 de l'orchestration, jamais retournée par `run_engine()`. Résultat : aucune couche avale (Coach Intelligence, Coach Agent) ne peut savoir *pourquoi* le moteur a classé un coureur d'un niveau donné — seulement le niveau final.

**Décision :** ajouter deux champs à `DecisionEnvelope`, en queue de schéma, avec valeurs par défaut (compatibilité arrière garantie pour tout code qui construit un `DecisionEnvelope` sans les fournir) :

```
DecisionEnvelope:
    ...  (champs v1.2/v1.3/v1.3.1 inchangés)
    experience_level: str = "beginner"           // recopie computed.experience_level
    experience_level_source: str = "declared"    // recopie computed.experience_level_source
```

Aucune règle, seuil, ou formule n'est modifié. `compute_experience_level()` reste inchangée. Le seul changement est que sa sortie, déjà calculée, cesse d'être jetée à la fin de l'étape 2.

**Non-objectif explicite :** cette clarification ne change pas la logique de réconciliation (declared vs calculated vs reconciled) — ce garde-fou anti-surestimation reste tel que défini en §5 v1.2. Elle rend seulement sa décision visible.

### Cas limites

| `experience_level_source` | Signifie | Ce que la couche avale peut en dire |
|---------------------------|----------|--------------------------------------|
| `"declared"` | Déclaré plus prudent que ce que la charge autoriserait → respecté | "Je respecte ce que tu m'as dit, même si ta charge récente serait compatible avec plus." |
| `"calculated"` | Déclaré plus flatteur que ce que la charge autorise → ignoré | "Ta charge récente ne confirme pas encore ce niveau, donc je reste prudent malgré ce que tu as déclaré." |
| `"reconciled"` | Déclaré == calculé | Pas de discordance à expliquer. |

---

## Mise à jour requise du contrat

`KB_IMPLEMENTATION_CONTRACT_V1.md` doit référencer ce document comme priorité 0 (prime sur v1.3.1) et `ENGINE_VERSION`/`SCHEMA_VERSION` passer à `"1.3.2"`.
