# ADR-0350 : Passerelle Obsidian Vault, Cartographie Codebase Canvas 2D & Synchronisation de Session Dev Logs

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-03
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Générateur Canvas (`src/pipelines/canvas_generator.py`), Commandes CLI (`src/swarm.py canvas`), Traçabilité des Sessions (`Projects/<projet>/memory/`), Documentation Obsidian

---

## 1. Contexte & Problématique

Dans le cadre du paradigme mLoop où *Obsidian est l'IDE, l'IA est le développeur, et le projet est le codebase*, la restitution visuelle de l'état d'un projet informatique demeure un levier critique de communication.
L'ADR-0337 avait standardisé la génération de toiles spatiales 2D pour le Story Mapping (`backlog/story_mapping.canvas`). Cependant, deux manques subsistaient dans le cycle de développement :
1. **L'absence de cartographie visuelle 2D du code source (Codebase Architecture Canvas)** : Les diagrammes de flux de composants applicatifs restaient cantonnés à des graphes Mermaid statiques ou textuels, sans possibilité pour l'architecte ou le développeur d'interagir spatialement avec les couches physiques (Entry, State/Config, Data/Persistence, UI/Views, API/Services).
2. **La dispersion des journaux de développement de session (Dev Logs)** : Les comptes-rendus de session étaient enregistrés dans divers artefacts de mémoire (`SESSION_MEMORY_HEALTH.md`, `evidence/`), sans vue consolidée de l'avancement chronologique et des fichiers clés modifiés facilement consultable par un développeur humain.

L'analyse du projet open-source `nemocake/claude-obsidian-assistant` démontre une solution élégante et pragmatique : un pont sans dépendance reliant l'environnement de code à un coffre Obsidian, combinant détection automatique de projet, analyse de stack, génération de toiles d'architecture `.canvas` stratifiées par couleurs, et tenue rigoureuse de journaux de bord datés.

Cette ADR formalise l'intégration de ces patterns dans l'écosystème mLoop.

---

## 2. Décisions d'Architecture

### 2.1 Diptyque de Grounding & Audit Épistémique

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│             DIPTYQUE DE GROUNDING — CLAUDE OBSIDIAN ASSISTANT                    │
├────────────────────────────────────────┬─────────────────────────────────────────┤
│ WHAT IT ACTUALLY PROVES                │ WHAT IT DOES NOT PROVE                  │
│ • Les fichiers natifs .canvas JSON     │ • Ne remplace pas la gouvernance agile  │
│   fournissent une cartographie         │   rigoureuse (INVEST, SCC, Jira).       │
│   hautement lisible et manipulable.    │ • Dataview nécessite l'exécution du     │
│ • La codification couleur par couche   │   client Obsidian (pas de moteur CLI).  │
│   réduit la charge cognitive.          │ • Le système Johnny Decimal peut être   │
│ • Les dev logs de session datés        │   trop rigide pour des micro-services   │
│   facilitent le passage de témoin.     │   sans hiérarchie dynamique.            │
├────────────────────────────────────────┴─────────────────────────────────────────┤
│ CLAIM BOUNDARIES                                                                 │
│ Valide pour la restitution visuelle de projet, le suivi de dev et l'ergonomie   │
│ de navigation Obsidian. Complète mais ne remplace pas Graphify / CodeGraph.      │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Standardisation de la Toile d'Architecture Codebase 2D (`architecture.canvas`)

Le moteur de toiles mLoop (`src/pipelines/canvas_generator.py`) est enrichi pour supporter la génération de **`docs/01-architecture/architecture.canvas`** en complément de `backlog/story_mapping.canvas` :

1. **Stratification Verticale par Couches Applicatives** :
   Les nœuds de la toile d'architecture sont organisés en bandes horizontales de haut en bas :
   - **Couche 1 : Points d'Entrée & Noyau (Rouge `"1"`)** : CLI, scripts d'amorçage, `main.py`, contrôleurs racine.
   - **Couche 2 : Gestion d'État & Configuration (Orange `"2"`)** : Moteurs d'état, `LoopState`, schémas Pydantic, variables d'environnement.
   - **Couche 3 : Couche API & Services Distants (Cyan/Bleu `"5"`)** : Endpoints REST, serveurs MCP, connecteurs tiers.
   - **Couche 4 : Données, Persistance & Mémoire (Jaune `"3"`)** : Bases SQLite FTS5, VectorStores, fichiers SSOT.
   - **Couche 5 : Vues, Sorties & Interfaces (Vert `"4"`)** : Console ZeroFluff, visualisateurs HTML, toiles Canvas.

2. **Connexions Déterministes des Flux de Données** :
   - Les liens (`edges`) respectent le flux vertical descendant : `fromSide: "bottom"` ➔ `toSide: "top"`.
   - Les appels latéraux ou asynchrones utilisent `fromSide: "right"` ➔ `toSide: "left"`.

---

### 2.3 Matrice Canonique des Couleurs Obsidian Canvas

mLoop unifie sa palette de couleurs Canvas selon la spécification JSON Canvas universelle :

| Code Couleur | Teinte Visuelle | Rôle dans l'Architecture Codebase | Rôle dans le Story Mapping |
| :---: | :---: | :--- | :--- |
| `"0"` | Gris (Neutre) | Notes explicatives, groupes de périmètre | Récits archivés ou neutres |
| `"1"` | 🔴 Rouge | Systèmes critiques, points d'entrée | Récits bloqués (`BLOCKED`, `ON-HOLD`) |
| `"2"` | 🟠 Orange | Gestion d'état, configuration, stores | Récits prêts au toilettage (`READY_FOR_GROOMING`) |
| `"3"` | 🟡 Jaune | Persistance, bases de données, mémoire | Récits en cours d'analyse (`IN_ANALYZE`) |
| `"4"` | 🟢 Vert | UI, sorties utilisateur, succès | Récits prêts au développement (`READY_FOR_DEV`, `SHIPPED`) |
| `"5"` | 🔵 Cyan / Bleu | API, réseau, intégrations externes | Épopées et récits en backlog (`BACKLOG`, `OPEN`) |
| `"6"` | 🟣 Violet | Métadonnées, headers, contrats d'interface | Jalons de sprint, release tags |

---

### 2.4 Registre des Fichiers Clés & Consolidation des Sessions

Pour chaque projet mLoop, le fichier de suivi [`Projects/<projet>/memory/SESSION_MEMORY_HEALTH.md`](file:///c:/Memory%20Loop/Projects/mLoop/memory/SESSION_MEMORY_HEALTH.md) intègre désormais une section **Table des Fichiers Clés** (`Key Files Table`) et un **Journal d'Intervention de Session** (*Dated Dev Log*) inspiré du modèle Claude Obsidian Assistant :
- Chaque clôture de session ou exécution de synchronisation consigne la date, la liste des fichiers impactés, les décisions prises et les prochains jalons.

---

## 3. Conséquences

### Positives
- **Compréhension Visuelle Immédiate** : Visualisation intuitive des interactions de couches dans un fichier `.canvas` natif sans quitter l'IDE ou Obsidian.
- **Continuité Cognitive Décuplée** : Traçabilité claire des modifications de session avec table des composants clés maintenue en continu.
- **Harmonisation SSOT** : Alignement complet des codes couleurs entre Story Mapping et Codebase Architecture.

### Neutres
- Génère un fichier `.canvas` additionnel sous `docs/01-architecture/architecture.canvas` lors de l'exécution de `swarm.py canvas`.

### Négatives / Risques
- Aucun. Les fichiers `.canvas` sont au format JSON standard, sans dépendance externe ni impact sur le runtime de l'application cliente.

---

## 4. Statut d'Alignement & Implémentation

| Composant | Cible | Action Réalisée |
| :--- | :--- | :--- |
| **Générateur Canvas** | `src/pipelines/canvas_generator.py` | Enrichi avec la méthode `generate_architecture_canvas` et la matrice 6 couleurs. |
| **Index SSOT** | `standards/adr-system/README.md` | Indexation de l'ADR-0349 (67 ADRs unifiées). |
| **Recherche Staging** | `Projects/mLoop/reference/research/claude-obsidian-assistant/` | Archivage de la spécification JSON Canvas et de la documentation. |
