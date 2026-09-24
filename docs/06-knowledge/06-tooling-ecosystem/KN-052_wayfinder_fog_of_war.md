---
id: KN-052
title: Pattern Wayfinder — Cartographie Décisionnelle et Navigation dans le Brouillard
domain: tooling-ecosystem
status: VALIDATED
confidence_score: 0.96
tags: [wayfinder, fog-of-war, decision-mapping, hitl, afk-subagents, big-ideas]
related_adrs: [ADR-0201, ADR-0204, ADR-0315]
---

# 🧭 Pattern Wayfinder — Cartographie Décisionnelle et Navigation dans le Brouillard

> [!ABSTRACT]
> Mécanisme d'on-ramp pour initiatives complexes : découpe un effort trop massif ou brumeux pour une seule session d'agent en une carte partagée de tickets de décisions (questions à trancher) plutôt qu'en tranches d'exécution technique prématurées.

## 1. Principes Fondamentaux & Mécanique
- **Planifier, ne pas exécuter** : Chaque ticket résout une question ou un arbitrage d'architecture. La carte est terminée lorsque l'itinéraire est limpide et qu'il ne reste plus rien à trancher avant de construire.
- **La Destination comme Pivot** : Définie avant le premier ticket, la destination fixe le périmètre contre lequel chaque décision est mesurée.
- **Brouillard de Guerre & Frontière** :
  - *Frontière* : Tickets débloqués, formulables avec précision ici et maintenant.
  - *Brouillard* : Décisions à venir que l'on pressent mais que l'on ne peut pas encore spécifier. Résoudre un ticket de la frontière dissipe le brouillard et gradue de nouveaux tickets.
- **Typologie Duale des Tickets** :
  - *HITL (Human In The Loop)* : Résolu via échange interactif (grilling, clarification). L'agent ne répond jamais à ses propres questions critiques.
  - *AFK (Agent Alone)* : Tickets d'investigation ou de benchmark confiés à un sous-agent `/research` asynchrone pour ne pas ralentir la session principale.

## 2. Découpage Épistémique
- **what_it_actually_proves** : Prévient l'effet « tunnel » où un agent commence à coder un projet d'envergure sans avoir levé les incertitudes conceptuelles majeures.
- **what_it_does_not_prove** : Ne produit pas le livrable logiciel final ; une fois la route dégagée, la main doit être passée à la spécification technique fine (ex: `to-spec` ou phase planning mLoop).
