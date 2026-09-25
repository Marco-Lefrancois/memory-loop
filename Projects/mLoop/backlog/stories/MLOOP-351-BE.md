---
id: MLOOP-351-BE
jira_key: ''
epic_key: EPIC-35-REFIGBENCH-ARTIFACT-HARNESS-V2
type: Feature
title: Grille d'Audit Découplée 5-Axes Pénétrante (T20 + S30 + L15 + E25 + V10)
tags:
- core
- audit
- scoring
- rubric
- refigbench
- backend
status: READY_FOR_QA
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-350-BE
created_at: '2026-09-25'
validated_by: Marco
validated_at: '2026-09-25T16:53:50Z'
dossier_ref: memory/evidence/MLOOP-351-BE_fact_dossier.md
ttl_cycles: 2
---

# Grille d'Audit Découplée 5-Axes Pénétrante (T20 + S30 + L15 + E25 + V10)

---

## Description
**En tant qu'** Responsable Qualité Architecture ou Moteur d'Audit mLoop (Phase 2 & Phase 4),  
**je veux** remplacer la formule d'évaluation à 2 variables par la grille d'audit standardisée à 5 axes issue de ReFigBench ($T_{20} + S_{30} + L_{15} + E_{25} + V_{10}$), intégrant une sanction éliminatoire sur la structure sémantique ($S < 15$) et le plafonnement anti-collage $c(P)$,  
**afin d'** obtenir un diagnostic chiffré pénétrant séparant formellement l'intégrité topologique, l'éditabilité et le rendu cosmétique des schémas d'architecture.

---

## Contexte & Périmètre

### Contexte Métier
L'ADR-0392 a introduit dans `src/pipelines/audit_decoupler.py` une première formule multiplicative $\text{Score} = S_{\text{topo}} \times (0.7 + 0.3 \times S_{\text{visuel}})$. L'étude ReFigBench (*arXiv:2609.18844*) apporte le standard de référence industriel complet articulé autour de 5 composantes pondérées sur 100 points :
- $T$ (Exactitude Textuelle - 20 pts) : conformité des libellés avec le lexique officiel du projet.
- $S$ (Structure Sémantique - 30 pts) : modules, hiérarchie et graphe des relations dirigées.
- $L$ (Fidélité de Disposition - 15 pts) : topologie spatiale et ordre de lecture.
- $E$ (Éditabilité Native - 25 pts) : richesse de l'arbre d'objets et connecteurs vivants.
- $V$ (Détails Visuels - 10 pts) : alignements, typographie et palette graphique.

### In-Scope
- Refonte et extension de `src/pipelines/audit_decoupler.py` (strictement $\le 300$L, `RULE-AST-01`, `ADR-0202`).
- Moteur de calcul `calculate_refigbench_5axis_score(text_score, semantic_score, layout_score, editability_score, visual_score, raster_ratio=0.0, gate_passed=True, causal_inversion=False) -> FiveAxisAuditResult`.
- Validation stricte des bornes natives : $T \in [0, 20]$, $S \in [0, 30]$, $L \in [0, 15]$, $E \in [0, 25]$, $V \in [0, 10]$ (avec levée de `ScoreOutOfBoundsError` si violation).
- Formule composite ReFigBench : $Q = T + S + L + E + V$ (total sur 100).
- Plafond anti-collage déterministe ReFigBench $c(P)$ :
  - Si `raster_ratio >= 0.85` (ou $> 0.05$ avec déficit d'objets natifs) : $c(P) = 50$, sinon $100$.
- Formule finale : $s(P) = g(P) \times \min(Q, c(P))$, où $g(P)=0$ si porte échouée ou inversion causale ($S=0, s=0$).
- Sanction éliminatoire sémantique : si $S < 15/30$, marquage `SEMANTIC_STRUCTURE_DEFICIT`, disqualification et plafonnement à $\le 49/100$.
- Critères cumulatifs de certification Gate 2 et Gate 4 : $s(P) \ge 85/100$ ET $S \ge 22/30$.
- Rétrocompatibilité totale avec `calculate_decoupled_architecture_score` pour les tests amont.

### Out-of-Scope
- Détection fine matricielle de l'inversion causale de flux (déléguée au linter matriciel `MLOOP-352-BE`).
- Extraction directe des objets depuis les fichiers graphiques (assurée en amont par `MLOOP-350-BE`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Calcul du Score Découplé 5-Axes
* **Entrée Métier** : Les 5 sous-scores ($T, S, L, E, V$), le ratio d'emprise matricielle (`raster_ratio`), l'état de la porte déterministe (`gate_passed: bool`) et l'indicateur d'inversion causale (`causal_inversion: bool`).
* **Règles d'admissibilité & Validation** : Chaque sous-score doit être numérique et borné dans son intervalle respectif.
* **Traitement & Algorithme Métier** :
  1. Validation des bornes avec `ScoreOutOfBoundsError` en cas d'anomalie.
  2. Traitement d'inversion causale : si `causal_inversion=True`, forcer $S = 0.0$, $s(P) = 0.0$ et consigner `CAUSAL_FLOW_INVERSION_DETECTED`.
  3. Traitement de la porte binaire : si `gate_passed=False`, forcer $s(P) = 0.0$.
  4. Calcul de la somme brute $Q = T + S + L + E + V$.
  5. Application de la barrière sémantique : si $S < 15$, consigner `SEMANTIC_STRUCTURE_DEFICIT` et borner le score à $\min(Q, 49.0)$.
  6. Application du plafond anti-collage : si `raster_ratio >= 0.85`, consigner `ANTI_RASTER_CAP_ACTIVE` et appliquer $c(P) = 50.0$.
  7. Évaluation de la certification DoR/DoD : `is_certified = (s(P) >= 85.0 and S >= 22.0 and not penalties)`.
* **Résultat Métier & Mutations** : Objet immuable `FiveAxisAuditResult` exposant `total_score` (sur 100), `normalized_score` (sur 1.0), `is_certified`, `subscores` et `penalties`.
* **Cas de Rejet Métier** : Rejet si $s(P) < 85$ ou $S < 22$ avec motif documenté.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.audit_decoupler:calculate_refigbench_5axis_score(...) -> FiveAxisAuditResult`
- `src.pipelines.audit_decoupler:calculate_decoupled_architecture_score(...) -> AuditScoreResult` *(rétrocompatibilité)*

| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `calculate_refigbench_5axis_score` | `src.pipelines.audit_decoupler:calculate_refigbench_5axis_score` | Évaluation standardisée 5-axes sur 100 | `(t, s, l, e, v, raster_ratio, gate_passed, causal_inversion) -> FiveAxisAuditResult` |
| `calculate_decoupled_architecture_score` | `src.pipelines.audit_decoupler:calculate_decoupled_architecture_score` | Évaluation historique 2-variables (ADR-0392) | `(topology_score, visual_score, causal_inversion, anomalies) -> AuditScoreResult` |

### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `calculate_refigbench_5axis_score` | `src.pipelines.audit_decoupler:calculate_refigbench_5axis_score` | Évaluation standardisée 5-axes sur 100 | `(t, s, l, e, v, raster_ratio, gate_passed, causal_inversion) -> FiveAxisAuditResult` |
| `calculate_decoupled_architecture_score` | `src.pipelines.audit_decoupler:calculate_decoupled_architecture_score` | Évaluation historique 2-variables (ADR-0392) | `(topology_score, visual_score, causal_inversion, anomalies) -> AuditScoreResult` |

> OQ-351-1 : Ce récit définit des fonctions Python internes (module `src.pipelines.audit_decoupler`), pas des endpoints HTTP/REST. La "Route / Point d'Entrée" référence le chemin de module Python qualifié (`module:function`), conforme au standard Zéro Fausse Route (ADR-0319) pour les APIs internes. **[API de soumission à définir]** — Aucune route HTTP/REST n'est exposée par ce module.

## Règles d'affaires

- **Souveraineté de la Sémantique (Arbitrage Micro-Grill Q2)** : Aucune perfection esthétique ($T=20, L=15, E=25, V=10$, soit 70 points) ne peut compenser un effondrement structurel ($S < 15$). Le score est alors bridé à $\le 49/100$ avec `SEMANTIC_STRUCTURE_DEFICIT`.
- **Plafonnement Strict Anti-Collage (Arbitrage Micro-Grill Q3)** : Tout schéma dont la surface matricielle dépasse 85% voit son score plafonné mécaniquement à 50/100 via $c(P)=50$.
- **Normalisation Hybride (Arbitrage Micro-Grill Q1)** : Le moteur expose conjointement la note brute ReFigBench sur 100 (`total_score`) et le ratio normalisé $[0.0, 1.0]$ (`normalized_score`).
- **Modularité Étroite (ADR-0202)** : Le fichier source `src/pipelines/audit_decoupler.py` doit strictement respecter la limite de $\le 300$ lignes.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-351-BE_fact_dossier.md`](../../memory/evidence/MLOOP-351-BE_fact_dossier.md)
- 📄 **Publication de Référence** : ReFigBench (*arXiv:2609.18844*, Section 3 : *Evaluating Fidelity and Editability*, Équations $Q(P, x)$ et $s(P, x)$).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Architecture Normative** : [`standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md`](../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md)
- 📜 **ADR Associé** : [ADR-0396](../../standards/adr-system/0396-audit-artefacts-5-axes-et-anti-inversion-causale-refigbench.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Grille d'Audit Découplée 5-Axes Pénétrante

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Certification d'un schéma d'architecture atteignant l'excellence sur les 5 axes
    Étant donné un artefact ayant T=18, S=28, L=14, E=23, V=9
    Et un ratio matriciel de 0% avec la porte binaire g(P) validée
    Quand le calcul de la grille 5-axes est appliqué
    Alors la note globale est de 92/100 et le score normalisé est de 0.92
    Et le livrable est certifié conforme avec "is_certified = Vrai"

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Échec éliminatoire pour déficit sémantique malgré un rendu très soigné
    Étant donné un schéma très soigné ayant T=20, L=15, E=25, V=10 mais S=10 sur 30
    Quand la grille d'audit calcule le résultat
    Alors la note est sanctionnée par "SEMANTIC_STRUCTURE_DEFICIT" et plafonnée à 49/100
    Et le livrable est rejeté avec "is_certified = Faux" malgré une somme brute de 80 points

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Application du plafond déterministe de 50 points sur un collage raster
    Étant donné un livrable où une image bitmap couvre 88% de la surface
    Même si la somme brute théorique est de 75 points
    Quand le contrôle anti-aplatissement est exécuté
    Alors le score final est plafonné à exactement 50/100 avec "ANTI_RASTER_CAP_ACTIVE"

  # INVERSION CAUSALE RADICALE
  Scénario: Disqualification absolue immédiate sur inversion causale de dépendances
    Étant donné un schéma comportant une inversion causale signalée
    Quand la grille 5-axes est évaluée
    Alors le sous-score S est forcé à 0 et le score global est strictement égal à 0.0
    Et la pénalité "CAUSAL_FLOW_INVERSION_DETECTED" est consignée
```

---

## Definition of Ready (DoR) Checklist

- [x] **1. Description & Périmètre** : Clairs, contextualisés par ReFigBench et formulés autour de la grille 5-axes ($T_{20} + S_{30} + L_{15} + E_{25} + V_{10}$).
- [x] **2. Critères d'Acceptation** : Spécifications mathématiques déterministes, seuils d'admissibilité et gestion des barrières.
- [x] **3. Contrats d'Échange API & Données** : Signature `calculate_refigbench_5axis_score` et classe immuable `FiveAxisAuditResult` définies.
- [x] **4. Dépendances & Impacts** : Dépend de `MLOOP-350-BE` (opérationnel) et s'articule avec `MLOOP-352-BE`.
- [x] **5. Dossier de Preuves Sourcé** : Preuves factuelles établies dans `memory/evidence/MLOOP-351-BE_fact_dossier.md`.
- [x] **6. Validation Micro-Grill PO** : 3 arbitrages techniques (échelles natives + normalisées, seuil sémantique $S < 15$, formule ReFigBench) intégrés.
