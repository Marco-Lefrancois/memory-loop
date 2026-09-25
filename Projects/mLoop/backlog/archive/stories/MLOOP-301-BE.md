---
id: MLOOP-301-BE
jira_key: ""
epic_key: EPIC-30-MULTIMODAL-ARTIFACT-HARNESS
type: Feature
title: "Validation Topologique Anti-Effondrement des Connecteurs Archify (ConnectorIntegrityValidator)"
tags: [core, archify, topology, graph, backend]
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: "2026-09-25"
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# Validation Topologique Anti-Effondrement des Connecteurs Archify (ConnectorIntegrityValidator)

---

## Description
**En tant qu'** Architecte ou Développeur consommant les diagrammes interactifs Archify générés par un agent,  
**je veux** que le moteur de validation d'Archify contrôle rigoureusement que les connecteurs et flux d'échange sont reliés à de véritables nœuds déclaratifs avec des ancres valides et un sens de propagation causal univoque,  
**afin d'** interdire le phénomène de *Connector Collapse* (effondrement des connecteurs) et empêcher qu'un modèle ne maquille un diagramme avec des lignes brisées orphelines ou des relations sans sémantique.

---

## Contexte & Périmètre

### Contexte Métier
L'étude ReFigBench a mis en évidence le phénomène critique de *Connector Collapse* : lors de la refactorisation de diagrammes d'architecture, les agents ont tendance à remplacer les connecteurs natifs de graphes par de simples traits vectoriels non ancrés ou à les omettre totalement, créant un ensemble de boîtes flottantes sans liens formels. Dans mLoop, Archify est l'outil SSOT de cartographie visuelle. Pour que ses diagrammes soient utilisables par les agents avals, le graphe doit être structurellement fermé et formellement valide.

### In-Scope
- Extension du validateur dans `tools/archify/` et `src/commands/handlers/archify_core.py` (≤ 300L, `RULE-AST-01`).
- Implémentation du composant `ConnectorIntegrityValidator`.
- Règle du Graphe Fermé Strict : toute arête (`edge`) dans la spécification JSON IR doit obligatoirement relier un `from` (identifiant de nœud existant) et un `to` (identifiant de nœud existant).
- Rejet immédiat de toute arête orpheline (`CONNECTOR_INTEGRITY_FAIL`).
- Détection d'effondrement relationnel : tout diagramme comportant plus de 3 blocs modulaires mais aucun connecteur relationnel est bloqué avec l'erreur `CONNECTOR_COLLAPSE_DETECTED`.
- Vérification du sens causal univoque (`direction: forward | backward | bidirectional`).

### Out-of-Scope
- Réagencement automatique par algorithme de force layout (les coordonnées spatiales déclarées sont préservées).
- Rendu SVG dans le navigateur (la validation s'opère en amont sur la spécification intermédiaire JSON IR).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Validation Topologique de Connecteurs (`validate_connector_integrity`)
* **Entrée Métier** : Spécification JSON IR du diagramme Archify (`nodes: list[dict]`, `edges: list[dict]`).
* **Règles d'admissibilité & Validation** : La spécification doit contenir un ensemble cohérent de nœuds munis d'identifiants uniques non vides.
* **Traitement & Algorithme Métier** :
  1. Construction du registre des identifiants de nœuds valides.
  2. Parcours de chaque arête pour vérifier que `edge["from"]` et `edge["to"]` appartiennent au registre de nœuds.
  3. Vérification de l'absence d'auto-boucles non déclarées ou de connecteurs sans extrémité définie.
  4. Si le nombre de nœuds est supérieur à 3 et que la liste d'arêtes est vide, émission d'une alerte critique d'effondrement topologique.
* **Résultat Métier & Mutations** : Objet `ConnectorValidationResult(is_valid: bool, errors: list[str], node_count: int, edge_count: int)`.
* **Cas de Rejet Métier** : Rejet bloquant au build avec code `CONNECTOR_INTEGRITY_FAIL` ou `CONNECTOR_COLLAPSE_DETECTED`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- **Validation Topologique CLI** : `python tools/archify/archify_runner.py validate <diagram.json>`.
- **Intégration Python Locale** : `src.commands.handlers.archify_core:validate_diagram_topology`.

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `validate_connector_integrity` | `src.commands.handlers.archify_core:validate_connector_integrity` | Validation topologique anti-effondrement de connecteurs Archify | `(diagram: dict) -> ConnectorValidationResult` |
| `archify_runner validate` | `tools/archify/archify_runner.py validate` | Validation CLI du graphe relationnel de schéma | `(json_path: Path) -> int` |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-301-01** : Ce composant backend opère en local dans le runtime Archify et l'outillage Python (aucune interface HTTP/REST distante exposée). `[API de soumission à définir]` — toute exposition future via micro-service est reportée et à confirmer dans un récit dédié.

- **Admission of Limits & Résilience Système** :
  - **Absence de réseau / Timeout** : Moteur de graphe 100 % local (in-memory / file system), insensible aux coupures réseau et timeouts distants (503/408).
  - **Concurrence & Anti-Rebond** : Protection contre les exécutions concurrentes ou invocations multiples rapides via exécution stateless sans verrou partagé bloquant.
  - **Session & Authentification** : Composant headless sans session utilisateur ni token d'authentification (hors domaine 401/session expirée).
  - **Validation des Entrées Extrêmes** : Tout graphe vide (champ vide), identifiant avec caractère spécial, valeur null ou payload JSON corrompu est intercepté proprement et renvoie `is_valid = Faux` avec code d'erreur explicite.

---

## Règles d'affaires

- **Règle du Graphe Fermé** : Aucune liaison orpheline ne peut exister dans un diagramme Archify certifié ; chaque arête relie strictement deux composants réels.
- **Interdiction du Maquillage Visuel** : L'utilisation de simples lignes géométriques pour simuler un lien sans déclarer l'arête dans le modèle relationnel est formellement interdite.
- **Seuil Anti-Effondrement** : Tout diagramme modulaire (> 3 blocs) sans flux relationnel est considéré comme non fini et ne peut franchir la Gate 2 (DoR).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-301-BE_fact_dossier.md`](../../memory/evidence/MLOOP-301-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **ADR Projet** : [ADR-016 : Harnais de Fidélité Visuelle](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md)
- 📜 **ADR Système** : [ADR-0392 : Standard Topologique des Artefacts](../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md)
- 🔬 **Référence Scientifique** : *ReFigBench: Benchmarking Scientific Figure Reconstruction* (arXiv:2609.18844, Section 5).

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Validation Topologique Anti-Effondrement des Connecteurs Archify (ConnectorIntegrityValidator)

  # CHEMIN NOMINAL (Graphe Fermé & Valide)
  Scénario: Validation d'un diagramme Archify avec topologie complète et fermée
    Étant donné un schéma Archify composé de 4 nœuds déclarés
    Et de 3 arêtes reliant valablement chaque source à sa destination
    Quand le validateur topologique exécute le contrôle d'intégrité
    Alors le résultat indique is_valid = Vrai
    Et aucune erreur de connecteur n'est relevée

  # EXCEPTIONS & REJETS MÉTIER (Connecteur Orphelin)
  Scénario: Rejet d'un connecteur pointant vers un nœud cible inexistant
    Étant donné un schéma Archify comportant une arête dont la cible "node_inconnu" n'existe pas dans le graphe
    Quand le validateur topologique analyse la spécification
    Alors la validation échoue avec le code d'erreur "CONNECTOR_INTEGRITY_FAIL"
    Et le rapport d'erreur identifie l'arête en faute et le nœud manquant

  # RÉSILIENCE TECHNIQUE (Détection de Connector Collapse)
  Scénario: Blocage d'un diagramme à blocs multiples dépourvu de toute arête relationnelle
    Étant donné un schéma d'architecture comportant 5 blocs modulaires distincts
    Mais dont la liste des arêtes relationnelles est vide (Connector Collapse)
    Quand le validateur topologique inspecte le schéma
    Alors le build est interrompu avec l'erreur "CONNECTOR_COLLAPSE_DETECTED"
    Et l'artefact ne peut pas être estampillé conforme

  # UX, OBSERVABILITÉ & LOGS (Rapport d'Audit Détaillé)
  Scénario: Émission du bilan topologique lors du build Archify
    Étant donné la compilation d'un diagramme vers son format interactif
    Quand le contrôle de topologie s'achève avec succès
    Alors un journal récapitulatif affiche le nombre de nœuds, d'arêtes et la complétude topologique (100 %)
```