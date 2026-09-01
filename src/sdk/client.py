"""
MLoop Client SDK - Python Interface (ADR-0309 - Google MCP Toolbox Alignment)
Expose une API cliente Python unifiée pour interagir avec le serveur MCP mLoop.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger("mloop_sdk")


class MLoopClient:
    """
    Client Python SDK pour les services et ponts MCP mLoop.
    Inspiré de ToolboxClient (Google MCP Toolbox).
    """

    def __init__(self, project_name: str = "mLoop", root_dir: Optional[Path] = None):
        self.project_name = project_name
        self.root_dir = root_dir or Path(".")
        self.project_path = self.root_dir / "Projects" / project_name

    def load_manifest(self) -> Dict[str, Any]:
        """
        Charge le manifeste déclaratif tools.yaml à la racine (ADR-0309).
        """
        manifest_path = self.root_dir / "tools.yaml"
        if not manifest_path.exists():
            return {}
        try:
            import yaml
            return yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logger.warning(f"Impossible de charger tools.yaml : {e}")
            return {}

    def get_toolset(self, phase: str) -> List[str]:
        """
        Retourne la liste des noms d'outils autorisés pour une phase spécifique depuis tools.yaml.
        """
        manifest = self.load_manifest()
        phase_upper = phase.upper()
        for ts in manifest.get("toolsets", []):
            if isinstance(ts, dict) and ts.get("name", "").upper() == phase_upper:
                return ts.get("tools", [])
        return []

    def list_tools(self, phase: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère la liste des outils MCP disponibles, filtrables par Phase (SPEC, PLAN, BUILD, VALIDATE, SHIP).
        """
        from src.bridges.mcp_loop_mem import handle_tools_list
        res = handle_tools_list(req_id=1, params={"phase": phase} if phase else {})
        return res.get("result", {}).get("tools", [])

    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche sémantique FTS5 dans la mémoire d'observations mLoop.
        """
        from src.loop_mem.db import search_observations
        return search_observations(query=query, project_name=self.project_name) or []

    def check_story_compliance(self, story_markdown: str) -> Dict[str, Any]:
        """
        Audite la conformité d'une User Story (4 Piliers Gherkin & Isolation Technique).
        """
        from src.bridges.mcp_loop_mem import audit_story_compliance
        return audit_story_compliance(story_markdown)

    def preload_story(self, story_id: str) -> Dict[str, Any]:
        """
        Précharge les engrammes sémantiques en RAM pour une story.
        """
        from src.bridges.mcp_loop_mem import preload_story_context
        return preload_story_context(story_id, project=self.project_name)
