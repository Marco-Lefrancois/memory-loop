# Active Context — Memory Loop (mLoop)

## 1. Current Sprint Focus
Le sprint actif est centré sur l'**Orchestration Bimodale OpenCode + Cline** (EPIC-25 et EPIC-26), l'intégration du standard Memory Bank et le Circuit-Breaker Herdr.

## 2. Recent Architectural Decisions
- Enrôlement de Cline comme runtime de travail officiel dans `WORKER_RUNTIMES`.
- Verrouillage obligatoire de `--plan` en Phase 2 tant que DoR < 6/6.
- Garantie inviolable de fallback automatique vers OpenCode en cas de panne.

## 3. Active Stories (Extrait SSOT)
- **MLOOP-260-BE** : Bridge de Mémoire Bidirectionnel mLoop <-> Cline Memory Bank (`memory-bank/`) (Bridges/Cline) — Statut: `⚪ `DRAFT``
- **MLOOP-261-BE** : Génération Automatique de la Parité `.clinerules` depuis `CONSTRAINTS.md` & `AGENTS.md` (Rules/Cline) — Statut: `⚪ `DRAFT``
- **MLOOP-262-BE** : Intégration du Mode Plan/Act de Cline (`--plan`) avec les Gates de Cycle de Vie mLoop (Workflow/Cline) — Statut: `⚪ `DRAFT``
- **MLOOP-263-BE** : Adaptateur Worker Cline Agent Teams (`--team-name`) pour Swarm Multitâches (Swarm/Cline) — Statut: `⚪ `DRAFT``
- **MLOOP-264-FULL** : Commandes CLI `mloop cline-sync` & Harnais de Validation Pré-Vol Vibe-Check (CLI/Cline) — Statut: `⚪ `DRAFT``
- **MLOOP-012-BE** : Compression MLA KV Cache (Memory) — Statut: `Remplacé par OpaqueArtifactBus & Compaction contextuelle`
- **MLOOP-022-BE** : Audit Intentionnel `J-Lens` (Safety) — Statut: `Remplacé par Invariants NLI & Assertions déterministes EPIC-9`
- **MLOOP-032-BE** : `Skill Auto-Creator` (Skill) — Statut: `Élagué — Risque de sécurité HITL & règle Zero-Bloat ADR-0362`
- **MLOOP-041-BE** : Bridge `OfficeCLI` (Skill) — Statut: `Élagué — Périmètre SSOT 100% Markdown (couvert par MarkItDown)`
- **MLOOP-042-FE** : Visualiseur de Rendu HTML Office (Frontend) — Statut: `Élagué par transitivité avec MLOOP-041-BE`

## 4. Next Immediate Steps
1. Finaliser le générateur de Memory Bank (MLOOP-260-BE).
2. Générer la parité .clinerules/mloop.md (MLOOP-261-BE).
3. Valider le Circuit-Breaker avec test unitaire dédié (MLOOP-263-BE).
