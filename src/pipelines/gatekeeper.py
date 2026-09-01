"""
mLoop Pipeline - Gatekeeper (CLI Pipeline for Runnable Gates & Depth Tree)
Standard : ADR-0341
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from src.core.gates import (
    GateLedger,
    LedgerStatus,
    lint_ledger,
    parse_gates,
    render_depth_tree_visual,
    verify_ledger,
)
class GatekeeperPipeline:
    """Pipeline d'orchestration et d'exécution des Runnable Gates."""

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()

    def execute(
        self,
        file_path: Optional[str] = None,
        mode: str = "verify",
        reverify: bool = False,
        lint: bool = False,
        scope: Optional[str] = None,
    ) -> int:
        """Point d'entrée d'exécution du pipeline Gatekeeper."""
        print("\n=== MLOOP GATEKEEPER & DEPTH TREE RUNNER (ADR-0341) ===")

        target_files = self._resolve_target_files(file_path, scope)
        if not target_files:
            print("[!] Aucun fichier de gates (.gates.md ou GATES.md) trouvé pour ce périmètre.")
            return 1

        total_files = len(target_files)
        all_passed = True
        handoff_any = False

        workspace_root = Path.cwd() if (Path.cwd() / "src").exists() else (self.project_path.parent.parent if (self.project_path.parent.parent / "src").exists() else self.project_path)

        for target in target_files:
            print(f"\n--- Examen du Grand Livre : {target.relative_to(self.project_path) if target.is_relative_to(self.project_path) else target} ---")
            raw_text = target.read_text(encoding="utf-8")
            ledger = parse_gates(raw_text, file_path=target)

            if not ledger.is_valid:
                print(f"[!] Erreurs de syntaxe strictes dans '{target.name}' :")
                for err in ledger.errors:
                    print(f"    - ❌ {err}")
                all_passed = False
                continue

            if lint:
                issues = lint_ledger(ledger)
                if not issues:
                    print(f"✔ [LINT OK] Aucune anomalie d'oracle détectée dans '{target.name}'.")
                else:
                    print(f"[!] {len(issues)} avertissement(s) de linting détecté(s) :")
                    for iss in issues:
                        badge = "❌" if iss.severity == "ERROR" else "⚠️"
                        print(f"    - {badge} [Ligne {iss.line_no}] {iss.gate_id}: {iss.message}")
                    if any(i.severity == "ERROR" for i in issues):
                        all_passed = False

            if mode == "status":
                status = verify_ledger(ledger, root_dir=workspace_root, reverify=False, update_file=False)
            else:
                status = verify_ledger(ledger, root_dir=workspace_root, reverify=reverify, update_file=True)
                self._update_evidence_pack(target, status)

            # Rendu visuel
            visual_tree = render_depth_tree_visual(
                title=ledger.title,
                status=status,
                scope=ledger.scope or scope or "default",
                owns=ledger.owns,
            )
            print(visual_tree)

            if not status.all_met:
                all_passed = False
            if status.handoff_required:
                handoff_any = True

        if handoff_any:
            print("\n[!] ⛔ HANDOFF REQUIRED : Au moins une gate requise a été abandonnée avec restitution obligatoire.")
            return 1

        if not all_passed:
            print("\n[!] ⚠️ Des portails sont encore PENDING ou FAILED.")
            return 1

        print("\n✔ ALL MET : Tous les portails d'acceptation sont validés avec empreinte cryptographique.")
        return 0

    def _resolve_target_files(self, file_path: Optional[str], scope: Optional[str]) -> List[Path]:
        """Localise les fichiers de gates à évaluer."""
        if file_path:
            p = Path(file_path)
            if not p.is_absolute():
                p = self.project_path / p
            if p.exists():
                return [p]
            return []

        candidates: List[Path] = []
        gates_dir = self.project_path / "backlog" / "gates"
        if gates_dir.exists():
            candidates.extend(gates_dir.rglob("*.gates.md"))
            candidates.extend(gates_dir.rglob("*.md"))

        root_gates = self.project_path / "GATES.md"
        if root_gates.exists():
            candidates.append(root_gates)

        if scope:
            candidates = [c for c in candidates if scope.lower() in c.name.lower()]

        return sorted(list(set(candidates)))

    def _update_evidence_pack(self, target_file: Path, status: LedgerStatus) -> None:
        """Injecte l'empreinte des gates dans le sidecar EvidencePack JSON."""
        stem = target_file.stem.replace(".gates", "")
        evidence_dir = self.project_path / "memory" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if target_file is in a subfolder under backlog/gates
        rel_sub = ""
        try:
            rel_sub = target_file.relative_to(self.project_path / "backlog" / "gates").parent
        except Exception:
            rel_sub = Path(".")
            
        target_ev_dir = evidence_dir / rel_sub if rel_sub != Path(".") else evidence_dir
        target_ev_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if existing evidence file exists recursively
        existing_matches = list(evidence_dir.rglob(f"{stem}_evidence.json"))
        evidence_file = existing_matches[0] if existing_matches else (target_ev_dir / f"{stem}_evidence.json")

        data = {}
        if evidence_file.exists():
            try:
                data = json.loads(evidence_file.read_text(encoding="utf-8"))
            except Exception:
                data = {}

        data["gate_execution_ledger"] = {
            "source_file": target_file.name,
            "status": "ALL_MET" if status.all_met else ("HANDOFF_REQUIRED" if status.handoff_required else "IN_PROGRESS"),
            "total_gates": status.total_gates,
            "met_gates": status.met_gates,
            "gates": [
                {
                    "id": r.gate_id,
                    "title": r.title,
                    "passed": r.passed,
                    "exit_code": r.exit_code,
                    "output_digest": r.output_digest,
                    "output_bytes": r.output_bytes,
                    "path_fingerprint": r.path_fingerprint,
                    "abandon_reason": r.abandon_reason,
                    "duration_ms": round(r.duration_ms, 2),
                }
                for r in status.results
            ],
        }

        evidence_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
