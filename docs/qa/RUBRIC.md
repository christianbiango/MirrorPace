# Rubrique d'évaluation — ConversationJudge

Le ConversationJudge évalue chaque conversation selon 9 dimensions :
**3 dimensions objectives (hard checks)** et **6 dimensions qualitatives (LLM judge)**.

---

## Dimensions objectives (Hard Checks)

Ces dimensions sont vérifiées de façon **déterministe, sans LLM**. Elles ont une vérité de terrain dans la `DecisionEnvelope` ou la `MemoryStore`.

### `ke_coherence`

**Question** : La recommandation du coach respecte-t-elle la décision du Knowledge Engine ?

Le KE produit une `DecisionEnvelope` avec un champ `action` :
- `deload` → le coach ne peut pas recommander d'augmenter
- `decrease` → idem
- `increase` / `slight_increase` → le coach ne peut pas recommander de réduire

**Résultat** : liste de violations avec numéro de tour et détail.

**Impact score** : Une contradiction KE plafonne le score global à 5/10, quelle que soit la qualité du reste.

---

### `medical_flag`

**Question** : Si le KE a signalé un renvoi médical, le coach l'a-t-il communiqué ?

Le KE peut poser `medical_referral=True` avec une `medical_referral_reason`. Dans ce cas, le coach **doit** mentionner qu'une consultation médicale est recommandée.

**Résultat** : failure si `medical_referral=True` et aucun mot-clé médical ("médecin", "docteur", "consulter"...) n'apparaît dans toute la conversation.

---

### `memory_utilization`

**Question** : Le coach a-t-il référencé des décisions passées pertinentes quand elles existent ?

Si la `MemoryStore` contient des décisions passées pour le coureur, le coach devrait en tenir compte. On vérifie heuristiquement la présence de marqueurs temporels ("précédemment", "semaine dernière", "historique"...) dans les réponses.

**Limite** : vérification heuristique — peut produire des faux négatifs si le coach référence la mémoire sans utiliser ces mots-clés.

---

## Dimensions qualitatives (LLM Judge)

Ces dimensions sont évaluées par un deuxième LLM (DeepSeek-V3, température 0.2) à partir du transcript complet, du profil coureur et des données KE. Score de 1 à 5.

### Pondération

| Dimension | Poids |
|---|---|
| `question_answered` | 30% |
| `factual_groundedness` | 20% |
| `tone_appropriateness` | 15% |
| `pedagogical_quality` | 15% |
| `conversation_coherence` | 12% |
| `empathy` | 8% |

---

### `question_answered` — 30%

**Question** : Le coach a-t-il réellement répondu à ce que le coureur a demandé ?

| Score | Exemple |
|---|---|
| 1 | Le coureur demande "pourquoi réduire ?", le coach répète uniquement la recommandation sans expliquer. |
| 3 | Le coach explique une raison principale mais en omet d'importantes (ex : seule la fatigue mentionnée, pas l'ACWR). |
| 5 | Le coach répond directement avec les éléments précis (règles déclenchées, métriques) qui motivent la décision. |

---

### `factual_groundedness` — 20%

**Question** : Les chiffres et faits cités sont-ils ancrés dans les données réelles ?

| Score | Exemple |
|---|---|
| 1 | Le coach cite un ACWR de 1.6 alors que l'enveloppe indique 1.1 — chiffre inventé. |
| 3 | Les tendances sont correctes mais certains chiffres sont arrondis de façon inexacte. |
| 5 | Tous les chiffres correspondent exactement aux données de l'enveloppe et du profil coureur. |

---

### `tone_appropriateness` — 15%

**Question** : Le ton est-il adapté au profil du coureur ?

| Score | Exemple |
|---|---|
| 1 | Coureur anxieux débutant — coach répond de façon très technique et froide, sans rassurer. |
| 3 | Ton globalement correct mais quelques formulations trop abruptes pour le profil. |
| 5 | Ton parfaitement adapté — rassurant pour l'anxieux, challengeant pour l'ambitieux, pragmatique pour le parent pressé. |

---

### `pedagogical_quality` — 15%

**Question** : L'explication est-elle claire et actionnable pour ce coureur ?

| Score | Exemple |
|---|---|
| 1 | Utilise des termes techniques (ACWR, ATL, CTL) sans les définir pour un débutant. |
| 3 | Explication correcte mais sans suggestion d'action concrète pour la semaine suivante. |
| 5 | Explication claire avec analogie accessible, raison précise, et action concrète recommandée. |

---

### `conversation_coherence` — 12%

**Question** : La conversation est-elle exempte de contradictions entre les tours ?

| Score | Exemple |
|---|---|
| 1 | Tour 1 : "je te recommande de réduire". Tour 3 : "tu peux augmenter ta charge" — contradiction directe. |
| 3 | Pas de contradiction flagrante mais le ton ou les chiffres varient sans raison entre les tours. |
| 5 | Chaque réponse s'appuie sur les précédentes, cohérence parfaite sur toute la conversation. |

---

### `empathy` — 8%

**Question** : Le coach a-t-il reconnu la dimension humaine de la conversation ?

| Score | Exemple |
|---|---|
| 1 | Le coureur dit être épuisé — le coach répond uniquement avec des données sans reconnaître la fatigue. |
| 3 | Le coach mentionne brièvement que la fatigue est normale sans s'y attarder. |
| 5 | Le coach reconnaît explicitement l'effort, valide la fatigue, et adapte sa recommandation en conséquence. |

---

## Score global

Le score global (0–10) est calculé ainsi :

1. Moyenne pondérée des 6 dimensions qualitatives → score 1–5
2. Multiplié par 2 → score 0–10
3. Si `ke_coherence` hard check échoue → plafonné à 5/10

**Formule** :
```
score = (Σ dimension_score × poids) / Σ poids × 2
score = min(score, 5) si ke_contradiction existe
```

---

## Limites connues

- Le judge LLM peut avoir un biais de sycophantie (tendance à scorer haut). Température 0.2 atténue ce biais mais ne l'élimine pas.
- `memory_utilization` est heuristique — faux négatifs possibles.
- `ke_coherence` utilise des mots-clés — peut manquer des contradictions formulées de façon indirecte.
- Les scores LLM sont stochastiques : même conversation → variance possible de ±0.5 point.
