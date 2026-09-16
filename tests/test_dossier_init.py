import argparse
from pathlib import Path
from src.commands.handlers.analysis import handle_dossier_init
from src.state import LoopState


def test_dossier_init_creates_scaffold(tmp_path):
    project_dir = tmp_path / "TestProjectDossierInit"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "INC-010-BE.md"
    story_file.write_text(
        """---
id: INC-010-BE
jira_key: COUVBOIRE-2000
title: API Test Nouvelle Fonctionnalité
status: IN_ANALYZE
---
# [COUVBOIRE-2000] API Test Nouvelle Fonctionnalité (INC-010-BE)
""",
        encoding="utf-8",
    )

    args = argparse.Namespace(story="INC-010-BE", force=False)
    state = LoopState(project_name="TestProjectDossierInit")

    ret = handle_dossier_init(args, state, project_dir)
    assert ret == 0

    dossier = project_dir / "memory" / "evidence" / "INC-010-BE_fact_dossier.md"
    assert dossier.exists()

    content = dossier.read_text(encoding="utf-8")
    assert "story_id: INC-010-BE" in content
    assert "jira_key: COUVBOIRE-2000" in content
    assert "dossier_status: CURRENT" in content
    assert "## 🔬 2. Faits Extraits & Verbatims" in content
    assert "## 🗄️ 3. Schéma Relationnel SSOT" in content
    assert "```mermaid" in content
    assert "## 🎯 4. Contrats Déclaratifs Cibles" in content
