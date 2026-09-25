# ADR-0205 : Cycle de Vie Sous-Agents Herdr & Isolation de Contexte

**Statut** : Accepté  
**Date** : 17 août 2026  
**Auteurs** : Équipe mLoop & Co-Architecte Agentique  
**Domaine** : Runtime Multi-Agents, Gestion de Contexte (AI Coding Loop), Herdr PTY Multiplexer, Traçabilité  
**Amendement ADR-0389 (25 sept. 2026)** : Actualisation des drapeaux de lancement des workers — `--auto --agent worker` pour OpenCode, `--auto-approve true` pour Cline.

---

## 1. Contexte et Problématique

L'analyse de l'**AI Coding Loop** (Matt Pocock / AI Hero) et les observations empiriques sur les agents de code (Claude Code, OpenCode, Codex) démontrent deux goulots d'étranglement critiques :

1. **La Dérive par Saturation de Contexte (*Compounding Errors in Dumb Zone*)** :
   Au-delà d'un certain seuil d'occupation de la fenêtre de contexte (> 50-60%), l'attention du modèle s'effondre, générant des hallucinations, des régressions de règles d'affaires et la réinvention de code existant. Les plans d'implémentation monolithiques géants exécutés dans une seule session s'effondrent sous leur propre poids.

2. **La Pollution Terminale & Le Bruit des Logs (*Terminal Bloat*)** :
   Les sorties PTY brutes (séquences ANSI, spinners, barres de progression, traces verbeuses) gaspillent des milliers de tokens précieux si elles sont réinjectées sans filtrage dans le contexte maître.

3. **Le Besoin d'un Runtime Unattended Déterministe** :
   L'orchestrateur maître ne doit jamais exécuter le code de bas niveau dans son propre volet terminal principal `p1`. Il doit déléguer l'implémentation à un sous-agent travailleur (*Worker*) dans un environnement de terminal dédié et isolé, tout en conservant une traçabilité synchrone.

---

## 2. Décisions Architecturales

Nous actons l'intégration et le renforcement des composants suivants :

### A. Modèle d'Isolation Contextuelle « Clean Slate per Story »
* Chaque User Story (`MMA-XXXX` ou `US-XX`) issue de la phase PLAN/to-tickets est traitée comme une unité d'exécution hermétique.
* L'orchestrateur mLoop instancie un sous-agent Herdr dédié (`worker_<STORY_ID>`) dans un volet terminal scindé (`pane split --no-focus`).
* **Progressive Disclosure** : Le prompt transmis au worker contient uniquement un pointeur vers son contrat fonctionnel (`Projects/<project>/backlog/stories/<STORY_ID>.md`) et les contraintes normatives essentielles, garantissant un démarrage à zéro token parasite.

### B. Commandes CLI Swarm Haut-Niveau pour Herdr
Pour éviter toute manipulation manuelle de volets terminaux, mLoop expose 4 primitives CLI natives :
1. `python src/swarm.py worker-spawn --project <nom> --story <ID> [--kind <opencode|claude|codex>]` : Scinde le volet, démarre l'agent en mode Unattended (`--yolo` / `--dangerously-skip-permissions`) et envoie le prompt initial.
2. `python src/swarm.py worker-status --project <nom>` : Interroge le runtime Herdr et affiche l'état de santé des workers (`working`, `blocked`, `idle`, `done`).
3. `python src/swarm.py worker-harvest --project <nom> --story <ID>` : Moissonne le flux PTY déballé (`recent-unwrapped`), applique le filtre anti-bloat et synchronise l'EvidencePack JSON (`memory/evidence/<STORY_ID>_evidence.json`).
4. `python src/swarm.py worker-close --project <nom> --story <ID>` : Ferme le volet terminal et libère les ressources système.

### C. Moisson Déterministe & Filtrage Anti-Bloat (*Pruning Engine*)
La méthode `HerdrAdapter.filter_terminal_bloat` applique une élimination AST/Regex des séquences ANSI, des artefacts de retours chariot (`\r`), des glyphes de spinners et des répétitions pour ne conserver que la matière d'exécution utile à l'audit QA Sentinel.

### D. Arbre de Décision de Gestion de Contexte (Context Routing Tree)
L'orchestrateur suit l'arbre de décision strict suivant :
* 🧹 **`Clear`** : Lors du passage à une initiative ou un domaine fonctionnel différent.
* 📦 **`Compact`** : Lors de la transition entre phases d'un même récit (ex: après *Grill with Docs* vers la rédaction Gherkin).
* 🤝 **`Handoff`** : Lors du transfert de relais vers l'agent Sentinel/Validate via `SESSION_MEMORY_HEALTH.md`.
* 🤖 **`Subagent (Herdr Worker)`** : Pour toute exploration lourde de code source ou toute phase d'écriture physique BUILD.

---

## 3. Conséquences

### Positives
* **Zéro Dérive Cognitive** : Chaque récit dispose de 100% de sa fenêtre de raisonnement (*Smart Zone*) sans bagage contextuel résiduel.
* **Traçabilité Synchrone & Automatique** : La moisson PTY injecte automatiquement les preuves d'exécution dans les EvidencePacks machine sans intervention humaine.
* **Robustesse Multi-Harness** : Compatible avec tout agent de terminal CLI (Claude Code, OpenCode, Pi, Codex, Gemini CLI).
* **Mode Unattended Sécurisé** : L'interception de l'état `blocked` permet de relayer les questions critiques à l'humain sans blocage silencieux.

### Négatives / Mitigations
* **Dépendance au Daemon Herdr** : Si Herdr n'est pas actif sur la machine hôte, l'adaptateur bascule de façon transparente en mode de repli (*Graceful Fallback / Mock Simulation*).

---

## 4. Références & Alignement SSOT
* **Adaptateur Core** : `src/core/herdr_adapter.py`
* **Pipeline** : `src/pipelines/worker_pipeline.py`
* **Commandes CLI** : `src/commands/handlers/worker.py` & `src/commands/_registry.py`
* **Skill Associé** : `.agents/skills/herdr-orchestration/SKILL.md`
* **ADRs Liés** : ADR-0029 (Herdr Integration), ADR-0309 (Agent Plugins 1.0), ADR-0323 (Sequential CLI Boot).
