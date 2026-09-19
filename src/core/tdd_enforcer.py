"""
Protocole TDD Red-Green Enforcement et Verrouillage Gate 3 (MLOOP-082-BE / ADR-0381).
Scelle cryptographiquement l'échec initial (RedSnapshot) puis le succès intégral
(GreenSnapshot) dans l'EvidencePack pour interdire toute validation de récit sans preuve TDD.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

from src.core.ast_checker import check_file_ast

logger = logging.getLogger(__name__)


class MissingRedSnapshotError(RuntimeError):
    """Levée lorsqu'un sceau Green est tenté sans preuve Red préalable."""
    pass


class UnexpectedPassingTestError(RuntimeError):
    """Levée lorsque le banc de test passe au vert dès la phase Red initiale."""
    pass


class TestFailureError(RuntimeError):
    """Levée lorsque les tests échouent lors de la tentative de scellement Green."""
    __test__ = False



class AstViolationError(RuntimeError):
    """Levée lorsque le code viole les règles AST lors du scellement Green."""
    pass


@dataclass
class RedSnapshot:
    """Empreinte immuable de l'échec initial du test."""
    story_id: str
    test_file: str
    test_sha256: str
    exit_code: int
    failure_signature: str
    timestamp_utc: str


@dataclass
class GreenSnapshot:
    """Empreinte immuable du succès final du code et des tests."""
    story_id: str
    test_file: str
    test_sha256: str
    source_file: str
    source_sha256: str
    exit_code: int
    duration_seconds: float
    ast_passed: bool
    timestamp_utc: str


def _sha256_file(path: Path) -> str:
    """Calcule le hachage SHA-256 d'un fichier."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _now_iso() -> str:
    """Renvoie l'horodatage UTC ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


class TddEnforcer:
    """Moteur de vérification et scellement du cycle TDD Red-Green."""

    def __init__(self) -> None:
        pass

    def record_red(
        self,
        story_id: str,
        test_file: Path,
        evidence_path: Optional[Path] = None,
    ) -> RedSnapshot:
        """Exécute les tests avant implémentation et scelle l'échec initial obligatoire."""
        test_path = Path(test_file)
        if not test_path.exists():
            raise FileNotFoundError(f"Banc de test introuvable : {test_file}")

        env = os.environ.copy()
        repo_root = str(Path.cwd().resolve())
        target_dir = str(test_path.parent.resolve())
        env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{target_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

        res = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path.resolve()), "-q"],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if res.returncode == 0:
            raise UnexpectedPassingTestError(
                f"Le test {test_file} a réussi dès la phase RED. "
                "Un test TDD valide doit obligatoirement échouer avant l'écriture du code de production."
            )

        test_sha = _sha256_file(test_path)
        sig = (res.stderr or res.stdout).strip().splitlines()[-1] if (res.stderr or res.stdout) else "Failure"

        snapshot = RedSnapshot(
            story_id=story_id,
            test_file=test_path.as_posix(),
            test_sha256=test_sha,
            exit_code=res.returncode,
            failure_signature=sig[:200],
            timestamp_utc=_now_iso(),
        )

        if evidence_path:
            self._save_evidence_snapshot(evidence_path, "red", asdict(snapshot))

        return snapshot

    def record_green(
        self,
        story_id: str,
        test_file: Path,
        source_file: Path,
        evidence_path: Optional[Path] = None,
    ) -> GreenSnapshot:
        """Valide et scelle le succès complet (tests 100% verts + 0 violation AST)."""
        test_path = Path(test_file)
        src_path = Path(source_file)

        if not test_path.exists():
            raise FileNotFoundError(f"Banc de test introuvable : {test_file}")
        if not src_path.exists():
            raise FileNotFoundError(f"Fichier source introuvable : {source_file}")

        # 1. Vérifier la présence préalable du RedSnapshot
        if evidence_path and evidence_path.exists():
            try:
                with open(evidence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                tdd_cycle = data.get("tdd_cycle", {})
                if not tdd_cycle.get("red"):
                    raise MissingRedSnapshotError(
                        f"Aucun RedSnapshot scellé pour {story_id} dans {evidence_path}. "
                        "Le cycle TDD impose une preuve d'échec initial avant tout succès Green."
                    )
            except (json.JSONDecodeError, OSError) as e:
                logger.debug("Erreur lecture evidence : %s", e, exc_info=True)
                raise MissingRedSnapshotError("Fichier d'évidence corrompu ou illisible.")
        elif evidence_path:
            raise MissingRedSnapshotError(f"Fichier d'évidence absent : {evidence_path}")

        # 2. Hard Gate AST sur le code source
        ast_rep = check_file_ast(src_path)
        if not ast_rep.passed:
            reasons = "; ".join(f"[{v.rule_id}] {v.message}" for v in ast_rep.violations)
            raise AstViolationError(
                f"Le code de production {source_file} enfreint les règles AST : {reasons}"
            )

        # 3. Exécution Pytest
        env = os.environ.copy()
        repo_root = str(Path.cwd().resolve())
        target_dir = str(src_path.parent.resolve())
        env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{target_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

        t0 = time.perf_counter()
        res = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path.resolve()), "-q"],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        duration = time.perf_counter() - t0

        if res.returncode != 0:
            raise TestFailureError(
                f"Échec des tests pour le scellement GREEN ({test_file}) : {res.stderr or res.stdout}"
            )

        snapshot = GreenSnapshot(
            story_id=story_id,
            test_file=test_path.as_posix(),
            test_sha256=_sha256_file(test_path),
            source_file=src_path.as_posix(),
            source_sha256=_sha256_file(src_path),
            exit_code=0,
            duration_seconds=round(duration, 3),
            ast_passed=True,
            timestamp_utc=_now_iso(),
        )

        if evidence_path:
            self._save_evidence_snapshot(evidence_path, "green", asdict(snapshot))

        return snapshot

    def verify_gate_3_compliance(
        self,
        story_id: str,
        evidence_path: Optional[Path] = None,
    ) -> bool:
        """Vérifie si le récit dispose du couple complet et intègre (RedSnapshot, GreenSnapshot)."""
        if not evidence_path or not evidence_path.exists():
            return False

        try:
            with open(evidence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tdd_cycle = data.get("tdd_cycle", {})
            red = tdd_cycle.get("red")
            green = tdd_cycle.get("green")
            if not red or not green:
                return False
            red_sid = red.get("story_id") or data.get("story_id")
            green_sid = green.get("story_id") or data.get("story_id")
            if red_sid != story_id or green_sid != story_id:
                return False
            return True
        except Exception as e:
            logger.debug("Erreur lecture conformité Gate 3 : %s", e, exc_info=True)
            return False

    def _save_evidence_snapshot(self, evidence_path: Path, phase: str, snapshot_dict: dict[str, Any]) -> None:
        """Persiste le snapshot dans le bloc tdd_cycle du fichier d'évidence JSON."""
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {}
        if evidence_path.exists():
            try:
                with open(evidence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.debug("Lecture fichier evidence existant échouée : %s", e, exc_info=True)

        if "tdd_cycle" not in data or not isinstance(data["tdd_cycle"], dict):
            data["tdd_cycle"] = {}
        data["tdd_cycle"][phase] = snapshot_dict

        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def format_tdd_status(red: Optional[RedSnapshot], green: Optional[GreenSnapshot]) -> str:
    """Formate le statut TDD pour affichage console."""
    lines = ["=== PROTOCOLE TDD ENFORCER (ADR-0381) ==="]
    if red:
        lines.append(f"  [RED] Sceau validé | {red.story_id} | Test SHA: {red.test_sha256[:12]}... | Échec certifié")
    else:
        lines.append("  [RED] ❌ Non scellé (Échec initial manquant)")

    if green:
        lines.append(f"  [GREEN] Sceau validé | {green.story_id} | Code SHA: {green.source_sha256[:12]}... | Tests 100% verts & AST OK")
    else:
        lines.append("  [GREEN] ⏳ En attente de réalisation du code")

    gate3_ready = "OUI (Prêt pour approbation)" if (red and green) else "NON (Verrouillé)"
    lines.append(f"Conformité Gate 3 : {gate3_ready}")
    return "\n".join(lines)
