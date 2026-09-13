# ADR-0366 : Standard Story 2.0, Handoff Tripartite et Maillage Référentiel

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-13
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Récits utilisateurs (`backlog/stories/`), Gabarits (`standards/blueprints/story_template.md`), Paquet de Handoff (`backlog/handoff/`), Checklists d'intégrité (`.agents/references/`), Linters de validation (`src/pipelines/struct_checker.py`, `src/pipelines/evidence_pack.py`)
- **Autorité** : [ADR-0100](0100-structure-repertoire-projet-client.md), [ADR-0103](0103-segmentation-memory-loop-openspec.md), [ADR-0301](0301-standard-gherkin-outlines-4-piliers.md), [ADR-0319](0319-dual-agent-handoff-openspec-ready.md), [ADR-0326](0326-fact-search-socle-factuel.md), [ADR-0365](0365-harmonisation-symbiotique-skills-et-standard-agent-skills.md)

---

## 1. Contexte & Problématique

L'harmonisation symbiotique des compétences (ADR-0365) a doté Memory Loop d'un socle d'excellence d'ingénierie logicielle (TDD, Beyoncé Rule, décomposition de tâches). Cependant, l'examen de la transmission opérationnelle entre l'amont fonctionnel et l'aval technique a mis en évidence quatre ruptures critiques :

1. **Confusion entre Spécification Fonctionnelle et Implémentation Technique** :
   Les récits utilisateurs (`backlog/stories/`) tendaient soit à s'alourdir de détails d'implémentation (requêtes SQL, bouts de code, bruit de traçabilité violant l'ADR-0319), soit à rester trop abstraits pour guider directement un agent IA ou un développeur dans la phase de build.
2. **Ambiguïté sur l'Hébergement du Handoff et Respect des Piliers Client** :
   L'ADR-0100 et l'ADR-0103 sanctuarisent la Loi des 3 Piliers (`reference/`, `docs/`, `backlog/`, `memory/`) et interdisent les répertoires `src/` et `openspec/` à la racine des projets clients pour éviter de confondre le dépôt d'analyse SSOT avec le dépôt de code applicatif. L'injection d'un dossier racine `openspec/` dans un projet client mLoop crée un conflit d'arborescence direct.
3. **Fragilité du Maillage de Références (Mono-Lien & Rupture de Contexte)** :
   L'utilisation exclusive de chemins relatifs locaux (ex: `../../memory/evidence/REC_fact_dossier.md`) brise la navigation dans les portails Web distants (Azure DevOps Git, Wikis, GitHub) ; inversement, l'emploi exclusif d'URLs HTTP distantes empêche l'ouverture instantanée en un clic dans les IDE locaux (Cursor, VS Code, Antigravity) et pénalise les environnements déconnectés.
4. **Faux Positifs Structurels sur les Récits Backend** :
   Le linter structurel (`struct_checker.py`) imposait un gabarit unique orienté interface utilisateur (`### Spécifications de l'Interface`, `### Liste Call to Actions`), déclenchant des violations C4 injustifiées sur les récits de pure API backend (`layer: backend`).

---

## 2. Décisions d'Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             CHAÎNE DE VALEUR STORY 2.0 & HANDOFF                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│   1. AMONT : Preuves & Grounding Factuel                                                         │
│   ├── docs/00-ingested/ (Ateliers, specs) & docs/05-assets/ (Maquettes SVG vectorielles)         │
│   ├── memory/evidence/<ID>_fact_dossier.md (Extraits verbatim ≥ 15 mots, Schéma DBML, Arbitrage) │
│   └── memory/evidence/<ID>_evidence.json (Empreintes SHA-256, Statut NLI, Requêtes FTS5)         │
│                                      │                                                           │
│                                      ▼                                                           │
│   2. CŒUR : Spécification Fonctionnelle Pure Story 2.0 (Zero-Bruit, No-Code)                     │
│   └── backlog/stories/<module>/<ID>.md                                                           │
│       ├── Frontmatter YAML typé (id, jira_key, epic_key, type, title, tags, layer, status)       │
│       ├── Description & Contexte (INVEST, périmètre métier pur, zéro snippet de code)            │
│       ├── Critères d'acceptation (Matrice des opérations / CTA, règles d'affaires)               │
│       ├── Navigation / Contrats d'échange API (Profil A/B déclaratif, schémas JSON)              │
│       ├── Références (3 sous-blocs étanches avec Dual-Link Web + Local file:///...)              │
│       └── Scénarios de test (Les 4 Piliers Gherkin : Nominal, Exceptions, Résilience, Empty)     │
│                                      │                                                           │
│                                      ▼                                                           │
│   3. AVAL : Paquet de Handoff Développeur Tripartite (Inspiration OpenSpec & Zero-Dépendance)   │
│   └── backlog/handoff/<ID>/ (ou openspec/changes/<ID>/ dans le dépôt applicatif)                 │
│       ├── proposal.md (Le Pourquoi : Rationale technique, impact architectural, sécurité)        │
│       ├── specs/api.md (Le Quoi : Schémas JSON d'échange, routes OpenAPI, codes HTTP)            │
│       └── tasks.md (Le Comment : Checklist atomique de micro-tâches < 5 fichiers, TDD)           │
│                                      │                                                           │
│                                      ▼                                                           │
│   4. EXÉCUTION : Ingénierie Physique (Agent-Skills d'Addy Osmani)                               │
│       ├── test-driven-development (Red-Green-Refactor, Règle de Beyoncé)                         │
│       ├── source-driven-development (Doc SDK read-only, respect des versions)                    │
│       └── Definition of Done (.agents/references/definition-of-done.md)                          │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Séparation Stricte : Récit Fonctionnel (Cœur) vs Handoff Technique (Aval)
- **Le Récit Fonctionnel (`backlog/stories/`)** : Reste 100% métier, lisible par les Product Owners et l'équipe d'affaires. Il obéit à la règle **No-Code** stricte de l'ADR-0319 : aucun snippet de code source (C#, Swift, TypeScript), aucune présomption de framework UI, description déclarative des contrats d'échange.
- **Le Paquet de Handoff Tripartite (`backlog/handoff/<ID>/`)** : Fournit le pont technique immédiat vers l'implémentation logicielle, rédigé en Markdown souverain sans exiger aucun binaire externe ni dépendance npm :
  1. `proposal.md` : Rationale technique, impact sur les tables de données, découplage architectural, considérations de performance et sécurité.
  2. `specs/api.md` (ou `specs/<domaine>.md`) : Contrats d'échange formels, spécification OpenAPI / JSON Schema, codes d'état HTTP, idempotence et gestion d'erreurs.
  3. `tasks.md` : Découpage ordonné en micro-tâches atomiques (< 5 fichiers) suivant le cycle Red-Green-Refactor et la Règle de Beyoncé ("Si tu y tiens, écris un test").

### 2.2 Emplacement Canonique du Handoff (Loi des 3 Piliers Préservée)
- **Au sein du Dépôt d'Analyse mLoop (Mode CLIENT)** : Le handoff technique réside sous [`backlog/handoff/<STORY_ID>/`](../../Projects/). Cette arborescence :
  - Respecte scrupuleusement la Loi des 3 Piliers (ADR-0100 : `reference/`, `docs/`, `backlog/`, `memory/`).
  - Évite toute collision avec l'interdiction de `src/` et `openspec/` à la racine du projet client.
  - Se synchronise naturellement avec les récits (`backlog/stories/`) et revues Rubber Duck (`backlog/reviews/`).
- **Dans le Dépôt de Code Applicatif du Développeur** : Si l'équipe de développement exploite le tooling OpenSpec, les fichiers du handoff se projettent ou se copient 1:1 sous `openspec/changes/<STORY_ID>/` dans le dépôt de code cible.

### 2.3 Standardisation du Bloc `## Références` et Pattern « Dual-Link »
La section `## Références` de tout récit utilisateur est obligatoirement subdivisée en 3 sous-blocs étanches :
1. `### 1. Preuves Amont & Traçabilité Factuelle` :
   - Lien vers le Dossier de Preuves Factuelles (`*_fact_dossier.md`).
   - *Règle Zéro-Bruit* : La revue interne Sentinel / Rubber Duck (`rubber_duck_<ID>.md`) demeure archivée sous `backlog/reviews/` pour l'audit de gouvernance, mais est retirée du corps de la User Story pour ne pas polluer l'expérience de lecture des développeurs et du PO.
2. `### 2. Spécifications & Modèles de Données SSOT` :
   - Liens vers les fichiers SSOT du dépôt (`Structure-de-données.md`, cas d'utilisation, ADRs d'architecture).
3. `### 3. Paquet OpenSpec (Handoff Développeur)` :
   - Lien vers la proposition technique (`proposal.md`).
   - Lien vers les contrats d'échange formels (`specs/api.md`).
   - Lien vers le plan de découpage TDD (`tasks.md`).
   - Lien vers la Definition of Done (`reference/definition-of-done.md`).

**Règle du Dual-Link Web + Relatif** : Chaque document du dépôt de documentation doit être cité avec son lien distant HTTPS (Azure DevOps Git `Wiki_AF_Segment2` / GitHub) **ET** son chemin relatif Markdown au sein du dépôt (`../../...`). L'usage de chemins absolus Windows locaux (`file:///C:/...`) est formellement proscrit dans les récits afin de garantir la portabilité universelle pour toute l'équipe et sur les portails Web.

### 2.4 Clause Anti-Leak sur la Pagination & Garde-fous Épistémiques
- **Interdiction de Fuite sur la Pagination** : Tout calcul d'indicateur global (ex: ancienneté maximale, total des stocks, seuil de priorité biologique) DOIT être impérativement calculé côté serveur sur l'ensemble de la population éligible et non sur la seule page courante retournée à l'interface.
- **Format de Date ISO 8601** : Toute date d'échange inter-systèmes doit être typée explicitement en format canonique (ex: `YYYY-MM-DD` pour les dates de ponte, ISO 8601 UTC avec millisecondes pour les horodatages de traçabilité).
- **Couverture de l'Empty State (Pilier 4)** : Les scénarios Gherkin doivent impérativement comporter un scénario explicite couvrant le cas d'inventaire ou de résultat vide (Empty State), validant le retour d'une liste vide `[]` avec code `200 OK` (et non `404 Not Found`).

### 2.5 Adaptation Déterministe du Pipeline de Contrôle
- **`src/pipelines/struct_checker.py`** : La règle C4 (`_check_c4_gold_standard_diff`) distingue le champ `layer` du frontmatter. Pour `layer: backend`, elle reconnaît les sections canoniques (`### Opérations Métier & Logique Backend`, `### Contrats d'échange API`, `### Matrice des Réponses HTTP & Filtres Métier`) évitant tout faux positif C4.
- **`src/pipelines/evidence_pack.py`** : Les chemins candidats de résolution incluent désormais nativement `self.project_path / "memory" / "evidence" / src_name` et `self.project_path / "backlog"`, permettant le calcul d'empreinte SHA-256 déterministe et éliminant le statut dégradé `NOT_CALCULATED_LOCAL_ONLY`.

---

## 3. Conséquences & Bénéfices

- **Clarté Cognitive Maximale** : Le métier lit un récit épuré sans jargon technique ; le développeur dispose d'un plan d'action d'ingénierie prêt pour le TDD.
- **Zéro Régression Constitutionnelle** : La Loi des 3 Piliers de l'ADR-0100 est rigoureusement préservée dans les projets clients, sans pollution de répertoires non standard.
- **Navigation Fluide et Omnicanale** : Les liens `file:///...` et Web HTTPS assurent la continuité de navigation dans tous les environnements d'exploitation.
- **Fiabilité Déterministe** : Le pipeline mLoop (`struct-check`, `confidence`, `calibrate`) valide l'ensemble de la constellation sans friction ni faux positifs.
