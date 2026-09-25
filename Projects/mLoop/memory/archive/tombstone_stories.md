# 🗄️ Registre des Récits Dépréciés & Élagués (TOMBSTONE Archive) — mLoop

**Date d'archivage** : 2026-09-19  
**Décideurs** : Marco (Architecte Propriétaire), Lead Architect (Antigravity)  
**Autorité** : [ADR-0365](file:///C:/Memory%20Loop/standards/adr-system/0365-harmonisation-symbiotique-skills-et-standard-agent-skills.md), [ADR-0369](file:///C:/Memory%20Loop/standards/adr-system/0369-python-senior-robustness-and-resource-governance.md)  
**Raison** : Assainissement du backlog opérationnel par suppression des concepts spéculatifs, de la sur-ingénierie et des dépassements de périmètre, tout en préservant l'historique complet.

---

## Récits Élagués et Motifs de Clôture

| Récit ID | Épopée d'Origine | Composant | Titre du Récit | Motif Architectural de Dépréciation & Solution de Substitution |
| :--- | :--- | :--- | :--- | :--- |
| **`MLOOP-012-BE`** | EPIC-2-HYBRID-MEMORY | Memory | Compression MLA KV Cache | **Sur-ingénierie mathématique**. Le besoin de réduction d'empreinte sémantique est déjà intégralement résolu par l'intercepteur de frontières `boundary_trace` avec déport automatique vers `OpaqueArtifactBus` ([MLOOP-071-BE](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-071-BE.md)) et la compaction contextuelle déterministe. |
| **`MLOOP-022-BE`** | EPIC-3-SAFETY-GOVERNANCE | Safety | Audit Intentionnel `J-Lens` (Jacobian Lens) | **Spéculatif & Lourd**. Nécessitait le déploiement d'un modèle local lourd (Ornith-1.0-9B) pour l'analyse d'activation neuronale. Remplacé par les contrôles d'invariants formels, de fuite privée et de non-contradiction NLI d'EPIC-9 ([MLOOP-091-BE](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-091-BE.md)), infiniment plus rapides et déterministes. |
| **`MLOOP-032-BE`** | EPIC-4-SKILL-ECOSYSTEM | Skill | `Skill Auto-Creator` (Création autonome d'outils) | **Risque de Sécurité & Violation HITL**. L'auto-création récursive de scripts par un agent sans supervision humaine directe viole les principes de confinement et la règle anti-prolifération de compétences ([ADR-0362](file:///C:/Memory%20Loop/standards/adr-system/0362-skills-token-budget-and-context-rot.md) Zero-Bloat Skills). |
| **`MLOOP-041-BE`** | EPIC-5-INGESTION-OFFICE | Skill | Bridge `OfficeCLI` (Modification chirurgicale .docx / .xlsx) | **Hors Périmètre SSOT**. Le framework mLoop fonctionne selon le principe absolu du Markdown universel pur (`docs/00-ingested/`). La manipulation directe de binaires Office opaques introduit de la fragilité inutile. L'ingestion MarkItDown ([MLOOP-040-BE](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-040-BE.md)) couvre 100% des besoins. |
| **`MLOOP-042-FE`** | EPIC-5-INGESTION-OFFICE | Frontend | Visualiseur de Rendu HTML Office | **Élagué par transitivité**. Composant de prévisualisation watch lié directement au bridge OfficeCLI (`MLOOP-041-BE`). Rendu sans objet suite à la dépréciation du format binaire. |

---

## Bilan d'Impact sur le Sprint Backlog

- **Total récits initiaux** : 34
- **Récits certifiés (`SHIPPED` / `DONE_TESTED`)** : 21
- **Récits archivés (`TOMBSTONE`)** : 5
- **Récits actifs restants (`OPEN`)** : 8
