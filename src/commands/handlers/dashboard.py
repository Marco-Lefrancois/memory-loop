# -*- coding: utf-8 -*-
"""Handler CLI mLoop pour le tableau de bord d'observabilité souverain."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.state import LoopState


def handle_dashboard(
    args: argparse.Namespace,
    state: Optional[LoopState] = None,
    project_path: Optional[Path] = None,
) -> int:
    """
    Lance le tableau de bord d'observabilité et de supervision souverain mLoop (FastAPI / Uvicorn).
    """
    from src.dashboard.runner import serve_dashboard

    port = getattr(args, "port", 8080)
    no_browser = getattr(args, "no_browser", False)
    proj_name = getattr(args, "project", None) or (state.project_name if state else None)

    serve_dashboard(
        port=port,
        project=proj_name,
        open_browser=not no_browser,
    )
    return 0
