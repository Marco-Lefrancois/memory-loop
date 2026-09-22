"""
shadow_estimator.py - Shadow Estimator & Contradictory Risk Challenger (ADR-0346)

Dispatches a Red-Team validation worker to analyze an Epic/SOW, formulating
a pessimistic, risk-grounded counter-estimate to eliminate over-optimism and blindspots.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional

from src.cli import ZeroFluffConsole
from src.core.herdr_adapter import herdr
from src.utils.logger import get_logger

logger = get_logger("pipelines.delegation.shadow_estimator")


def run_shadow_estimator(
    project_name: str,
    target_id: str,
    scope_description: Optional[str] = None,
    timeout_sec: int = 150,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Executes a contradictory risk-based shadow estimation on an Epic, Feature, or SOW.
    """
    ZeroFluffConsole.section(f"SHADOW ESTIMATOR & RISK CHALLENGER — {target_id}")

    proj_dir = Path.cwd() / "Projects" / project_name
    if not proj_dir.exists() and (Path.cwd() / "memory").exists():
        proj_dir = Path.cwd()

    plan_dir = proj_dir / "memory" / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    out_file = plan_dir / f"shadow_estimation_{target_id.lower().replace('-', '_')}.json"

    ZeroFluffConsole.info(f"Cible d'estimation : {target_id}")
    ZeroFluffConsole.info(f"Rapport de contre-expertise : {out_file.name}")

    if dry_run:
        sample_data = {
            "target_id": target_id,
            "baseline_estimate_days": 5,
            "shadow_estimate_days": 9,
            "variance_ratio": 1.8,
            "identified_risks": [
                "Latence et rate-limiting sur l'API externe tierce",
                "Gestion complexe des tokens refresh et sessions expirées",
                "Migrations de schémas de données asynchrones sans downtime"
            ],
            "recommendations": "Prévoir un Spike technique préalable sur le SDK d'authentification."
        }
        out_file.write_text(json.dumps(sample_data, indent=2, ensure_ascii=False), encoding="utf-8")
        ZeroFluffConsole.info("[Dry Run] Contre-estimation simulée rédigée avec succès.")
        return {"success": True, "status": "ESTIMATION_COMPLETED", "data": sample_data}

    # 1. Spawn Red-Team worker (GPT-5.6 Terra Thinking)
    worker_name = f"worker_shadow_{target_id.lower().replace('-', '_')}"[:32]
    split_res = herdr.split_pane(target_pane_id="p1", direction="right", no_focus=True)
    pane_id = split_res.get("new_pane_id") or "p_shadow"

    herdr.start_agent(
        agent_name=worker_name,
        kind="opencode",
        pane_id=str(pane_id),
        extra_args=["--yolo", "--model", "nmedia_cloud/gpt-5.6-terra-thinking"]
    )

    # 2. Formulate Prompt
    prompt_text = (
        f"## MISSION : SHADOW ESTIMATOR & CONTRADICTORY RISK CHALLENGE\n\n"
        f"**Cible** : {target_id}\n"
        f"**Description / Contexte** : {scope_description or 'Analyse des récits et dépendances du sprint'}\n"
        f"**Fichier de sortie** : `{out_file.resolve()}`\n\n"
        f"### Consignes d'audit contradictoire :\n"
        f"1. Prends le rôle d'un auditeur technique intransigeant et pessimiste.\n"
        f"2. Identifie tous les points de défaillance uniques, contraintes réseau, dépendances bloquantes et edge-cases.\n"
        f"3. Rédige un rapport JSON dans `{out_file.resolve()}` avec :\n"
        f"   - target_id\n"
        f"   - baseline_estimate_days (estimation optimiste de base)\n"
        f"   - shadow_estimate_days (contre-estimation réaliste avec marges de risque)\n"
        f"   - variance_ratio\n"
        f"   - identified_risks (liste de 3 à 5 risques techniques précis)\n"
        f"   - recommendations (actions de mitigation / spikes recommandés)\n"
        f"4. Termine par `[ESTIMATION_COMPLETED]`.\n"
    )

    herdr.prompt_agent(worker_name, prompt_text, wait=True, timeout_ms=timeout_sec * 1000)

    # 3. Harvest & Teardown
    read_res = herdr.read_agent_output(worker_name, lines=60, source="recent-unwrapped")
    cleaned_logs = herdr.filter_terminal_bloat(read_res.get("raw_output") or "")
    herdr.cleanup_worker(worker_name)

    result_data = {}
    if out_file.exists():
        try:
            result_data = json.loads(out_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(
                "Résultat de contre-estimation illisible, sortie vide utilisée",
                exc_info=True,
                extra={
                    "component": "pipelines.delegation.shadow_estimator",
                    "operation": "read_shadow_result",
                    "error": str(e),
                },
            )

    ZeroFluffConsole.success(f"Contre-estimation complétée : {result_data.get('shadow_estimate_days', 'N/A')} j (vs {result_data.get('baseline_estimate_days', 'N/A')} j).")
    herdr.show_notification(
        title="🕵️ Shadow Estimation Prête",
        body=f"Target: {target_id} | Risques majeurs consignés dans {out_file.name}",
        sound="done"
    )

    return {
        "success": True,
        "status": "ESTIMATION_COMPLETED",
        "output_file": str(out_file),
        "data": result_data,
        "summary": cleaned_logs[-300:] if len(cleaned_logs) > 300 else cleaned_logs
    }
