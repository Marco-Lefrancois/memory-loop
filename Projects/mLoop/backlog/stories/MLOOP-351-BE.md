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
status: DRAFT
grill_me: PENDING
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-350-BE
created_at: '2026-09-25'
ttl_cycles: 3
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
L'ADR-0392 a introduit dans `src/pipelines/audit_decoupler.py` une première formule multiplicative $\text{Score} = S_{\text{topo}} \times (0.7 + 0.3 \times S_{\text{visuel}})$. L'étude ReFigBench apporte le standard de référence industriel complet articulé autour de 5 composantes pondérées sur 100 points :
- $T$ (Exactitude Textuelle - 20 pts) : conformité des libellés avec le lexique officiel du projet.
- $S$ (Structure Sémantique - 30 pts) : modules, hiérarchie et graphe des relations dirigées.
- $L$ (Fidélité de Disposition - 15 pts) : topologie spatiale et ordre de lecture.
- $E$ (Éditabilité Native - 25 pts) : richesse de l'arbre d'objets et connecteurs vivants.
- $V$ (Détails Visuels - 10 pts) : alignements, typographie et palette graphique.

### In-Scope
- Refonte de `src/pipelines/audit_decoupler.py` (strictement $\le 300$L, `RULE-AST-01`).
- Moteur de calcul `calculate_refigbench_5axis_score(text_score, semantic_score, layout_score, editability_score, visual_score, raster_ratio) -> FiveAxisAuditResult`.
- Normalisation des sous-scores aux bornes strictes de chaque dimension.
- Formule composite : $Q = T + S + L + E + V$ (total sur 100).
- Application du plafond déterministe ReFigBench $c(P)$ :
  $$c(P) = \begin{cases} 50 & \text{si raster\_ratio} \ge 0.85 \text{ avec peu d'objets natifs} \\ 100 & \text{sinon} \end{cases}$$
- Score final : $s(P) = g(P) \times \min(Q, c(P))$.
- Sanction éliminatoire : si $S < 15/30$, l'artefact est immédiatement déclaré non certifié (`SEMANTIC_STRUCTURE_DEFICIT`).
- Seuil d'approbation Gate 2 et Gate 4 : $s(P) \ge 85/100$ et $S \ge 22/30$.

### Out-of-Scope
- Détection fine de l'inversion causale de flux (déléguée au linter matriciel MLOOP-352-BE).
- Génération automatique des annotations humaines Elo.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Calcul du Score Découplé 5-Axes (`calculate_refigbench_5axis_score`)
* **Entrée Métier** : Les 5 notes partielles ($T \in [0, 20]$, $S \in [0, 30]$, $L \in [0, 15]$, $E \in [0, 25]$, $V \in [0, 10]$), métriques d'objets natifs.
* **Règles d'admissibilité & Validation** : Chaque sous-score doit être numérique et respecter l'intervalle défini de son axe.
* **Traitement & Algorithme Métier** :
  1. Sommation brute des 5 dimensions $Q = T + S + L + E + V$.
  2. Contrôle de la barrière sémantique : si $S < 15$, marquage éliminatoire `SEMANTIC_STRUCTURE_DEFICIT`.
  3. Évaluation du ratio raster : si $\ge 0.85$, plafonnement de la note globale à 50.
  4. Détermination du statut de certification DoR/DoD ($s \ge 85$ et $S \ge 22$).
* **Résultat Métier & Mutations** : Objet `FiveAxisAuditResult(total_score: float, is_certified: bool, subscores: dict, penalties: list[str])`.
* **Cas de Rejet Métier** : Refus d'approbation si la note totale est $< 85$ ou si le sous-score sémantique est défaillant.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.audit_decoupler:calculate_refigbench_5axis_score(...) -> FiveAxisAuditResult`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `calculate_refigbench_5axis_score` | `src.pipelines.audit_decoupler:calculate_refigbench_5axis_score` | Évaluation standardisée 5-axes sur 100 | `(scores: dict, gate: bool) -> FiveAxisAuditResult` |

---

## Règles d'affaires

- **Souveraineté de la Sémantique** : Aucune perfection esthétique ($T=20, L=15, E=25, V=10$, soit 70 points) ne peut compenser un effondrement structurel ($S < 15$).
- **Plafonnement Strict Anti-Collage** : Tout schéma dont la surface matricielle dépasse 85% voit son score plafonné mécaniquement à 50/100, interdisant toute promotion en phase aval.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves** : [`memory/evidence/EPIC-35_refigbench_fact_dossier.md`](../../memory/evidence/EPIC-35_refigbench_fact_dossier.md)
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
    Alors la note globale est de 92/100
    Et le livrable est certifié conforme avec "is_certified = Vrai"

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Échec éliminatoire pour déficit sémantique malgré un rendu très soigné
    Étant donné un schéma très joli ayant T=20, L=15, E=25, V=10 mais S=10 sur 30
    Quand la grille d'audit calcule le résultat
    Alors la note est sanctionnée par "SEMANTIC_STRUCTURE_DEFICIT"
    Et le livrable est rejeté avec "is_certified = Faux" malgré une somme brute élevée

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Application du plafond déterministe de 50 points sur un collage raster
    Étant donné un livrable où une image bitmap couvre 88% de la surface
    Même si la somme brute théorique est de 75 points
    Quand le contrôle anti-aplatissement est exécuté
    Alors le score final est plafonné à exactement 50/100

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Restitution détaillée du diagramme en radar des 5 dimensions
    Étant donné une évaluation finalisée
    Quand le rapport d'audit est formaté
    Alors les 5 composantes T, S, L, E, V sont explicitement présentées avec leur seuil cible
```
