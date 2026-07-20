# ADR-003: Le coach s'adapte aux données disponibles

## Statut
Accepté — 2026-07-20

## Contexte

Certaines données souhaitables sont structurellement absentes ou difficiles
à obtenir. Dans ce projet :

- La fréquence cardiaque n'est pas disponible : la Huawei Watch Fit enregistre
  la FC, mais Strava ne l'inclut pas dans l'export gratuit, et l'API Strava
  est désormais payante. Un export manuel depuis Huawei Health est possible
  mais activité par activité.
- D'autres données (puissance, VFC, sommeil) peuvent manquer selon le matériel
  ou la période.

Il serait tentant de bloquer le développement ou l'analyse jusqu'à ce que
toutes les données idéales soient disponibles.

## Décision

Le coach raisonne avec ce qui existe. Il ne bloque pas sur ce qui manque.

Chaque couche du système (Runner Intelligence, Coach Agent) est conçue
pour dégrader gracieusement : si la FC est absente, l'analyse porte sur
l'allure et le volume. Si la FC est présente, elle enrichit l'analyse.

Les champs manquants en DB (`avg_hr`, `max_hr`) restent `NULL` — ils sont
prêts à être renseignés si les données deviennent disponibles.

## Conséquences

- Le système est utilisable dès maintenant, sans attendre un dataset parfait.
- L'ajout de nouvelles sources de données (ceinture HR, nouvelle montre,
  export Huawei Health) enrichit automatiquement les analyses sans refonte.
- Le coach ne génère pas d'affirmations sur des données qu'il n'a pas.
- Cette règle s'applique à toutes les futures intégrations matérielles.
