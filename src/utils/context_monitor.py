# -*- coding: utf-8 -*-
"""
Context Monitor & Dumb-Zone Watcher (mLoop Core - ADR-0326).

Inspiré de ctop / ClawMetry (Awesome Agents) :
Surveille l'occupation de la fenêtre de contexte et prévient la dérive cognitive
lorsque la session dépasse 60% du budget token maximal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("context_monitor")


@dataclass
class ContextHealthReport:
    """Rapport de santé contextuelle et estimation de la zone de raisonnement."""

    total_chars: int
    estimated_tokens: int
    max_context_window: int
    occupancy_pct: float
    zone: str  # "SMART_ZONE", "CAUTION_ZONE", "DUMB_ZONE"
    recommendation: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_chars": self.total_chars,
            "estimated_tokens": self.estimated_tokens,
            "max_context_window": self.max_context_window,
            "occupancy_pct": round(self.occupancy_pct, 2),
            "zone": self.zone,
            "recommendation": self.recommendation,
            "details": self.details,
        }


class ContextMonitor:
    """Surveillant de la charge contextuelle et de la dérive d'attention."""

    # Seuils de référence standards
    DEFAULT_MAX_CONTEXT = 200_000  # 200k tokens par défaut
    SMART_THRESHOLD = 0.40  # 40%
    DUMB_ZONE_THRESHOLD = 0.60  # 60% (Saturation cognitive)

    def __init__(self, max_context_tokens: int = DEFAULT_MAX_CONTEXT) -> None:
        self.max_context_tokens = max_context_tokens

    def estimate_tokens(self, text: str) -> int:
        """Estimation heuristique robuste (1 token ~= 4 caractères pour le code/français)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def evaluate_text(self, text: str, label: str = "session_context") -> ContextHealthReport:
        """Évalue l'état de saturation d'un texte ou prompt."""
        char_count = len(text)
        tokens = self.estimate_tokens(text)
        pct = (tokens / self.max_context_tokens) * 100.0

        if pct < (self.SMART_THRESHOLD * 100):
            zone = "SMART_ZONE"
            rec = "Excellente attention du modèle. Poursuivre le travail en cours."
        elif pct < (self.DUMB_ZONE_THRESHOLD * 100):
            zone = "CAUTION_ZONE"
            rec = "Attention modérée. Envisager un compactage (Compact / Summarize) à la fin de la tâche."
        else:
            zone = "DUMB_ZONE"
            rec = "[ALERTE DÉROCHAGE] Saturation contextuelle > 60%. Déléguer impérativement au worker Herdr ou Clear."

        return ContextHealthReport(
            total_chars=char_count,
            estimated_tokens=tokens,
            max_context_window=self.max_context_tokens,
            occupancy_pct=pct,
            zone=zone,
            recommendation=rec,
            details={"label": label},
        )

    def evaluate_project_state(self, project_path: Path | str) -> ContextHealthReport:
        """Évalue l'empreinte mémoire totale du projet (backlog + docs + memory)."""
        path = Path(project_path)
        total_text = []

        # Parcourir les fichiers markdown du projet (hors caches et reference)
        if path.exists():
            for f in path.rglob("*.md"):
                rel = str(f).replace("\\", "/")
                if any(
                    x in rel
                    for x in [
                        "node_modules",
                        ".git",
                        "reference",
                        "memory/cache",
                        "scratch",
                        ".system_generated",
                    ]
                ):
                    continue
                try:
                    total_text.append(f.read_text(encoding="utf-8", errors="ignore"))
                except OSError as e:
                    logger.debug(
                        "Lecture fichier projet ignorée",
                        exc_info=True,
                        extra={"file": str(f), "error": str(e)},
                    )

        combined = "\n".join(total_text)
        return self.evaluate_text(combined, label=f"project_{path.name}")

    def check_file_bloat(self, file_path: Path | str, max_chars: int = 60_000) -> Optional[str]:
        """Alerte si un fichier unitaire dépasse la taille sécuritaire (requiert un découpage chunk)."""
        p = Path(file_path)
        if not p.exists():
            return None
        size = p.stat().st_size
        if size > max_chars:
            tok = size // 4
            return f"[ALERTE CONTEXT-BLOAT] Le fichier '{p.name}' ({size:,} octets, ~{tok:,} tokens) est trop volumineux. Utiliser 'python src/swarm.py chunk --file <chemin>' au lieu de l'injecter brut."
        return None

    def render_ascii_gauge(self, report: ContextHealthReport) -> str:
        """Génère une barre de progression visuelle ASCII pour la console."""
        bar_length = 30
        filled = min(bar_length, int((report.occupancy_pct / 100.0) * bar_length))
        bar = "█" * filled + "░" * (bar_length - filled)

        status_icon = (
            "🟢"
            if report.zone == "SMART_ZONE"
            else ("🟡" if report.zone == "CAUTION_ZONE" else "🔴")
        )

        lines = [
            f"Context Meter: [{bar}] {report.occupancy_pct:.1f}% ({report.estimated_tokens:,} / {report.max_context_window:,} tokens)",
            f"{status_icon} Zone: {report.zone} — {report.recommendation}",
        ]
        return "\n".join(lines)
