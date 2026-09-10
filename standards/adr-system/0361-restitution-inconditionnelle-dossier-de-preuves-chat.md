---
id: 0361
title: "Restitution Inconditionnelle du Dossier de Preuves Documentaires dans le Chat & Interdiction des Plans d'Intention Abstraits"
status: "ACCEPTÉ / SSOT NORMATIF"
date: "2026-09-08"
deciders: ["Marco Lefrançois", "mLoop Architecture & Gouvernance Agentique"]
domain: "Cadrage Fonctionnel, Fact-Search, Anti-Opacité Épistémique, Expérience Utilisateur PO"
validation_rules: []
---

# ADR-0361 : Restitution Inconditionnelle du Dossier de Preuves Documentaires dans le Chat & Interdiction des Plans d'Intention Abstraits

- **Statut** : ACCEPTÉ / SSOT NORMATIF
- **Date** : 8 septembre 2026
- **Décideurs** : Marco Lefrançois, Équipe mLoop, Architecture & Gouvernance Agentique
- **Domaine** : Cadrage Fonctionnel, Fact-Search Déterministe, Anti-Opacité Épistémique, Expérience Utilisateur PO
- **Références Constitutionnelles** :
  - [ADR-0320 : Grill-Me, Frontier Design Tree & Alignement Métier](0320-grill-me-frontier-design-tree-alignment.md)
  - [ADR-0326 : Fact-Search Obligatoire, Preuves Visibles en 4 Couches & Revue Sémantique](0326-fact-search-and-substantive-content-review.md)
  - [ADR-0353 : Confiance & Traçabilité en RAG Agentique : Flight Recorder & Admission of Limits](0353-agentic-rag-trust-evidence-retrieval-flight-recorder.md)
  - [DOSSIER_DE_PREUVES_PROTOCOL.md](../protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
  - [Gabarit Officiel](../blueprints/dossier_de_preuves_template.md)

---

## 1. Contexte & Problème

Dans le cycle de vie mLoop, l'étape de cadrage / incubation d'un récit constitue le pivot épistémique déterminant la qualité de toute la chaîne aval (INVEST, Gherkin 4 piliers, EvidencePack, tests et code).

Bien que l'ADR-0326 ait instauré le principe d'un Dossier de Preuves Documentaires, une dérive comportementale récurrente a été observée chez les agents d'orchestration :
1. **La fuite dans le « méta-plan » abstrait** : Lorsqu'un utilisateur demande de cadrer ou d'analyser un récit (ex: *« J'aimerais tester les analyses pour le récit INC-005-BE »*), l'agent réagit fréquemment en créant un plan d'implémentation procédural générique (*« Je vais explorer les fichiers, puis je ferai un fact-search, puis je créerai le dossier de preuves »*).
2. **L'opacité pour le Product Owner / Architecte** : Ce réflexe impose une friction inutile à l'utilisateur, qui doit valider un vœu d'intention vide au lieu d'avoir sous les yeux la matière première métier concrète (les citations exactes du client, les liens des maquettes d'écrans, le modèle de données, les routes cibles et les questions d'arbitrage).

L'utilisateur a formellement acté cette exigence : **« C'est exactement le résultat que je veux voir à tout coup à cette étape svp, peux-tu le cristalliser dans Memory Loop »**.

---

## 2. Décision Retenue

### 2.1. Règle d'Or : Interdiction des Plans d'Intention Abstraits au Cadrage
Dès lors qu'une requête utilisateur sollicite le **cadrage**, l'**analyse**, l'**incubation**, la **spécification** ou le **grooming** d'une User Story :
* **Interdiction absolue** de répondre par une simple promesse d'action, une liste de tâches futures ou un plan d'implémentation générique vide de substance.
* L'agent a l'obligation formelle d'exécuter immédiatement la recherche factuelle FTS5 en arrière-plan et de **restituer IN EXTENSO dans le chat** le Dossier de Preuves Documentaires complet.

### 2.2. Restitution Textuelle Intégrale dans le Dialogue
Le Dossier de Preuves ne doit pas être dissimulé derrière un simple lien ou un fichier silencieux. Il doit être affiché dans le corps même de la réponse de l'agent, garantissant une lisibilité directe et immédiate pour l'humain.

### 2.3. Les 7 Composantes Inviolables du Dossier Restitué
Tout Dossier de Preuves présenté à cette étape doit obligatoirement intégrer :
1. **En-tête Métier Pur** : Identifiants (id, jira_key, pic_key), couche technique (ackend/rontend), dépendances amont et aval.
2. **Sources Physiques & Maquettes SSOT (Liens Cliquables)** : Tableau exhaustif des maquettes vectorielles (.svg sous docs/05-assets/ avec liens locaux RFC ile:///... et liens Figma distants), transcriptions d'ateliers et spécifications.
3. **Matrice de Résolution des Conflits** : Arbitrage explicite selon la *Hierarchy of Truth* à 4 niveaux (N1 Grill PO > N2 Figma > N3 Specs > N4 Verbatims).
4. **Extraits Verbatim Sourcés (Passage-Level Grounding & Double Ancrage)** : Citations mot-à-mot intégrales d'au moins 15 mots avec bornage précis de lignes (#LXX-LYY) et déduction déterministe du fait établi.
5. **Schéma de Données & Tables Clés** : Diagramme Mermaid relationnel (ERD) illustrant les entités manipulées et le détail des mutations d'inventaire / états de transition.
6. **Contrats Déclaratifs Cibles** : Endpoints REST complets (méthodes, routes, idempotence, payloads JSON exemple, codes HTTP) pour le backend, ou Matrice Call-to-Actions pour le frontend.
7. **Évaluation de la Frontière Active & Admission of Limits** : Constat formel de frontière vide (Cas B si zéro ambiguïté) ou questions fermées d'arbitrage A/B motivées (Cas A), assorti de la mention de confiance et des limites de preuve (ADR-0353).

### 2.4. Double Matérialisation Atomique
En parallèle de son affichage immédiat dans le chat, l'agent consigne le dossier dans le système de fichiers sous :
Projects/<PROJET>/memory/evidence/<STORY_ID>_fact_dossier.md

---

## 3. Conséquences & Impact Opérationnel

* **Zéro Friction Décisionnelle** : Le PO valide en un coup d'œil l'exhaustivité de la compréhension métier de l'agent sans allers-retours superflus.
* **Éradication des Coquilles Vides** : Tout début de récit repose sur un socle physique prouvé, éliminant à la racine les hallucinations de paramètres ou de logique d'affaires.
* **Auditabilité Parfaite** : Les preuves affichées correspondent bit-à-bit au fichier sidecar archivé dans memory/evidence/.
