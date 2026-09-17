"""
Moteur de Restauration Point-in-Time Déterministe (ADR-0202, ADR-0369 & ADR-0371).
"""
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.state import LoopState, SavepointManager
from src.utils.logger import get_logger

logger = get_logger("agent_resilience.rollback")


class AgentStateRollbackEngine:
    """
    Moteur de Restauration Point-in-Time Déterministe (PITR) pour mLoop.
    """

    @staticmethod
    def _compute_sha256(filepath: Path) -> str:
        if not filepath.exists() or not filepath.is_file():
            return ""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def list_restore_points(
        cls, project_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        target_dir = SavepointManager.get_checkpoints_dir(project_path)
        checkpoints = sorted(
            target_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        points: List[Dict[str, Any]] = []
        for idx, cp in enumerate(checkpoints):
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                state_data = data.get("state", {})
                points.append({
                    "step": idx + 1,
                    "filename": cp.name,
                    "path": str(cp),
                    "timestamp": data.get("timestamp", int(cp.stat().st_mtime)),
                    "datetime_utc": data.get("datetime_utc", ""),
                    "reason": data.get("reason", "unknown"),
                    "phase": state_data.get("current_phase", "unknown"),
                    "sha256": cls._compute_sha256(cp),
                    "size_bytes": cp.stat().st_size,
                })
            except Exception as e:
                logger.debug(
                    "Impossible de lire le checkpoint",
                    exc_info=True,
                    extra={"checkpoint": cp.name, "error": str(e)},
                )
        return points

    @classmethod
    def verify_evidence_integrity(
        cls, project_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        base = project_path or Path(".")
        evidence_dir = base / "memory" / "evidence"
        if not evidence_dir.exists():
            return {"total": 0, "valid": 0, "corrupted": 0, "details": []}

        files = sorted(evidence_dir.glob("*_evidence.json"))
        valid_count = 0
        corrupted_count = 0
        details: List[Dict[str, Any]] = []

        for ef in files:
            sha = cls._compute_sha256(ef)
            try:
                with open(ef, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                has_ledger = "gate_execution_ledger" in payload
                valid_count += 1
                details.append({
                    "file": ef.name,
                    "status": "VALID",
                    "sha256": sha,
                    "has_ledger": has_ledger,
                })
            except Exception as e:
                corrupted_count += 1
                details.append({
                    "file": ef.name,
                    "status": "CORRUPTED",
                    "error": str(e),
                    "sha256": sha,
                })

        return {
            "total": len(files),
            "valid": valid_count,
            "corrupted": corrupted_count,
            "details": details,
        }

    @classmethod
    def rollback_to_step(
        cls,
        project_name: str,
        step: int,
        project_path: Optional[Path] = None,
        selective_partition: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_path = project_path or (Path("Projects") / project_name)
        points = cls.list_restore_points(target_path)
        if not points:
            return {"success": False, "error": "Aucun point de restauration disponible."}

        target_point = None
        for p in points:
            if p["step"] == step:
                target_point = p
                break

        if not target_point:
            return {
                "success": False,
                "error": f"Point de restauration étape {step} introuvable (disponibles: 1 à {len(points)}).",
            }

        cp_path = Path(target_point["path"])
        try:
            with open(cp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            restored_state = data.get("state", {})

            current_sha = cls._compute_sha256(cp_path)
            if current_sha != target_point["sha256"]:
                return {
                    "success": False,
                    "error": f"Corruption détectée : l'empreinte SHA-256 du checkpoint {cp_path.name} ne correspond pas.",
                }

            if selective_partition:
                partition_file = target_path / "memory" / f"{selective_partition}.json"
                if partition_file.exists():
                    backup_p = partition_file.with_suffix(".bak")
                    partition_file.rename(backup_p)

            state_obj = LoopState.load(project_name, project_path=target_path)
            for k, v in restored_state.items():
                if hasattr(state_obj, k) and k not in ("sprint_backlog", "knowledge_graph"):
                    try:
                        setattr(state_obj, k, v)
                    except Exception as e:
                        logger.debug(
                            "Attribut d'état non restauré",
                            exc_info=True,
                            extra={"field": k, "error": str(e)},
                        )
            state_obj.save(target_path)

            return {
                "success": True,
                "restored_step": step,
                "checkpoint_file": cp_path.name,
                "timestamp": target_point["timestamp"],
                "phase": target_point["phase"],
                "sha256": current_sha,
                "selective_partition": selective_partition,
            }
        except Exception as e:
            logger.error(
                "Échec du rollback",
                exc_info=True,
                extra={"project": project_name, "step": step, "error": str(e)},
            )
            return {"success": False, "error": str(e)}
