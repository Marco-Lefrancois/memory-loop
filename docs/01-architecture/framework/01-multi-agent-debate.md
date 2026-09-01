# Synthèse de l'Implémentation : Moteur de Débat Agentique & Topologie DAG (Architecture d'Affaires)

## 1. L'Objectif et le Problème Initial

Dans le cadre du protocole **Plan-First** de mLoop, la phase d'analyse (Vertical Slicing) sert à découper les fonctionnalités et à définir les règles d'affaires. 
Cependant, nous avons identifié une faille majeure : **La Dérive Technique (Scope Creep)**.

Lorsqu'on demandait à l'IA d'analyser une règle complexe (ex: anti-collision hors-ligne), elle proposait immédiatement des schémas de base de données (SQL), des structures JSON et des API bas niveau. Ce comportement violait la règle stricte de mLoop : *l'analyse doit rester au niveau des comportements et des critères d'acceptation (Gherkin/BDD)*, pas de l'implémentation physique.

## 2. L'Ajustement du Niveau d'Abstraction & Topologie DAG

Pour corriger le tir, nous avons recâblé le moteur de débat agentique (`agentic_debate.py`) et l'avons intégré au cœur de la topologie **Graph Engineering (DAG Multi-Agents)** sous le Pattern Diamant :

*   **Le Proposeur (DDD Architect / `node_plan_be`/`node_plan_fe`)** : Agit comme un Architecte d'Affaires (DDD). Il a l'interdiction absolue de générer du code et doit proposer une solution conceptuelle (flux, comportements).
*   **Le Challenger / Red Team (`node_critic` / Evaluator Node)** : Attaque la proposition en cherchant les failles logiques, les problèmes de sécurité, et les edge-cases opérationnels (ex: crash applicatif, délai réseau).
*   **Le Juge Synthétiseur (`orchestrator` / Reducer Node)** : Résout les conflits et traduit l'architecture finale sous forme de **Scénarios de test Gherkin respectant les 4 Piliers** (Nominal, Rejet/Exception, Mode Dégradé, UX/Observabilité) directement intégrables dans le Backlog.

**Résultat :** L'analyse d'une fonctionnalité complexe est passée d'un brouillon technique à une architecture d'affaires robuste (mise en place d'un système de *Lease (TTL)*, d'une *Clé d'idempotence*, et de 9 scénarios Gherkin explicites pour la gestion hors-ligne).

## 3. L'Automatisation (Batch Debate & Topologie `graph-run`)

Face à l'immense valeur générée par ce débat, la nécessité de l'appliquer à **l'ensemble des récits du Backlog** s'est imposée.

Nous avons développé le script d'automatisation `batch_debate.py` et la commande CLI `python src/swarm.py graph-run` :
1.  **Moissonnage** : Scanne de manière autonome tous les fichiers `.md` du dossier `backlog/stories`.
2.  **Extraction Intelligente** : Identifie la problématique métier ou la faille architecturale la plus critique de chaque récit.
3.  **Orchestration DAG** : Exécute le débat agentique en injectant cette problématique spécifique à travers la topologie DAG.
4.  **Archivage & EvidencePacks** : Sauvegarde la synthèse sous `memory/debate_transcript_<ID_story>.md` ET génère l'artefact JSON structuré `memory/evidence/<STORY_ID>_evidence.json` via `EvidencePackEngine`.

> **Performance et Coût** : Ce processus d'analyse en rafale traite un backlog complet en quelques dizaines de minutes de façon asynchrone (tâche de fond). Grâce au *Token Budget Guard* et au *Confidence Gate*, le coût LLM est optimisé tout en garantissant un ROI exceptionnel.

## 4. Bénéfice pour les Projets Clients

Cette implémentation garantit que **chaque récit du backlog est soumis à un stress-test architectural complet** avant même qu'un développeur humain ne touche à une ligne de code. 

Cela permet au Product Owner / Analyste (l'Humain) de :
- Recevoir des scénarios de tests robustes sur un plateau d'argent.
- Lever des **Questions Ouvertes (OQ)** pertinentes (ex: `OQ-003` sur la rigidité d'un mode hors ligne) bien avant que la faille n'atteigne la production.
- Conserver le dossier `docs/` et `backlog/` pur, libre de toute pollution de code technique.
- Assurer une synchronisation transparente vers Jira Cloud via `python src/swarm.py jira_sync` sous la gouvernance Story-Only.
