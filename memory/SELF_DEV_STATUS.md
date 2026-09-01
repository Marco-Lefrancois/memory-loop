# Self-Dev Harness Status - mLoop

**Status**: Active Self-Iteration Loop
**Anomalies détectées**: 2

## Matrice d'Étalonnage
- [PASS] CLI -> OpenCode Shortcuts: Les 29 commandes CLI sont alignées.
- [PASS] MCP Bridges -> opencode.json: Tous les 4 ponts MCP sont configurés.
- [PASS] Skills -> Router Index: Les 18 skills sont répertoriés dans l'index.
- [PASS] Directives AGENTS.md/GEMINI.md: AGENTS.md et GEMINI.md contiennent les directives essentielles.
- [PASS] Gabarits standards/blueprints: Gabarit officiel unique story_template.md validé.
- [WARN] Synchronisation Sémantique & Graphify: Avertissement lors de la sync : [ÉCHEC DE VALIDATION INVEST] 21 récits ne respectent pas le gabarit officiel (Gherkin/INVEST manquant).
Ce n'est pas un crash système, mais une validation métier ! Lisez memory/wikifix_report.md, corrigez les fichiers, et relancez la validation.
- [PASS] Registre Open Notebook SHA256: 0 document(s) indexés sans doublons.
- [FAIL] Validation 3 Guardrails (audit-loop): Status global : FAIL
- [PASS] ADR Contract Sync: ProjectLayout aligné avec adr-contracts.json (ADR-0100/0102/0103).

## Instructions d'Auto-Évolution (Exception de Développement mLoop)
1. **Périmètre sous `src/`** : L'agent mLoop est autorisé à corriger directement le code Python sous `src/` et `src/bridges/`.
2. **Validation** : Après toute modification, relancer `python src/swarm.py self-dev --project mLoop` jusqu'à résolution des WARN/FAIL.
