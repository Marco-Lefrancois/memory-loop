# 📜 Code Evidence Ledger : EPIC-8-BUILD-HARNESS-GOVERNANCE

> **Source Unique de Vérité Déterministe — Traçabilité Ligne par Ligne (Dogfooding Souverain)**  
> **Initiative** : Harnais Déterministe de Phase 3 : Linter Statique AST, Tournoi TDD Multi-Candidats & Traçabilité Red-Green  
> **Statut Épistémique** : `VERIFIED_DETERMINISTIC`  
> **Autorité** : Marco (PO/Architecte), Lead Architect (Antigravity), Co-Architecte Senior (`agentic_co_architect`)  
> **Date de Création** : 19 Septembre 2026

---

## 🏛️ Invariants Constitutionnels & Standards Référencés
* **ADR-0202** : Modularité interne stricte ($\le 300$ lignes physiques, $\le 15$ Ko par module).
* **ADR-0369** : Gouvernance des Ressources & Robustesse Python Senior (7 Standards mLoop).
* **ADR-0372** : Replay Simulator Hors-Ligne & Auto-Amélioration Récursive (Dream RSI).
* **ADR-0373** : Génération Multi-Branches & Tournoi Auto-Évaluatif Local.
* **ADR-0381** : Standard du Harnais Déterministe de Phase 3 (Linter AST, Tournoi Pareto, TDD Red-Green).

---

## 📋 Registre des Blocs de Code & Évidences Déterministes

| ID Bloc | Récit | Fichier & Lignes | Symbole / Entité | Pilier Gherkin | Règle / Invariant Formel | Banc de Test & Assertion | Statut |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **`CEL-080-001`** | MLOOP-080-BE | [`src/core/ast_checker.py:17-34`](file:///c:/Memory%20Loop/src/core/ast_checker.py#L17-L34) | `AstViolation`, `AstAuditReport` | Pilier 4 - UX & Observabilité | Dataclasses typées immuables pour rapport d'audit statique. | `test_ast_checker_format_report` | `VERIFIED_PASS` |
| **`CEL-080-002`** | MLOOP-080-BE | [`src/core/ast_checker.py:65-115`](file:///c:/Memory%20Loop/src/core/ast_checker.py#L65-L115) | `_AstRuleVisitor.visit_Call` | Pilier 2 - Exceptions & Rejets | Détection stricte des ressources nues (`RULE-AST-02`), timeouts manquants (`RULE-AST-03`) et `stacklevel=2` manquant (`RULE-AST-05`). | `test_ast_checker_rule_02/03/05` | `VERIFIED_PASS` |
| **`CEL-080-003`** | MLOOP-080-BE | [`src/core/ast_checker.py:117-142`](file:///c:/Memory%20Loop/src/core/ast_checker.py#L117-L142) | `_AstRuleVisitor.visit_ExceptHandler` | Pilier 2 - Exceptions & Rejets | Détection du `except: pass` silencieux sans logger (`RULE-AST-04`). | `test_ast_checker_rule_04_silent_except_pass` | `VERIFIED_PASS` |
| **`CEL-080-004`** | MLOOP-080-BE | [`src/core/ast_checker.py:145-236`](file:///c:/Memory%20Loop/src/core/ast_checker.py#L145-L236) | `AstChecker.audit_file` | Pilier 1 - Nominal / Pilier 3 - Résilience | Plafond $\le 300$ lignes / $\le 15$ Ko (ADR-0202), parsing AST sécurisé, résilience aux erreurs de syntaxe. Exécution $<50$ ms. | `test_ast_checker_nominal_clean_file`, `test_rule_01`, `test_resilience_*` | `VERIFIED_PASS` |
| **`CEL-080-005`** | MLOOP-080-BE | [`src/commands/handlers/build_harness.py:18-72`](file:///c:/Memory%20Loop/src/commands/handlers/build_harness.py#L18-L72) | `handle_code_check` | Pilier 4 - UX & Observabilité | Commande CLI `swarm.py code-check` (`--file`, `--story`, `--all`) avec synthèse d'audit. | `python src/swarm.py code-check --file src/core/ast_checker.py` | `VERIFIED_PASS` |
| **`CEL-081-001`** | MLOOP-081-BE | [`src/pipelines/code_tournament.py:31-54`](file:///c:/Memory%20Loop/src/pipelines/code_tournament.py#L31-L54) | `CandidateResult`, `TournamentReport` | Pilier 4 - UX & Observabilité | Modélisation typée immuable des résultats d'arbitrage de tournoi. | `test_tournament_format_report` | `VERIFIED_PASS` |
| **`CEL-081-002`** | MLOOP-081-BE | [`src/pipelines/code_tournament.py:102-187`](file:///c:/Memory%20Loop/src/pipelines/code_tournament.py#L102-L187) | `CodeTournamentEngine._evaluate_candidate` | Pilier 2 - Exceptions & Rejets | Inviolabilité des Portes Dures (100% Pytest + 0 violation AST) avec disqualification immédiate. | `test_tournament_disqualifies_ast_violator` | `VERIFIED_PASS` |
| **`CEL-081-003`** | MLOOP-081-BE | [`src/pipelines/code_tournament.py:65-100, 189-236`](file:///c:/Memory%20Loop/src/pipelines/code_tournament.py#L65-L100) | `CodeTournamentEngine.run_tournament` | Pilier 1 - Nominal / Pilier 3 - Résilience | Fonction de fitness Pareto $S_{\text{pareto}} = 0.40R + 0.35S + 0.25P$ et promotion Golden Master vers `src/`. | `test_tournament_nominal_two_valid_candidates` | `VERIFIED_PASS` |
| **`CEL-081-004`** | MLOOP-081-BE | [`src/commands/handlers/build_harness.py:80-136`](file:///c:/Memory%20Loop/src/commands/handlers/build_harness.py#L80-L136) | `handle_code_tournament` | Pilier 4 - UX & Observabilité | Commande CLI `swarm.py code-tournament` avec affichage de la matrice comparative Pareto. | `python src/swarm.py code-tournament --help` | `VERIFIED_PASS` |
| **`CEL-082-001`** | MLOOP-082-BE | [`src/core/tdd_enforcer.py:42-66`](file:///c:/Memory%20Loop/src/core/tdd_enforcer.py#L42-L66) | `RedSnapshot`, `GreenSnapshot` | Pilier 4 - UX & Observabilité | Empreintes cryptographiques immuables (SHA-256) pour le cycle TDD. | `test_tdd_enforcer_format_status` | `VERIFIED_PASS` |
| **`CEL-082-002`** | MLOOP-082-BE | [`src/core/tdd_enforcer.py:89-131`](file:///c:/Memory%20Loop/src/core/tdd_enforcer.py#L89-L131) | `TddEnforcer.record_red` | Pilier 2 - Exceptions & Rejets | Obligation d'Échec Initial Réel — échec pytest avant implémentation sinon rejet UnexpectedPassingTestError. | `test_tdd_enforcer_rejects_red_if_test_passes` | `VERIFIED_PASS` |
| **`CEL-082-003`** | MLOOP-082-BE | [`src/core/tdd_enforcer.py:133-199`](file:///c:/Memory%20Loop/src/core/tdd_enforcer.py#L133-L199) | `TddEnforcer.record_green` | Pilier 1 - Nominal / Pilier 2 - Exceptions | Scellement Green après succès intégral (tests 100% verts + 0 violation AST) et présence du RedSnapshot. | `test_tdd_enforcer_nominal_cycle` | `VERIFIED_PASS` |
| **`CEL-082-004`** | MLOOP-082-BE | [`src/core/tdd_enforcer.py:201-224`](file:///c:/Memory%20Loop/src/core/tdd_enforcer.py#L201-L224) | `TddEnforcer.verify_gate_3_compliance` | Pilier 3 - Résilience | Inviolabilité du Verrou de Gate 3 — refus d'approbation si le couple (RedSnapshot, GreenSnapshot) est incomplet. | `test_tdd_enforcer_gate3_missing_evidence` | `VERIFIED_PASS` |
| **`CEL-082-005`** | MLOOP-082-BE | [`src/commands/handlers/build_harness.py:138-216`](file:///c:/Memory%20Loop/src/commands/handlers/build_harness.py#L138-L216) | `handle_tdd_enforce` | Pilier 4 - UX & Observabilité | Commande CLI `swarm.py tdd-enforce` supportant red, green et verify avec synchronisation de l'EvidencePack. | `python src/swarm.py tdd-enforce --help` | `VERIFIED_PASS` |

---
*Ce registre est alimenté et vérifié à chaque écriture de code conformément au protocole de traçabilité zéro-blindspot.*
