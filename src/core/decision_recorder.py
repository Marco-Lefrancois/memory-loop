"""
Moteur de capture automatique des décisions d'implémentation et citations ancrées
dans l'EvidencePack (MLOOP-181-BE / EPIC-18 Phase 3 Build).

Points de capture branchés (schema MLOOP-180-BE) :
  - CA-1 : tournoi multi-draft -> décision `architecture` (arbitrage Pareto)
  - CA-2 : cycle TDD red-green -> décision `testing` par cycle complet
  - CA-3 : hook public `record_decision()` avec dédoublonnage hash category+rationale
  - CA-4 : extraction citations hybride D depuis le diff git (1/fichier, ancrage [start, end] réel)
  - CA-5 : contrats déclaratifs — route inconnue -> `[API de soumission à définir]` + OQ (zéro invention)
  - CA-6 : horodatage UTC ISO 8601 + alternatives_considered systématiques
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger("core.decision_recorder")

CONTRACT_TO_DEFINE = "[API de soumission à définir]"

_ALLOWED_CATEGORIES = {
    "architecture",
    "pattern",
    "refactoring",
    "performance",
    "security",
    "tooling",
    "testing",
}


# Re-export canonique (CA-4) : la classe unique lève depuis CitationExtractor.
from src.core.citation_extractor import CitationExtractionError  # noqa: F401


class DecisionRecorder:
    """Hook public de capture des décisions/citations/contrats vers l'EvidencePack."""

    def __init__(self, project_path: Path) -> None:
        self.project_path = Path(project_path).resolve()

    # ── Utilitaires internes ─────────────────────────────────────────────────

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _decision_hash(category: str, rationale: str) -> str:
        raw = f"{category}::{rationale.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _load_pack(self, evidence_path: Path) -> Dict[str, Any]:
        """Charge le pack existant ou crée une structure minimale (résilience)."""
        if evidence_path.exists():
            try:
                with open(evidence_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.debug(
                    "EvidencePack illisible, régénération d'une structure minimale",
                    exc_info=True,
                    extra={
                        "component": "core.decision_recorder",
                        "operation": "_load_pack",
                        "path": str(evidence_path),
                        "error": str(e),
                    },
                )
        return {"implementation_decisions": [], "declarative_contracts": [], "alerts": []}

    def _save_pack(self, evidence_path: Path, data: Dict[str, Any]) -> None:
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(evidence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ── CA-3 : Hook public record_decision ───────────────────────────────────

    def record_decision(
        self,
        story_id: str,
        evidence_path: Path,
        category: str,
        rationale: str,
        alternatives_considered: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Enregistre une décision d'implémentation dans le pack (CA-3, CA-6).

        Dédoublonnage par hash sha256(category+rationale) : une décision
        identique est skippée avec log DEBUG 'duplicate_decision_skipped'.

        Raises:
            ValueError: catégorie hors liste fermée (fail-closed, ADR-0369).
        """
        if category not in _ALLOWED_CATEGORIES:
            raise ValueError(
                f"[MLOOP-181-BE] Catégorie hors liste fermée : {category!r}. "
                f"Autorisées : {sorted(_ALLOWED_CATEGORIES)}"
            )

        data = self._load_pack(evidence_path)
        decisions: List[Dict[str, Any]] = data.setdefault("implementation_decisions", [])
        d_hash = self._decision_hash(category, rationale)
        if any(d.get("decision_id") == f"DEC-{d_hash}" for d in decisions):
            logger.debug(
                "duplicate_decision_skipped",
                extra={
                    "component": "core.decision_recorder",
                    "operation": "record_decision",
                    "story_id": story_id,
                    "decision_hash": d_hash,
                },
            )
            return decisions[-1]

        decision = {
            "decision_id": f"DEC-{d_hash}",
            "category": category,
            "rationale": rationale,
            "alternatives_considered": list(alternatives_considered or []),
            "timestamp": self._now_iso(),
        }
        decisions.append(decision)
        self._save_pack(evidence_path, data)
        return decision

    # ── CA-1 : Capture tournoi multi-draft ───────────────────────────────────

    def record_tournament_decision(
        self,
        evidence_path: Path,
        story_id: str,
        winner_id: str,
        winner_pareto_score: float,
        losers: List[Tuple[str, float]],
    ) -> Dict[str, Any]:
        """Convertit l'arbitrage Pareto du tournoi en décision `architecture` (CA-1)."""
        alternatives = [f"{cid} (rejeté: score {score})" for cid, score in losers]
        return self.record_decision(
            story_id=story_id,
            evidence_path=evidence_path,
            category="architecture",
            rationale=(
                f"Arbitrage Pareto : {winner_id} promu Golden Master "
                f"(score Pareto retenu : {winner_pareto_score})"
            ),
            alternatives_considered=alternatives,
        )

    # ── CA-2 : Capture cycle TDD ─────────────────────────────────────────────

    def record_tdd_cycle_decision(
        self,
        evidence_path: Path,
        story_id: str,
        test_file: str,
        red_exit_code: int,
        green_exit_code: int,
    ) -> Dict[str, Any]:
        """Une décision `testing` par cycle complet red-green (CA-2, Grill Déc. 2)."""
        return self.record_decision(
            story_id=story_id,
            evidence_path=evidence_path,
            category="testing",
            rationale=(
                f"Cycle TDD complet scellé (red exit={red_exit_code} -> green exit={green_exit_code}) "
                f"sur {test_file}"
            ),
            alternatives_considered=[
                "test unitaire isolé (rejeté: granularité par cycle complet retenue, Grill Déc. 2)"
            ],
        )

    # ── CA-4 : Extraction citations (délégation CitationExtractor) ───────────

    def extract_citations_from_diff(
        self,
        story_id: str,
        timeout: float = 30.0,
        max_files: int = 20,
        return_warnings: bool = False,
        evidence_path: Optional[Path] = None,
    ):
        """
        Extraction hybride D (CA-4) déléguée à `CitationExtractor`.

        Raises:
            CitationExtractionError: si git échoue (dépôt invalide, timeout subprocess).
        """
        from src.core.citation_extractor import CitationExtractionError, CitationExtractor

        extractor = CitationExtractor(project_path=self.project_path)
        return extractor.extract_citations_from_diff(
            story_id=story_id,
            timeout=timeout,
            max_files=max_files,
            return_warnings=return_warnings,
            evidence_path=evidence_path,
        )

    # ── CA-5 : Contrats déclaratifs (Zéro Fausse Route) ──────────────────────

    def record_contract(
        self,
        story_id: str,
        evidence_path: Path,
        project_path: Path,
        method: str,
        path: Optional[str] = None,
        hint: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Optional[Path]]:
        """
        Enregistre un contrat déclaratif dans le pack (CA-5 — Zéro Fausse Route).

        Route inconnue (aucun `path`) -> '[API de soumission à définir]' avec
        `status: to_define` et consignation d'une OQ-XXX sous docs/04-transverse/.
        Aucune URI n'est jamais inventée.

        Returns:
            (contrat, chemin_OQ_ou_None)
        """
        known = bool(path and str(path).strip())
        contract: Dict[str, Any] = {
            "method": method if known else "N/A",
            "path": path if known else CONTRACT_TO_DEFINE,
            "status": "defined" if known else "to_define",
            "source": source or f"build:{story_id}",
        }

        data = self._load_pack(evidence_path)
        contracts: List[Dict[str, Any]] = data.setdefault("declarative_contracts", [])
        c_hash = hashlib.sha256(
            f"{contract['method']}::{contract['path']}".encode("utf-8")
        ).hexdigest()[:16]
        if not any(c.get("path") == contract["path"] and c.get("method") == contract["method"]
                   for c in contracts):
            contracts.append(contract)
            self._save_pack(evidence_path, data)

        oq_path: Optional[Path] = None
        if not known:
            oq_path = self._write_open_question(
                project_path=project_path, story_id=story_id, hint=hint or path or "",
                method=method,
            )
        return contract, oq_path

    def _write_open_question(
        self, project_path: Path, story_id: str, hint: str, method: str
    ) -> Path:
        """Consigne une OQ-XXX déterministe sous docs/04-transverse/ (CA-5)."""
        oq_dir = Path(project_path) / "docs" / "04-transverse"
        oq_dir.mkdir(parents=True, exist_ok=True)

        existing = sorted(oq_dir.glob("OQ-*.md"))
        max_num = 0
        for p in existing:
            m = re.match(r"OQ-(\d+)", p.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
        oq_path = oq_dir / f"OQ-{max_num + 1:03d}.md"

        oq_path.write_text(
            "# Open Question — Contrat API à définir\n\n"
            f"- **Origine** : build {story_id} (MLOOP-181-BE, capture automatique CA-5)\n"
            f"- **Méthode pressentie** : {method}\n"
            f"- **Besoin fonctionnel** : {hint}\n"
            f"- **Route** : {CONTRACT_TO_DEFINE}\n"
            "- **Statut** : OUVERTE — aucune URI inventée (Zéro Fausse Route)\n",
            encoding="utf-8",
        )
        return oq_path

    # ── Pilier 4 / Déc. 5 : Multiplicateur de richesse ───────────────────────

    def compute_richness(self, evidence_path: Path) -> Dict[str, Any]:
        """Calcule la richesse du pack (décisions + citations) pour le rapport build."""
        data = self._load_pack(evidence_path)
        decisions = len(data.get("implementation_decisions", []))
        citations = len(data.get("verbatim_extracts", []))
        if decisions == 0 and citations == 0:
            richness = "EMPTY"
        elif decisions >= 2 and citations >= 2:
            richness = "OK"
        else:
            richness = "PARTIAL"
        return {"decisions": decisions, "citations": citations, "richness": richness}
