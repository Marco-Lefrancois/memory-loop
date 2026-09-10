# 📑 Protocole Normatif : Dossier de Preuves Documentaires & Cadrage Pré-Rédaction

**Statut** : SSOT Normatif  
**Standard** : mLoop Epistemic Grounding Protocol 1.0  
**Date d'effet** : 3 septembre 2026  
**Domaine** : Cadrage Fonctionnel, Fact-Search Déterministe, Anti-Hallucination, Alignement Métier  
**Références Constitutionnelles** :  
- [ADR-0320 : Grill-Me, Frontier Design Tree & Alignement Métier](../adr-system/0320-grill-me-frontier-design-tree-alignment.md)  
- [ADR-0326 : Fact-Search Obligatoire, Preuves Visibles en 4 Couches & Revue Sémantique](../adr-system/0326-fact-search-and-substantive-content-review.md)  
- [FACT_SEARCH_PROTOCOL.md](FACT_SEARCH_PROTOCOL.md)  
- [PROJECT_LIFECYCLE_STAGES.md](PROJECT_LIFECYCLE_STAGES.md)  
- [Gabarit Officiel](../blueprints/dossier_de_preuves_template.md)  

---

## 1. Vision & Fondement Méthodologique

Le **Dossier de Preuves Documentaires & Cadrage** constitue le document officiel et le point de passage obligatoire (*Quality Gate*) précédant toute phase de rédaction de User Story ou de développement dans l'écosystème **Memory Loop (mLoop)**.

### Le Principe de Non-Opacité Épistémique
Dans le développement assisté par IA, la recherche de faits ne doit **jamais** être un processus occulte où l'agent prétend comprendre le domaine sans en prouver la source. Même lorsque les exigences paraissent simples ou limpides, l'agent a l'obligation formelle de restituer son socle de faits établis afin que le Product Owner et l'Architecte puissent valider instantanément la justesse de sa compréhension avant d'engager le moindre effort de rédaction.

---

## 2. Règle d'Exécution Inconditionnelle

> [!IMPORTANT]
> **Règle de Transparence Inconditionnelle (Gate Pré-Rédaction)** :  
> La production et la restitution du Dossier de Preuves Documentaires sont **obligatoires pour chaque récit**, qu'une session de Grilling interactive soit requise ou non.  
> Il est formellement interdit de passer directement de la phase d'ingestion à la rédaction d'un récit (`backlog/stories/<ID>.md`) sans avoir au préalable généré, affiché et archivé ce dossier.

---

## 3. Les 5 Sections Normatives du Dossier de Preuves

Tout Dossier de Preuves doit impérativement respecter la structure du gabarit officiel ([`standards/blueprints/dossier_de_preuves_template.md`](../blueprints/dossier_de_preuves_template.md)) :

1. **Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)** :
   - Liens officiels distants (Figma avec `node-id`, Azure DevOps Wiki).
   - Liens locaux cliquables `file:///...` vers les assets vectoriels SVG (`docs/05-assets/`) et les documents normalisés (`docs/00-ingested/`).
   - *Clause d'Exemption Headless* : Pour les tâches d'infrastructure, migrations DB ou Spikes techniques sans interface visuelle, la mention `N/A - Headless` est autorisée, et le code source physique ou script technique devient la source principale.
2. **Extraits Verbatim Sourcés (Passage-Level Grounding)** :
   - *Règle du Double Ancrage Indélébile* : Obligation de combiner (a) l'ancrage géométrique (`Lignes X–Y`), (b) la citation textuelle mot-à-mot intégrale d'au moins 15 mots (`« Citation »`), et (c) le fait établi déduit. Cette combinaison immunise la preuve contre tout décalage ultérieur lors de rééditions du document source.
3. **Schéma de Données & Tables Clés (Modèle DBML / Dataverse)** :
   - Diagramme Mermaid ERD des relations d'entités.
   - Énumération des entités référentielles et transactionnelles impliquées.
4. **Contrats Déclaratifs Cibles** :
   - Backend : Endpoints REST (méthodes, schémas JSON requête/réponse, idempotence).
   - Frontend : Matrice Call-to-Actions (déclencheurs UI, états visuels, rétroaction).
5. **Évaluation de la Frontière Active (Issue A ou B)** :
   - **Cas A (Si arbitrage requis)** : Question d'arbitrage unitaire 1:1 motivée, assortie d'options A/B et de la recommandation technique mLoop.
   - **Cas B (Si zéro arbitrage requis)** : Constat formel de frontière vide attestant que tous les faits sont documentés sans ambiguïté, sollicitant la validation humaine du socle avant rédaction.

---

### 3.1. Hiérarchie de Vérité mLoop (Hierarchy of Truth)

En cas de divergence ou de conflit direct entre plusieurs sources d'information (*Cross-Source Contradiction*), l'arbitrage applique rigoureusement la préséance suivante :

1. 🥇 **Niveau 1 (Souverain)** : **Arbitrage PO explicite** consigné en séance Grill (résout définitivement l'impasse).
2. 🥈 **Niveau 2 (Visuel & Interaction)** : **Maquette Figma validée la plus récente** (fait foi pour l'agencement des écrans, les champs visibles et les déclencheurs UI).
3. 🥉 **Niveau 3 (Spécifications Métier)** : **Guides formels ingérés** (`PLAN-XXX`, `ADR-XXX`).
4. 🎖️ **Niveau 4 (Contexte & Historique)** : **Transcriptions d'ateliers et réunions** (éclairent l'intention initiale, mais s'effacent devant un document contractuel ou une maquette postérieure).

---

## 4. Persistance, Dérive Temporelle & Archivage des Dossiers

Afin d'assurer la pérennité de l'audit et l'accès ergonomique, chaque dossier de preuves est matérialisé sous un double format :
1. **Fichier Markdown Sidecar** : Sauvegardé sous `Projects/<PROJET>/memory/evidence/<STORY_ID>_fact_dossier.md`.
2. **Widget Interactif HTML (Optionnel & Recommandé)** : Généré sous forme de widget autonome Antigravity / Generative UI (Tailwind CSS) pour une consultation enrichie dans l'IDE ou le navigateur.

### 4.1. Gestion de la Dérive Temporelle (Staleness Detection)
Chaque dossier comporte un en-tête YAML contenant la date de création et les empreintes des sources citées. Si un document source ou le récit Markdown associé subit une modification postérieure à la date de création du dossier, le dossier est marqué au statut `STALE_PENDING_REVISION` et doit être revalidé avant tout passage en développement.

---

## 5. Sanctuarisation de la Pureté Fonctionnelle & Handoff Développeur

Conformément à l'**ADR-0319** et à l'**ADR-0326** :
* Le dossier de preuves vit **exclusivement** dans le dialogue de cadrage et dans le répertoire `memory/evidence/`.
* Le fichier physique de la User Story (`backlog/stories/<JIRA_KEY>.md`) reste strictement no-code et purement fonctionnel ; il se termine **strictement** après la section `## Scénarios de test`.
* **Passerelle de Handoff Développeur** : Afin que les développeurs et agents d'implémentation retrouvent immédiatement le dossier de preuves sans recherche arborescente, la section `## Références` du récit Markdown inclut obligatoirement le lien relatif :
  ```markdown
  - 📂 **Dossier de Preuves & Cadrage SSOT** : [<STORY_ID>_fact_dossier.md](../../memory/evidence/<STORY_ID>_fact_dossier.md)
  ```
