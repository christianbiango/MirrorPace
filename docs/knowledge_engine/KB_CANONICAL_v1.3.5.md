# KB_CANONICAL v1.3.5 — RULE-027 : structuration spécifique/affûtage en fenêtre courte

> Version : 1.3.5
> Version parente : KB_CANONICAL_v1.3.4.md
> Statut : **READY FOR IMPLEMENTATION**
> Scope : nouvelle règle P4, aucune règle existante modifiée dans son comportement (RULE-015/021 inchangées par ce document — voir v1.3.4 pour leur propre correctif)
> Objectif : combler le trou entre RULE-021 (affûtage, ≤2 sem.) et RULE-015 (macro-plan complet, ≥16 sem.) — une course entre les deux ne recevait aucune structuration, silencieusement

---

## Sommaire

| ID | Problème | Type |
|----|----------|------|
| C-19 | Entre 3 et 15 semaines avant course, aucune règle ne propose de structuration — RULE-021 exige `current_phase == "taper"` (≤2 sem. par construction), RULE-015 exige `weeks_to_race >= 16`. Un coureur qui a déjà démarré sa prépa et dont la course tombe dans cette fenêtre n'a aucun retour structuré, sans qu'aucun signal ne l'indique. | Nouvelle règle P4 |

**Origine** : remonté par l'athlète lui-même en testant une course à 10 semaines. Signalé
que le seuil de RULE-015 (16 sem.) est cohérent avec la littérature de périodisation
(Canova) et ne doit pas être abaissé — mais qu'un scénario "prépa déjà commencée,
fenêtre plus courte" est légitime et fréquent, et doit rester possible.

---

## C-19 — RULE-027 : bloc spécifique + affûtage en fenêtre courte

**Condition de déclenchement** (toutes requises) :

```
weeks_to_race is not None
AND taper_duration_weeks < weeks_to_race < macro_plan_min_weeks   // ]2, 16[ par défaut
AND len(weekly_distance_history) >= 4                              // même garde que RULE-015
AND coefficient_of_variation(weekly_distance_history) < cv_max_regular
AND NOT (experience_level == "beginner" AND chronic_load_distance < beginner_base_min_km)
```

La dernière condition réutilise exactement le signal déjà utilisé par RULE-016 : si le
coureur n'a pas encore la base nécessaire (même logique que "débutant + charge chronique
faible → cycle préparatoire d'abord"), proposer un découpage spécifique/affûtage serait
prématuré — combler l'écart de forme reste la priorité affichée (via RULE-016), pas cette
règle.

**Sortie** — même niveau d'abstraction que RULE-015 (nombre de semaines par bloc, jamais
de nombre de cycles ni de contenu de séance — ça reste une décision de personnalisation
laissée à la couche Coach Intelligence, pas une constante du moteur) :

```
specific_weeks = weeks_to_race - taper_duration_weeks
taper_weeks    = taper_duration_weeks

plan_hint = "structure_specific_block"
extras    = {"plan_type": "specific_block",
             "suggested_phases": {"specific": specific_weeks, "taper": taper_weeks}}
```

**Aucun nouveau seuil de config** : la règle réutilise `taper_duration_weeks`,
`macro_plan_min_weeks`, `cv_max_regular`, `beginner_base_min_km`, tous déjà définis pour
RULE-015/016/021.

---

## Mise à jour requise du contrat

`KB_IMPLEMENTATION_CONTRACT_V1.md` doit référencer ce document comme priorité 0 (prime
sur v1.3.4) et `ENGINE_VERSION`/`SCHEMA_VERSION` passer à `"1.3.5"`.
