"""Tests unitaires pour la procédure de création de projet et le scaffolding agnostique (ADR-0330)."""
import json
import shutil
from argparse import Namespace
from pathlib import Path

from src.commands.handlers.project import handle_init
from src.state import LoopState


def test_handle_init_generates_agnostic_files():
    """Vérifie que handle_init génère un projet 100% agnostique de mLoop."""
    test_project = "Test_Project_Agnostic_Tmp"
    p = Path("Projects") / test_project
    
    # Nettoyage préventif
    if p.exists():
        shutil.rmtree(p)

    try:
        args = Namespace(project=test_project)
        state = LoopState(project_name=test_project)
        
        ret = handle_init(args, state, p)
        assert ret == 0, "handle_init a échoué"

        # 1. Vérifier l'arborescence des 3 Piliers
        assert (p / "reference").is_dir(), "Dossier reference/ manquant"
        assert (p / "docs" / "00-ingested").is_dir(), "Dossier docs/00-ingested/ manquant"
        assert (p / "docs" / "01-architecture").is_dir(), "Dossier docs/01-architecture/ manquant"
        assert (p / "docs" / "02-business-rules").is_dir(), "Dossier docs/02-business-rules/ manquant"
        assert (p / "docs" / "04-transverse").is_dir(), "Dossier docs/04-transverse/ manquant"
        assert (p / "backlog" / "stories").is_dir(), "Dossier backlog/stories/ manquant"
        assert (p / "memory").is_dir(), "Dossier memory/ manquant"

        # 2. Vérifier AGENTS.md agnostique
        agents_file = p / "AGENTS.md"
        assert agents_file.exists(), "AGENTS.md manquant"
        agents_content = agents_file.read_text(encoding="utf-8")
        assert "python src/swarm.py" not in agents_content, "Pollution CLI interne dans AGENTS.md"
        assert "loop_mem_search" not in agents_content, "Pollution MCP interne dans AGENTS.md"
        assert "4 Piliers Gherkin" in agents_content, "Directives 4 Piliers absentes de AGENTS.md"

        # 3. Vérifier opencode.json agnostique
        opencode_file = p / "opencode.json"
        assert opencode_file.exists(), "opencode.json manquant"
        config = json.loads(opencode_file.read_text(encoding="utf-8"))
        assert "mcp" not in config, "Ponts MCP locaux internes présents dans opencode.json"
        assert "commands" not in config, "Commandes CLI internes présentes dans opencode.json"
        assert config.get("project") == test_project, "Nom de projet incorrect dans opencode.json"
        assert "AGENTS.md" in config.get("instructions", []), "Instructions AGENTS.md manquantes"

        # 4. Vérifier README.md et .gitignore
        assert (p / "README.md").exists(), "README.md manquant"
        assert (p / ".gitignore").exists(), ".gitignore manquant"

    finally:
        if p.exists():
            shutil.rmtree(p)
