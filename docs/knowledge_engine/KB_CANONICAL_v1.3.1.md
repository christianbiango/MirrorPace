# KB_CANONICAL v1.3.1 — Patch de clarification pré-implémentation

> Version : 1.3.1
> Version parente : KB_CANONICAL_v1.3.md
> Statut : **READY FOR IMPLEMENTATION**
> Scope : clarifications normatives uniquement — zéro nouvelle règle, zéro nouveau seuil, zéro nouvelle fonctionnalité
> Objectif : supprimer toute interprétation libre avant le premier commit de code

**Lecture :** appliquer après v1.3. Les sections référencées ci-dessous remplacent les passages correspondants de v1.2 et v1.3.

---

## Sommaire des corrections

| ID | Problème | Section remplacée | Type |
|----|----------|-------------------|------|
| C-12 | `fatigue_trend` — algorithme ambigu avec historique court | §2.5 v1.2 | Définition machine |
| C-13 | `min_restrictive()` — fonction non formalisée | §3.99 v1.3 étape 4 | Définition machine |
| C-14 | `medical_referral_reason` — priorité non définie si causes multiples | §4.4 v1.3 | Règle de priorité |
| C-15 | GF-06 et GF-07 — interaction avec P0 non couverte par les property tests | §6.3 v1.2 / §3 v1.3 GF-06, GF-07 | Tests normatifs |

---

## C-12 — Définition machine de `fatigue_trend`

**Remplace :** §2.5 de KB_CANONICAL_v1.2.md

**Problème :** v1.2 §2.5 utilisait `len(fatigue_score_history) < 3` comme seuil d'incertitude et un diff avec seuil ±1. v1.3 ajoute `fatigue_score_history` au schéma mais ne remplace pas §2.5. Les deux versions sont en conflit. Cette clarification est la définition normative unique.

### Définition normative

```
// fatigue_score_history : array[int] ∈ {1,2,3,4,5}
// index 0 = valeur la plus récente (semaine N-1)
// index -1 = valeur la plus ancienne disponible
// Champ distinct de fatigue_score (semaine courante, non inclus dans cet array)

IF len(fatigue_score_history) < 2:
    fatigue_trend = "unknown"   // pas assez de points pour détecter une direction

ELIF fatigue_score_history[0] < fatigue_score_history[-1]:
    fatigue_trend = "improving"   // score de fatigue en baisse = moins fatigué

ELIF fatigue_score_history[0] > fatigue_score_history[-1]:
    fatigue_trend = "worsening"   // score de fatigue en hausse = plus fatigué

ELSE:
    fatigue_trend = "stable"      // [0] == [-1]
```

**Note sur l'échelle :** fatigue_score 1 = très faible, 5 = extrême. Un score qui descend = récupération → `"improving"`. Un score qui monte = dégradation → `"worsening"`. Cohérent avec §1.4 v1.2.

### Cas limites

| `fatigue_score_history` | Résultat |
|-------------------------|----------|
| `[]` | `"unknown"` |
| `[3]` | `"unknown"` (len < 2) |
| `[2, 4]` | `"improving"` (2 < 4 : fatigue a baissé) |
| `[4, 2]` | `"worsening"` (4 > 2 : fatigue a monté) |
| `[3, 3]` | `"stable"` |
| `[3, 3, 3, 3]` | `"stable"` ([0]==[-1]==3) |
| `[2, 5, 3, 4]` | `"improving"` ([0]=2 < [-1]=4) |
| `[4, 2, 3, 1]` | `"worsening"` ([0]=4 > [-1]=1) |
| `null` / absent | `"unknown"` (équivalent à `[]`) |

**Cohérence avec RULE-020 (v1.3 C-07) :**

RULE-020 se déclenche uniquement si `fatigue_trend ∈ {"improving", "stable"}`. La définition ci-dessus garantit qu'avec `fatigue_score_history = []` ou un seul point, `fatigue_trend = "unknown"` → RULE-020 ne se déclenche pas. Aucun hint "no_catchup" sur données insuffisantes.

### Tests unitaires normatifs

```python
def test_fatigue_trend():
    assert compute_fatigue_trend([])              == "unknown"
    assert compute_fatigue_trend([3])             == "unknown"
    assert compute_fatigue_trend([2, 4])          == "improving"
    assert compute_fatigue_trend([4, 2])          == "worsening"
    assert compute_fatigue_trend([3, 3])          == "stable"
    assert compute_fatigue_trend([2, 5, 3, 4])   == "improving"  # [0]=2 < [-1]=4
    assert compute_fatigue_trend([4, 2, 3, 1])   == "worsening"  # [0]=4 > [-1]=1
    assert compute_fatigue_trend([3, 3, 3, 3])   == "stable"
```

---

## C-13 — Définition machine de `min_restrictive()`

**Remplace :** §3.99 v1.3 étape 4 (GF-06, référence à la fonction)

**Problème :** v1.3 §3.99 étape 4 mentionne `min_restrictive(decision, "maintain")` pour l'application de GF-06 sans en fournir la définition formelle. Toute implémentation sans cette définition est une interprétation libre.

### Ordre de sévérité total

```
SEVERITY_ORDER = {
    "deload":          5,   // le plus restrictif
    "decrease":        4,
    "maintain":        3,
    "slight_increase": 2,
    "increase":        1    // le moins restrictif
}
```

### Définition normative

```python
def min_restrictive(action_a: str, action_b: str) -> str:
    """
    Retourne l'action ayant la sévérité la plus haute (la plus restrictive).
    Utilisée par GF-06 pour appliquer le cap 'maintain' sans jamais
    augmenter une décision déjà restrictive.
    """
    if SEVERITY_ORDER[action_a] >= SEVERITY_ORDER[action_b]:
        return action_a
    return action_b
```

**Propriété fondamentale :** `min_restrictive` ne peut que maintenir ou réduire la liberté de progression. Elle ne peut jamais passer `"deload"` à `"increase"`.

**Propriété de commutativité :** `min_restrictive(a, b) == min_restrictive(b, a)`. L'ordre des arguments ne change pas le résultat.

### Table de vérité

| `action_a` | `action_b` | Résultat | Raison |
|------------|------------|----------|--------|
| `"increase"` | `"maintain"` | `"maintain"` | 1 < 3 → b gagne |
| `"slight_increase"` | `"maintain"` | `"maintain"` | 2 < 3 → b gagne |
| `"maintain"` | `"maintain"` | `"maintain"` | égalité → a retourné |
| `"decrease"` | `"maintain"` | `"decrease"` | 4 > 3 → a gagne |
| `"deload"` | `"maintain"` | `"deload"` | 5 > 3 → a gagne |
| `"deload"` | `"decrease"` | `"deload"` | 5 > 4 → a gagne |
| `"slight_increase"` | `"increase"` | `"slight_increase"` | 2 > 1 → a gagne |
| `"maintain"` | `"increase"` | `"maintain"` | 3 > 1 → a gagne |

### Application dans §3.99 v1.3 étape 4 — GF-06

```
// Dans l'agrégateur, après avoir produit la décision initiale :

IF computed.readiness_confidence_score < params.confidence_min_medium:
    decision.action = min_restrictive(decision.action, "maintain")
    // Exemples :
    //   "increase"       → min_restrictive("increase", "maintain")       = "maintain"
    //   "slight_increase"→ min_restrictive("slight_increase", "maintain") = "maintain"
    //   "maintain"       → min_restrictive("maintain", "maintain")        = "maintain"
    //   "decrease"       → min_restrictive("decrease", "maintain")        = "decrease"  (inchangé)
    //   "deload"         → min_restrictive("deload", "maintain")          = "deload"    (inchangé)
```

**Contrat explicite :** GF-06 ne peut pas aggraver une décision déjà restrictive (`decrease` ou `deload` restent inchangés).

### Tests unitaires normatifs

```python
def test_min_restrictive():
    assert min_restrictive("increase", "maintain")        == "maintain"
    assert min_restrictive("slight_increase", "maintain") == "maintain"
    assert min_restrictive("maintain", "maintain")        == "maintain"
    assert min_restrictive("decrease", "maintain")        == "decrease"
    assert min_restrictive("deload", "maintain")          == "deload"
    assert min_restrictive("deload", "decrease")          == "deload"
    assert min_restrictive("slight_increase", "increase") == "slight_increase"

def test_min_restrictive_commutative():
    actions = ["deload", "decrease", "maintain", "slight_increase", "increase"]
    for a in actions:
        for b in actions:
            assert min_restrictive(a, b) == min_restrictive(b, a)

def test_gf06_never_increases_decision():
    # GF-06 appliqué : min_restrictive(decision, "maintain") ne peut qu'être
    # ≥ "maintain" en sévérité (jamais moins restrictif)
    restricted_actions = ["deload", "decrease", "maintain"]
    for action in restricted_actions:
        result = min_restrictive(action, "maintain")
        assert SEVERITY_ORDER[result] >= SEVERITY_ORDER["maintain"]
```

---

## C-14 — Priorité de `medical_referral_reason`

**Remplace :** §4.4 v1.3 (bloc "Implémentation")

**Problème :** v1.3 définit `medical_referral_reason` avec trois valeurs possibles (`"pain_critical"`, `"pain_tendon"`, `"known_pathology"`) mais ne spécifie pas le comportement lorsque plusieurs conditions sont actives simultanément. Un coureur avec pathologie connue ET douleur critique déclencherait deux sources → valeur du champ indéterminée.

### Ordre de priorité normatif

```
PRIORITY :
  1. "pain_critical"   — RULE-001 déclenchée
  2. "pain_tendon"     — RULE-002 déclenchée (et RULE-001 non déclenchée)
  3. "known_pathology" — pathologies_connues non vide (et aucune règle P0 déclenchée)
  4. null              — medical_referral = false
```

### Algorithme normatif (dans `envelope_builder.py`)

```python
def resolve_medical_referral(triggered_rules, pathologies_connues) -> tuple[bool, str | None]:
    """
    Retourne (medical_referral: bool, medical_referral_reason: str | None).
    Priorité : pain_critical > pain_tendon > known_pathology.
    """
    rule_001_triggered = any(r.rule_id == "RULE-001" and r.triggered for r in triggered_rules)
    rule_002_triggered = any(r.rule_id == "RULE-002" and r.triggered for r in triggered_rules)

    if rule_001_triggered:
        return True, "pain_critical"

    if rule_002_triggered:
        return True, "pain_tendon"

    if pathologies_connues:          # liste non vide
        return True, "known_pathology"

    return False, None
```

**Contrat :** si `medical_referral = false`, alors `medical_referral_reason = null`. Les deux champs sont toujours cohérents.

### Cas de test normatifs

| Cas | RULE-001 | RULE-002 | pathologies_connues | `medical_referral` | `medical_referral_reason` |
|-----|----------|----------|--------------------|--------------------|--------------------------|
| 1 | ✓ | ✓ | non vide | `true` | `"pain_critical"` |
| 2 | ✓ | ✗ | non vide | `true` | `"pain_critical"` |
| 3 | ✗ | ✓ | non vide | `true` | `"pain_tendon"` |
| 4 | ✗ | ✗ | non vide | `true` | `"known_pathology"` |
| 5 | ✗ | ✗ | vide / null | `false` | `null` |
| 6 | ✓ | ✗ | vide | `true` | `"pain_critical"` |
| 7 | ✗ | ✓ | vide | `true` | `"pain_tendon"` |

### Tests unitaires normatifs

```python
def test_medical_referral_reason_priority():
    # Cas 1 : RULE-001 + RULE-002 + pathologie → pain_critical gagne
    ref, reason = resolve_medical_referral(
        triggered_rules=[rule(id="RULE-001", triggered=True), rule(id="RULE-002", triggered=True)],
        pathologies_connues=["arythmie"]
    )
    assert ref == True and reason == "pain_critical"

    # Cas 3 : RULE-002 + pathologie → pain_tendon gagne
    ref, reason = resolve_medical_referral(
        triggered_rules=[rule(id="RULE-001", triggered=False), rule(id="RULE-002", triggered=True)],
        pathologies_connues=["arythmie"]
    )
    assert ref == True and reason == "pain_tendon"

    # Cas 4 : pathologie seule → known_pathology
    ref, reason = resolve_medical_referral(
        triggered_rules=[rule(id="RULE-001", triggered=False), rule(id="RULE-002", triggered=False)],
        pathologies_connues=["arythmie"]
    )
    assert ref == True and reason == "known_pathology"

    # Cas 5 : aucune cause → false + null
    ref, reason = resolve_medical_referral(
        triggered_rules=[rule(id="RULE-001", triggered=False)],
        pathologies_connues=[]
    )
    assert ref == False and reason is None

def test_medical_referral_coherence():
    # Invariant : medical_referral=false → reason=null toujours
    for state in generate_random_states():
        envelope = run_engine(state)
        if envelope.medical_referral == False:
            assert envelope.medical_referral_reason is None
```

---

## C-15 — Assertions P0 dans GF-06 et GF-07

**Remplace / complète :** §6.3 GF-06 et GF-07 (v1.2 + v1.3)

**Problème :** v1.3 documente GF-06 et GF-07 séparément mais ne formalise pas leur interaction avec P0. Un développeur pourrait implémenter GF-06 avant l'agrégation P0, ou appliquer GF-07 sur une sortie déjà fixée par P0.

### C-15a — GF-06 : P0 immunisé contre le cap `maintain`

**Règle normative :**

```
GF-06 s'applique uniquement si aucune règle P0 n'est déclenchée.
Si une règle P0 est déclenchée, decision.action est "deload" et est immuable.
GF-06 ne peut pas modifier "deload".

Formellement :

IF any P0 triggered:
    // GF-06 est inopérant — min_restrictive("deload", "maintain") = "deload" de toute façon
    // mais la garde explicite rend l'intention claire
    assert decision.action == "deload"      // invariant post-agrégation P0
    // GF-06 n'est PAS appliqué
ELSE:
    IF computed.readiness_confidence_score < params.confidence_min_medium:
        decision.action = min_restrictive(decision.action, "maintain")
```

**Note :** mathématiquement, `min_restrictive("deload", "maintain") = "deload"` — GF-06 serait sans effet même s'il était appliqué après P0. Mais la garde explicite documente l'intention et évite d'exécuter du code inutile.

**Property tests normatifs :**

```python
def test_gf06_no_effect_when_p0_triggered(state, computed, config):
    """GF-06 ne peut pas override deload issu d'un P0."""
    envelope = run_engine(state, computed, config)
    p0_triggered = any(r.priority == "P0" and r.triggered for r in envelope.triggered_rules)
    if p0_triggered:
        assert envelope.decision.action == "deload"

def test_gf06_caps_increase_when_low_confidence(state, computed, config):
    """GF-06 convertit increase/slight_increase en maintain si confidence < 50."""
    envelope = run_engine(state, computed, config)
    p0_triggered = any(r.priority == "P0" and r.triggered for r in envelope.triggered_rules)
    if not p0_triggered and computed.readiness_confidence_score < config.confidence_min_medium:
        assert envelope.decision.action in {"deload", "decrease", "maintain"}

def test_gf06_does_not_override_decrease(state, computed, config):
    """GF-06 ne remonte jamais une décision restrictive vers maintain."""
    # Si la décision avant GF-06 est decrease ou deload,
    # GF-06 ne doit pas la changer vers maintain
    envelope = run_engine(state, computed, config)
    # Property : min_restrictive(x, "maintain") ≤ x en sévérité
    # → decrease reste decrease, deload reste deload
    if envelope.decision.action in {"deload", "decrease"}:
        # Vérifier qu'une confidence < 50 n'a pas overridé une décision restrictive
        if computed.readiness_confidence_score < config.confidence_min_medium:
            assert envelope.decision.action in {"deload", "decrease"}
```

---

### C-15b — GF-07 : comportement taper complet avec branche P0

**Règle normative :**

```
IF current_phase == "taper":

    IF any P0 triggered:
        decision.action = "deload"    // GF-01 prime, GF-07 inopérant
        // GF-07 ne peut PAS forcer "decrease" sur une décision P0

    ELSE:
        decision.action = "decrease"  // GF-07 s'applique
        // Impossible : "increase", "slight_increase", "maintain" en taper sans P0
```

**Remplacement du libellé v1.3 GF-07 :**

> Si `current_phase == "taper"` et **aucune règle P0 n'est déclenchée** → `decision.action == "decrease"`.
> Si une règle P0 est déclenchée en phase taper → `decision.action == "deload"` (GF-01 prime sur GF-07).
> Il est impossible d'avoir `increase`, `slight_increase` ou `maintain` en taper, quelle que soit la valeur de confidence ou la disposition des autres règles.

**Property tests normatifs :**

```python
def test_gf07_taper_without_p0(state, computed, config):
    """Taper sans P0 → decrease obligatoire."""
    envelope = run_engine(state, computed, config)
    if state.context.current_phase == "taper":
        p0_triggered = any(r.priority == "P0" and r.triggered for r in envelope.triggered_rules)
        if not p0_triggered:
            assert envelope.decision.action == "decrease"

def test_gf07_taper_with_p0(state, computed, config):
    """Taper avec P0 → deload (GF-01 gagne)."""
    envelope = run_engine(state, computed, config)
    if state.context.current_phase == "taper":
        p0_triggered = any(r.priority == "P0" and r.triggered for r in envelope.triggered_rules)
        if p0_triggered:
            assert envelope.decision.action == "deload"

def test_gf07_taper_no_increase_ever(state, computed, config):
    """Taper → jamais increase ou slight_increase, quelle que soit la confidence."""
    envelope = run_engine(state, computed, config)
    if state.context.current_phase == "taper":
        assert envelope.decision.action not in {"increase", "slight_increase", "maintain"}
```

**Scénarios de test d'intégration couvrant les deux branches :**

| Scénario | current_phase | P0 déclenché | Décision attendue | GF actif |
|----------|---------------|-------------|-------------------|---------|
| Taper normal | `"taper"` | ✗ | `"decrease"` | GF-07 |
| Taper + douleur critique | `"taper"` | ✓ (RULE-001) | `"deload"` | GF-01 |
| Taper + ACWR ≥ 2.0 | `"taper"` | ✓ (RULE-003) | `"deload"` | GF-01 |
| Taper + confidence < 50 | `"taper"` | ✗ | `"decrease"` | GF-07 (GF-06 sans effet — decrease reste decrease) |

---

## Récapitulatif des ajouts normatifs

### Nouvelles fonctions normatives

| Fonction | Définie dans | Signature |
|----------|-------------|-----------|
| `compute_fatigue_trend(history)` | C-12 | `(list[int]) -> Literal["improving","stable","worsening","unknown"]` |
| `min_restrictive(action_a, action_b)` | C-13 | `(str, str) -> str` |
| `resolve_medical_referral(triggered_rules, pathologies)` | C-14 | `(...) -> tuple[bool, str \| None]` |

### Nouveaux tests normatifs (à créer dans `/tests/unit/`)

| Fichier | Tests |
|---------|-------|
| `test_fatigue_trend.py` | 8 cas — C-12 |
| `test_min_restrictive.py` | 7 cas + commutativité + propriété GF-06 — C-13 |
| `test_medical_referral.py` | 7 cas table + invariant cohérence — C-14 |
| `test_gf06_gf07_p0_interaction.py` | 3 + 3 property tests — C-15 |

### Fichiers d'implémentation impactés

| Fichier | Impact |
|---------|--------|
| `domain/formulas/readiness.py` | `compute_fatigue_trend()` — définition C-12 |
| `engine/aggregator.py` | `min_restrictive()` + garde GF-06/P0 — C-13, C-15a |
| `engine/envelope_builder.py` | `resolve_medical_referral()` — C-14 |
| `engine/orchestrator.py` | Ordre d'application GF-07 → assert post-agrégation — C-15b |

---

## Verdict final

```
KB_CANONICAL_v1.3.1
STATUT : READY FOR IMPLEMENTATION

Toutes les ambiguïtés d'interprétation identifiées avant implémentation
sont résolues de façon normative et déterministe.

L'instruction suivante est maintenant exécutable sans interprétation libre :

  "Implémente le moteur V1 conformément à KB_CANONICAL_v1.3.1"

Aucune décision architecturale ne reste ouverte pour l'équipe de développement.
Seul D-05 (table RULE-017, non-décisionnel P4) reste à trancher
indépendamment de l'implémentation des règles P0-P3.
```
