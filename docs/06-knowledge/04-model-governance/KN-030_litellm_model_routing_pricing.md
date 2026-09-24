---
id: KN-030
title: Routage Multi-Modèles LiteLLM, Forensics & Gestion Budgétaire
domain: model-governance
status: VALIDATED
confidence_score: 0.95
tags: [litellm, pricing, budget, anti-sycophancy, routing]
related_adrs: [ADR-0308, ADR-0338]
---

# 💳 Routage Multi-Modèles LiteLLM, Forensics & Gestion Budgétaire

> [!ABSTRACT]
> Stratégie dynamique de sélection de modèles (Claude Opus 4.8, GPT-5.6 Terra Thinking, Claude Sonnet, Gemini Flash Lite) optimisant le compromis coût / latence / esprit critique.

## 1. Matrice de Sélection
- **Architecture & Grill Critique** : Modèles de raisonnement profond avec scepticisme agressif (Anti-Sycophancy).
- **Validation Déterministe & Linters** : Modèles légers et rapides (Gemini Flash Lite) pour respecter l'instruction budget.
- **Développement & Worker-Spawn (`build`)** : Free tier natif OpenCode `opencode/mimo-v2.6-flash-free` (ADR-0388, 24 sept. 2026) — zéro coût LiteLLM, hors du périmètre nmedia_cloud. Les task-types `deepening`/`validation`/`deepsearch`/`compaction` restent sur LiteLLM (portes qualité inchangées).
