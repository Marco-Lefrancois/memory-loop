# 📋 Fact Dossier — `MLOOP-301-BE` : Validation Topologique Anti-Effondrement des Connecteurs Archify

---

- **Récit Cible** : `MLOOP-301-BE`
- **Épopée** : `EPIC-30-MULTIMODAL-ARTIFACT-HARNESS`
- **Composant** : `Tools/Archify` (`tools/archify/`, `src/commands/handlers/archify_core.py`)
- **Établi le** : 2026-09-25 — Session Macro-Grill VALIDÉE (PO Marco)
- **Autorité** : PO mLoop (Marco) / Architecte Framework
- **Références** : [ADR-016](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md), [ADR-0392](../../../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md), *ReFigBench* (arXiv:2609.18844, Section 5).

---

## ⚖️ 1. Matrice des Décisions Validées en Session Macro-Grill

| # | Question Grillée | Option Retenue | Justification & Impact Technique |
| :- | :--- | :---: | :--- |
| **Q2** | Traitement du Connector Collapse dans Archify | **Règle du Graphe Fermé Strict** | Toute arête (`edge`) doit obligatoirement relier un `from` et un `to` valides. Rejet bloquant `CONNECTOR_INTEGRITY_FAIL` en cas d'arête orpheline. Rejet `CONNECTOR_COLLAPSE_DETECTED` si un diagramme à plus de 3 blocs ne possède aucun connecteur relationnel. |

---

## 🔍 2. Extraits Sourcés & Vérité Terrain

### Extrait 1 — *ReFigBench* (arXiv:2609.18844, Section 5)
> "In iterative refinement workflows, models frequently suffer from Connector Collapse, dropping relational connectors in favor of unconnected bounding boxes. Strict topology-preserving linters must enforce graph closedness."

### Extrait 2 — Codebase locale `tools/archify/archify_runner.py`
* **Fait Établi** : Archify dispose d'un validateur JSON IR mais n'applique pas de contrôle d'arêtes orphelines bloquant.
* **Impact** : Implémentation de `ConnectorIntegrityValidator` pour garantir le graphe fermé.
