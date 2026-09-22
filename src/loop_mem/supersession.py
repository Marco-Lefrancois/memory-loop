# -*- coding: utf-8 -*-
"""
Memory Supersession Engine (mLoop Core - ADR-0326).

Inspiré de Statewave / SAGE (Awesome Agents) :
Détecte et archive déterministement les règles et décisions d'architecture
qui ont été remplacées (superseded) pour éviter les hallucinations de règles obsolètes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from src.utils.logger import get_logger

logger = get_logger("loop_mem.supersession")


@dataclass
class SupersessionRecord:
    """Enregistrement d'une règle ou d'une décision rendue obsolète."""

    target_id: str  # ex: "ADR-001" ou "RM-04"
    superseded_by: str  # ex: "ADR-0324"
    reason: str  # Raison de la caducité
    effective_date: str
    target_file: str
    status: str = "SUPERSEDED"  # "SUPERSEDED", "DEPRECATED", "ACTIVE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "superseded_by": self.superseded_by,
            "reason": self.reason,
            "effective_date": self.effective_date,
            "target_file": self.target_file,
            "status": self.status,
        }


class MemorySupersessionEngine:
    """Moteur de détection et de gestion de supersession des connaissances."""

    def __init__(self, project_path: Path | str) -> None:
        self.project_path = Path(project_path)
        self.ledger_file = self.project_path / "memory" / "supersession_ledger.json"

    def scan_adrs_for_supersessions(
        self, adr_dir: Optional[Path | str] = None
    ) -> List[SupersessionRecord]:
        """Scanne les ADRs pour identifier les clauses de remplacement."""
        target_dir = Path(adr_dir) if adr_dir else (self.project_path / "docs" / "01-architecture")
        if not target_dir.exists():
            # Fallback vers docs/01-architecture global
            alt = Path("docs") / "01-architecture"
            if alt.exists():
                target_dir = alt
            else:
                return []

        records: List[SupersessionRecord] = []
        now_str = datetime.now().strftime("%Y-%m-%d")

        for adr_file in sorted(target_dir.glob("*.md")):
            content = adr_file.read_text(encoding="utf-8", errors="ignore")
            current_adr_id = self._extract_adr_id(adr_file.name, content)

            # Recherche de mentions : "Remplace : ADR-XXX" ou "Supersedes : ADR-XXX"
            supersede_matches = re.findall(
                r"(?:Remplace|Supersedes|Remplac[ée]e? par)\s*:\s*\[?(ADR-\w+)\]?",
                content,
                re.IGNORECASE,
            )
            for old_id in supersede_matches:
                records.append(
                    SupersessionRecord(
                        target_id=old_id.upper(),
                        superseded_by=current_adr_id,
                        reason=f"Remplacé par la décision {current_adr_id}",
                        effective_date=now_str,
                        target_file=str(adr_file.name),
                    )
                )

        return records

    def sync_ledger(self, records: Optional[List[SupersessionRecord]] = None) -> Dict[str, Any]:
        """Met à jour le registre permanent memory/supersession_ledger.json."""
        if records is None:
            records = self.scan_adrs_for_supersessions()

        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)

        ledger_data = {
            "last_synced_at": datetime.now().isoformat(),
            "total_superseded": len(records),
            "superseded_items": {r.target_id: r.to_dict() for r in records},
        }

        self.ledger_file.write_text(
            json.dumps(ledger_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return ledger_data

    def is_superseded(self, item_id: str) -> Optional[SupersessionRecord]:
        """Vérifie si un élément est obsolète."""
        if not self.ledger_file.exists():
            self.sync_ledger()

        try:
            data = json.loads(self.ledger_file.read_text(encoding="utf-8"))
            items = data.get("superseded_items", {})
            if item_id.upper() in items:
                d = items[item_id.upper()]
                return SupersessionRecord(**d)
        except Exception as e:
            logger.debug(
                "Lecture du ledger de supersession échouée, retour None",
                exc_info=True,
                extra={
                    "component": "loop_mem.supersession",
                    "operation": "is_superseded",
                    "item_id": item_id,
                    "ledger_file": str(self.ledger_file),
                    "error": str(e),
                },
            )
        return None

    def _extract_adr_id(self, filename: str, content: str) -> str:
        """Extrait l'identifiant ADR canonique (ex: ADR-0325)."""
        m = re.search(r"^(ADR-\d+[a-zA-Z0-9]*)", filename, re.IGNORECASE)
        if m:
            return m.group(1).upper()
        m2 = re.search(r"^#\s+(ADR-\d+[a-zA-Z0-9]*)", content, re.MULTILINE)
        if m2:
            return m2.group(1).upper()
        return filename
