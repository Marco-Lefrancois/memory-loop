from pathlib import Path
from src.state import LoopState
from src.cli import ZeroFluffConsole

def run_self_dev(project_name: str, state: LoopState, project_path: Path):
    """
    Axe 4 jcode (ADR-0308) : Pipeline d'Auto-Développement mLoop (Self-Dev Mode).
    Permet au framework mLoop d'exécuter un cycle fermé d'auto-audit, d'auto-refactorisation 
    sous l'exception de développement mLoop (src/), et d'auto-calibration.
    """
    ZeroFluffConsole.section(f"Cycle Self-Dev Harness - Auto-Évolution mLoop ({project_name})")
    
    # 1. Étape 1 : Diagnostic des composants et ponts MCP
    ZeroFluffConsole.step_s1("Self-Dev Audit", "Audit synchrone de l'écosystème mLoop...")
    from src.pipelines.calibrate import EcosystemCalibrator
    engine = EcosystemCalibrator(Path("."), project_name)
    is_success = engine.run_full_calibration()
    results = engine.report_matrix
    
    warn_or_fail = [r for r in results if r.get("status") in ["WARN", "FAIL"]]
    ZeroFluffConsole.info(f"Nombre d'anomalies détectées : {len(warn_or_fail)}")
    
    # 2. Étape 2 : Inspection des opportunités d'optimisation
    scratchpad_path = Path("memory") / "SELF_DEV_STATUS.md"
    scratchpad_path.parent.mkdir(parents=True, exist_ok=True)
    
    anomalies_str = "\n".join([f"- [{r.get('status')}] {r.get('name')}: {r.get('details')}" for r in results])
    scratchpad_content = f"""# Self-Dev Harness Status - {project_name}

**Status**: Active Self-Iteration Loop
**Anomalies détectées**: {len(warn_or_fail)}

## Matrice d'Étalonnage
{anomalies_str}

## Instructions d'Auto-Évolution (Exception de Développement mLoop)
1. **Périmètre sous `src/`** : L'agent mLoop est autorisé à corriger directement le code Python sous `src/` et `src/bridges/`.
2. **Validation** : Après toute modification, relancer `python src/swarm.py self-dev --project {project_name}` jusqu'à résolution des WARN/FAIL.
"""
    scratchpad_path.write_text(scratchpad_content, encoding="utf-8")
    ZeroFluffConsole.success(f"Rapport d'état consigné sous {scratchpad_path.name}")
    
    # 3. Étape 3 : Exécution de WikiFix
    try:
        from src.pipelines.wikifix import WikiFixAgent
        WikiFixAgent().execute(state)
        ZeroFluffConsole.success("Contrôle WikiFix validé avec succès.")
    except Exception as e:
        ZeroFluffConsole.warning(f"Note d'audit WikiFix lors du Self-Dev : {e}")

    ZeroFluffConsole.success("Pipeline Self-Dev terminé. Le framework mLoop est calibré pour l'auto-itération.")
