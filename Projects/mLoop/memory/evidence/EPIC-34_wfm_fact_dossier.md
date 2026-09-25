# Dossier de Preuves — EPIC-34-WFM-COGNITIVE-WIKI-GRAPH

**Statut** : CURRENT  
**Date** : 2026-09-25  
**Récits couverts** : MLOOP-340-BE à MLOOP-344-FULL  
**Base légale** : ADR-0395 (Wiki-Graph Dual Layer & Fact-Search Réflexif WFM), ADR-0369, ADR-0393  
**Publication de référence** : WFM (*arXiv:2609.18182*) — *Wiki Graph Construction and Dual-Space Initialization*  

---

## 1. Sources primaires
| Source | Emplacement | Usage |
|:---|:---|:---|
| Papier WFM | arXiv:2609.18182 | Définition 2, Équations 1-2, Section 3.1 & 3.4 |
| ADR-0395 | `standards/adr-system/0395-wiki-graph-dual-layer-et-fact-search-reflexif-wfm.md` | Spécification SSOT du schéma dual-layer SQLite |
| Backlog épopée | `Projects/mLoop/backlog/epics/` | Découpage INVEST des 5 récits |

---

## 2. Extraits verbatim sourcés

**Extrait 1 — ADR-0395 (§3.1)** : « Le Wiki-Graph dual-layer formalise la séparation entre les entités sémantiques stables et les passages textuels sources pour garantir un ancrage réflexif sans perte de contexte. » ➔ **Fait établi** : Tables dédiées `wiki_entities`, `wiki_passages`, `wiki_hyper_edges`.

**Extrait 2 — WFM arXiv:2609.18182 (§3.1)** : « Dual-space representation ensures that entity embeddings capture invariant topological relations while passage embeddings preserve local discursive semantics. » ➔ **Fait établi** : Double indexation sémantique et topologique.

**Extrait 3 — ADR-0369 (Standards de Robustesse)** : « Isolation des transactions SQLite et mode WAL obligatoire pour tout nouveau stockage persistant. » ➔ **Fait établi** : Configuration DDL SQLite avec intégrité référentielle stricte.

---

## 3. Contrats déclaratifs cibles
- `src/core/wiki_graph/` : package modulaire respectant ADR-0202 (fichiers ≤ 300L).
- Tests d'intégration et unitaires dédiés avec isolation en base mémoire / SQLite temporaire.
