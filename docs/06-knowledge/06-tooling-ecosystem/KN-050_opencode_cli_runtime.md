---
id: KN-050
title: OpenCode CLI Runtime & Orchestration Multi-Fournisseurs
domain: tooling-ecosystem
status: VALIDATED
confidence_score: 0.97
tags: [opencode, cli, tui, runtime, litellm, orchestration]
related_adrs: [ADR-0003, ADR-0200, ADR-0370]
---

# 💻 OpenCode CLI Runtime & Orchestration Multi-Fournisseurs

> [!ABSTRACT]
> Runtime CLI et TUI permettant l'orchestration directe d'agents d'ingénierie logicielle avec configuration déclarative modulaire (`opencode.json`), routage multi-fournisseurs (LiteLLM, Anthropic, Google, DeepSeek) et exécution déterministe.

## 1. Principes Fondamentaux & Mécanique
- **Configuration Déclarative** : Priorité ascendante entre la configuration globale (`~/.config/opencode/opencode.json`) et la configuration projet (`./opencode.json`).
- **Support Multi-Fournisseurs** : Définition des profils de modèles, proxies (ex: port 4000 pour LiteLLM) et clés d'API sans couplage au code source.
- **Modes d'Exécution Dual** :
  - *TUI Interactif* : Sessions immersives avec navigation dans l'arbre de contexte et validation humaine.
  - *CLI Non-Interactif / Headless* : Mode scriptable pour pipelines d'automatisation et intégration continue.
- **Règles & Prompts Dédiés** : Injection de consignes contextuelles via `rules` ou templates markdown spécifiques au projet.

## 2. Découpage Épistémique
- **what_it_actually_proves** : Capacité à piloter des agents de développement en mode local ou distribué avec isolation des configurations de modèles.
- **what_it_does_not_prove** : Ne remplace pas la mémoire épistémique à long terme (LLM-Wiki) ni la gouvernance de graphe d'un dépôt complexe sans l'intégration de Memory Loop.
