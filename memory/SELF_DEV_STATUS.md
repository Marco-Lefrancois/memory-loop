# Self-Dev Harness Status - mLoop

**Status**: Active Diagnostic-First Self-Iteration Loop
**Anomalies de Calibration**: 2

## 1. Diagnostic Médico-Légal des Défaillances (HarnessDev Principle r=0.57)
- Aucune trace d'échec critique détectée dans les journaux.

## 2. Matrice d'Étalonnage
- [PASS] CLI -> OpenCode Shortcuts: Dispatcher universel '/loop' et les 14 raccourcis métier sont alignés.
- [PASS] MCP Bridges -> opencode.json: Tous les 6 ponts MCP sont configurés.
- [PASS] Skills -> Router Index: Les 34 skills sont répertoriés dans l'index.
- [PASS] Directives AGENTS.md/GEMINI.md/CLAUDE.md: AGENTS.md, GEMINI.md et CLAUDE.md sont synchronisés.
- [PASS] Gabarits standards/blueprints: Gabarits officiels (story_template.md, sow_evaluation_template.md) validés.
- [WARN] Synchronisation Sémantique & Graphify: Avertissement lors de la sync : [ÉCHEC DE VALIDATION INVEST] 12 récit(s) ne respectent pas le gabarit officiel (Gherkin/INVEST manquant).
Ce n'est pas un crash système, mais une validation métier ! Lisez memory/wikifix_report.md, corrigez les fichiers, et relancez la validation.
- [PASS] Registre Ingestion MarkItDown SHA256: Registre MarkItDown propre.
- [PASS] Validation 3 Guardrails (audit-loop): Status global : PASS
- [PASS] ADR Contract Sync: ProjectLayout aligné avec adr-contracts.json (ADR-0100/0102/0103).
- [PASS] Memory Structural Sync: Structure canonique de memory/ à 6 sous-dossiers validée.
- [PASS] Project Canonical Root & Anti-Drift: Projet framework mLoop / racine.
- [PASS] ADR Integrity & Stub Purge: Tous les ADRs sont substantiels et conformes à la nomenclature kebab-case.
- [PASS] Docs Root & Hierarchy Guard: Racine de docs/ 100% conforme (index.md unique + 5 sous-dossiers).
- [WARN] Git Cache & Weight Shield: Fichier .gitignore introuvable.
- [PASS] Jargon & Functional Purity Linter: Documentation projet épurée de tout jargon interne ou nom personnel.
- [PASS] Reviews Hierarchy & Cleanliness Guard: Structure backlog/reviews/ étanche par sous-dossiers et 100% propre.
- [PASS] StoryType & Naming Standard Guard: Tous les récits ont un StoryType valide et une nomenclature standardisée.

## 3. Protocole d'Évolution Conforme ADR-0352
1. **Diagnostic First** : Interdiction de modifier le code sans cibler un mode d'échec explicite ci-dessus.
2. **Non-Degeneracy Gating** : Tout patch doit être validé via `CompletionGate` (rejet des stubs et patchs vides).
3. **Validation & Non-Régression** : Relancer `python src/swarm.py self-dev --project mLoop` pour vérifier la résolution.
