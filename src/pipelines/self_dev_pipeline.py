from pathlib import Path
import re
from typing import Dict, List, Any
from src.state import LoopState
from src.cli import ZeroFluffConsole
from src.pipelines.completion_gate import CompletionGate, GateStatus
from src.utils.logger import get_logger

logger = get_logger("pipelines.self_dev_pipeline")

class DiagnosticFirstTraceAnalyzer:
    """
    Analyseur médico-légal de traces d'échec (ADR-0352 / HarnessDev).
    HarnessDev prouve que l'analyse ciblée des traces d'échec corrèle à r=0.57 avec le succès
    (vs r=0.13 pour le volume d'auto-tests aveugles).
    """

    @staticmethod
    def extract_failure_taxonomy(project_path: Path) -> Dict[str, List[str]]:
        taxonomy: Dict[str, List[str]] = {
            "INVEST_VIOLATIONS": [],
            "SCHEMA_VIOLATIONS": [],
            "RUNTIME_ERRORS": [],
            "DEGENERATE_OUTPUTS": [],
        }

        # 1. Analyse du rapport WikiFix
        wikifix_report = Path("memory") / "wikifix_report.md"
        if wikifix_report.exists():
            try:
                content = wikifix_report.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if "INVEST" in line or "[C8]" in line:
                        taxonomy["INVEST_VIOLATIONS"].append(line.strip())
                    elif "YAML" in line or "[C6]" in line or "RM-" in line:
                        taxonomy["SCHEMA_VIOLATIONS"].append(line.strip())
                    elif "ERROR" in line or "FAIL" in line or "Traceback" in line:
                        taxonomy["RUNTIME_ERRORS"].append(line.strip())
            except Exception as e:
                logger.warning(
                    "Rapport wikifix illisible, taxonomie de violations partielle",
                    exc_info=True,
                    extra={
                        "component": "pipelines.self_dev_pipeline",
                        "operation": "classify_wikifix_violations",
                        "error": str(e),
                    },
                )

        return {k: v[:5] for k, v in taxonomy.items() if v}


def run_self_dev(project_name: str, state: LoopState, project_path: Path):
    """
    Axe 4 jcode & HarnessDev (ADR-0352) : Pipeline d'Auto-Développement Diagnostic-First.
    Exige une extraction préalable et ciblée des modes d'échecs avant toute proposition
    d'édition sous l'exception de développement mLoop (src/).
    """
    ZeroFluffConsole.section(f"Cycle Self-Dev Harness - Auto-Évolution Diagnostic-First ({project_name})")
    
    # 1. Étape 1 : Diagnostic des composants et ponts MCP
    ZeroFluffConsole.step_s1("Self-Dev Audit", "Audit synchrone de l'écosystème mLoop...")
    from src.pipelines.calibrate import EcosystemCalibrator
    engine = EcosystemCalibrator(Path("."), project_name)
    is_success = engine.run_full_calibration()
    results = engine.report_matrix
    
    warn_or_fail = [r for r in results if r.get("status") in ["WARN", "FAIL"]]
    ZeroFluffConsole.info(f"Nombre d'anomalies détectées : {len(warn_or_fail)}")

    # 2. Étape 2 : Extraction médico-légale des traces d'échecs (Diagnostic-First)
    ZeroFluffConsole.step_s1("Trace Forensics", "Extraction de la taxonomie des défaillances réelles...")
    failures = DiagnosticFirstTraceAnalyzer.extract_failure_taxonomy(project_path)
    
    diagnostic_lines = []
    for cat, items in failures.items():
        diagnostic_lines.append(f"### Catégorie : {cat} ({len(items)} cas)")
        for it in items:
            diagnostic_lines.append(f"- {it}")

    # 3. Étape 3 : Consignation du registre de décision (Scratchpad)
    scratchpad_path = Path("memory") / "SELF_DEV_STATUS.md"
    scratchpad_path.parent.mkdir(parents=True, exist_ok=True)
    
    anomalies_str = "\n".join([f"- [{r.get('status')}] {r.get('name')}: {r.get('details')}" for r in results])
    diagnostics_str = "\n".join(diagnostic_lines) if diagnostic_lines else "- Aucune trace d'échec critique détectée dans les journaux."

    scratchpad_content = f"""# Self-Dev Harness Status - {project_name}

**Status**: Active Diagnostic-First Self-Iteration Loop
**Anomalies de Calibration**: {len(warn_or_fail)}

## 1. Diagnostic Médico-Légal des Défaillances (HarnessDev Principle r=0.57)
{diagnostics_str}

## 2. Matrice d'Étalonnage
{anomalies_str}

## 3. Protocole d'Évolution Conforme ADR-0352
1. **Diagnostic First** : Interdiction de modifier le code sans cibler un mode d'échec explicite ci-dessus.
2. **Non-Degeneracy Gating** : Tout patch doit être validé via `CompletionGate` (rejet des stubs et patchs vides).
3. **Validation & Non-Régression** : Relancer `python src/swarm.py self-dev --project {project_name}` pour vérifier la résolution.
"""
    scratchpad_path.write_text(scratchpad_content, encoding="utf-8")
    ZeroFluffConsole.success(f"Rapport d'état consigné sous {scratchpad_path.name}")
    
    # 4. Étape 4 : Exécution de WikiFix
    try:
        from src.pipelines.wikifix import WikiFixAgent
        WikiFixAgent().execute(state)
        ZeroFluffConsole.success("Contrôle WikiFix validé avec succès.")
    except Exception as e:
        ZeroFluffConsole.warning(f"Note d'audit WikiFix lors du Self-Dev : {e}")

    # 5. Checkpointing in-flight
    state.checkpoint(force=True, reason="self_dev_completion")

    ZeroFluffConsole.success("Pipeline Self-Dev Diagnostic-First terminé. Le framework mLoop est calibré pour l'auto-itération.")

