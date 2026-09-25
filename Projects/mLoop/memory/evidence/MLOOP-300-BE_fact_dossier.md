# 📋 Fact Dossier — `MLOOP-300-BE` : Porte Déterministe d'Artefacts & Anti-Raster Paste pour Livrables Visuels

---

- **Récit Cible** : `MLOOP-300-BE`
- **Épopée** : `EPIC-30-MULTIMODAL-ARTIFACT-HARNESS`
- **Composant** : `Gate/Artifacts` (`src/pipelines/artifact_gate.py`)
- **Établi le** : 2026-09-25 — Session Macro-Grill VALIDÉE (PO Marco)
- **Autorité** : PO mLoop (Marco) / Architecte Framework
- **Références** : [ADR-016](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md), [ADR-0392](../../../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md), *ReFigBench* (arXiv:2609.18844, Section 3).

---

## ⚖️ 1. Matrice des Décisions Validées en Session Macro-Grill

| # | Question Grillée | Option Retenue | Justification & Impact Technique |
| :- | :--- | :---: | :--- |
| **Q1** | Rigueur et seuil de la porte anti-raster | **Barrière Déterministe Binaire Stricte ($g(P) \in \{0, 1\}$)** | Rejet immédiat si un livrable d'architecture (Archify, SVG, Canvas) dépasse 80% de surface matricielle raster (PNG/JPEG) sans arêtes vectorielles éditables associées. Motif : `RASTER_PASTE_DETECTED`. Aucun appel LLM n'est autorisé en cas d'échec binaire. |

---

## 🔍 2. Extraits Sourcés & Vérité Terrain

### Extrait 1 — *ReFigBench* (arXiv:2609.18844, Section 3)
> "When evaluating scientific figures, agents frequently bypass vector generation by embedding raw raster images within an SVG or presentation wrapper, scoring high on superficial visual similarity while destroying editability. A deterministic gate $g(P) \in \{0, 1\}$ filtering unopenable files and raster-heavy pasteboards is required prior to semantic scoring."

### Extrait 2 — Codebase locale mLoop `tools/archify/`
* **Fait Établi** : Actuellement, aucune vérification ne bloque un fichier SVG contenant une simple balise `<image href="data:image/png;base64,...">` étirée sur toute la page.
* **Impact** : Création du module `src/pipelines/artifact_gate.py` (≤ 300L) avec la fonction `evaluate_artifact_gate(file_path: Path) -> ArtifactGateResult`.
