---
name: plan
description: Analyse d'affaires, découpage en Stories verticales, arbitrage de décisions et rédaction d'ADR via le protocole Grill with Docs.
---

# 🎯 plan (Skill Analyse & Architecture mLoop)

> **Status:** Active | **Standard:** mLoop Core 5-Step Workflow

## 🧠 Introduction

Ce skill régit la conduite de la **Phase d'Analyse mLoop en 5 Étapes**. Il orchestre la transformation d'une intention d'affaires en un backlog de **Stories verticales**, formalise les **décisions d'architecture (ADR)** et garantit la qualité documentaire via le protocole **Grill with Docs**.

---

## 🚨 Directives Anti-Dérive & Veto Anti-Annulation (Non Négociable)

0. **🛑 Checklist Pré-Vol Plan-First (Auto-Contrôle Incontournable — ADR-0305)** :
   - Avant TOUTE création ou modification de fichier métier (Backlog, Story, Directives, Code), l'agent applique la **matrice de criticité à 3 niveaux** :
     - **Niveau 1 (Trivial)** : Exécution directe (typos, lints, lecture seule, statuts).
     - **Niveau 2 (Moyen)** : Micro-plan résumé dans le chat (1 à 2 fichiers, retouches mineures).
     - **Niveau 3 (Critique / Architecture)** : Plan formel bloquant obligatoire rédigé selon le gabarit unique [`standards/blueprints/plan_template.md`](file:///c:/Memory%20Loop/standards/blueprints/plan_template.md) (rendu via Plannotator en CLI ou Artefact interactif dans Antigravity) et attente de l'accord EXPLICITE de l'humain.
   - Aucune modification de fichier de Niveau 3 n'est autorisée avant cet accord écrit.

1. **Veto Anti-Annulation (No-Shortcut Rule)** :
   - L'agent `plan` A L'INTERDICTION STRICTE de modifier le statut d'un récit vers `CANCELLED` ou d'abandonner l'analyse de sa propre initiative suite à une réponse de simplification (ex: *"non-bloquant"*, *"géré plus tard"*, *"fait ailleurs"*).
   - L'annulation d'un récit exige un ordre écrit explicite et non équivoque de l'utilisateur (ex: *"Annule le récit REC-XXX"*).

2. **Mandat de Requalification Obligatoire (Simplified Requirement ≠ Erased Story)** :
   - Lorsqu'un besoin métier est simplifié ou déscopé d'un écran visuel, l'agent DOIT **requalifier le récit** pour couvrir le nouveau besoin fonctionnel (ex: journalisation de logs d'anomalies, événements d'audit, télémétrie non-bloquante).
   - L'agent DOIT rédiger l'intégralité du récit sous le Gabarit Unique (`story_template.md`) avec les **4 Piliers Gherkin obligatoires** et valider `python src/swarm.py wikifix` avec un Exit Code 0.


3. **📂 Le Backlog comme Source Unique de Vérité Exécutable (`sprint_backlog.md`)** :
   - Le backlog (`backlog/sprint_backlog.md` et `backlog/stories/`) est la source de vérité dynamique unique de l'exécution des récits.
   - Toute modification de récit (requalification, changement d'état, réestimation) doit être **refletée immédiatement et de manière synchrone** dans `backlog/sprint_backlog.md`.
   - Séquence d'états autorisée en Phase B : `OPEN` ➔ `IN_ANALYZE` ➔ `READY_FOR_GROOMING` (après `wikifix`). La transition `IN_ANALYZE` ➔ `CANCELLED` est bloquée pour les agents autonomes.

4. **🏷️ Règle de Référencement Jira Exclusif** :
   - Lorsque l'agent fait référence à un autre récit dans le corps du texte (règles d'affaires, critères d'acceptation, contextes, Gherkin), il DOIT **impérativement utiliser la référence Jira** (ex: `PROJET-123`) dès lors qu'elle est connue, à la place de l'identifiant interne (ex: `ST-001`).
   - Si la clé Jira n'est pas encore connue ou assignée, l'identifiant interne mLoop est utilisé en fallback temporaire.

5. **🔍 Fact-Search Mandatory, Passage-Level Grounding & Preuves Visibles (ADR-0326)** :
   - **Fact-Search Mandatory (Dual-Engine - ADR-0204)** : 
     - Pour la documentation et l'architecture : Exécuter `graphify query` / `loop_mem_search` dans `docs/` sur les concepts métier clés.
     - Pour le code source physique existant : Utiliser obligatoirement l'outil MCP `codegraph_explore` ou `python src/swarm.py code-explore` pour inspecter les signatures, classes et routes réelles en un seul appel, **sans aucune lecture brute de fichiers**.
   - **Passage-Level Grounding** : Chaque règle métier énoncée dans la User Story doit être explicitement adossée à une source physique vérifiée (`docs/00-ingested/...`, `docs/02-business-rules/...`, `ADR-XXX`).
   - **Affichage des Preuves Console** : Afficher en direct `(i) [FACT-SEARCH] 🔍 Requête FTS5 : '...' ➔ Fait vérifié` lors des analyses.
   - **Veto de Substitution** : Si la fonctionnalité n'a pas de récit présent au `sprint_backlog.md`, l'agent A L'INTERDICTION STRICTE de la rattacher par défaut à un récit existant non conçu pour cela. Il DOIT créer une `OQ-XXX` et signaler l'absence du récit au PO.

6. **🔗 Veto Anti-Omission de Contrats API (Symétrie FE/BE — ADR-0319)** :
   - **Cross-Check Obligatoire** : L'agent DOIT impérativement croiser les récits Frontend (FE) et Backend (BE). Toute action interactive définie dans le FE (bouton de soumission, chargement de liste) DOIT posséder son contrat exact (ex: `POST /api/...`) listé dans la section technique du récit FE ET du récit BE.
   - Si un endpoint existe dans le BE mais n'est pas appelé par le FE (ou inversement), l'agent DOIT bloquer l'analyse et corriger l'asymétrie.
   - **Règle Conditionnelle Routes Connues** : Les routes documentées dans un récit `layer: backend` ou `layer: fullstack` DOIVENT figurer dans la Matrice des Contrats API (Profil B) avec la méthode HTTP, le chemin et la finalité métier. Un récit `layer: frontend` DOIT référencer la même méthode/route dans sa Matrice CTA (colonne `Action (Navigation/API)`).
   - **Anti-Invention de Route (Zéro Hallucination)** : Si la route n'est pas confirmée par le modèle de données, les ADRs ou les conventions du projet, l'agent DOIT consigner le manque sous la forme `OQ-XXX : Route [Opération X] à confirmer` dans `docs/04-transverse/00-questions-ouvertes.md` et utiliser `[API de soumission à définir]` comme valeur déclarative dans le Profil B. Il est STRICTEMENT INTERDIT d'inventer une route fictive (ex: `/api/dummy`).

7. **📑 Génération Synchrone & Obligatoire d'EvidencePack (Zero-Ask Evidence Rule & ADR-0326 / ADR-0333)** :
   - Tout changement de récit (création, scission, requalification, arbitrage d'architecture) implique **obligatoirement et sans exception** la création ou la mise à jour synchrone de son `EvidencePack` sidecar sous `memory/evidence/<STORY_ID>_evidence.json` (incluant `fact_search_proofs`). Le récit Markdown se termine strictement après `## Scénarios de test` (Zero-Bruit SSOT).
   - Journalisation synchrone des requêtes dans `memory/fact_search_log.jsonl`.
   - Interdiction formelle de s'arrêter pour demander l'autorisation au PO avant de générer cet artefact d'audit : la génération d'EvidencePack est une étape interne mécanique et obligatoire.

---

## 🛡️ Scope Capping & Meta-Orchestration (Wayfinder)

Avant toute analyse unitaire, l'agent doit impérativement évaluer la complexité et la taille du périmètre :
- **Déclencheur Wayfinder (Seuil de Brouillard)** : L'agent DOIT invoquer la commande `wayfinder` pour ordonnancer les décisions si l'une des conditions suivantes est remplie : multi-codebases, plus de 5 `OQ` actives, ou présence d'un ticket bloquant.
- **Déclencheur de Capping** : Si la demande concerne une Epic entière, plus de 3 domaines fonctionnels ou un projet complet, l'agent **refuse le grillage global**.
- **Action** : L'agent impose le découpage immédiat en **Stories Verticales** ("Grillable Chunks") et limite la session de Grilling à **une seule Story verticale à la fois** pour maintenir le contexte dans la "Smart Zone" (< 120k tokens).

---

## 🗺️ Le Cycle d'Analyse mLoop (Les 5 Étapes)

### Étape 1 : Plan Sommaire & Découpage en Stories Verticales

1. **Vertical Slicing (Découpage Vertical Obligatoire)** : Chaque récit créé doit représenter une tranche verticale de valeur utilisateur (du parcours UI jusqu'au contrat d'échange/persistance), de façon fonctionnelle, autonome et agnostique du code physique.
2. **Backlog Sommaire** : Génération des récits "sommaires" dans `backlog/stories/` (Frontmatter YAML, Description, Contexte).
3. **Statut Initial** : `status: OPEN`.
4. **Validation Scope** : Accord explicite de l'utilisateur sur le découpage vertical.

### Étape 2 : Session "Grill with Docs" (Analyse Unitaire)

1. **Séparation Faits v/s Décisions** :
   - **Faits** : Exploration documentaire via `graphify query` et extraction chirurgicale du code physique via `codegraph_explore` pour établir l'existant sans devinettes.
   - **Décisions** : Arbitrages fonctionnels et techniques à trancher avec l'utilisateur.
2. **La Règle d'Or de l'Interview** :
   - **Une seule question par tour** : Posez une et une seule question à la fois. Interdiction absolue de produire des listes de questions à puces.
   - **Recommandation motivée systématique** : Pour chaque question posée, proposez toujours une option recommandée claire et justifiée pour guider l'utilisateur.
   - **Questions Ouvertes** : Documenter immédiatement toute interrogation non résolue sous forme d'entrée `OQ-XXX` dans `docs/04-transverse/00-questions-ouvertes.md`.
    - **Grill Frontend (D-A-F-E & Read/Write - ADR-0340)** : Pour les récits UI, griller obligatoirement la matrice **Disponibilité, Action, Feedback, Erreur**, auditer l'écran selon la matrice Read/Write Model (découpage en 4 zones UX : *Header/Contexte*, *Body/Read Model/Consultation*, *Footer/Write Model/Actions*, *Matrice des 8 États d'Interaction* : Nominal, Hover, Focus-Visible, Active, Disabled, Loading, Error, Success), et sélectionner une **macrostructure UI dédiée** parmi les 21 formes du référentiel ([`standards/blueprints/ui_macrostructures.md`](file:///c:/Memory%20Loop/standards/blueprints/ui_macrostructures.md)) en respectant la règle de diversification multi-écrans.

3. **Statut** : Passage à `status: IN_ANALYZE` après confirmation de la compréhension partagée.

### Étape 3 : Génération du Récit (Full Story - Dev-Ready & Agent-Ready)

1. **Standards de Rédaction & Gold Standard Binding (Obligatoire Avant Toute Écriture)** :

   **Étape préalable non négociable** : Avant de rédiger la moindre ligne de la story, l'agent DOIT exécuter dans l'ordre :

   a. **Lire le Gabarit Unique** : `standards/blueprints/story_template.md` — structure YAML, niveaux de titres H3/H4, sections obligatoires, format des listes.

   b. **Identifier et lire le Gold Standard de l'épic en cours** :
      - Chercher dans `backlog/stories/<EPIC-ID>/` le récit le plus récent avec `status: READY_FOR_DEV` ou `invest_score: 6/6`.
      - Si le frontmatter du récit précédent contient `gold_standard_ref`, utiliser ce fichier comme référence de style.
      - Sinon : utiliser `standards/blueprints/story_template.md` seul comme référence.

   c. **Calquer le style observé** dans le Gold Standard identifié :
      - Niveaux de titres H3/H4 : formulations concises, sans parenthèses bilingues redondantes (ex: `#### 1. En-tête de la Cabane` et **non** `#### 1. En-tête de la Cabane (Top Bar)`).
      - Format de listes : **tirets `-` uniquement** dans les sections UX (jamais `*` ni `+`).
      - Densité et formulation des éléments `[Label]` dans les critères d'acceptation.

   **Règle d'or** : Le Gold Standard l'emporte sur toute autre convention en cas d'ambiguïté stylistique. **Aucune rédaction de story ne peut démarrer sans ces 3 lectures préalables.**

   Emploi obligatoire du Gabarit Unique [`standards/blueprints/story_template.md`](file:///c:/Memory%20Loop/standards/blueprints/story_template.md) et alignement sur la galerie des [`Gold Standards`](file:///c:/Memory%20Loop/standards/gold_standards/README.md).
2. **Blindage Gherkin & Anti-Pollution (SSOT)** : Respect strict des 4 Piliers de test (Nominal, Rejets `RM-XXX`, Résilience, UX/Observabilité) et omission des commentaires d'échafaudage (`# PILIER X...`), conformément aux directives de [`standards/GHERKIN_GUIDELINES.md`](file:///c:/Memory%20Loop/standards/GHERKIN_GUIDELINES.md).
3. **Pureté de la Fonctionnalité** : La ligne `Fonctionnalité:` contient **uniquement le titre métier pur** (sans parenthèses d'identifiants externes). Les clés et Jira IDs sont gérées exclusivement dans le frontmatter YAML.
4. **Contrats Déclaratifs & Zéro Code Physique (ADR-0319 Universal Dev Handoff)** : Interdiction formelle d'insérer du code source, du pseudo-code syntaxique (`== true`, blocs C#/MAUI) ou des noms de classes/méthodes physiques d'une codebase spécifique (`LegalMentionsView`, `GetCookiesWebView()`, `MauiProgram`). Décrire les parcours, composants et règles en français fonctionnel naturel (ex: *"l'écran des Mentions Légales"*, *"la redirection web historique"*).
5. **Principe Doc-First SDKs & Tiers (ADR-0319)** : Remplacer tout code d'intégration tiers par des liens directs vers la documentation officielle ingérée (`docs/00-ingested/...`) afin de fournir un cahier des charges fonctionnel pur et universel à l'équipe de dev.


### Étape 4 : Validation Sémantique & Auto-Audit (WikiFix)

1. **Auto-Réparation (Self-Healing)** : Exécution automatique en arrière-plan de `python src/swarm.py wikifix` et `python src/swarm.py sync --project <nom_projet>`.
2. **Correction en Boucle** : Si WikiFix signale des erreurs (ex: pilier Gherkin manquant, fuite de jargon technique), l'agent se corrige silencieusement jusqu'à obtenir un Exit Code 0.
3. **Passage de Statut** : Transition vers `status: READY_FOR_GROOMING` (invest_score > 80%).

### Étape 5 : Export JIRA & Universal Dev Handoff (Relais Dev / Agent IA)

1. **Export & Freeze** : Exécution de `python src/swarm.py to-tickets` pour formater l'export Jira/DevOps.
2. **Universal Dev Handoff (ADR-0319)** : Le récit validé est prêt à être consommé par n'importe quel développeur ou agent IA aval (Renaud, Cursor, Copilot, OpenSpec, etc.) pour la phase de build physique.
3. **Statut Final** : `status: READY_FOR_DEV` ou `SYNCED`.

---

## 🏛️ Gestion Améliorée des ADRs (`docs/01-architecture/`)

Pour garantir l'**Isolation Technique** (le backlog reste fonctionnel, les détails techniques et choix d'implémentation vont dans les ADRs), toute décision structurante prise pendant le Grilling génère un ADR.

### 1. Critères de Déclenchement d'un ADR

Un ADR est rédigé si la décision remplit au moins **deux de ces critères** :
- **Choix d'Architecture / Librairie** : Arbitrage entre au moins 2 alternatives viables (ex: SDK Alpha vs API REST).
- **Difficile à Inverser** : Décision avec un impact important sur la structure du projet (*hard to reverse*).
- **Impact Multi-Composants** : Décision qui influence plusieurs récits ou plusieurs codebases (ex: App A, App B, App C).

### 2. Emplacement & Naming Standard

- **Chemin** : `Projects/<nom_projet>/docs/01-architecture/ADR-XXX-<slug_titre>.md`
- **Numérotation** : Séquentielle à 3 chiffres (`ADR-001-`, `ADR-002-`, etc.).

### 3. Structure Optimisée d'un ADR (Gabarit 4 Sections)

```markdown
# ADR-XXX : [Titre Concis de la Décision]

## 1. Contexte & Problème
[Explication en 2-3 phrases de l'enjeu et de la problématique technique/métier à résoudre.]

## 2. Décision Retenue
[Description claire de la solution choisie et des composantes retenues.]

## 3. Justification & Alternatives Rejetées
* **Option Choisie** : [Pourquoi cette option l'emporte].
* **Option(s) Rejetée(s)** : [Pourquoi les autres alternatives ont été écartées].

## 4. Traçabilité & Impacts
* **Stories Impactées** : [Nom de la Fonctionnalité / Titre de la Story].
* **Règles Métier associées** : [RM-XXX].
```

---

## 📊 Critères de Qualité INVEST (Audit Interne)

- L'injection de jargon technique dans la Story au lieu d'un ADR fait chuter la note d'Isolation Fonctionnelle.
- Omettre l'un des 4 piliers Gherkin entraîne un échec immédiat de WikiFix.
- Poser plus d'une question à la fois viole la Règle d'Or de l'Interview.
