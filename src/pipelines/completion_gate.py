"""
Completion & Non-Degeneracy Gate (ADR-0352 / HarnessDev).
Évite les pièges des créateurs autonomes :
- 441 soumissions dégénérées non détectées dans HarnessDev.
- Diff vide ou simulation passive avec affirmation trompeuse de succès.
- Détection des stubs (TODO, pass, NotImplementedError).
- Émission du statut DEGENERATE_CANDIDATE exigeant confirmation HITL.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Set
import re

class GateStatus(str, Enum):
    PASS = "PASS"
    DEGENERATE_CANDIDATE = "DEGENERATE_CANDIDATE"
    FAIL = "FAIL"

class HandoffEvidencePolicy(str, Enum):
    """
    Politique de preuve d'effort lors du Handoff (ADR-0355, inspiré de Sortie).
    - OBSERVED : Refuse si absence formelle de changement constatée; accepte si indéterminable.
    - STRICT   : Refuse si absence ou si indéterminable.
    - OFF      : Aucune vérification d'évidence physique.
    """
    OBSERVED = "observed"
    STRICT = "strict"
    OFF = "off"

@dataclass
class CompletionGateResult:
    status: GateStatus
    is_degenerate: bool
    requires_hitl: bool
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    patch_stats: dict = field(default_factory=dict)

class CompletionGate:
    """
    Gatekeeper d'intégrité des livrables et patchs.
    Conforme aux enseignements HarnessDev et au standard HITL validé par l'utilisateur.
    """

    STUB_PATTERNS = [
        re.compile(r'^\s*pass\s*$', re.MULTILINE),
        re.compile(r'raise\s+NotImplementedError', re.IGNORECASE),
        re.compile(r'#\s*(TODO|FIXME|XXX)\b', re.IGNORECASE),
        re.compile(r'//\s*(TODO|FIXME|XXX)\b', re.IGNORECASE),
    ]

    @classmethod
    def validate_patch(
        cls,
        patch_text: str,
        claimed_status: str = "success",
        allow_empty_if_docs: bool = False
    ) -> CompletionGateResult:
        """
        Valide un diff de code source ou un artefact de patch.
        """
        reasons = []
        warnings = []
        
        # 1. Vérification de patch vide
        clean_patch = patch_text.strip()
        patch_chars = len(clean_patch)
        
        added_lines = [l for l in clean_patch.splitlines() if l.startswith("+") and not l.startswith("+++")]
        removed_lines = [l for l in clean_patch.splitlines() if l.startswith("-") and not l.startswith("---")]
        
        stats = {
            "patch_chars": patch_chars,
            "added_lines": len(added_lines),
            "removed_lines": len(removed_lines),
            "claimed_status": claimed_status
        }
        
        if patch_chars == 0 or len(added_lines) == 0:
            if claimed_status.lower() in ("success", "done", "complete"):
                reasons.append("Patch vide ou sans ajout réel alors que le statut revendique 'success' (Faux positif).")
        
        # 2. Détection des stubs sur les lignes ajoutées
        added_text = "\n".join(added_lines)
        stub_hits = []
        for pattern in cls.STUB_PATTERNS:
            matches = pattern.findall(added_text)
            if matches:
                stub_hits.extend(matches)
                
        if stub_hits:
            warnings.append(f"Détection de {len(stub_hits)} stub(s) / placeholder(s) non résolu(s) dans le code ajouté.")
            
        # 3. Ratio de suppression destructive
        if len(removed_lines) > 50 and len(added_lines) < 5:
            warnings.append(f"Ratio de suppression asymétrique suspect : {len(removed_lines)} lignes supprimées pour seulement {len(added_lines)} ajoutées.")

        # 4. Décision de Gate (HITL vs PASS vs FAIL)
        if reasons:
            return CompletionGateResult(
                status=GateStatus.DEGENERATE_CANDIDATE,
                is_degenerate=True,
                requires_hitl=True,
                reasons=reasons,
                warnings=warnings,
                patch_stats=stats
            )
        elif warnings:
            return CompletionGateResult(
                status=GateStatus.DEGENERATE_CANDIDATE,
                is_degenerate=True,
                requires_hitl=True,
                reasons=["Anomalies potentielles détectées nécessitant validation HITL."],
                warnings=warnings,
                patch_stats=stats
            )
        else:
            return CompletionGateResult(
                status=GateStatus.PASS,
                is_degenerate=False,
                requires_hitl=False,
                reasons=[],
                warnings=[],
                patch_stats=stats
            )

    @classmethod
    def validate_story_coverage(
        cls,
        story_path: Path | str,
        project_name: str,
        db_path: Optional[Path] = None,
        min_coverage_ratio: float = 0.5,
    ) -> CompletionGateResult:
        """
        Valide la couverture factuelle d'une User Story via FactSearchCoverageEvaluator.
        Si le ratio est inférieur au seuil ou si des critères critiques n'ont aucune preuve SSOT,
        émet un statut DEGENERATE_CANDIDATE exigeant confirmation HITL.
        """
        from src.engine.fact_search.coverage import FactSearchCoverageEvaluator

        coverage_data = FactSearchCoverageEvaluator.evaluate_story_coverage(
            story_path=story_path,
            project_name=project_name,
            db_path=db_path,
        )

        ratio = coverage_data.get("coverage_ratio", 0.0)
        total = coverage_data.get("total_criteria", 0)
        covered = coverage_data.get("covered_criteria", 0)
        uncovered = coverage_data.get("uncovered", [])
        proofs = coverage_data.get("proofs", [])

        stats = {
            "story_path": str(story_path),
            "project_name": project_name,
            "coverage_ratio": ratio,
            "total_criteria": total,
            "covered_criteria": covered,
            "uncovered_count": len(uncovered),
            "proofs_count": len(proofs),
        }

        reasons = []
        warnings = []

        # Synthèse d'Aveu des Limites (ADR-0353 / The New Stack)
        if uncovered:
            admission_of_limits = (
                f"⚠️ LIMITES DE PREUVE : {covered}/{total} critère(s) étayés. "
                f"{len(uncovered)} critère(s) sans ancrage SSOT (exige arbitrage HITL)."
            )
        else:
            admission_of_limits = f"✅ Preuves complètes : {total}/{total} critère(s) couverts par le SSOT."
        stats["admission_of_limits"] = admission_of_limits

        if total > 0 and ratio < min_coverage_ratio:
            reasons.append(
                f"Couverture factuelle insuffisante ({ratio:.0%} < seuil {min_coverage_ratio:.0%}) : "
                f"{len(uncovered)}/{total} critère(s) sans preuve SSOT déterministe."
            )

        if uncovered:
            sample = [c[:80] + "..." if len(c) > 80 else c for c in uncovered[:3]]
            warnings.append(admission_of_limits)
            warnings.append(
                f"{len(uncovered)} critère(s) non documenté(s) dans le SSOT documentaire : "
                + "; ".join(sample)
            )

        if reasons:
            return CompletionGateResult(
                status=GateStatus.DEGENERATE_CANDIDATE,
                is_degenerate=True,
                requires_hitl=True,
                reasons=reasons,
                warnings=warnings,
                patch_stats=stats,
            )
        elif warnings:
            is_partial = ratio < 0.8
            return CompletionGateResult(
                status=GateStatus.DEGENERATE_CANDIDATE if is_partial else GateStatus.PASS,
                is_degenerate=is_partial,
                requires_hitl=is_partial,
                reasons=["Critères fonctionnels non sourcés nécessitant validation HITL."] if is_partial else [],
                warnings=warnings,
                patch_stats=stats,
            )
        else:
            return CompletionGateResult(
                status=GateStatus.PASS,
                is_degenerate=False,
                requires_hitl=False,
                reasons=[],
                warnings=[],
                patch_stats=stats,
            )

    @classmethod
    def validate_workspace_evidence(
        cls,
        project_path: Path | str,
        story_id: str,
        spawn_timestamp: Optional[float] = None,
        policy: HandoffEvidencePolicy = HandoffEvidencePolicy.OBSERVED,
        signal: Optional[Any] = None,
    ) -> CompletionGateResult:
        """
        Valide l'existence d'une preuve d'effort physique (fichiers modifiés/créés)
        avant d'autoriser le Handoff ou la complétion du worker (ADR-0355).
        """
        if policy == HandoffEvidencePolicy.OFF:
            return CompletionGateResult(
                status=GateStatus.PASS,
                is_degenerate=False,
                requires_hitl=False,
                reasons=[],
                warnings=["Politique d'évidence Handoff désactivée (mode 'off')."],
                patch_stats={"policy": policy.value}
            )

        # 1. Vérification d'un signal explicite 'NO_CHANGE_NEEDED'
        sig_type = getattr(signal, "signal_type", None)
        sig_value = getattr(sig_type, "value", str(sig_type)) if sig_type else ""
        if sig_value == "NO_CHANGE_NEEDED":
            reason_msg = getattr(signal, "reason", "Déclaration explicite sans changement")
            return CompletionGateResult(
                status=GateStatus.PASS,
                is_degenerate=False,
                requires_hitl=False,
                reasons=[],
                warnings=[f"Déclaration explicite 'NO_CHANGE_NEEDED' retenue : {reason_msg}"],
                patch_stats={"policy": policy.value, "declared_no_change": True}
            )

        # 2. Vérification d'un signal 'BLOCKED'
        if sig_value == "BLOCKED":
            reason_msg = getattr(signal, "reason", "Worker bloqué")
            return CompletionGateResult(
                status=GateStatus.FAIL,
                is_degenerate=True,
                requires_hitl=True,
                reasons=[f"Worker bloqué : {reason_msg}"],
                warnings=[],
                patch_stats={"policy": policy.value, "signal": "BLOCKED"}
            )

        # 3. Inspection des fichiers cibles
        proj_dir = Path(project_path)
        clean_id = story_id.replace("\\", "/").split("/")[-1].replace(".md", "")
        
        candidates = [
            proj_dir / "backlog" / "stories" / f"{clean_id}.md",
            proj_dir / "memory" / "evidence" / f"{clean_id}_evidence.json",
            proj_dir / "memory" / "plan" / f"implementation_plan_{clean_id}.md",
        ]

        modified_files = []
        for file_path in candidates:
            if file_path.is_file() and file_path.stat().st_size > 0:
                mtime = file_path.stat().st_mtime
                if spawn_timestamp is None or mtime >= (spawn_timestamp - 2.0):  # 2s margin for clock skew
                    modified_files.append((str(file_path), file_path.stat().st_size))

        stats = {
            "policy": policy.value,
            "target_story": story_id,
            "modified_candidates_count": len(modified_files),
            "modified_files": [f[0] for f in modified_files],
        }

        # 4. Décision selon la politique
        if not modified_files:
            if policy in (HandoffEvidencePolicy.OBSERVED, HandoffEvidencePolicy.STRICT):
                return CompletionGateResult(
                    status=GateStatus.DEGENERATE_CANDIDATE,
                    is_degenerate=True,
                    requires_hitl=True,
                    reasons=[
                        f"Aucune preuve d'effort physique observée pour {story_id} "
                        f"(aucun fichier cible modifié ou généré post-spawn). Handoff refusé."
                    ],
                    warnings=["Vérifier si l'agent a rencontré un blocage silencieux ou a omis de persister."],
                    patch_stats=stats
                )

        return CompletionGateResult(
            status=GateStatus.PASS,
            is_degenerate=False,
            requires_hitl=False,
            reasons=[],
            warnings=[],
            patch_stats=stats
        )

