---
id: MLOOP-350-BE
jira_key: ''
epic_key: EPIC-35-REFIGBENCH-ARTIFACT-HARNESS-V2
type: Enabler
title: Moteur d'Audit Déterministe d'Arbre d'Objets Natifs pour Livrables d'Architecture
tags:
- core
- artifacts
- audit
- object-tree
- svg
- canvas
- backend
status: READY_FOR_GROOMING
grill_me: COMPLETED
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-25'
ttl_cycles: 3
---

# Moteur d'Audit Déterministe d'Arbre d'Objets Natifs pour Livrables d'Architecture

---

## Description
**En tant qu'** Auditeur d'Artefacts Système mLoop (Phase 2 & Phase 4),  
**je veux** disposer d'un analyseur déterministe d'arbre d'objets natifs capable d'extraire et de dénombrer mécaniquement les boîtes texte, formes modulaires, connecteurs relationnels et ratios d'images matricielles des schémas d'architecture (SVG, JSON Canvas, Archify IR),  
**afin de** fournir une cartographie objective de la structure interne des livrables et empêcher le camouflage de diagrammes plats sous forme de dessins libres non manipulables, conformément au protocole d'audit ReFigBench (*arXiv:2609.18844*).

---

## Contexte & Périmètre

### Contexte Métier
Dans l'étude ReFigBench, l'audit de l'arbre d'objets natifs ($O(P)$) constitue le rempart fondamental empêchant qu'une simple capture d'écran ou un ensemble de traits de dessin statiques ne soient validés comme un document d'architecture exploitable. Les agents multimodaux ont une propension démontrée à provoquer l'effondrement de connecteurs (*Connector Collapse* : 91% à 100% de perte des connecteurs natifs) en remplaçant les connecteurs vivants par de simples lignes sans ancrage. Pour mLoop, qui fournit des architectures de référence destinées au Dev Handoff, ce moteur fournit la télémétrie structurelle exacte de chaque artefact avant notation 5-axes.

### In-Scope
- Implémentation du module `src/pipelines/object_tree_auditor.py` (strictement $\le 300$L, `RULE-AST-01`, `ADR-0202`).
- Moteur d'extraction déterministe `audit_native_object_tree(file_path: Path) -> NativeObjectTreeSummary`.
- Support des trois formats souverains de livrables d'architecture de mLoop :
  - **SVG Sémantique** (`.svg`) : dénombrement des balises `<text>` / `<tspan>`, formes vectorielles (`<rect>`, `<circle>`, `<ellipse>`, `<polygon>`, `<path>`), conteneurs hiérarchiques (`<g>`) et détection hybride des connecteurs (attributs sémantiques `data-edge-from`/`data-edge-to` OU balises `<path>`/`<line>` avec marqueurs `marker-end`/`marker-start` reliant deux nœuds identifiés).
  - **Archify JSON IR** (`.json` avec clés `components` ou `connections`) : dénombrement des composants, connexions relationnelles (`from` et `to` résolus) et frontières de groupement (`boundaries`).
  - **JSON Canvas (`.canvas`)** : comptage des cartes texte, fichiers, formes et arêtes connectées (`fromNode` / `toNode`).
- Calcul surfacique de l'emprise des balises matricielles `<image>` rapportée au `viewBox` total (`raster_ratio`).
- Restitution des métriques brutes scellées : `text_count`, `shape_count`, `connector_count`, `group_count`, `raster_ratio`, `is_valid`, `error_code`, `sha256`.
- Contrat d'audit résilient sans interruption de pipeline batch : en cas de document corrompu ou format non supporté, retour systématique d'un `NativeObjectTreeSummary` avec `is_valid=False` et code d'erreur explicite.

### Out-of-Scope
- Rendu visuel bitmap ou conversion de format graphique.
- Évaluation qualitative de l'esthétique ou calcul des 5 axes ReFigBench complets (couvert par `MLOOP-351-BE`).
- Analyse de l'orientation causale des dépendances AST vs diagramme (couvert par `MLOOP-352-BE`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Audit Déterministe d'Arbre d'Objets (`audit_native_object_tree`)
* **Entrée Métier** : Chemin de fichier (`file_path: Path`) d'un artefact d'architecture existant.
* **Règles d'admissibilité & Validation** :
  - Le fichier doit exister, être accessible en lecture et posséder une extension supportée (`.svg`, `.json`, `.canvas`).
  - Si l'extension n'est pas reconnue, retourner immédiatement `NativeObjectTreeSummary` avec `is_valid=False` et `error_code="UNSUPPORTED_ARTIFACT_FORMAT"`.
* **Traitement & Algorithme Métier** :
  1. Calcul de l'empreinte SHA-256 du fichier analysé.
  2. Parsing syntaxique sécurisé sans exécution de code arbitraire (protection contre l'expansion d'entités XML).
  3. Dénombrement et classification déterministe des primitives selon le format :
     - Pour SVG : parcours récursif, comptage des `<text>`, formes primitives, groupes `<g>`, détection hybride des connecteurs ancrés.
     - Pour Archify IR : inspection du dictionnaire JSON (`components`, `connections`, `boundaries`).
     - Pour JSON Canvas : inspection des listes `nodes` et `edges`.
  4. Calcul du `raster_ratio` : surface géométrique cumulée des balises `<image>` divisée par la surface totale du viewBox.
  5. Détection de non-éditabilité : flagger l'artefact si `text_count == 0` ou `connector_count == 0` alors que `shape_count >= 2`.
* **Résultat Métier & Mutations** : Objet immuable `NativeObjectTreeSummary` scellé par l'empreinte SHA-256.
* **Cas de Rejet & Résilience** : En cas d'erreur de parsing XML (`ParseError`) ou JSON corrompu (`JSONDecodeError`), retourner `is_valid=False` avec `error_code="CORRUPT_DOCUMENT_STRUCTURE"` sans faire échouer l'application appelante.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.object_tree_auditor:audit_native_object_tree(file_path: Path) -> NativeObjectTreeSummary`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `audit_native_object_tree` | `src.pipelines.object_tree_auditor:audit_native_object_tree` | Audit déterministe d'objets natifs | `(file_path: Path) -> NativeObjectTreeSummary` |

#### Spécification de la Structure de Données SSOT
```python
@dataclass(frozen=True)
class NativeObjectTreeSummary:
    file_path: str
    format: str  # "svg", "archify_ir", "json_canvas", "unknown"
    text_count: int
    shape_count: int
    connector_count: int
    group_count: int
    raster_ratio: float
    is_valid: bool
    error_code: Optional[str] = None
    sha256: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
```

- **Admission of Limits & Résilience Système** :
  - **Fichiers Corrompus** : Interception gracieuse de toute anomalie syntaxique avec levée de `CORRUPT_DOCUMENT_STRUCTURE`.
  - **Complexité Algorithmique** : Parcours itératif linéaire en temps $\mathcal{O}(N)$ où $N$ est le nombre d'éléments du document, temps de traitement garanti $< 50\text{ms}$ par fichier typique.

---

## Règles d'affaires

- **Dénombrement Déterministe des Connecteurs (Arbitrage Micro-Grill Q1)** : Seuls les connecteurs explicitement rattachés à deux nœuds valides (attributs sémantiques ou marqueurs reliant deux cibles) sont comptabilisés dans `connector_count` ; les segments flottants ou décoratifs sont reversés dans `shape_count`.
- **Calcul Surfacique de Charge Matricielle (Arbitrage Micro-Grill Q2)** : Le `raster_ratio` est le ratio géométrique de surface des balises `<image>` sur la surface totale (`viewBox`). Tout ratio $> 0.05$ (5%) consigne une alerte de non-éditabilité pour le plafonnement ReFigBench $c(P) \le 50$.
- **Résilience Non-Bloquante de Pipeline (Arbitrage Micro-Grill Q3)** : Zéro exception non-gérée. En cas d'erreur de parsing ou format inconnu, le contrat retourne un résumé scellé avec `is_valid=False` et `error_code` documenté.
- **Plafond Strict de Modularité (ADR-0202)** : Le fichier source `src/pipelines/object_tree_auditor.py` doit strictement respecter la limite de $\le 300$ lignes.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Dédié** : [`memory/evidence/MLOOP-350-BE_fact_dossier.md`](../../memory/evidence/MLOOP-350-BE_fact_dossier.md)
- 📄 **Publication de Référence** : ReFigBench (*arXiv:2609.18844*, Section 3 : *Evaluating Fidelity and Editability*, Table 15 & Figure 6).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Spécifications Archify** : [`tools/archify/README.md`](../../tools/archify/README.md)
- 📜 **ADR Associé** : [ADR-0396](../../standards/adr-system/0396-audit-artefacts-5-axes-et-anti-inversion-causale-refigbench.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Moteur d'Audit Déterministe d'Arbre d'Objets Natifs

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Audit d'un diagramme Archify IR comportant nœuds, connecteurs et frontières
    Étant donné un fichier Archify JSON contenant 5 nœuds, 4 arêtes et 1 groupe
    Quand l'auditeur d'arbre d'objets analyse le fichier
    Alors le résumé indique "shape_count = 5", "connector_count = 4" et "group_count = 1"
    Et le "raster_ratio" est strictement égal à 0.0
    Et le statut "is_valid" est Vrai avec un SHA-256 scellé

  # CHEMIN NOMINAL SVG AVEC CONNECTEURS ET TEXTES
  Scénario: Audit d'un schéma vectoriel SVG avec connecteurs hybrides et textes
    Étant donné un fichier SVG comportant 3 balises texte, 2 rectangles et 1 connecteur sémantique "data-edge-from"
    Quand l'auditeur d'arbre d'objets analyse le fichier SVG
    Alors le résumé indique "text_count = 3", "shape_count = 2" et "connector_count = 1"
    Et le statut "is_valid" est Vrai

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rejet gracieux lors de l'analyse d'un format de fichier non supporté
    Étant donné un fichier portant l'extension ".bin" ou ".pdf"
    Quand l'auditeur tente d'analyser le fichier
    Alors le résumé renvoie "is_valid = Faux" avec "error_code = 'UNSUPPORTED_ARTIFACT_FORMAT'"
    Et aucun crash n'interrompt le pipeline

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Traitement résilient d'un document SVG syntaxiquement tronqué ou corrompu
    Étant donné un fichier SVG dont la balise de fermeture est manquante
    Quand l'audit est exécuté
    Alors le système intercepte l'erreur XML sans planter
    Et le résumé signale "is_valid = Faux" avec "error_code = 'CORRUPT_DOCUMENT_STRUCTURE'"
    Et le SHA-256 du fichier tronqué est calculé

  # UX, OBSERVABILITÉ & DÉTECTION RASTER
  Scénario: Détection d'un diagramme camouflé contenant une image matricielle
    Étant donné un fichier SVG comportant une balise "<image>" couvrant plus de 5% du viewBox
    Quand l'auditeur inspecte le document
    Alors le "raster_ratio" calculé est supérieur à 0.05
    Et le résumé consigne une alerte d'éditabilité dans les métadonnées
```

---

## Definition of Ready (DoR) Checklist

- [x] **1. Description & Périmètre** : Clairs, contextualisés par ReFigBench et délimités aux 3 formats cibles (SVG, Archify IR, JSON Canvas).
- [x] **2. Critères d'Acceptation** : Spécifications fonctionnelles déterministes, gestion des connecteurs et charge matricielle.
- [x] **3. Contrats d'Échange API & Données** : Signature `audit_native_object_tree` et classe immuable `NativeObjectTreeSummary` définies.
- [x] **4. Dépendances & Impacts** : Dépendances nulles en amont, alimentation de `MLOOP-351-BE` et `MLOOP-352-BE` en aval.
- [x] **5. Dossier de Preuves Sourcé** : Preuves factuelles établies dans `memory/evidence/MLOOP-350-BE_fact_dossier.md`.
- [x] **6. Validation Micro-Grill PO** : Les 3 arbitrages techniques (connecteurs hybrides, ratio surfacique, contrat sans crash) sont intégrés.
