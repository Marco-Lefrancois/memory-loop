# ADR-0371 : Paradigme Dual Harnais Préventif & Point-in-Time Recovery Agentique (Synthèse Cohesity Agent Resilience)

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-16
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Cœur d'orchestration mLoop (src/pipelines/agent_resilience.py), Gestion d'état (src/state.py), Registre CLI (src/commands/_registry.py), Commandes gent-resilience, 	opology, 
ollback
- **Autorité** : [ADR-0001](0001-python-state-graph.md), [ADR-0310](0310-vibe-code-session-resume.md), [ADR-0335](0335-deep-paper-note-ingestion-epistemic-grounding.md), [ADR-0346](0346-specialized-agent-delegation-gates.md), [ADR-0355](0355-sortie-inspired-resilient-subagent-and-handoff-architecture.md), [ADR-0364](0364-hooks-pre-compaction-et-checkpoint-boundaries.md), [ADR-0370](0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md)

---

## 1. Contexte & Problématique

Le 16 septembre 2026, à la conférence Catalyst, Cohesity a officiellement annoncé **Cohesity Agent Resilience**, une initiative majeure étendant la cyber-résilience aux infrastructures d'agents IA (avec support initial sur Amazon Bedrock AgentCore et une feuille de route pour Microsoft et Google Cloud).

L'analyse de cette annonce et son croisement avec les invariants mLoop (documentés dans 
eference/Croisement Cohesity mLoop.pdf et normalisés dans docs/00-ingested/Croisement_Cohesity_mLoop.md) confirment un postulat fondateur :
> *« La détection peut indiquer qu'un agent a dévié, mais elle ne peut pas annuler les modifications. »*

Les observatoires, linters et tours de contrôle d'IA détectent les anomalies et dérives cognitives après coup, mais manquent d'un **chemin de reprise déterministe (*recovery path*)**. L'état opérationnel d'un agent (mémoire épisodique, contexte appris, prompts, identifiants, guardrails) constitue un actif critique distinct. Si cet état est empoisonné (par injection indirecte, dérive de raisonnement ou scope creep), toutes les décisions ultérieures sont corrompues, même si le code source de l'agent est intact.

---

## 2. Diptyque Épistémique & Analyse Comparative

### 2.1 Matrice Fondamentale : Prévention Proactive vs Restauration Curative

| Dimension | Cohesity Agent Resilience | Memory Loop (mLoop v2.x) | Synthèse & Synergie R&D (ADR-0371) |
| :--- | :--- | :--- | :--- |
| **Philosophie d'intervention** | **Réactive / Curative** : Restauration après sinistre (*Recovery / Clean-Room*). | **Proactive / Préventive & Invariante** : Bloquer la dérive avant l'écriture via le Système 1. | **Paradigme Dual** : Prévention stricte en amont (SCC) doublée d'un filet de sécurité curatif déterministe (Rollback PITR). |
| **Protection de l'état (Agent State)** | Snapshots, sauvegardes immuables et point-in-time recovery (PITR). | Schéma Pydantic strict LoopState, OpaqueArtifactBus scellé par SHA-256. | Checkpoints horodatés avec empreintes SHA-256 d'EvidencePacks pour restauration sélective par étape. |
| **Périmètre cible (What Agents Manage)** | Restauration des bases et systèmes de fichiers altérés par l'agent. | Règle d'or Zéro Code Source : story_guard.py et contrats stricts SCC. | Audit pré-vol de la topologie et calcul du **Blast Radius** avant tout lancement de worker unattended. |
| **Écosystème & Souveraineté** | Cloud entreprise managé (AWS Bedrock, Azure, Google Cloud). | Souveraineté Locale Absolue : 100% local, SQLite FTS5, L3 In-Memory, sockets herdr.sock. | 100% exécutable en local sans aucune dépendance cloud propriétaire. |
| **Gestion mémoire corrompue** | Restauration d'un snapshot sain antérieur (*known-good state*). | Hygiène continue par tombstoning (dream_collector), isolation PTY et règles RHO. | Restauration granulaire d'une sous-partition mémoire altérée sans écraser les artefacts sains validés. |

### 2.2 Validation Industrielle de la Thèse « Harnais > Modèle »
Le positionnement de Cohesity valide empiriquement que l'intelligence probabiliste des LLMs requiert obligatoirement un harnais logiciel externe d'infrastructure d'état pour garantir l'intégrité, l'idempotence et la récupérabilité des flux de travail autonomes.

---

## 3. Décisions d'Architecture mLoop

`	ext
┌────────────────────────────────────────────────────────────────────────────────────────┐
PARADIGME DUAL HARNAIS PRÉVENTIF & RESTAURATION CURATIVE (ADR-0371)     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [AMONT : PRÉVENTION ABSOLUE]                                                         │
│   Story Constraint Contract (SCC) ──> story_guard.py ──> Boundary Système 1             │
│   (Interdiction formelle de toute écriture hors périmètre contractuel)                 │
│                                                                                        │
│   [PRE-FLIGHT : AUDIT DE TOPOLOGIE & BLAST RADIUS]                                     │
│   python src/swarm.py topology --agent <role>                                          │
│   └──> Cartographie : Agent -> [Partitions Mémoire, Répertoires Cibles, Outils]        │
│   └──> Calcul Blast Radius (Surface d'exposition & Autorisation Unattended)             │
│                                                                                        │
│   [AVAL : FILET DE SÉCURITÉ & RESTAURATION DÉTERMINISTE]                               │
│   SavepointManager (In-Flight Snapshots) + EvidencePacks SHA-256                         │
│   └──> python src/swarm.py rollback --step <n>                                         │
│   └──> Restauration sélective : LoopState + Partition Mémoire ciblée                  │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
`

### 1. Cartographie Topologique et Calcul du Rayon d'Impact (AgentTopologyMapper)
mLoop intègre un moteur de découverte topologique assignant à chaque rôle d'agent (orchestrator, worker, 
esearch, qa, crawler, sentinel) son enveloppe de droits stricts :
- Répertoires d'écriture autorisés (ex: docs/, acklog/, 
eference/research/, memory/).
- Interdiction des répertoires vitaux (code client en mode client, fichiers d'environnement .env).
- Calcul d'un score de *Blast Radius* (Faible, Modéré, Élevé, Critique) conditionnant l'autorisation d'exécution en mode autonome non supervisé (*Unattended*).

### 2. Restauration Déterministe Point-in-Time (AgentStateRollbackEngine)
- Extension de SavepointManager (src/state.py) pour lier à chaque snapshot une signature d'intégrité SHA-256 des artefacts produits et des EvidencePacks.
- Commande CLI python src/swarm.py rollback --step <n> permettant de remonter à une étape saine précédente avec restauration sélective :
  - Restauration de LoopState au step ciblé.
  - Purge des partitions mémoires corrompues tout en préservant les livrables validés par les portes de gouvernance antérieures.

### 3. Audit de Résilience Agentique (ResilienceAudit)
- Commande CLI python src/swarm.py agent-resilience inspectant :
  - La présence et la fraîcheur des checkpoints in-flight.
  - La parité des empreintes SHA-256 des EvidencePacks.
  - L'hygiène de session (SESSION_MEMORY_HEALTH.md) et le risque d'empoisonnement contextuel.

---

## 4. Conséquences & Invariants

- **Hybridation Préventive / Curative** : mLoop conserve son avantage amont (zéro écriture non autorisée) tout en s'armant de la capacité de retour arrière déterministe si un raisonnement dévie dans son périmètre légitime.
- **Auditabilité Cryptographique** : Chaque étape restaurable est adossée à un EvidencePack scellé par SHA-256.
- **Zéro Régression de Souveraineté** : Aucun tiers cloud requis. Tout le mécanisme de topologie et de snapshot opère localement via Python et le système de fichiers standard.
