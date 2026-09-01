---
id: KN-040
title: Standard BDD Gherkin 4 Piliers, INVEST et Pureté Déclarative
domain: software-spec
status: VALIDATED
confidence_score: 0.99
tags: [gherkin, 4-pillars, invest, bdd, vertical-slicing, scc]
related_adrs: [ADR-0300, ADR-0301, ADR-0319]
---

# 📐 Standard BDD Gherkin 4 Piliers, INVEST et Pureté Déclarative

> [!ABSTRACT]
> Spécification fonctionnelle formelle exigeant que chaque User Story soit découpée verticalement et couverte par 4 piliers Gherkin stricts (Nominal, Exceptions, Résilience, UX).

## 1. Les 4 Piliers Gherkin Obligatoires
1. **Pilier 1 (Nominal)** : Scénarios nominaux d'utilisation heureuse (Happy Path).
2. **Pilier 2 (Exceptions & Erreurs)** : Cas limites, validations de formulaires, erreurs 4xx/5xx.
3. **Pilier 3 (Résilience & Réseau)** : Mode hors-ligne, timeouts, retry, reprise d'état.
4. **Pilier 4 (Interface & UX)** : Les 4 états d'UI (Empty, Loading, Error, Success) et accessibilité.
