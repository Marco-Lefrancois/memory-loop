# ADR-0330 : Cycle de Vie Création Projet & Échafaudage

> **Statut :** ACCEPTÉ  
> **Date :** 18 Août 2026  
> **Auteur :** Équipe d'Architecture & Gouvernance mLoop  
> **Décideurs :** Marco Lefrançois, Architecte en Chef IA  
> **Concerne :** CLI `init`, Scaffolding agnostique, Protocoles de démarrage projet  

---

## 📌 1. Contexte & Problématique

Lors de la création de nouveaux projets dans mLoop via `python src/swarm.py init`, deux dérives architecturales ont été constatées :

1. **Pollution Interne du Dépôt Client** : Les fichiers générés par défaut (`AGENTS.md`, `opencode.json`) contenaient des commandes internes au framework (`python src/swarm.py`, `src.mcp_server`). Or, les équipes de développement clientes et leurs assistants IA n'utilisent pas mLoop directement et requièrent un espace de travail 100 % agnostique.
2. **Saut d'Étapes & Hallucination Prématurée de Backlog** : En l'absence d'une procédure formalisée, des agents IA ont tenté d'inventer des règles d'affaires et des User Stories sans attendre le dépôt et l'ingestion des matières premières clientes sous `reference/`.

---

## 🎯 2. Décisions d'Architecture

1. **Scaffolding Agnostique Déterministe (`Universal Dev Handoff - ADR-0319`)** :
   - `python src/swarm.py init` génère obligatoirement des fichiers `AGENTS.md` et `opencode.json` sans aucune commande interne de framework.
   - Les fichiers générés sont focalisés sur la structure du projet, les **4 Piliers Gherkin**, la pureté fonctionnelle et la documentation sous `docs/00-ingested/`.

2. **Protocole de Création en 5 Étapes Séquentielles** :
   - Formalisation du document normatif SSOT : [`standards/protocols/PROJECT_CREATION_PROCEDURE.md`](../../standards/protocols/PROJECT_CREATION_PROCEDURE.md).
   - Les 5 étapes obligatoires sont :
     1. **Initialisation & Scaffolding** (`swarm.py init`)
     2. **Dépôt & Ingestion Documentaire** (`reference/` ➔ `swarm.py ingest`)
     3. **Cadrage Macro & Énoncé des Travaux** (`swarm.py to-sow` ➔ Porte 1)
     4. **Découpage Vertical du Backlog** (`sprint_backlog.md` ➔ Statut `OPEN` / `IN_ANALYZE`)
     5. **Spécification Interactive & Grilling** (`swarm.py grill` ➔ Porte 2 DoR `READY_FOR_DEV`)

3. **Guidage Console Proactif** :
   - La commande CLI `init` affiche directement les étapes suivantes à exécuter pour éviter toute dérive ou précipitation de l'agent.

---

## 🚀 3. Conséquences & Bénéfices

* **Sécurité & Zéro Hallucination** : Garantie qu'aucun backlog n'est généré sans matières premières réelles.
* **Propreté Git & Partage Développeur** : Tout projet initialisé peut être immédiatement publié sur Azure DevOps / GitHub sans retouche manuelle.
* **Traçabilité & Alignement SOW** : Respect rigoureux du cycle de vie en 6 phases (ADR-0329).
