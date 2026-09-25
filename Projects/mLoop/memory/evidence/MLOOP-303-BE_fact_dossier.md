# 📋 Fact Dossier — `MLOOP-303-BE` : Grille d'Audit Architectural Découplée (Structure Sémantique vs Rendu)

---

- **Récit Cible** : `MLOOP-303-BE`
- **Épopée** : `EPIC-30-MULTIMODAL-ARTIFACT-HARNESS`
- **Composant** : `Pipelines/Audit` (`src/pipelines/audit_decoupler.py`)
- **Établi le** : 2026-09-25 — Session Macro-Grill VALIDÉE (PO Marco)
- **Autorité** : PO mLoop (Marco) / Architecte Framework
- **Références** : [ADR-016](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md), [ADR-0392](../../../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md), *ReFigBench* (arXiv:2609.18844, Découplage Topologique).

---

## ⚖️ 1. Matrice des Décisions Validées en Session Macro-Grill

| # | Question Grillée | Option Retenue | Justification & Impact Technique |
| :- | :--- | :---: | :--- |
| **Q5** | Formule mathématique de notation découplée | **Formule à Barrière Multiplicative** | $\text{Score} = S_{\text{topo}} \times (0.7 + 0.3 \times S_{\text{visuel}})$. Si une dépendance est manquante ou inversée ($S_{\text{topo}} < 1.0$), la note globale s'effondre immédiatement même si l'esthétique est parfaite. Note 0/100 éliminatoire immédiate en cas d'inversion causale de flux. |

---

## 🔍 2. Extraits Sourcés & Vérité Terrain

### Extrait 1 — *ReFigBench* (arXiv:2609.18844)
> "Superficial visual metrics like SSIM/CLIP rate inverted pipelines above 85%. Multiplicative barrier scoring ensures topological fidelity acts as a non-negotiable gating precondition."

### Extrait 2 — Codebase locale `src/commands/handlers/analysis_audit.py`
* **Fait Établi** : Aucun calcul multiplicatif de pénalité topologique n'existait dans la grille de scoring d'architecture.
* **Impact** : Création du module `src/pipelines/audit_decoupler.py` (≤ 300L).
