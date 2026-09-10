# ADR-0362 : Hygiène Contextuelle, Skill Doctor, Plafonnement Mémoire 200 Lignes et Isolation des Sous-Agents

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-10
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Swarm (`src/pipelines/skill_doctor.py`, `src/pipelines/dream_consolidator.py`, `src/pipelines/session_resume.py`, `src/commands/`), Spécification de Compétences (`.agents/skills/`), Directives d'Agents (`CLAUDE.md`, `AGENTS.md`), Configuration de Sécurité (`.claude/settings.json`)

---

## 1. Contexte & Problématique

L'exploitation intensive des systèmes multi-agents et des grands modèles de langage fait émerger des pathologies d'ingénierie contextuelle bien identifiées dans les évolutions récentes des harnais agentiques (Anthropic Claude Code v2.1.250-v2.1.267, ADR-0334, ADR-0347) :

1. **La dérive du *Context Rot* par prolifération des compétences** :
   Chaque compétence déclarée dans `.agents/skills/` injecte sa description et ses métadonnées dans le prompt système initial de l'agent. Lorsque le nombre de compétences augmente (35+ dans mLoop) ou que les fichiers `SKILL.md` enflent, le coût fixe de démarrage grimpe de façon invisible, saturant la fenêtre d'attention avant même la première action utilisateur.
2. **L'explosion de l'auto-mémoire de session** :
   Le fichier de consolidation de session (`memory/SESSION_MEMORY_HEALTH.md`) tend naturellement à accumuler l'historique complet des EvidencePacks, des backlogs et des audits. Non maîtrisé, ce fichier dépasse plusieurs milliers de lignes, dégradant la fidélité de rappel (Write-Path Fidelity, ADR-0347) et induisant des hallucinations par saturation.
3. **L'illusion et le surcoût de la multi-délégation incontrôlée** :
   L'instanciation de sous-agents communicants en équipes maillées (*Agent Teams*) engendre un facteur multiplicateur de tokens de 3x à 7x par rapport aux sous-agents hiérarchiques isolés. De plus, l'injection de prompts volumineux par arguments de ligne de commande provoque des erreurs de troncature OS et des fuites de directives.
4. **Les risques d'exfiltration et de dérive de sécurité du Write-Path** :
   L'utilisation d'outils de génération graphique (ex. serveurs de rendu distants) ou l'absence de garde-fous stricts d'écriture sur les fichiers d'environnement (`.env`) menacent la souveraineté et l'étanchéité du workspace.

Cette ADR formalise les décisions constitutionnelles pour éradiquer ces pathologies dans **mLoop**.

---

## 2. Décisions d'Architecture

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │           HYGIÈNE CONTEXTUELLE & SKILL DOCTOR          │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                        ┌─────────────────────────────────────┼─────────────────────────────────────┐
                        │                                     │                                     │
                        ▼                                     ▼                                     ▼
        ┌───────────────────────────────┐     ┌───────────────────────────────┐     ┌───────────────────────────────┐
        │  1. PLAFONNEMENT STRICT       │     │  2. MÉTROLOGIE SKILL DOCTOR   │     │  3. CONFINEMENT & SOUS-AGENTS │
        │ • Max 200 lignes / 25 Ko      │     │ • Découverte déterministe     │     │ • Prompt injecté par fichier  │
        │ • SESSION_MEMORY_HEALTH.md    │     │ • Seuil boot total: 15k tok   │     │ • Teams gâté (Phase 2 créa)   │
        │ • Offload satellite JSON      │     │ • Seuil skill unitaire: 2k tok│     │ • Sécurité .claude/settings   │
        │ • Zéro redondance de backlog  │     │ • Détection skills dormants   │     │ • Rendu diagrammes 100% local │
        └───────────────────────────────┘     └───────────────────────────────┘     └───────────────────────────────┘
```

### 2.1 Plafonnement Strict de l'Auto-Mémoire de Session (Règle des 200 Lignes / 25 Ko)

- **Plafond formel** : Le fichier d'auto-mémoire racine [`memory/SESSION_MEMORY_HEALTH.md`](file:///C:/Memory%20Loop/memory/SESSION_MEMORY_HEALTH.md) ne doit **jamais excéder 200 lignes ni 25 Ko**.
- **Déportation satellite déterministe** :
  - Les synthèses détaillées de preuves et historiques d'EvidencePacks sont systématiquement externalisées dans [`memory/evidence/summaries/consolidated_evidence_index.json`](file:///C:/Memory%20Loop/memory/evidence/summaries/consolidated_evidence_index.json).
  - Seules les métriques agrégées, les alertes de santé actives, l'index synthétique et le résumé d'hygiène des compétences sont maintenus dans `SESSION_MEMORY_HEALTH.md`.
- **Règle de troncature d'urgence** :
  Si lors de l'exécution de `DreamConsolidationDaemon` ou de `session_resume.py` la mémoire excède 200 lignes, une troncature intelligente est appliquée : conservation intégrale du bloc d'en-tête et d'alerte, compression des tableaux de métriques, et mention explicite de pointage vers l'index JSON satellite.

### 2.2 Skill Doctor : Métrologie Déterministe et Anti-Context-Rot

- **Politique "Zéro Compétence Créée" (Zero-Bloat)** :
  Pour éviter l'inflation du registre `.agents/skills/`, aucun nouveau dossier de compétence n'est créé pour les tâches d'audit d'outils. Les compétences maîtresses existantes (`calibrate`, `dream_consolidator`, `rho_optimizer`) sont bonifiées, et le moteur d'évaluation est implémenté sous forme de module Python déterministe pur ([`src/pipelines/skill_doctor.py`](file:///C:/Memory%20Loop/src/pipelines/skill_doctor.py)).
- **Seuils de vigilance métrologique** :
  - **Plafond global de démarrage** : 15 000 jetons cumulés sur l'ensemble des descriptions et instructions d'amorçage.
  - **Plafond individuel par compétence** : 2 000 jetons. Toute compétence dépassant ce seuil est marquée *OVERSIZED* et doit faire l'objet d'un élagage ou d'un découpage en sous-procédures appelées à la demande.
- **Détection des compétences dormantes (Dormant Skills)** :
  Le moteur croise l'inventaire des compétences avec `memory/token_ledger.jsonl` et `memory/events.jsonl`. Les compétences non invoquées sur les sessions récentes sont identifiées et proposées pour marquage `TOMBSTONE` ou mise en quarantaine.
- **Points d'injection obligatoires** :
  1. **CLI Autonome** : `python src/swarm.py skill-doctor` ou `python src/swarm.py doctor --skills` (support JSON, seuils personnalisables).
  2. **Calibrage Global** : Étape 3/8-bis de `python src/swarm.py calibrate`.
  3. **Rêve / Consolidation** : Intégration dans la section Santé du Swarm de `SESSION_MEMORY_HEALTH.md`.

### 2.3 Isolation des Sous-Agents et Modèle d'Équipes

- **Injection de Prompt par Fichier** :
  Lors de la transmission de directives volumineuses ou de configurations contextuelles à un sous-agent, celles-ci doivent être transmises via un fichier éphémère (ex. paramètre `--append-subagent-system-prompt-file` ou fichier scratch d'artefact) plutôt qu'en argument brut de ligne de commande, éliminant les limitations d'échappement Shell et de taille de tampon OS sous Windows/POSIX.
- **Gating Constitutionnel : Subagents vs Agent Teams** :
  - **Sous-agents hiérarchiques (Default)** : Pour 90% des tâches (recherche, vérification, exécution unitaire, refactoring ciblé). Coût prédictible, contexte isolé, retour d'information synthétique au superviseur.
  - **Agent Teams (Phase 2 Créative uniquement)** : Réservé exclusivement à la co-conception complexe, à l'exploration contradictoire d'architectures et aux revues croisées multi-perspectives. Tout déploiement d'Agent Teams doit comporter une limite stricte de tours (`max_turns <= 5`) et un budget jetons borné pour endiguer le multiplicateur 3x-7x.

### 2.4 Confinement Local et Sécurité du Write-Path

- **Confinement Local des Données & Schémas** :
  Toute génération visuelle (diagrammes de composants, états, flux) doit être effectuée via des moteurs locaux (Mermaid JS, SVG local, Graphviz local). Toute exfiltration de code source ou de métadonnées vers des services tiers non authentifiés (ex. générateurs en ligne non souverains) est strictement interdite.
- **Règles de déni d'accès déclaratives** :
  Le fichier [`.claude/settings.json`](file:///C:/Memory%20Loop/.claude/settings.json) applique des règles de rejet impératives sur la lecture/écriture des secrets (`.env`, `.env.bak`) et sur l'écrasement des répertoires de référence protégés.
- **Capacité de Tampon Étendue** :
  Les variables `bashOutputMaxChars` et `taskOutputMaxChars` sont configurées à 128 000 caractères pour permettre les audits volumineux et traces de tests sans troncature prématurée de l'information critique.

---

## 3. Conséquences & Impacts

### 3.1 Avantages
- **Préservation de la fenêtre d'attention** : Réduction de 40% à 70% de la charge cognitive inutile lors de l'amorce de chaque commande.
- **Garantie anti-régression mémorielle** : Respect permanent de la règle des 200 lignes empêchant l'amnésie ou la dérive hallucinée du modèle.
- **Auditabilité totale et falsifiable** : Chaque compétence est profilée de façon déterministe sans coût LLM.
- **Élimination des bugs de synchronisation** : Disparition des doublons de backlog et cohérence de l'index satellite JSON.

### 3.2 Engagements Opérationnels
- Tout nouvel ajout ou refactoring de compétence dans `.agents/skills/` doit être validé via `python src/swarm.py doctor --skills` avant merge.
- Les rapports de session `SESSION_MEMORY_HEALTH.md` non conformes au plafond de 200 lignes sont automatiquement rejetés par le daemon de consolidation.
