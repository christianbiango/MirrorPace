# KB_CANONICAL v1.3.3 — Expose `PlanHint.reason`

> Version : 1.3.3
> Version parente : KB_CANONICAL_v1.3.2.md
> Statut : **READY FOR IMPLEMENTATION**
> Scope : ajout additif au schéma de sortie uniquement — zéro nouvelle règle, zéro nouveau seuil, zéro changement de comportement de calcul
> Objectif : permettre d'afficher au coureur le texte humain d'un plan_hint (pourquoi cette recommandation, avec quels chiffres) plutôt que son seul code interne

**Lecture :** appliquer après v1.3.2. N'introduit aucun conflit — étend uniquement §6.2.

---

## Sommaire des corrections

| ID | Problème | Section étendue | Type |
|----|----------|------------------|------|
| C-17 | `RuleOutcome.reason` (texte humain, ex. "Macro-plan (18 sem., CV historique 0.12)") calculé par chaque règle P4 mais jamais copié sur `PlanHint` — celui-ci n'expose que `.hint` (code interne, ex. `"structure_macroplan"`) et `.params` (chiffres bruts) | §6.2 v1.2 (`DecisionEnvelope` → `PlanHint`) | Extension additive de schéma |

---

## C-17 — `PlanHint` expose `reason`

**Étend :** §6.2 de KB_CANONICAL_v1.2.md (schéma `PlanHint`)

**Problème :** les règles P4 (`RULE-015` à `RULE-022`) produisent chacune un `RuleOutcome.reason`
lisible ("Taper : -50% volume sur 3 sem., intensité maintenue"), mais `build_envelope()`
ne construit `PlanHint` qu'avec `hint=o.plan_hint` (un code court, ex.
`"taper_structure"`) et `params=dict(o.extras)`. Le prompt du Coach Intelligence
(`prompt_builder.py`) ne consomme que `.hint` — le coureur ne voit jamais le texte
explicatif, seulement un code ou une reformulation potentiellement inventée par le LLM.

**Décision :** ajouter un champ à `PlanHint`, avec valeur par défaut (compatibilité
arrière garantie) :

```
PlanHint:
    rule_id: str
    hint: str
    params: dict = {}
    reason: str = ""    # nouveau — recopie RuleOutcome.reason
```

Aucune règle, seuil ou formule n'est modifié. `build_envelope()` copie simplement
`o.reason` dans `PlanHint.reason` au lieu de le jeter.

---

## Mise à jour requise du contrat

`KB_IMPLEMENTATION_CONTRACT_V1.md` doit référencer ce document comme priorité 0 (prime
sur v1.3.2) et `ENGINE_VERSION`/`SCHEMA_VERSION` passer à `"1.3.3"`.
