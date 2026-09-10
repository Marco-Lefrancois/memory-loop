# ADR-0349 : Paradigme Karpathy LLM Wiki, Concept-Table Navigable & Gouvernance Déterministe du Crawler Web

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-03
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Pipeline Crawler (`src/pipelines/crawler.py`), Pipeline Research (`src/pipelines/research_pipeline.py`), Ingestion & Connaissances OKF (`docs/06-knowledge/`, `reference/`), Linter WikiFix (`src/pipelines/wikifix.py`)

---

## 1. Contexte & Problématique

L'ingestion documentaire et la persistance mémorielle dans les architectures agentiques s'affrontent historiquement sur deux modèles d'exploitation des connaissances :
1. **L'illusion du RAG Query-Time Éphémère** : Les flux de travail documentaires conventionnels (NotebookLM, assistants de chat, vectorstores naïfs) découpent les sources brutes en fragments linéaires statiques. À chaque requête, le grand modèle de langage redécouvre les fragments pertinents, tente une synthèse impromptue sans mémoire intermédiaire et perd aussitôt toute structure déduite (*Zero Accumulation, Context Rot*).
2. **La Démonstration Karpathy LLM Wiki** : Formalisé initialement par Andrej Karpathy et instrumenté dans le repository canonique `nanzhipro/Karpathy-llm-wiki-bootstrap-skill`, le modèle **LLM Wiki** déplace l'effort de synthèse au moment de l'ingestion (`ingest time`). L'agent agit comme compilateur et mainteneur continu d'un ensemble structuré et interconnecté de fichiers Markdown (`wiki/`) placé en avant-poste des sources brutes immuables (`raw/`), sous le contrôle d'un contrat d'exploitation unifié (`SCHEMA.md`).
3. **La Dérive Opérationnelle Isolée dans le Crawler mLoop** : L'audit du moteur `src/pipelines/crawler.py` a mis en lumière une fuite de périmètre : lors de l'appel avec un paramètre `--url <URL>` explicite, l'agent crawler extrayait sans distinction toutes les URLs trouvées dans l'ensemble des répertoires du projet (`DOCS`, `DIRECTIVES`, `REFERENCE`, `BACKLOG`), déclenchant des dizaines de requêtes réseau non sollicitées, gaspillant la bande passante et créant des erreurs sur les domaines fictifs ou privés.

Cette ADR formalise l'ancrage constitutionnel des enseignements du Karpathy LLM Wiki dans mLoop et arrête les règles de gouvernance étanche du crawler web.

---

## 2. Décisions d'Architecture

### 2.1 Diptyque de Grounding & Audit Épistémique

Conformément au standard [ADR-0335](0335-deep-paper-note-ingestion-epistemic-grounding.md), toute intégration technologique repose sur un découpage épistémique strict :

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   DIPTYQUE DE GROUNDING — KARPATHY LLM WIKI                      │
├────────────────────────────────────────┬─────────────────────────────────────────┤
│ WHAT IT ACTUALLY PROVES                │ WHAT IT DOES NOT PROVE                  │
│ • La compilation à l'ingestion         │ • Pas de scalabilité prouvée sur des    │
│   surpasse le RAG au query-time sur    │   bases massives (> 10 000 pages) sans  │
│   les requêtes multi-documents.        │   coût d'inférence cumulé (Ripple).     │
│ • La séparation tripartite hermétique  │ • La résolution de contradictions       │
│   (raw / wiki / SCHEMA) prévient       │   critiques reste tributaire d'un       │
│   le pourrissement de contexte.        │   arbitrage humain (HITL).              │
│ • Le BM25 local SQLite FTS5 est un     │ • Le texte/Markdown seul ne remplace    │
│   excellent Candidate Finder sans coût.│   pas un graphe de code AST (CodeGraph).│
├────────────────────────────────────────┴─────────────────────────────────────────┤
│ CLAIM BOUNDARIES                                                                 │
│ Valide pour les bases de connaissances d'architecture, règles métier, recherche  │
│ et backlogs vivants. N'invalide pas l'indexation de code physique.               │
└──────────────────────────────────────────────────────────────────────────────────┘
```

#### Ce que la source démontre formellement (`what_it_actually_proves`)
- **Compounding Knowledge** : Un wiki incrémental maintenu par l'IA capitalise la connaissance au lieu de la reconstituer à chaque session.
- **Règle d'Immuabilité des Preuves** : Le dossier source (`reference/` dans mLoop, `raw/` dans le skill) doit demeurer en lecture seule absolue pour garantir la vérifiabilité des assertions.
- **Contrat Opérationnel Unique** : Les fichiers d'amorçage pour les runtimes (`AGENTS.md`, `GEMINI.md`, `CLAUDE.md`) doivent rester des pointeurs légers vers le contrat d'exploitation SSOT (`standards/` et schémas), sans duplication sauvage de règles.
- **Candidate Finder Non-Autoritaire** : Tout moteur FTS/BM25 ne sert qu'à localiser les passages candidats ; l'agent a l'obligation formelle d'ouvrir la page source avant d'émettre une réponse.

#### Ce que la source ne démontre pas (`what_it_does_not_prove`)
- Ne garantit pas la scalabilité sans graphe structuré sur des référentiels de plus de 10 000 pages où les cascades de mise à jour (*Ripple Updates*) deviendraient prohibitives en tokens.
- Ne résout pas de manière autonome les contradictions sans heuristique formelle ou validation HITL.

---

### 2.2 Concept-Table comme Surface de Navigation Condensée

mLoop adopte formellement le patron de **Table de Concepts Navigable** (`concept-table.md`) au sein de sa bibliothèque de connaissances (`docs/06-knowledge/` et `Projects/<projet>/docs/`) :

1. **Structure Canonique du Tableau de Concepts** :
   ```markdown
   | Concept | Définition Essentielle | Relations / Pages | Sources Probatoires | Statut de Confiance | Notes de Maintenance |
   ```
2. **Propriétés & Rôle Mnémonique** :
   - Sert de carte cognitive condensée de haut niveau pour l'orchestrateur et les agents en phase de triage/spec.
   - Permet à l'agent de vérifier l'existence d'une entité ou d'un concept métier en un seul regard sans charger les pages de détail.
   - Audité lors du linting sémantique WikiFix pour prévenir toute divergence d'indexation (*Concept Table Drift*).

---

### 2.3 Gouvernance Déterministe du Web Crawler mLoop (`src/pipelines/crawler.py`)

Pour éliminer définitivement les fuites de périmètre et le gaspillage d'appels réseau, les règles suivantes sont gravées dans le moteur :

```
                                  ┌────────────────────────────────┐
                                  │   INVOCATION DU WEB CRAWLER    │
                                  └───────────────┬────────────────┘
                                                  │
                                                  ▼
                                      ┌───────────────────────┐
                                      │ explicit_url fourni ? │
                                      └───────────┬───────────┘
                                                  │
                                  ┌───────────────┴───────────────┐
                               OUI│                             NON│
                                  ▼                               ▼
                 ┌────────────────────────────────┐  ┌────────────────────────────────┐
                 │ CRAWL STRICTEMENT CIBLÉ        │  │ SCAN DOCUMENTAIRE DU PROJET    │
                 │ • initial_urls = [explicit_url]│  │ • Scan DOCS, BACKLOG, REF      │
                 │ • Découverte limitée à max_depth│ │ • Concurrence contrôlée (5)    │
                 │ • ZÉRO crawl du reste du projet│  │ • Cache TTL systématique       │
                 └────────────────────────────────┘  └────────────────────────────────┘
```

1. **Règle de Confinement d'URL Explicite (Strict Target Isolation)** :
   - Lorsque `explicit_url` est transmis à `WebCrawlerAgent.execute` ou via la CLI (`--url <URL>`), le crawler **ne doit analyser que cette cible précise** et ses liens dérivés jusqu'à `max_depth`.
   - Le balayage automatique des répertoires de documentation (`DOCS`, `DIRECTIVES`, `REFERENCE`, `BACKLOG`) n'est déclenché **que si aucune URL explicite n'est fournie**, ou si le drapeau explicite `--all-sources` est activé.
2. **Prise en Compte Systématique du Cache Déterministe TTL** :
   - Dans le pipeline R&D (`research_pipeline.py`), `WebCrawlerAgent` est instancié avec un `max_age=86400` (24 heures) par défaut. Toute ressource déjà ingérée sous `memory/crawler/cache/` et valide est servie sans solliciter le réseau.
3. **Support Étendu des Repositories de Code & Packages Agentiques** :
   - Lorsque l'URL cible est un dépôt GitHub (ex: `https://github.com/org/repo`), le crawler sonde en priorité le `README.md` brut, puis, si `max_depth > 0` ou s'il s'agit d'un skill/package, extrait les fichiers documentaires clés (`SKILL.md`, `SCHEMA.md`, `references/`) via la détection des liens Markdown internes.

---

### 2.4 Intégration dans le Linter Sémantique WikiFix

Le linter sémantique `src/pipelines/wikifix.py` intègre les 4 vérifications structurelles canoniques inspirées du workflow de lint Karpathy :
- **Orphan Pages** : Fichiers markdown dans `docs/` ne recevant aucun lien entrant.
- **Broken Wikilinks** : Liens sous syntaxe `[[target]]` ou markdown pointant vers des ancres ou fichiers inexistants.
- **Index Drift** : Documents créés dans l'arborescence mais omis du sommaire `index.md` ou du backlog.
- **Pending Contradictions** : Marquage explicite des blocs de divergence nécessitant arbitrage (`Resolution: pending`).

---

## 3. Conséquences

### Positives
- **Élimination Immédiate du Bruit Réseau** : L'exécution de `swarm.py crawl --url <cible>` ne déclenche plus l'exploration fantôme de 50+ URLs du projet.
- **Richesse Mnémonique Décuplée** : Standardisation du Concept Table offrant un compromis optimal entre compacité d'instruction budget et exhaustivité sémantique.
- **Fidélité au Grounding Épistémique** : Traçabilité totale des faits extraits avec maintien du statut de confiance (`single-source`, `verified`).

### Neutres
- Nécessite d'exécuter explicitement `swarm.py crawl --all-sources` pour auditer l'ensemble des liens externes du projet.

### Négatives / Risques
- Une discipline stricte de mise à jour des métadonnées YAML reste obligatoire (surveillée par `swarm.py vibe-check`).

---

## 4. Statut d'Alignement & Implémentation

| Composant | Fichier Cible | Action Réalisée |
| :--- | :--- | :--- |
| **Crawler Engine** | `src/pipelines/crawler.py` | Confinement strict sur `explicit_url`, support de `all_sources`. |
| **CLI Registry** | `src/commands/_registry.py` | Enregistrement de l'argument `--all-sources` pour la commande `crawl`. |
| **Research Pipeline** | `src/pipelines/research_pipeline.py` | Application du TTL par défaut (`max_age=86400`). |
| **Recherche Staging** | `Projects/mLoop/reference/research/CURRENT_RESEARCH.md` | Rapport de recherche consolidé et archivage des sources brutes. |
| **Index SSOT** | `standards/adr-system/README.md` | Enregistrement constitutionnel de l'ADR-0348. |
