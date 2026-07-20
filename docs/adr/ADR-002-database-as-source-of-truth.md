# ADR-002: La base de données est la source de vérité quantitative

## Statut
Accepté — 2026-07-19

## Contexte

Dans un système LLM-first, on serait tenté de laisser le modèle répondre
directement à des questions sur les métriques : "quelle est ma allure moyenne
sur les 4 dernières semaines ?". C'est simple à implémenter mais dangereux :
les LLMs hallucinent sur les calculs, et les résultats ne sont pas reproductibles.

Alternativement, on pourrait tout vectoriser et faire du RAG sur les activités
brutes. Mais une requête d'agrégation sur 39 activités ne se fait pas bien
par similarité sémantique.

## Décision

Toutes les données quantitatives (distance, durée, allure, dénivelé, FC)
sont stockées dans une base de données relationnelle (SQLite en développement,
PostgreSQL possible en production).

Les calculs sur ces données (moyennes, tendances, charges) sont effectués
de façon déterministe par le code, pas par le LLM.

Le LLM reçoit des **faits calculés**, pas des données brutes à interpréter.

## Conséquences

- Les métriques sont reproductibles et vérifiables.
- Le LLM ne peut pas halluciner sur les chiffres de l'athlète.
- SQLite suffit pour un athlète unique — pas de sur-ingénierie.
- Les données brutes (fichiers FIT/GPX) sont toujours préservées.
- La DB est une donnée dérivée : elle se reconstruit depuis l'export Strava.
