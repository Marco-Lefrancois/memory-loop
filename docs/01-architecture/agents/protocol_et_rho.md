# Protocole d'Analyse et Auto-Amélioration (mLoop Framework)

## Cycle de Vie Standard d'Analyse en 5 Étapes (mLoop Workflow)
Ce cycle de vie est la **marche à suivre obligatoire** pour toute nouvelle fonctionnalité, initiative ou récit au sein du framework mLoop. Tous les agents (Antigravity, OpenCode, Cursor, etc.) et modèles LLM doivent impérativement respecter cette séquence linéaire :

1. **Étape 1 : Plan Sommaire & Découpage Préliminaire**
   - **Objectif** : Identifier le périmètre fonctionnel et découper l'initiative en récits (*tracer bullets*) sans rédaction prématurée de Gherkin.
   - **Outillage** : `python src/swarm.py wayfinder`, `to-spec`, RAG Open Notebook (`on_search_notes`).
   - **Livrable** : Récits "sommaires" dans `backlog/stories/` (Titre, Description, Contexte) avec statut `OPEN`.
   - **Gate de Sortie 1** : Accord explicite de l'utilisateur sur le découpage et le périmètre.

2. **Étape 2 : Session "Grill with Docs" (Analyse Unitaire & Architecture)**
   - **Objectif** : Explorer le code source physique et la documentation pour séparer les **Faits** (extraits du codebase/Open Notebook) des **Décisions** (à trancher par l'utilisateur).
   - **Outillage** : Interrogation interactive (`/grill-me`, `python src/swarm.py grill`), Open Notebook MCP (`on_chat`), Graphify (`graphify query`, `graphify path`).
   - **Règles Strictes** :
     - Formuler systématiquement les questions ouvertes (`OQ-XXX`) dans `docs/04-transverse/00-questions-ouvertes.md`.
     - Générer/mettre à jour immédiatement les ADRs dans `docs/01-architecture/ADR-XXX.md` pour chaque décision structurante.
     - Pour les récits Front-End : Griller systématiquement la matrice **D-A-F-E** (Disponibilité, Action, Feedback, Erreur) pour chaque CTA visuel.
   - **Gate de Sortie 2** : Porte de confirmation franchie + Aucune `OQ-XXX` bloquante non résolue + Statut passe à `IN_ANALYZE`.

3. **Étape 3 : Génération du Récit (Full Story)**
   - **Objectif** : Rédaction intégrale du récit selon les standards de qualité mLoop.
   - **Gabarits Obligatoires** : Utilisation stricte des templates `standards/blueprints/story_template_FE.md` ou `story_template_BE.md`.
   - **Blindage Gherkin (Les 4 Piliers Obligatoires)** :
     1. *Chemin Nominal* (Happy path & persistance).
     2. *Exceptions & Rejets Métier* (Règles `RM-XXX`, rejets HTTP 400/409, messages d'erreur).
     3. *Résilience Technique & Mode Dégradé* (Offline, timeouts, idempotence, coupure réseau).
     4. *Comportement UX & Observabilité* (Toasts, spinners, états grisés, redirections, logs d'audit).
   - **Gate de Sortie 3** : Récit entièrement rédigé avec l'en-tête YAML valide et la couverture exhaustive des 4 piliers Gherkin.

4. **Étape 4 : Validation Sémantique & Auto-Audit (WikiFix Self-Healing)**
   - **Objectif** : Validation automatisée de l'isolation fonctionnelle (Zero-Jargon) et certification INVEST.
   - **Outillage & Auto-Correction** : Exécution immédiate en arrière-plan de `python src/swarm.py wikifix` et `python src/swarm.py sync --project <nom_projet>`. En cas d'échec de linting, l'agent se corrige silencieusement en boucle jusqu'à succès.
   - **Gate de Sortie 4** : Execution de `wikifix` avec Exit Code 0 + Score INVEST > 80% + Statut passe à `READY_FOR_GROOMING`.

5. **Étape 5 : Export JIRA & Synchronisation Externe**
   - **Objectif** : Congélation du récit validé et export vers l'outil de gestion externe.
   - **Outillage** : `python src/swarm.py to-tickets`, `python src/swarm.py sync --project <nom_projet>`.
   - **Handoff Critique** : Transmettre la notification officielle de fin d'analyse pour passage au développement physique.
   - **Gate de Sortie 5** : Fichiers SQLite/Graphify synchronisés + Export généré + Statut passe à `READY_FOR_DEV` / `SYNCED`.

---

## Directives d'Engagement (Functional Compliance Protocol)
Pour les IDE Agentiques agissant comme "Coworker" (Antigravity, OpenCode, Cursor, Aider, etc.), ce protocole strict constitue les règles d'engagement absolues :

0. **Checklist Pré-Vol Anti-Amnésie & Plan-First** : Aucun fichier métier ou de gouvernance ne peut être créé ou édité sans soumission préalable de `implementation_plan.md` et validation explicite de l'utilisateur.
1. **Isolation Technique Absolue** : Le backlog doit rester agnostique de la technologie. Le découpage se fait de manière fonctionnelle (Vertical Slicing). Les librairies techniques et l'implémentation vont dans les ADRs, pas dans les User Stories.
2. **Anti-Drift Guardrail (Story Generation)** : Il est **strictement interdit** de générer des User Stories (Gherkin) de manière préemptive ou purement théorique. La rédaction d'une Story ne peut débuter qu'après une validation explicite du plan et une **analyse vérifiée du code source physique (`src/`)**. Toute histoire créée sans ancrage dans le code réel est une violation majeure.
3. **Fact-Search Before Grill & Veto de Substitution** : Recherche FTS/Graphify des règles métier (`RM-XXX`) obligatoire avant toute question au PO pour interdire la substitution d'une Story absente par une Story impropre.
4. **Veto Anti-Annulation (No-Shortcut Rule)** : Un agent A L'INTERDICTION STRICTE de modifier le statut d'un récit vers `CANCELLED` ou d'abandonner l'analyse en Étape 2/3 de sa propre initiative suite à une réponse de simplification (ex: *"non-bloquant"*, *"géré plus tard"*). L'annulation d'un récit exige un ordre écrit explicite du PO.
5. **Mandat de Requalification Obligatoire** : Lorsqu'un besoin métier est simplifié ou déscopé d'un écran visuel, l'agent DOIT **requalifier le récit** pour couvrir le nouveau besoin fonctionnel (ex: journalisation de logs d'anomalies, événements d'audit non-bloquants). L'agent DOIT rédigée l'intégralité du récit sous blueprint (`story_template_BE/FE.md`) avec les **4 Piliers Gherkin obligatoires** et valider `wikifix`.
6. **Règle de Référencement Jira Exclusif** : Dans le corps du texte des récits (règles d'affaires, critères d'acceptation, Gherkin), l'agent DOIT **impérativement privilégier la référence Jira** (ex: `COUVBOIRE-739`) dès lors qu'elle est connue, au lieu de l'identifiant interne (ex: `REC-007`).
7. **Gouvernance Synchrone Backlog SSOT (`sprint_backlog.md`)** : `backlog/sprint_backlog.md` et `backlog/stories/` constituent la source unique de vérité dynamique. Toute modification d'état, réestimation ou requalification doit être immédiatement répercutée de manière synchrone dans `sprint_backlog.md`.
8. **Auto-Synchronisation Sémantique Automatique** : Vous **devez** déclencher la mise à jour de Graphify et WikiFix **automatiquement** à la fin de vos modifications. Exécutez la commande `python src/swarm.py sync --project <nom_du_projet>` depuis la racine pour garantir que l'index SQLite FTS5 reste la source de vérité absolue.
9. **Grill des Interactions (D-A-F-E)** : Avant de finaliser un récit frontend, l'agent doit effectuer un "grill" système de chaque élément visuel cité.
10. **Validation Système** : La commande de synchronisation précédente valide à la fois la conformité d'affaires (WikiFix) et la santé du graphe. Ne clôturez jamais une tâche d'édition sans avoir exécuté cette pipeline de validation.

## L'Auto-Amélioration (RHO & STORY GUARD)
Le framework intègre la philosophie **Retrospective Harness Optimization (RHO)** pour garantir son intégrité et s'auto-améliorer :
1. **L'Intégrité Produit (Story Guard)** : L'IDE s'assure que le périmètre fonctionnel reste cohérent et aligné (Zero-Drift Execution).
2. **Chaos Testing & Auto-Apprentissage** : Lorsqu'un agent identifie une erreur ou un anti-pattern récurrent, il doit invoquer `python src/swarm.py optimize` pour auto-générer une règle sémantique (`rho_rules.yaml`).
3. **Double Portée RHO** : Le linter `wikifix` applique simultanément les règles d'exclusion globales (issues de `standards/`) et locales (issues de `memory/`).
