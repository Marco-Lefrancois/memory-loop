"""
DPO Few-Shot Trajectory Archive — Mémoire de Préférences et d'Arbitrages.

Capture les retours et corrections issus du Grill-with-Docs :
- Enregistre le triplet (Contexte, Proposition Initiale, Correction Humaine).
- Fournit des exemples Few-Shot dynamiques pour injecter l'alignement sur-mesure aux agents.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class PreferencePair:
    """Représente une paire de préférence DPO locale."""
    context: str
    rejected: str
    chosen: str
    category: str
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d["timestamp"] == 0.0:
            d["timestamp"] = time.time()
        return d


class DPOPreferenceArchive:
    """Gestionnaire de l'archive de préférences DPO."""

    def __init__(self, project_root: Path | str) -> None:
        self.project_root = Path(project_root)
        self.archive_file = self.project_root / "memory" / "preferences" / "dpo_pairs.json"

    def record_preference(self, context: str, rejected: str, chosen: str, category: str = "BUSINESS_RULE") -> None:
        """Enregistre une nouvelle décision/correction humaine."""
        self.archive_file.parent.mkdir(parents=True, exist_ok=True)
        pairs = self.get_all_preferences()

        new_pair = PreferencePair(
            context=context,
            rejected=rejected,
            chosen=chosen,
            category=category,
            timestamp=time.time(),
        )
        pairs.append(new_pair.to_dict())

        self.archive_file.write_text(json.dumps(pairs, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_all_preferences(self) -> List[Dict[str, Any]]:
        """Récupère l'ensemble des paires enregistrées."""
        if not self.archive_file.exists():
            return []
        try:
            return json.loads(self.archive_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def get_few_shot_prompt(self, limit: int = 3) -> str:
        """Formate les dernières préférences en bloc Few-Shot pour injection contextuelle."""
        pairs = self.get_all_preferences()
        if not pairs:
            return ""

        lines = ["### 🎯 Directives d'Alignement Antérieures (Few-Shot Corrections)", ""]
        for p in pairs[-limit:]:
            lines.append(f"**Contexte** : {p.get('context')}")
            lines.append(f"❌ *À Éviter* : {p.get('rejected')}")
            lines.append(f"✅ *Décision Retenue* : {p.get('chosen')}")
            lines.append("")

        return "\n".join(lines)
