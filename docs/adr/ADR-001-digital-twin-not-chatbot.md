# ADR-001: Construire un digital twin, pas un chatbot RAG

## Statut
Accepté — 2026-07-19

## Contexte

Le point de départ naturel pour un projet "IA + données sportives" serait
de construire un chatbot RAG sur les données Strava : importer les activités,
les vectoriser, et répondre à des questions comme "quelle était ma meilleure
semaine ?".

Cette approche est rapide à démarrer mais fondamentalement limitée :
un système RAG récupère de l'information, il ne représente pas un état persistant.
Il ne peut pas modéliser l'évolution d'un athlète dans le temps, détecter une
progression, ni raisonner sur une fatigue accumulée.

## Décision

Le projet construit un **digital twin** de l'athlète — un modèle persistant
qui suit son évolution dans le temps — plutôt qu'un chatbot qui interroge
un corpus de documents.

L'ordre de développement est fixé :

```
Data Engine → Runner Intelligence → Activity Intelligence
→ Runner Model → Knowledge Engine → Coach Agent
```

Le RAG n'intervient qu'au niveau du Knowledge Engine, pour la mémoire
sémantique et le contexte qualitatif. Jamais comme couche principale.

## Conséquences

- Le développement est plus long avant d'avoir un produit visible.
- La base de données est la source de vérité pour les données quantitatives.
- Le LLM est un moteur de raisonnement, pas une source de faits sur l'athlète.
- Chaque couche doit être stable avant de passer à la suivante.
- L'architecture finale sera plus robuste et plus utile qu'un chatbot générique.
