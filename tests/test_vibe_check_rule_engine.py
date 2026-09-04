"""
Test de validation du 11e contrôle Vibe-Check : Intégration Dynamique RuleEngine
(ADR-0328 §2.2). L'ADR promet que les règles déclaratives `validation_rules`
définies dans le frontmatter YAML des ADRs soient « injectées dynamiquement dans
les pipelines de validation (struct-check, vibe-check, validate) ». Ce test
vérifie le branchement réel dans run_vibe_check() (le seul des 3 pipelines cité
qui n'était pas câblé — struct-check et wikifix l'étaient déjà).
"""

from pathlib import Path
import shutil

from src.pipelines.vibe_check import run_vibe_check


def test_vibe_check_flags_rule_engine_blocking_violation():
    project_dir = Path("Projects") / "TestRuleEngineVibeProj"
    arch_dir = project_dir / "docs" / "01-architecture"
    stories_dir = project_dir / "backlog" / "stories"
    arch_dir.mkdir(parents=True, exist_ok=True)
    stories_dir.mkdir(parents=True, exist_ok=True)

    try:
        (arch_dir / "ADR-TEST-VIBE.md").write_text(
            """---
id: ADR-TEST-VIBE
title: Règle de test Vibe-Check
validation_rules:
  - check_id: no_local_file_paths
    severity: BLOCKING
    params:
      forbidden_patterns:
        - "C:\\\\\\\\Users"
---
# ADR-TEST-VIBE
""",
            encoding="utf-8",
        )
        (stories_dir / "US-01.md").write_text(
            "# US-01\n\nRéférence interdite : C:\\Users\\test\\fichier.md\n",
            encoding="utf-8",
        )

        result = run_vibe_check("TestRuleEngineVibeProj")
        re_checks = [c for c in result["checks"] if "RuleEngine" in c["check"]]
        assert len(re_checks) == 1
        assert re_checks[0]["status"] == "FAIL"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_vibe_check_passes_when_no_rule_violation():
    project_dir = Path("Projects") / "TestRuleEngineVibeProj2"
    arch_dir = project_dir / "docs" / "01-architecture"
    stories_dir = project_dir / "backlog" / "stories"
    arch_dir.mkdir(parents=True, exist_ok=True)
    stories_dir.mkdir(parents=True, exist_ok=True)

    try:
        (stories_dir / "US-01.md").write_text(
            "# US-01\n\nContenu propre.\n", encoding="utf-8"
        )

        result = run_vibe_check("TestRuleEngineVibeProj2")
        re_checks = [c for c in result["checks"] if "RuleEngine" in c["check"]]
        assert len(re_checks) == 1
        assert re_checks[0]["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
