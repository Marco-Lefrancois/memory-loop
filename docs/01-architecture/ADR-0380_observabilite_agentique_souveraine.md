# ADR-0380 : Observabilité Agentique Souveraine, Boundary Tracing & Immunisation Déterministe

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-19
- **Auteurs** : Marco, Lead Architect & Co-Architecte Framework Agentique
- **Périmètre** : Cœur d'orchestration (`src/agents/circuit_breaker.py`, `src/engine/artifacts/boundary_wrapper.py`, `src/utils/event_logger.py`), Tableau de Bord Cockpit 2.0 (`src/dashboard/routers/overview.py`, `swarm.py`, `dream_rsi.py`, `graph_db.py`, `static/index.html`), Backlog mLoop (`Projects/mLoop/backlog/stories/MLOOP-070-BE.md` à `075-FULL.md`)
- **Autorité** : [ADR-0001](../standards/adr-system/0001-python-state-graph.md), [ADR-0202](../standards/adr-system/0202-taille-des-modules.md), [ADR-0324](../standards/adr-system/0324-mesure-et-alerte-dumb-zone-contexte-llm.md), [ADR-0339](../standards/adr-system/0339-project-lifecycle-management-fsm-and-gates.md), [ADR-0371](../standards/adr-system/0371-paradigme-dual-harnais-preventif-et-point-in-time-recovery-agentique.md), [ADR-0372](../standards/adr-system/0372-replay-simulator-hors-ligne-et-auto-amelioration-recursive-du-harnais.md), [ADR-0375](../standards/adr-system/0375-project-lifecycle-5-phases-and-analysis-types.md), [ADR-0379](../standards/adr-system/0379-standards-graph-and-runtime-confinement-shield.md)

---

## 1. Contexte & Problématique

L'orchestration d'essaims d'agents autonomes génère trois pathologies structurelles majeures si elle n'est pas bornée par un harnais logiciel déterministe (Système 1) :
1. **Délégation Récursive Stérile (*Ping-Pong Loops*)** : Les agents se passent le flambeau indéfiniment sans modifier l'état physique du projet, dilapidant les quotas de jetons et créant un dérive de but (*goal drift*).
2. **Pollution Contextuelle Masquée** : L'injection non filtrée de retours de commandes de plusieurs dizaines de kilo-octets (ex: dumps de logs, réponses d'APIs brutes) précipite le modèle dans la « Dumb Zone » (>60% de contexte saturé) où sa capacité d'inférence logique s'effondre.
3. **Risque de Dépendance et Fuite Télémétrique SaaS** : Les solutions standards du marché (LangSmith, Langfuse, Datadog) obligent à router les échanges et fragments de code vers des nuages tiers. Pour garantir la souveraineté industrielle de mLoop, l'observabilité doit être **100 % locale, déterministe et conforme aux standards ouverts (OpenInference / OTel GenAI)**.

---

## 2. Piliers d'Implémentation Technique

### 2.1 Le Disjoncteur Ping-Pong Guard (`src/agents/circuit_breaker.py`)
- Maintient une pile d'historique bornée des délégations actives.
- Détecte l'alternance cyclique ($A \to B \to A \to B$) et coupe impérativement dès le **3e handoff consécutif non productif**.
- Lève `PingPongRecursionError`, consigne l'incident dans le journal d'état (`circuit_breaker:ping_pong_detected`) et arme le drapeau `LoopState.hitl_required = True`.
- Remise à zéro automatique dès qu'un agent persiste un livrable physique sur disque.

### 2.2 Boundary Tracing & Auto-Offload (`src/engine/artifacts/boundary_wrapper.py`)
- Encapsule les retours d'outils et appels CLI.
- Tout contenu excédant **2 000 caractères** ou 30 lignes est déporté dans `memory/artifacts/` sous clé SHA-256 (`OpaqueArtifactBus`).
- Remplacement transparent dans le contexte de raisonnement par le pointeur canonique `mloop://artifacts/{sha256}`.

### 2.3 Jauge Contextuelle Dynamique 3-Zones par Session (`overview.py` & Header Cockpit)
- Calée sur la fenêtre de contexte maximale du modèle configuré pour la session.
- **Smart Zone (0–40%)** : Vert, capacité nominale.
- **Caution Zone (40–60%)** : Jaune, surveillance d'attention.
- **Dumb Zone (>60%)** : Rouge, alerte immédiate et proposition d'élagage ou de snapshot PITR.

### 2.4 Télémétrie Locale Ouverte OpenInference / OTel GenAI (`event_logger.py`)
- Enrichissement des événements avec `openinference.span.kind` (`agent`, `chain`, `llm`, `tool`).
- Persistance exclusive dans `memory/events.jsonl` et requêtable via SQLite.
- Zéro dépendance réseau sortante.
