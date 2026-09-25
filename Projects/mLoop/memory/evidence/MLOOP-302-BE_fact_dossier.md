# 📋 Fact Dossier — `MLOOP-302-BE` : Filtre d'Ingestion Documentaire ORBIT pour Schémas d'Architecture

---

- **Récit Cible** : `MLOOP-302-BE`
- **Épopée** : `EPIC-30-MULTIMODAL-ARTIFACT-HARNESS`
- **Composant** : `Pipelines/Ingest` (`src/pipelines/ingest_file_processors.py`)
- **Établi le** : 2026-09-25 — Session Macro-Grill VALIDÉE (PO Marco)
- **Autorité** : PO mLoop (Marco) / Architecte Framework
- **Références** : [ADR-016](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md), [ADR-0392](../../../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md), *ReFigBench* (arXiv:2609.18844, Algorithme ORBIT).

---

## ⚖️ 1. Matrice des Décisions Validées en Session Macro-Grill

| # | Question Grillée | Option Retenue | Justification & Impact Technique |
| :- | :--- | :---: | :--- |
| **Q4** | Stratégie d'ancrage documentaire ORBIT | **Ingestion Hybride Ancrée (Figure + Caption + Paragraphe Référant)** | Tout schéma extrait sous `docs/00-ingested/` est obligatoirement lié à sa légende et aux phrases du texte qui le référencent. L'intégrité est scellée par hash SHA-256 dans `source_manifest.json`. Élimination des bannières décoratives. |

---

## 🔍 2. Extraits Sourcés & Vérité Terrain

### Extrait 1 — *ReFigBench* (arXiv:2609.18844)
> "The ORBIT algorithm harvests technical captions and surrounding body paragraphs citing figures (e.g., 'Figure 3: ...'), anchoring structural context before any downstream vision processing."

### Extrait 2 — Codebase locale `src/pipelines/ingest_file_processors.py`
* **Fait Établi** : L'ingestion MarkItDown actuelle isole les images dans `00-ingested/` sans fichier sidecar de légende contextuelle.
* **Impact** : Ajout de `OrbitCaptionHarvester` pour créer les fiches d'ancrage contextuelles.
