---
id: KN-002
title: Multiplexage PTY et Isolation de Contexte Herdr
domain: agentic-patterns
status: VALIDATED
confidence_score: 0.95
tags: [herdr, pty, subagents, context-isolation, daemon]
related_adrs: [ADR-0029, ADR-0203, ADR-0205]
---

# 🐑 Multiplexage PTY et Isolation de Contexte Herdr

> [!ABSTRACT]
> Gestion déterministe de sous-agents via le multiplexeur Herdr PTY v0.8.0, garantissant l'absence de fuites de contexte et l'isolation des processus lourds.

## 1. Principes Fondamentaux
- **Protocole Fork & Harvest** : worker-spawn $\rightarrow$ [mission] $\rightarrow$ worker-harvest $\rightarrow$ worker-close.
- **Teardown Gate** : Obligation de fermer chaque session worker avant la fin du tour principal (zéro session zombie).
- **Isolation Contextuelle** : Les sous-agents démarrent avec un contexte propre (Clean Slate) évitant de saturer la fenêtre de contexte de l'orchestrateur.
