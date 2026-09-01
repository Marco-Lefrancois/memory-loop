---
id: 0342
validation_rules: []
---

# ADR-0342 : Architecture de Projet Modulaire par Sous-Domaines & Isolation des Baux OWNS:

- **Statut** : ACCEPTÉ / SSOT NORMATIF
- **Date** : 29 août 2026
- **Décideurs** : Équipe mLoop, Architecture & Gouvernance Agentique
- **Domaine** : Organisation de Projet, Bounded Contexts, Isolation Multi-Modules, Concurrence Agentique

---

## Contexte & Problème

Lors de l'expansion d'un projet d'envergure couvrant plusieurs modules d'affaires interdépendants (ex: un Couvoir avicole comprenant la Réception, l'Incubation, les Mirages, les Éclosoirs et la Vente), deux dérives opposées menacent l'intégrité du système :

1. **La Fragmentation en Micro-Projets Indépendants** :
   - Créer un projet mLoop distinct par module (ex: `BoireFrere_Reception`, `BoireFrere_Incubation`, `BoireFrere_Ventes`) entraîne la duplication massive de la documentation de référence (Wiki SIGPA), la dérive des schémas de données Dataverse et la rupture du graphe sémantique FTS5 / Graphify.
   - Perte de la traçabilité continue du cycle de vie des entités métier (ex: un lot d'œufs qui traverse la réception jusqu'à l'éclosion).

2. **L'Entassement Plat et Non-Structuré** :
   - Regrouper tous les récits (`REC-001`, `INC-001`, `VNT-001`) et assets dans un dossier racine plat sans compartimentation génère des collisions de nommage, une dilution de l'attention de l'IA et l'impossibilité d'exécuter des sous-agents en parallèle sans conflits d'écriture.

Il est nécessaire d'institutionnaliser un standard pour **structurer un projet mLoop unique en sous-modules étanches** partageant le même socle de connaissances.

---

## Décision Retenue

1. **Le Principe du Bounded Context Modulaire mLoop** :
   - Dès lors que deux ou plusieurs modules partagent la même documentation source (Wiki client), les mêmes entités de données centrales (`docs/03-models/core/`) et le même lexique métier (`CONTEXT.md`), **ils résident obligatoirement dans un même projet mLoop unifié**.
   - Le projet est subdivisé en sous-dossiers de modules normalisés sous `reference/`, `docs/`, `backlog/` et `memory/`.

2. **Arborescence Standard Multi-Modules** :

   ```
   Projects/<PROJET_UNIFIÉ>/
   ├── reference/
   │   ├── shared/                        # Documentation transverse (Wiki, schémas DB maîtres)
   │   ├── 01-<module_a>/                 # Matière brute propre au module A (VTT, TXT, PDF)
   │   └── 02-<module_b>/                 # Matière brute propre au module B (VTT, PNG, TXT)
   │
   ├── docs/
   │   ├── 00-ingested/ (01-<module>/...) # Documents ingérés normalisés par module
   │   ├── 02-business-rules/
   │   │   ├── core/                      # Règles d'affaires transverses partagées (RM-001...)
   │   │   └── 01-<module>/               # Règles spécifiques au module (RM-MOD-XXX...)
   │   ├── 03-models/
   │   │   ├── core/                      # Schémas maîtres partagés (entités globales)
   │   │   └── 01-<module>/               # Entités ou tables spécifiques au module
   │   └── 05-assets/ (01-<module>/...)   # Maquettes vectorielles SVG classées par module
   │
   ├── backlog/
   │   ├── stories/ (01-<module>/...)     # User Stories 4 Piliers préfixées (MOD-001-FE...)
   │   ├── gates/ (01-<module>/...)       # Grands Livres <MODULE>.gates.md
   │   └── sprint_backlog.md              # Tableau de bord maître avec sections ## Module X
   │
   └── memory/
       └── evidence/ (01-<module>/...)    # EvidencePacks sidecar JSON structurés en miroir
   ```

3. **Isolation des Baux de Concurrence (`OWNS:`) par Module (ADR-0341)** :
   - Chaque grand livre de portails (`<MODULE>.gates.md`) déclare un périmètre de propriété strict et étanche :
     ```markdown
     OWNS: backlog/stories/02-incubation/**, memory/evidence/02-incubation/**, docs/02-business-rules/02-incubation/**
     ```
   - Deux workers agentiques (ex: Worker A sur la Réception et Worker B sur l'Incubation) peuvent s'exécuter en parallèle sans verrou bloquant ni collision de fichiers.

4. **Matrice d'Arbitrage : Projet Distinct vs Sous-Module** :

| Critère d'Arbitrage | Sous-Module dans le Projet Existant | Projet mLoop Distinct |
| :--- | :--- | :--- |
| **Documentation & Wiki** | Identique / Partagé (même wiki client) | Complètement distinct (client ou domaine différent) |
| **Modèle de Données** | Schéma Dataverse / SQL partagé | Bases de données totalement indépendantes |
| **Flux Métier** | Entités transmises d'une étape à l'autre | Zéro couplage fonctionnel |
| **Dépôt Git Client** | Même monorepo ou dépôt de specs | Dépôts Git physiquement séparés |
| **Gouvernance Backlog** | Un seul Sprint Backlog consolidé | Tableaux Jira / Sprint Backlogs distincts |

---

## Conséquences

### Positives
- **Zéro Duplication de Mémoire** : Les 4 500+ chunks FTS5 et le graphe sémantique Graphify sont immédiatement partagés entre tous les modules.
- **Concurrence Multi-Agents Sans Faille** : Baux `OWNS:` étanches permettant le travail simultané de plusieurs workers Herdr.
- **Clarté du Backlog** : Visualisation modulaire limpide dans `sprint_backlog.md` avec progression indépendante par module.
- **Rigueur Sidecar** : 100% de conformité avec le standard des EvidencePacks sans pollution de code.

### Négatives / Contraintes
- **Discipline de Préfixe** : Obligation d'utiliser des préfixes d'identifiants clairs (`REC-`, `INC-`, `VNT-`) pour éviter toute ambiguïté dans les liens de récits.
