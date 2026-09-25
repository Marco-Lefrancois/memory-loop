# 📋 Fact Dossier — `MLOOP-304-FULL` : Contrats de Dev Handoff Multi-Harnais & Commande CLI `artifact-check`

---

- **Récit Cible** : `MLOOP-304-FULL`
- **Épopée** : `EPIC-30-MULTIMODAL-ARTIFACT-HARNESS`
- **Composant** : `CLI/VibeCheck` (`src/commands/handlers/artifact_check.py`, `src/pipelines/vibe_check.py`)
- **Établi le** : 2026-09-25 — Session Macro-Grill VALIDÉE (PO Marco)
- **Autorité** : PO mLoop (Marco) / Architecte Framework
- **Références** : [ADR-016](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md), [ADR-0392](../../../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md), *ReFigBench* (arXiv:2609.18844, Harnais & Dev Handoff).

---

## ⚖️ 1. Matrice des Décisions Validées en Session Macro-Grill

| # | Question Grillée | Option Retenue | Justification & Impact Technique |
| :- | :--- | :---: | :--- |
| **Q3** | Sévérité et ancrage de la commande `artifact-check` | **Check 27 Bloquant dans Vibe-Check** | Intégration de la sonde de vol Check 27 bloquante en Phase 2 (Gate 2 / DoR) et Phase 4 (Gate 4 / QA) si un livrable d'architecture est corrompu ou viole les règles topologiques. |
| **Q6** | Format normatif de Dev Handoff | **Contrat Dual JSON IR + SVG Sémantique** | Tout schéma d'architecture certifié comporte son fichier `.ir.json` (spécification abstraite des nœuds/arêtes) et son fichier `.semantic.svg` annoté d'attributs `data-node-id`, `data-edge-from`, `data-edge-to`. |

---

## 🔍 2. Extraits Sourcés & Vérité Terrain

### Extrait 1 — *ReFigBench* (arXiv:2609.18844)
> "Harness primacy dictates that downstream code generators depend on structural metadata, not ambiguous visual layouts. Emitting machine-readable IR alongside semantic SVG ensures lossless developer handoff."

### Extrait 2 — Codebase locale `src/pipelines/vibe_check.py`
* **Fait Établi** : La suite Vibe-Check compte 26 contrôles.
* **Impact** : Ajout du Check 27 pour valider l'intégrité déterministe des artefacts dans les projets.
