# Knowledge Engine — MirrorPace

Ce dossier contient la base de connaissances d'entraînement de MirrorPace.

Il est **volontairement vide au départ**. Aucune connaissance ne doit être ajoutée sans source externe identifiée et tracée.

---

## Principe de traçabilité

Chaque décision du coach doit pouvoir être remontée jusqu'à sa source :

```
Décision du coach
    ↓
Règle décisionnelle  (rules/)
    ↓
Principe             (principles/)
    ↓
Source externe       (sources/)
```

Ce chaîne de traçabilité est non négociable. Elle garantit que le coach ne décide pas à partir de connaissances inventées ou non vérifiées.

---

## Les trois niveaux de connaissance

### Source (`sources/`)

Un document externe brut : livre, article scientifique, interview, vidéo.

Une source décrit ce qu'un auteur ou chercheur affirme. Elle n'est pas encore interprétée.

Exemples :
- un livre de Jack Daniels sur la physiologie de la course
- une étude sur la relation entre volume et blessure
- une interview d'un entraîneur d'élite

### Principe (`principles/`)

Une connaissance extraite d'une ou plusieurs sources, reformulée de manière générale et applicable.

Un principe n'est **pas encore une règle**. Il décrit ce qui est vrai dans un contexte donné, avec ses limites et ses exceptions.

Exemple :
> "La progression de charge doit être adaptée à l'expérience et à l'historique du coureur."

Un principe répond à la question : *"Que sait-on sur ce sujet ?"*

### Règle décisionnelle (`rules/`)

La transformation opérationnelle d'un principe en logique utilisable par le coach.

Une règle répond à la question : *"Dans cette situation, quelle décision un coach pourrait-il prendre ?"*

Exemple :
> "Si la charge augmente rapidement et que les indicateurs de récupération se dégradent, envisager une réduction temporaire."

---

## Rôle du Knowledge Engine

Le Knowledge Engine permet à l'agent coach de :

- comprendre les méthodologies d'entraînement existantes
- justifier chaque décision par une règle, elle-même ancrée dans des sources
- combiner plusieurs écoles de coaching
- adapter les principes généraux au profil individuel du coureur

---

## Ce que ce dossier n'est pas

- Ce n'est pas un wiki personnel de Christian
- Ce n'est pas un résumé de ce que Claude sait sur la course
- Ce n'est pas un recueil de conseils génériques

Tout ce qui est ajouté ici doit provenir d'une source externe identifiée.

---

## Structure

```
knowledge/
├── research_queue/     — questions auxquelles la recherche doit répondre
├── sources/            — documents externes bruts
├── principles/         — connaissances extraites des sources
├── rules/              — logique décisionnelle pour le coach
└── metadata/           — registre global des sources
```
