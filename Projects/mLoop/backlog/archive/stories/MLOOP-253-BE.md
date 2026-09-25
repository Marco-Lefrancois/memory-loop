---
id: MLOOP-253-BE
jira_key: ''
epic_key: EPIC-25-OPENCODE-ECOSYSTEM-HARNESS
type: Enabler
title: "Adaptateur Protocolaire Expérimental OpenCode ACP (JSON-RPC)"
tags:
- opencode
- acp
- json-rpc
- client
- worker
- backend
origin: SPEC_SLICING
source_ref: EPIC-25-§3
macro_size: L
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-25'
layer: backend
blocked_by:
- MLOOP-250-BE
created_at: '2026-09-24'
updated_at: '2026-09-25'
---

# 📖 MLOOP-253-BE : Adaptateur Protocolaire Expérimental OpenCode ACP (JSON-RPC)

## Description
**En tant qu'** Architecte Système et Orchestrateur Swarm mLoop,  
**je veux** un adaptateur client basé sur l'Agent Client Protocol (ACP) pour dialoguer en JSON-RPC bidirectionnel avec `opencode acp`,  
**afin d'** exécuter des workers d'implémentation de stories via un canal structuré haute fidélité, éliminant définitivement la fragilité des pseudo-terminaux (PTY) et du scraping de logs.

---

## Contexte & Périmètre

### Contexte Métier
L'exécution de workers d'implémentation reposait jusqu'ici sur des sessions de terminal virtuelles PTY, sujettes aux artefacts ANSI, aux coupures imprévues et aux difficultés de détection de fin de tour. L'Agent Client Protocol (ACP), standardisé par OpenCode, Zed et JetBrains, fournit une interface JSON-RPC typée sur les flux standard (stdin/stdout). Ce récit livre le client d'orchestration Python permettant de piloter des tâches OpenCode en tâche de fond.

**Décisions Grill-Me (2026-09-25) :**
- **Mode non-interactif confiné** : handshake ACP avec octroi automatique des permissions de lecture/écriture confinées strictement au répertoire de travail du projet (`workspace_root`). Tout accès hors frontière est automatiquement rejeté.
- **Gestion des délais d'expiration adaptatifs** : timeout de 180s par tour nominal, étendu à 480s pour les modèles de raisonnement long (Thinking models), réinitialisé à chaque réception de delta streamé (`message/chunk`).
- Coexistence avec l'adaptateur PTY existant, sélectionnable par configuration.

### In-Scope
- Développement du client asynchrone `src/bridges/opencode/acp_client.py` (≤ 300 lignes, ADR-0202).
- Gestion du cycle de vie du sous-processus `opencode acp` (initialisation, handshake des capacités, terminaison propre).
- Envoi et réception de messages JSON-RPC typés (`session/create`, `session/prompt`, `session/cancel`).
- Gestionnaire d'événements pour le streaming de réponses et la capture des diffs de code.
- Maintien d'un banc de tests mocké sans dépendance réseau.

### Out-of-Scope
- Remplacement immédiat forcé des workers Claude Code ou Codex (l'adaptateur ACP est dédié à OpenCode).
- Implémentation du côté serveur d'ACP (mLoop agit uniquement en tant que client ACP).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Client ACP — OpenCodeAcpClient
* **Entrée Métier** : Chemin du binaire `opencode`, répertoire de travail cible, paramètres de session.
* **Traitement & Algorithme Métier** :
  - Démarrage du sous-processus `opencode acp`.
  - Négociation de protocole (handshake v1) et échange des capacités.
  - Émission de prompts d'implémentation avec streaming des tokens.
  - Détection automatique et gestion des demandes d'autorisation dans les limites du workspace.
* **Résultat Métier & Mutations** : Exécution fluide de la tâche avec restitution structurée des modifications de fichiers et des logs d'exécution.

#### 2. Tolérance aux Pannes & Timeouts
* **Règles de Robustesse** : Si le processus distant cesse d'émettre des événements au-delà du seuil de timeout adaptatif, le client envoie un `session/cancel` ordonné puis termine le sous-processus.

---

## Règles d'affaires

- **Confinement Workspace Inviolable** : Le client ACP interdit formellement toute modification de fichier située en dehors du `workspace_root` déclaré.
- **Zéro Fuite de Processus** : En cas d'erreur ou d'interruption mLoop, le sous-processus `opencode acp` est immédiatement tué pour éviter les processus zombies.
- **Plafond Modulaire AST** : `src/bridges/opencode/acp_client.py` $\le 300$ lignes et $\le 15$ Ko (ADR-0202).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Gestionnaire Swarm Workers** : `src/swarm/`
- 📂 **Pont OpenCode existant** : `src/commands/handlers/opencode.py`
- 🏛️ **ADR** : [ADR-0377](../../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md) · [ADR-0369](../../../standards/adr-system/0369-standard-robustesse-python-senior.md) · [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📋 **Epic** : [`epics/epic_opencode_ecosystem_harness.md`](../epics/epic_opencode_ecosystem_harness.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Adaptateur Protocolaire OpenCode ACP (JSON-RPC)

  Scénario: Pilier 1 - Nominal (Happy path) : Handshake initial et exécution d'un tour
    Étant donné un serveur opencode acp simulé
    Quand le client OpenCodeAcpClient se connecte et initialise la session
    Alors le handshake ACP v1 est validé avec succès
    Et l'envoi d'un prompt produit un flux d'événements typés jusqu'à turn/completed

  Scénario: Pilier 2 - Exceptions (Cas d'erreur) : Échec de négociation de protocole
    Étant donné un serveur répondant avec une version incompatible d'ACP
    Quand le client tente d'établir la session
    Alors une exception AcpProtocolError est levée immédiatement
    Et le processus sous-jacent est nettoyé sans blocage

  Scénario: Pilier 3 - Résilience (Timeout adaptatif) : Réinitialisation du timeout sur streaming
    Étant donné une requête complexe sur modèle Thinking générant des deltas réguliers
    Quand le délai dépasse 180s mais que des événements sont reçus
    Alors le compteur de timeout est prolongé jusqu'à la limite haute de 480s
    Et la tâche va à son terme sans interruption prématurée

  Scénario: Pilier 4 - UX (Observabilité & Confinement) : Journalisation claire des requêtes
    Étant donné l'exécution d'un worker ACP sous mLoop
    Quand des échanges JSON-RPC ont lieu
    Alors les messages de traces sont épurés des artefacts de contrôle
    Et l'opérateur dispose d'une visibilité limpide sur l'avancement du worker
```
