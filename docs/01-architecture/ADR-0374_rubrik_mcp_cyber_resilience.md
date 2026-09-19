# ADR-0374 : Standard MCP de Cyber-Résilience Agentique & Workflows Déterministes Multi-Étapes (Synthèse Rubrik MCP & OWASP MCP Top 10)

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-17
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Ponts et Serveurs MCP (`src/bridges/mcp_resilience_guard.py`, `src/bridges/mcp_proxy_router.py`), Orchestration d'état (`src/state.py`), Pipelines de résilience (`src/pipelines/resilience/`), Gestion des Guardrails
- **Autorité** : [ADR-0001](0001-python-state-graph.md), [ADR-0202](0202-modularite-interne-agents.md), [ADR-0308](0308-mcp-prompts-and-evals-engine.md), [ADR-0335](0335-deep-paper-note-ingestion-epistemic-grounding.md), [ADR-0341](0341-runnable-gates-depth-tree-orchestration.md), [ADR-0354](0354-opaque-artifact-bus-leakage-gate-simplicity-guard.md), [ADR-0371](0371-paradigme-dual-harnais-preventif-et-point-in-time-recovery-agentique.md)

---

## 1. Contexte & Problématique

Le 15 septembre 2026, **Rubrik** (en collaboration étroite et co-ingénierie avec **Anthropic**) a annoncé **Rubrik MCP (Model Context Protocol)**, propulsant le protocole MCP comme l'interface souveraine d'interfaçage entre agents d'IA (Claude) et plateformes de cyber-résilience d'entreprise.
Alors que l'[ADR-0371](0371-paradigme-dual-harnais-preventif-et-point-in-time-recovery-agentique.md) (synthèse Cohesity) ancre le volet *curatif* et la restauration point-in-time (PITR) de l'état agentique, l'annonce Rubrik résout le chaînon manquant de l'**interfaçage opérationnel sécurisé** :

> *« Comment permettre à des agents autonomes d'interagir à la vitesse machine avec la télémétrie de sécurité et les plans de reprise sans créer une nouvelle faille critique d'exécution ou d'escalade d'outils ? »*

Les réponses industrielles apportées par Rubrik et validées par nos études de marché (Futurum Research) reposent sur trois piliers majeurs :
1. **L'exposition directe du schéma d'API via MCP** : Remplacer les connecteurs ad-hoc par une découverte typée et dynamique de capacités via JSON-RPC / MCP.
2. **La cristallisation de workflows déterministes réutilisables** : Convertir les résolutions probabilistes complexes multi-étapes (*multi-step reasoning*) en outils déterministes et rejouables instantanément lors des crises ultérieures.
3. **L'adossement au standard de sécurité émergent OWASP MCP Top 10** : Imposer la parité RBAC, la validation de schéma stricte, et l'encapsulation hermétique des données récupérées (*Retrieved Content is Data, Never Policy*).

---

## 2. Diptyque Épistémique & Synthèse Comparative

### 2.1 Matrice Tripartite de Résilience Agentique

| Dimension | Cohesity Agent Resilience (ADR-0371) | Rubrik MCP (Annonce 15-16 Sept 2026) | Synthèse & Standard mLoop (ADR-0374) |
| :--- | :--- | :--- | :--- |
| **Objectif Premier** | Restauration Curative / Sauvegardes immuables / PITR. | Interfaçage Programmable MCP & Automatisation Incident Response. | **Pipeline Complet** : Prévention (SCC) + Interfaçage Sécurisé (MCP Guard) + Rollback Curatif (PITR). |
| **Interface Agentique** | Plateformes cloud propriétaires (AWS Bedrock AgentCore, Azure). | **Model Context Protocol (MCP)** standardisé & ouvert (Anthropic Claude). | **MCP Local & Distribué** : Schémas stricts Pydantic, JSON-RPC, sockets unix/named pipes. |
| **Mode d'Exécution** | Détection rétrospective d'altération d'état. | **Workflows Déterministes Réutilisables** forgés par raisonnement multi-étapes. | **Cristallisation Système 2 $\rightarrow$ Système 1** : Transformation des plans validés en Runnable Gates déterministes. |
| **Framework de Sécurité** | Chiffrement & Clean-room snapshots. | **OWASP MCP Top 10** & Parité RBAC granulaire. | **`MCPResilienceGuard`** : Validation d'arguments, confinement anti-injection indirecte et plafond de charge utile. |
| **Gouvernance des Données** | Journalisation de snapshots. | Exposition directe de schéma sans fuite de privilèges. | **Encapsulation XML étanche** (`<mcp_untrusted_data>`) avec signature SHA-256. |

---

## 3. Décisions d'Architecture mLoop

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ STANDARD MCP DE CYBER-RÉSILIENCE & WORKFLOWS DÉTERMINISTES (ADR-0374)                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [COUCHE AGENT / PROMPT] (Claude Code, Antigravity, Swarm Système 2)                  │
│                          │                                                             │
│                          ▼ (Tool Call JSON-RPC)                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ MCPResilienceGuard (src/bridges/mcp_resilience_guard.py)                       │   │
│   │                                                                                │   │
│   │  1. Gate Schéma (MCP-01)        : Validation Pydantic stricte, zéro extra args │   │
│   │  2. Gate RBAC & Scope (MCP-03)   : Vérification Rôle (Read vs Unattended)       │   │
│   │  3. Gate Quota & Taille (MCP-04) : Troncature déterministe (< 32 Ko) + SHA-256 │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
│                          │                                                             │
│                          ▼ (Execution sûre)                                            │
│   [OUTIL MCP LOCAL / BRIDGES] (mcp_loop_mem, mcp_crawler, telemetry, restore)          │
│                          │                                                             │
│                          ▼ (Tool Result brut)                                          │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ Confinement Données (MCP-02 / "Data, Never Policy")                            │   │
│   │  Enrobage : <mcp_untrusted_data tool="..." sha256="...">...                    │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
│                          │                                                             │
│                          ▼ (Tool Result scellé réinjecté au modèle)                    │
│   [CRISTALLISATION DÉTERMINISTE] (WorkflowFreezer)                                     │
│   Chaîne de raisonnement multi-étapes validée ──> Recette déterministe Runnable Gate   │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Garde-Fou de Sécurité `MCPResilienceGuard` (OWASP MCP Top 10)
Tout pont MCP exposé ou consommé par mLoop doit transiter par le module de garde-fous `src/bridges/mcp_resilience_guard.py` :
1. **Validation Stricte des Schémas (MCP-01)** : Les arguments soumis par un agent doivent correspondre strictement au contrat typé déclaré. Tout paramètre inconnu ou type divergent entraîne un rejet immédiat (`MCPValidationError`).
2. **Confinement Hermétique Anti-Injection (MCP-02)** : Les données retournées par un outil (pages web, logs de sauvegarde, résultats d'audit) sont considérées comme non fiables. Elles sont obligatoirement encapsulées dans des balises isolées :
   ```xml
   <mcp_untrusted_data tool="tool_name" sha256="abc12345...">
   [CONTENU BRUT SÉCURISÉ]
   </mcp_untrusted_data>
   ```
3. **Contrôle d'Accès Basé sur les Rôles (MCP-03)** : Les outils modifiant l'état (écriture, purge, exécution de scripts) sont strictement interdits aux sessions déclarées en rôle de consultation (`READ_ONLY`, `INVESTIGATION`) ou aux workers non autorisés sans validation préalable.
4. **Protection Contre l'Épuisement Contextuel (MCP-04)** : Les retours d'outils sont plafonnés à une taille maximale déterministe (16 000 caractères par défaut). Au-delà, le contenu est tronqué de manière reproductible et estampillé avec son empreinte SHA-256.

### 3.2 Cristallisation des Workflows Déterministes Réutilisables
Conformément à la proposition de valeur de Rubrik :
- Lorsqu'une séquence d'incident response ou de diagnostic multi-étapes est résolue par le Système 2 (ex: identification d'une corruption de mémoire vive, calcul de blast radius et sélection d'un snapshot sain), sa signature opérationnelle est enregistrée.
- Cette séquence devient une recette d'exécution déterministe réutilisable sans ré-inférence cognitive coûteuse, intégrée dans le registre des Runnable Gates (`ADR-0341`).

---

## 4. Conséquences & Invariants

- **Zéro Évasion d'Outil** : Aucun serveur MCP sous mLoop ne peut être appelé avec des arguments arbitraires non contraints par un schéma Pydantic strict.
- **Séparation Étanche Données / Politiques** : Le modèle traitant un résultat d'outil ne peut plus confondre une directive injectée dans un fichier ou log externe avec une instruction système mLoop.
- **Idempotence des Recettes de Reprise** : Toute séquence de remédiation validée est pérennisée sous forme déterministe.
- **Souveraineté et Portabilité Totale** : Compatible avec tout client MCP (Claude Code, IDE Antigravity, OpenCode, VSCode) sans verrouillage propriétaire.
