# Dossier de Preuves — EPIC-35-REFIGBENCH-ARTIFACT-HARNESS-V2

**Statut** : CURRENT  
**Date** : 2026-09-25  
**Récits couverts** : MLOOP-350-BE à MLOOP-354-FULL  
**Base légale** : ADR-0396 (Audit Artefacts 5 Axes & Anti-Inversion Causale RefigBench), ADR-0392, ADR-0369  
**Publication de référence** : ReFigBench (*arXiv:2609.18844*) — *Evaluating Fidelity and Editability of Diagrammatic Artifacts*  

---

## 1. Sources primaires
| Source | Emplacement | Usage |
|:---|:---|:---|
| Papier ReFigBench | arXiv:2609.18844 | Section 3 : Équations $Q(P, x)$ et $s(P, x)$, 5 axes d'évaluation |
| ADR-0396 | `standards/adr-system/0396-audit-artefacts-5-axes-et-anti-inversion-causale-refigbench.md` | Spécification SSOT de l'audit 5 axes |
| ADR-0392 | `standards/adr-system/0392-fidelite-visuelle-artefacts-multimodaux.md` | Règle d'intégrité topologique et vectorielle |

---

## 2. Extraits verbatim sourcés

**Extrait 1 — ADR-0396 (§2)** : « L'audit déterministe d'arbre d'objets doit vérifier l'absence d'effondrement relationnel (connecteurs orphelins, boîtes disjointes) sur l'ensemble des livrables graphiques. » ➔ **Fait établi** : Vérification des connecteurs et formes modulaires.

**Extrait 2 — ReFigBench arXiv:2609.18844 (§3)** : « Structural fidelity encompasses element count, topology adjacency, and text-bounding box alignments, preventing hallucinated visual representations. » ➔ **Fait établi** : 5 axes métriques pour la certification d'artefacts.

**Extrait 3 — ADR-0369** : « Zéro dépendance de rendu graphique externe (headless safe). » ➔ **Fait établi** : Parsing AST vectoriel et JSON pur.

---

## 3. Contrats déclaratifs cibles
- Extension de `artifact_check.py` pour supporter les 5 axes ReFigBench.
- Validation des formats SVG, JSON Canvas et Archify IR.
