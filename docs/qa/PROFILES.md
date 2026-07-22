# Profils SimulatedRunner — MirrorPace QA

Un profil est un **prompt système** qui pilote le SimulatedRunner. Il définit qui est l'utilisateur simulé : sa personnalité, ses objectifs, ses contraintes, sa façon de réagir aux réponses du coach.

Le SimulatedRunner **ne connaît pas** l'implémentation du CoachAgent. Il voit uniquement les réponses textuelles, exactement comme un utilisateur réel.

---

## Profils disponibles (v1)

### `anxious_beginner` — Débutant anxieux

**Lucas, 28 ans, 6 mois de course.**

Profil type : débutant enthousiaste mais facilement anxieux. Ne connaît pas les termes techniques. Cherche de la réassurance avant tout. Satisfait quand le coach explique simplement et rassure.

Test prioritaire : pédagogie, ton, empathie.

---

### `ambitious_marathoner` — Marathonienne ambitieuse

**Sophie, 35 ans, 3 marathons, objectif sub-3h30.**

Profil type : coureuse expérimentée qui veut toujours augmenter. Conteste les recommandations conservatrices. Accepte une décision si elle est justifiée par des données solides.

Test prioritaire : ke_coherence, question_answered, conversation_coherence.

---

### `injured_runner` — Coureur en reprise de blessure

**Marc, 42 ans, reprise après tendinite au genou.**

Profil type : coureur prudent qui surveille son corps. Mentionne explicitement sa blessure récente. Prend très au sérieux les alertes médicales.

Test prioritaire : medical_flag, empathy, ke_coherence.

---

### `cautious_runner` — Coureur très prudent

**Isabelle, 50 ans, 10 ans de course.**

Profil type : coureuse qui préfère systématiquement la sécurité à la performance. Suit les règles à la lettre. Pose des questions de vérification ("tu es sûr ?").

Test prioritaire : tone_appropriateness, factual_groundedness.

---

### `busy_parent` — Parent avec peu de temps

**Thomas, 38 ans, père de deux enfants, séances de 45 minutes max.**

Profil type : pragmatique, contraintes de temps réelles. Ne peut pas augmenter la durée des séances. Veut des recommandations adaptées à son contexte, pas des conseils génériques.

Test prioritaire : question_answered, pedagogical_quality, tone_appropriateness.

---

### `performance_obsessed` — Compétiteur obsédé par les données

**Kevin, 32 ans, 7 ans de course, connait ACWR/ATL/CTL.**

Profil type : connaît très bien les concepts. Conteste activement les recommandations. Cherche des failles dans le raisonnement du coach. Satisfait seulement avec une explication chiffrée et rigoureuse.

Test prioritaire : ke_coherence, factual_groundedness, question_answered.

---

## Créer un nouveau profil

Un profil est une instance de `RunnerProfile` dans `src/qa_agent/profiles/`.

```python
# src/qa_agent/profiles/mon_profil.py
from src.qa_agent.domain.schemas.runner_profile import RunnerProfile

PROFILE = RunnerProfile(
    id="mon_profil",                    # identifiant unique, snake_case
    display_name="Mon profil",          # nom lisible pour les rapports
    system_prompt="""
    Tu es [prénom], [âge] ans, [contexte].
    Tu as [caractéristique 1].
    Tu as tendance à [comportement 1].
    Tu es satisfait quand [condition de satisfaction].
    Si [condition], tu [réaction].
    """,
    opening_messages=[
        "message d'ouverture 1",        # au moins 2 messages
        "message d'ouverture 2",
    ],
    expected_intents=["ANALYSIS_REQUEST", "EXPLANATION_REQUEST"],
    tags=["tag1", "tag2"],
)
```

Puis ajouter l'import dans `src/qa_agent/profiles/__init__.py`.

---

## Principes pour écrire un bon profil

**1. Un comportement de satisfaction clair**
Le SimulatedRunner doit savoir quand arrêter. Définir explicitement : "Tu es satisfait quand le coach te donne X."

**2. Un comportement de contestation naturel**
Définir comment le coureur réagit à une réponse insatisfaisante. "Si la réponse est vague, tu poses une question de clarification." "Si le coach ignore ta contrainte, tu la rappelles."

**3. Un niveau de connaissance précis**
Un débutant ne sait pas ce qu'est l'ACWR. Un compétiteur le cite. Définir clairement ce que le coureur sait ou ne sait pas.

**4. Pas de fuite vers les intents internes**
Le profil ne doit pas mentionner "ANALYSIS_REQUEST" ou d'autres termes d'implémentation. Le coureur ne connaît pas le système.

---

## Vision d'évolution : profils humanisés

Les 6 profils actuels sont des **archétypes** : ils représentent des comportements extrêmes pour maximiser la couverture des cas de test.

La prochaine étape est de créer des **profils humanisés** : des personas avec des contraintes de vie réelles, croisées avec différents comportements de coureur.

### Exemples de contraintes humaines à intégrer

**Contraintes de temps :**
- Parent avec des enfants en bas âge → séances courtes, horaires fixes, impossibilité d'augmenter la durée
- Professionnel avec voyages fréquents → séances irrégulières, fuseaux horaires, hôtels sans accès piscine/piste
- Travailleur en horaires décalés → impossibilité de courir le matin certaines semaines

**Contraintes physiques :**
- Coureur avec un genou fragile → historique de blessure, sensibilité à l'augmentation du volume
- Asthmatique → sensibilité à la qualité de l'air, limitations sur l'intensité
- Coureur en surpoids → progression plus lente, sensibilité aux impacts

**Contraintes psychologiques :**
- Coureur après dépression → la course comme thérapie, hypersensibilité aux messages négatifs
- Coureur perfectionniste → frustration si les objectifs ne sont pas atteints
- Coureur après burnout → priorité au plaisir sur la performance

**Profils croisés (exemples) :**
- Marathonienne ambitieuse + mère de famille → veut sous-3h30 mais a 3 heures de course max par semaine
- Débutant anxieux + historique de blessure → double source d'anxiété
- Compétiteur obsédé + reprise de blessure → tension entre données favorables et prudence médicale

### Principe directeur

Un bon profil humanisé crée des **tensions internes** : le coureur veut quelque chose (performance, volume, validation) mais a des contraintes qui limitent ce qu'il peut faire. Ces tensions produisent les conversations les plus riches pour tester le coach.

> Exemple : Thomas est père de deux enfants et veut faire un marathon. Il ne peut pas augmenter la durée de ses séances. Comment le coach adapte-t-il sa recommandation à cette réalité ?

Ce niveau de complexité permettra de tester si le Coach Agent **écoute vraiment** et adapte ses réponses au contexte de l'utilisateur, plutôt que de produire des réponses génériques basées uniquement sur les métriques.
