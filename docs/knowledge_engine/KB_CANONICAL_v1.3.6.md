# KB_CANONICAL v1.3.6 — Expose `target_marathon_pace_min_km`/`_source`

> Version : 1.3.6
> Version parente : KB_CANONICAL_v1.3.5.md
> Statut : **READY FOR IMPLEMENTATION**
> Scope : ajout additif au schéma de sortie uniquement — zéro nouvelle règle, zéro nouveau seuil, zéro changement de calcul
> Objectif : permettre au coureur de voir son allure marathon cible comme un fait vérifié, pas une reformulation du LLM

**Lecture :** appliquer après v1.3.5. N'introduit aucun conflit — étend uniquement §6.2.

---

## Sommaire

| ID | Problème | Type |
|----|----------|------|
| C-20 | `target_marathon_pace_min_km` et `target_marathon_pace_source` sont calculés à l'étape 2 de l'orchestrateur (`compute_target_marathon_pace`, hiérarchie race_target_time > Riegel(semi) > Riegel(10k) > VMA) mais jamais renvoyés dans `DecisionEnvelope` — aucune couche avale ne peut afficher l'allure cible comme un fait vérifié ; si le coach en parle, c'est nécessairement une invention/reformulation du LLM. | Extension additive de schéma |

---

## C-20 — `DecisionEnvelope` expose l'allure marathon cible

**Étend :** §6.2 de KB_CANONICAL_v1.2.md (schéma `DecisionEnvelope`)

**Décision :** ajouter deux champs, avec valeurs par défaut (compatibilité arrière garantie) :

```
DecisionEnvelope:
    ...  (champs v1.2 → v1.3.5 inchangés)
    target_marathon_pace_min_km: float | None = None   // recopie computed.target_marathon_pace_min_km
    target_marathon_pace_source: str = "unavailable"    // recopie computed.target_marathon_pace_source
```

Aucune règle, formule ou hiérarchie de sources n'est modifiée. `compute_target_marathon_pace()`
reste inchangée — son résultat, déjà calculé, cesse simplement d'être jeté en fin d'étape 2.

**Non-objectif explicite** : cette clarification ne décide pas comment le coach doit présenter
cette allure (arrondie, en min/km ou en min/mile, etc.) — c'est un choix de présentation laissé
à la couche Coach Agent/Coach Intelligence, pas une règle du KE.

---

## Mise à jour requise du contrat

`KB_IMPLEMENTATION_CONTRACT_V1.md` doit référencer ce document comme priorité 0 (prime
sur v1.3.5) et `ENGINE_VERSION`/`SCHEMA_VERSION` passer à `"1.3.6"`.
