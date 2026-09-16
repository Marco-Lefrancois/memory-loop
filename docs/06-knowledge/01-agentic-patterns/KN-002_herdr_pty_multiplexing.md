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

## 2. Observabilité & Contournement Timeout (Lacune L-01)
> [!WARNING]
> Le binaire Herdr natif (`cli:agent:wait`) présente des faux timeouts intermittents (`timed out waiting for agent status`) alors que le worker PTY travaille nominalement.
> 
> **Contournement officiel normatif** :
> 1. Ne pas bloquer l'orchestrateur sur `worker-wait`.
> 2. Utiliser la lecture PTY non-bloquante : `python src/swarm.py worker-status --project <nom> --story <ID>` ou `worker-read --source recent-unwrapped`.
> 3. Consulter le signal sidecar dans `memory/worker_<ID>.status` (ADR-0355).
