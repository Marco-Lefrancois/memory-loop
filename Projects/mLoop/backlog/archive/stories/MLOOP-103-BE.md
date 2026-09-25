---
id: MLOOP-103-BE
jira_key: '-'
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Feature
title: Transport MCP Réseau et Diffusion Événementielle SSE
tags: [mcp, sse, events, realtime, streaming, protocol-2026]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-10-SOVEREIGN-EXCELLENCE] Transport MCP Réseau et Diffusion Événementielle SSE (MLOOP-103-BE)

---

## Description
**En tant qu'** Orchestrateur Multi-Agents / Client MCP Distant,  
**je veux** disposer d'un transport réseau HTTP avec Server-Sent Events (SSE) et notifications asynchrones sur le serveur MCP mLoop,  
**afin de** recevoir en temps réel les flux d'observations, les changements de phase et les invalidations de cache sans recourir au polling bloquant stdio.

---

## Contexte & Périmètre

### Contexte Métier
Le serveur MCP actuel `src/bridges/mcp_loop_mem.py` fonctionne nativement en flux `stdio`, ce qui est parfait pour une extension IDE locale mais limite la communication temps réel lorsqu'un agent externe, un conteneur ou un tableau de bord distant souhaite s'abonner aux événements de session. L'ajout d'un point de terminaison HTTP SSE (conforme aux spécifications officielles du Model Context Protocol) permet la diffusion unidirectionnelle réactive des événements `resources/updated` et `tools/list_changed`.

### In-Scope
- Module de transport réseau `src/bridges/mcp_sse_server.py` ($\le 300$ lignes).
- Support double-mode : conservation intégrale du canal standard `stdio` et activation optionnelle du port HTTP SSE (`--port <port>` ou via `swarm.py`).
- Émission d'événements MCP `notifications/resources/updated` lors de l'ajout d'observations ou d'engrammes.
- Émission de `notifications/tools/list_changed` lors d'un basculement dynamique de phase d'exécution (ADR-0309).
- Banc de tests d'intégration simulant un client SSE réactif avec validation du handshake et de la réception des trames.

### Out-of-Scope
- Remplacement du protocole stdio pour les outils CLI existants (stdio reste le mode par défaut).
- Mise en place d'un système de gestion de droits complexes multi-utilisateurs (RBAC d'entreprise).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Diffusion Réactive des Événements MCP via Flux SSE
* **Entrée Métier** : Requête de connexion HTTP GET avec en-tête `Accept: text/event-stream` et identifiant de session mLoop.
* **Règles d'admissibilité & Validation** : Le serveur doit négocier la connexion SSE, attribuer un canal d'écoute isolé et envoyer immédiatement l'événement de bienvenue avec le protocole supporté.
* **Traitement & Algorithme Métier** : Maintien d'un pool de connexions asynchrones clientes, diffusion non-bloquante des trames JSON-RPC au format SSE `data: {...}\n\n` lors de chaque mutation de ressource ou de changement de toolset.
* **Résultat Métier & Mutations** : Notification instantanée des clients connectés avec latence inférieure à 50 millisecondes et conservation de l'intégrité de la session stateful.
* **Cas de Rejet Métier** : Déconnexion gracieuse et libération immédiate des ressources lors de la fermeture inattendue du socket client.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Transport MCP Réseau et Diffusion Événementielle SSE

  # CHEMIN NOMINAL
  Scénario: Établissement de connexion SSE et réception d'un événement d'invalidation
    Étant donné un serveur MCP démarré avec l'option transport réseau active
    Quand un client agent s'abonne au flux d'événements Server-Sent Events
    Alors la connexion est acceptée avec le type mime text/event-stream
    Et le client reçoit la notification lors de l'insertion d'une nouvelle observation

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet de trame JSON-RPC malformée sur le canal réseau
    Étant donné un message entrant ne respectant pas la spécification JSON-RPC 2.0
    Quand le serveur inspecte la charge utile
    Alors une réponse d'erreur standardisée avec code ParseError est retournée
    Et le flux d'événements des autres abonnés n'est pas perturbé

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Nettoyage et résilience lors de la déconnexion brutale d'un abonné
    Étant donné un client fermant brutalement sa connexion TCP
    Quand le serveur tente d'émettre la prochaine notification
    Alors l'abonné fantôme est purgé du pool des écouteurs sans lever d'exception non gérée
    Et les performances du serveur restent constantes

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Notification dynamique de changement de toolset lors d'un saut de phase
    Étant donné un agent effectuant une transition de la phase PLAN vers la phase BUILD
    Quand le registre des outils autorisés se reconfigure
    Alors l'événement tools/list_changed est émis sur le canal SSE
    Et le client met à jour son cache d'outils sans avoir à redémarrer sa session
```
