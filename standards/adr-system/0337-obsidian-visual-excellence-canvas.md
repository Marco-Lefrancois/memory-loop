# ADR-0337 : Standard Visuel Obsidian, Callouts & Canvas 2D

## Statut
**Accepté (SSOT Normatif)** — 25 août 2026

## Contexte & Problématique
Dans l'écosystème Memory Loop (mLoop), les fichiers Markdown constituent l'interface de travail et de transmission principale entre l'équipe d'architecture IA, le Product Owner, et l'équipe de développement.
Dans un visualiseur Markdown moderne tel qu'**Obsidian**, le texte brut traditionnel souffre de plusieurs limites :
1. **L'encombrement cognitif (*Wall of Text*)** : Les métadonnées d'audit, traces d'EvidencePacks et contrats d'API massifs noient les informations exécutives prioritaires (statut, valeur métier, critères d'acceptation).
2. **La fragilité des diagrammes Mermaid** : Les erreurs de parsing récurrentes (conflit de listes ordonnées `[1. Action]`, sous-graphes avec espaces, caractères non échappés) provoquent des écrans d'erreur `Parse error: Unsupported markdown: list`.
3. **Le manque de vue spatiale 2D** : La planification de backlog et le Story Mapping sous forme de longues tables Markdown linéaires rendent difficile la perception immédiate des dépendances et de l'ordonnancement séquentiel.

L'étude du projet de référence **Obsidian Visual Skills Pack** (`axtonliu/axton-obsidian-visual-skills`) apporte des solutions éprouvées : standardisation des Callouts natifs et repliables, grammaire Mermaid blindée contre les erreurs de parsing, et génération automatisée de toiles spatiales interactives **Obsidian JSON Canvas** (`.canvas`).

---

## Décision d'Architecture

### 1. Système de Callouts & Composants Markdown UI Normalisés
Tous les documents Markdown mLoop (Stories, ADRs, Backlogs, PRDs) adoptent le système de Callouts natifs Obsidian :

| Callout Obsidian | Sémantique & Rôle dans mLoop | Comportement |
|---|---|---|
| `> [!ABSTRACT]` / `> [!SUMMARY]` | **Bandeau Exécutif** en tête de document (synthèse 3 points, statut, valeur). | Déplié par défaut |
| `> [!NOTE]` | **Contexte Métier & Règles Fonctionnelles** générales. | Déplié par défaut |
| `> [!TIP]` | **Accélérateurs Développeur & Bonnes Pratiques**. | Déplié par défaut |
| `> [!IMPORTANT]` | **Exigence Non Négociable** (sécurité, conformité, invariant légal). | Déplié par défaut |
| `> [!WARNING]` / `> [!CAUTION]` | **Vigilance Technique & Angles Morts** (risques de régression, cas de bord). | Déplié par défaut |
| `> [!QUESTION]` | **Questions Ouvertes `OQ-XXX`** en attente d'arbitrage du PO. | Déplié par défaut |
| `> [!EXAMPLE]` | **Exemples de Payloads & Scénarios Nominaux**. | Déplié par défaut |
| `> [!NOTE]- Titre` | **Callouts Repliables (*Foldable*)** pour les zones denses : `Notes de Traçabilité & EvidencePack`, logs de fact-search, payloads d'erreur 4xx/5xx. | **Replié par défaut (`-`)** pour aérer la lecture |

---

### 2. Moteur Mermaid Stylisé & Règles de Prévention d'Erreurs (`visual-mermaid`)
Chaque diagramme Mermaid généré par mLoop applique obligatoirement les 3 règles de robustesse :
1. **Règle Anti-Collision de Liste Ordonnée** :
   - ❌ Interdit : `[1. Étape]` (provoque un conflit avec le parser de liste Markdown).
   - ✅ Obligatoire : `[① Étape]`, `[1.Étape]` ou `[Étape 1 - Titre]`.
2. **Règle de Nommage des Sous-Graphes** :
   - ❌ Interdit : `subgraph Couche API` (espace sans ID).
   - ✅ Obligatoire : `subgraph api["🌐 Couche API"]` avec liaison par ID (`A --> api`).
3. **Règle d'Échappement Systématique** :
   - Encadrer systématiquement les libellés comportant parenthèses, crochets ou ponctuations avec des guillemets : `node["Action (Détail)"]`.

---

### 3. Schémas Vectoriels Excalidraw Éditables (`visual-excalidraw`)
- Pour les architectures globales, les wireframes d'écrans et les topologies de flux, mLoop supporte la génération de schémas au format **Obsidian Excalidraw** (`.excalidraw.md`) ou `.excalidraw` sous `docs/05-assets/`.
- Ces schémas offrent un rendu visuel à main levée (*hand-drawn*) et demeurent **100% modifiables et interactifs directement dans Obsidian**.

---

### 4. Toiles Spatiales 2D Obsidian Canvas (`.canvas`)
mLoop intègre un générateur natif de fichiers `.canvas` (`src/pipelines/canvas_generator.py`) accessible via la commande CLI :
```bash
python src/swarm.py canvas --project <nom_projet>
```
Ce générateur produit automatiquement :
1. **`backlog/story_mapping.canvas`** : Carte spatiale 2D avec colonnes d'épopées, cartes d'acteurs et post-its colorés selon le statut (`READY_FOR_DEV` en vert, `IN_ANALYZE` en bleu, `ON-HOLD` en rouge).
2. **`backlog/sprint_dag.canvas`** : Graphe DAG de sprint montrant les flux d'ordonnancement séquentiel, les dépendances critiques et les goulets d'étranglement (ToC).
3. **Algorithme de Positionnement Déterministe** : Calcul des coordonnées $(x, y, w, h)$ avec marges de sécurité ($320\text{px}$ en horizontal, $200\text{px}$ en vertical) évitant tout chevauchement.

---

## Impacts sur les Blueprints & Standards

1. **`standards/blueprints/story_template.md`** :
   - Bandeau exécutif `> [!ABSTRACT]` en tête de document.
   - Section de traçabilité et hashs SHA-256 repliée par défaut dans `> [!NOTE]- 📑 Notes de Traçabilité & Preuves Fact-Search`.
   - Tableaux CTA et Contrats API avec feedback visuel et badges d'état.
2. **`standards/blueprints/sprint_backlog_template.md`** :
   - Intégration de jauges d'avancement textuelles (`[████████░░] 80%`) et lien bidirectionnel vers `sprint_dag.canvas`.
3. **`standards/blueprints/story_mapping_template.md`** :
   - Vue 360° reliant la table de synthèse et la toile interactive `story_mapping.canvas`.

---

## Conséquences & Bénéfices

- **Expérience Exécutive Haut de Gamme** : Lecture fluide, hiérarchie visuelle claire et suppression du bruit technique inutile en première lecture.
- **Zéro Échec de Rendu Mermaid** : Élimination totale des erreurs de parsing de diagrammes sur Obsidian et GitHub.
- **Vue Panoramique Intuitive** : L'équipe produit et les développeurs peuvent visualiser et naviguer spatialement dans le backlog et les dépendances grâce à Obsidian Canvas.
