# ADR-0310 : Vibe Code Common Sense, Restauration de Session Anti-Amnésie & Synchro CLAUDE.md

- **Statut** : Accepté
- **Date** : 2026-08-03
- **Auteurs** : Équipe mLoop Swarm & AI Assistant
- **Périmètre** : Framework Backend mLoop, Pipeline `session_resume`, Guardrail `vibe_check`, Fichier `CLAUDE.md`

---

## 1. Contexte

Les travaux de **Joe Njenga** sur la méthodologie **"Vibe Code Common Sense (Ships Faster & Never Forgets)"** démontrent que le développement assisté par IA souffre fréquemment d'une amnésie de contexte lors de l'interruption des sessions, entraînant des dérives d'architecture et des hallucinations.

Pour résoudre ce problème, la présente décision d'architecture implémente 4 garde-fous majeurs dans mLoop.

---

## 2. Décisions d'Architecture

### 2.1 Axe 1 : Moteur de Restauration de Session Anti-Amnésie (`python src/swarm.py resume`)
- **Mécanisme** : Création du pipeline `src/pipelines/session_resume.py` et de la sous-commande `python src/swarm.py resume --project mLoop`.
- **Rôle** : Au lancement d'une session, mLoop assemble et injecte instantanément l'état du backlog (`sprint_backlog.md`), les dernières tâches (`task.md`), et les 5 derniers souvenirs FTS5 dans l'esprit de l'agent.

### 2.2 Axe 2 : Guardrail "Vibe-Check" Pré-Vol Anti-Hallucination
- **Mécanisme** : Création du module `src/pipelines/vibe_check.py`.
- **Rôle** : Exécute une série de contrôles pré-vol déterministes avant toute modification de code (Fact-Search FTS5 sur les règles métier `RM-XXX`, vérification des pré-conditions Gherkin).

### 2.3 Axe 3 : Alignment Synchrone `CLAUDE.md` <-> `AGENTS.md`
- **Mécanisme** : Dans `src/pipelines/calibrate.py`, mLoop génère et maintient à jour un fichier `CLAUDE.md` à la racine de mLoop.
- **Rôle** : Garantir une parfaite équivalence de directives et de comportements quel que soit le client LLM terminal utilisé (Cursor, Claude Code, Gemini CLI, Antigravity).

### 2.4 Axe 4 : Consignation de la Rétention de Mémoire (`SESSION_MEMORY_HEALTH.md`)
- **Mécanisme** : Consignation automatique du score de fraîcheur et de rétention contextuelle sous `memory/SESSION_MEMORY_HEALTH.md`.

---

## 3. Conséquences

### Positives :
- **Zéro amnésie contextuelle** lors des reprises de session.
- **Vitesse de livraison élevée** couplée à une sécurité déterministe (Vibe-Check).
- **Interopérabilité totale** sur tous les harnais d'exécution terminal.

### Statut d'Alignement :
- ADR consigné sous `docs/01-architecture/ADR-0310_vibe_code_common_sense_and_session_resume.md`.
