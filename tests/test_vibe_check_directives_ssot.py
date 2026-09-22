"""
Tests du Check 20 (Intégrité Directives Projet & SSOT Canonique) et de la
sémantique tri-état du verdict Vibe-Check (ADR-0384).

Récit : MLOOP-164-BE. Le contrôle est CONDITIONNEL (n'agit que si le projet
déclare un répertoire `directives/`) et NON BLOQUANT (WARNING, jamais FAIL).
La sémantique du verdict passe de binaire à tri-état : un WARNING n'invalide
pas le verdict global (`fail_count == 0` suffit).
"""

from pathlib import Path
import shutil

import pytest

from src.pipelines.vibe_check import run_vibe_check


def _directives_check(result):
    matches = [c for c in result["checks"] if "Directives Projet" in c["check"]]
    assert len(matches) == 1, "Le Check 20 doit apparaître exactement une fois"
    return matches[0]


def _make_project(name):
    project_dir = Path("Projects") / name
    (project_dir / "backlog" / "stories").mkdir(parents=True, exist_ok=True)
    (project_dir / "backlog" / "sprint_backlog.md").write_text(
        "# Sprint Backlog\n", encoding="utf-8"
    )
    return project_dir


def _write_directives(project_dir, tech_content, business_content, with_context=True):
    directives_dir = project_dir / "directives"
    directives_dir.mkdir(parents=True, exist_ok=True)
    (directives_dir / "tech.md").write_text(tech_content, encoding="utf-8")
    (directives_dir / "business.md").write_text(business_content, encoding="utf-8")
    if with_context:
        (project_dir / "CONTEXT.md").write_text("# Contexte\n", encoding="utf-8")


@pytest.mark.parametrize(
    "case,tech,business,with_context,with_directives,expected_status",
    [
        # Cas 1 : directives conformes (SSOT canonique déclaré) → PASS
        (
            "conforme",
            "# Tech\nSSOT : docs/03-models/ fait foi absolue.\n",
            "# Business\nSource de vérité canonique déclarée.\n",
            True,
            True,
            "PASS",
        ),
        # Cas 2 : absence totale de répertoire directives/ → PASS (non-régression)
        ("sans_directives", None, None, False, False, "PASS"),
        # Cas 3 : directives présentes mais aucun SSOT déclaré → WARNING
        (
            "ssot_non_declare",
            "# Tech\nContenu technique sans mention de source canonique.\n",
            "# Business\nContenu métier générique.\n",
            True,
            True,
            "WARNING",
        ),
        # Cas 4 : tech.md vide → WARNING
        (
            "tech_vide",
            "   ",
            "# Business\nSSOT : docs/03-models/.\n",
            True,
            True,
            "WARNING",
        ),
        # Cas 5 : CONTEXT.md manquant → WARNING
        (
            "context_manquant",
            "# Tech\nSSOT : docs/03-models/.\n",
            "# Business\nSource de vérité canonique.\n",
            False,
            True,
            "WARNING",
        ),
    ],
)
def test_check20_conditional_status(
    case, tech, business, with_context, with_directives, expected_status
):
    project_name = f"TestDirectivesSSOT_{case}"
    project_dir = _make_project(project_name)
    try:
        if with_directives:
            _write_directives(project_dir, tech, business, with_context=with_context)
        result = run_vibe_check(project_name)
        check = _directives_check(result)
        assert check["status"] == expected_status, (
            f"Cas '{case}' : attendu {expected_status}, obtenu {check['status']} ({check['check']})"
        )
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_warning_does_not_invalidate_global_verdict():
    """
    Sémantique tri-état : un projet dont le Check 20 est en WARNING (directives
    incomplètes) mais sans aucun FAIL doit conserver un verdict global valide
    (status PASS), les avertissements n'étant pas bloquants.
    """
    project_name = "TestDirectivesSSOT_trietat"
    project_dir = _make_project(project_name)
    try:
        # Directives présentes mais sans SSOT déclaré → force un WARNING
        _write_directives(
            project_dir,
            "# Tech\nSans mention canonique.\n",
            "# Business\nGénérique.\n",
            with_context=True,
        )
        result = run_vibe_check(project_name)

        check = _directives_check(result)
        assert check["status"] == "WARNING"

        # Le verdict global ne doit pas être FAIL du seul fait d'un WARNING
        assert result["fail_count"] == sum(1 for c in result["checks"] if c["status"] == "FAIL")
        assert result["warning_count"] >= 1
        # is_valid == (fail_count == 0) : le status global reflète l'absence de FAIL
        if result["fail_count"] == 0:
            assert result["status"] == "PASS"
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_tristate_counters_present_in_result():
    """Le résultat expose les compteurs tri-état (passed/warning/fail)."""
    project_name = "TestDirectivesSSOT_counters"
    project_dir = _make_project(project_name)
    try:
        result = run_vibe_check(project_name)
        assert "passed_count" in result
        assert "warning_count" in result
        assert "fail_count" in result
        total = result["passed_count"] + result["warning_count"] + result["fail_count"]
        assert total == len(result["checks"])
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
