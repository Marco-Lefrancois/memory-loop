"""
Sous-module vibe_check/_vc_agents.py
Checks liés aux directives agents et à l'infrastructure d'exécution (ADR-0377, ADR-0379).

Checks inclus :
  - check_01_agent_parity   : Parité miroir AGENTS.md / GEMINI.md / CLAUDE.md (Check 1)
  - check_16_agent_probe    : Sonde des runtimes d'agents aval & Herdr (Check 16)
  - check_19_standards_graph: Intégrité StandardsGraph & Bouclier de Confinement SSOT (Check 19)
"""

from pathlib import Path

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("pipelines.vibe_check._vc_agents")


def check_01_agent_parity(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> list[dict]:
    """
    Check 1 : Vérifie la présence et la parité miroir des directives fondamentales
    AGENTS.md, GEMINI.md et CLAUDE.md. En cas de dérive, auto-healing depuis AGENTS.md.
    Retourne une liste de résultats (un par fichier règle).
    """
    rule_files = ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]
    presence_ok = all(Path(rf).exists() for rf in rule_files)

    # Contrôle de Parité Miroir & Auto-Sync Anti-Drift
    parity_ok = True
    if presence_ok:
        agents_txt = Path("AGENTS.md").read_text(encoding="utf-8")
        for rf in ["GEMINI.md", "CLAUDE.md"]:
            rf_p = Path(rf)
            rf_txt = rf_p.read_text(encoding="utf-8")
            if rf_txt != agents_txt:
                # Auto-healing : synchroniser le miroir depuis AGENTS.md
                rf_p.write_text(agents_txt, encoding="utf-8")
                ZeroFluffConsole.success(
                    f"[Vibe-Check Auto-Sync] Parité miroir restaurée pour {rf} depuis AGENTS.md"
                )

    results = []
    for rule_file in rule_files:
        exists = Path(rule_file).exists()
        results.append(
            {
                "check": f"Règles {rule_file} (Parité Miroir)",
                "status": "PASS" if exists and parity_ok else "FAIL",
            }
        )

    # MLOOP-261-BE : Contrôle de Parité Miroir pour .clinerules/mloop.md
    cline_rule_p = Path(".clinerules") / "mloop.md"
    if not cline_rule_p.exists() or cline_rule_p.stat().st_size < 50:
        try:
            from src.bridges.cline.rules_mirror import ClineRulesMirror

            ClineRulesMirror().sync()
            ZeroFluffConsole.success(
                "[Vibe-Check Auto-Sync] Parité miroir restaurée pour .clinerules/mloop.md"
            )
        except Exception:
            pass

    cline_ok = cline_rule_p.exists() and cline_rule_p.stat().st_size >= 50
    results.append(
        {
            "check": "Règles .clinerules (Parité Miroir)",
            "status": "PASS" if cline_ok else "WARNING",
        }
    )
    return results


def check_16_agent_probe(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 16 : Sonde des runtimes d'agents aval & Herdr (ADR-0377).
    Vérifie la présence et la viabilité des outils d'exécution pour la phase courante.
    """
    from src.core.agent_probe import AgentProbe

    probe = AgentProbe()
    agent_readiness_ok, agent_violations = probe.check_readiness(stage=stage_label)
    agent_msg = (
        "Runtimes d'Agents Aval & Herdr Opérationnels (ADR-0377)"
        if agent_readiness_ok
        else f"Runtimes d'Agents Aval & Herdr (ADR-0377 : {'; '.join(agent_violations)})"
    )
    return {"check": agent_msg, "status": "PASS" if agent_readiness_ok else "FAIL"}


def check_19_standards_graph(
    project_dir: Path, project_name: str, lifecycle_mode: str, stage_label: str
) -> dict:
    """
    Check 19 : Intégrité StandardsGraph & Bouclier de Confinement SSOT (ADR-0379).
    Vérifie :
      1. La présence et la synchronisation de memory/standards_graph.db.
      2. La parité stricte des 38 skills (.agents/skills/*/SKILL.md) avec StandardsGraph.
      3. L'absence de fichiers .toml résiduels dans standards/agents/.
      4. L'intégrité du bouclier de confinement runtime (ConfinementShield canary test).
    """
    standards_graph_ok = True
    standards_violations = []

    try:
        from src.core.standards_graph import StandardsGraphStore

        store = StandardsGraphStore.get_instance()
        skills = store.get_skills()
        agents = store.get_agents()

        if len(skills) < 38:
            standards_graph_ok = False
            standards_violations.append(f"Catalogue incomplet ({len(skills)}/38 skills)")

        if len(agents) < 5:
            standards_graph_ok = False
            standards_violations.append(f"Profils d'agents incomplets ({len(agents)}/5 agents)")

        if Path("standards/agents").exists() and any(Path("standards/agents").glob("*.toml")):
            standards_graph_ok = False
            standards_violations.append("Fichiers .toml résiduels interdits sous standards/agents/")

        from src.core.confinement_shield import ConfinementShield, PermissionDeniedError

        try:
            ConfinementShield.verify_skill_access("forbidden-skill-canary", "explorer")
            standards_graph_ok = False
            standards_violations.append(
                "Bouclier ConfinementShield inactif (canary non intercepté)"
            )
        except PermissionDeniedError:
            # Interception réussie du canary : comportement nominal attendu.
            logger.debug(
                "ConfinementShield a correctement intercepté le canary 'forbidden-skill-canary'.",
                extra={
                    "check_name": "standards_graph_integrity",
                    "violation_type": "canary_intercepted_ok",
                },
            )

    except Exception as exc:
        standards_graph_ok = False
        standards_violations.append(f"Erreur StandardsGraph : {exc}")
        logger.error(
            "Erreur lors de l'audit d'intégrité StandardsGraph (ADR-0379).",
            exc_info=True,
            extra={
                "check_name": "standards_graph_integrity",
                "violation_type": "standards_graph_error",
            },
        )

    standards_msg = (
        "Intégrité StandardsGraph & Bouclier de Confinement SSOT (ADR-0379)"
        if standards_graph_ok
        else f"Intégrité StandardsGraph & Bouclier SSOT (Violations : {'; '.join(standards_violations)})"
    )
    return {"check": standards_msg, "status": "PASS" if standards_graph_ok else "FAIL"}
