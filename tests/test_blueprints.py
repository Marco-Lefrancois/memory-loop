"""
Unit Tests - Blueprint Loader & Template Decoupling (ADR-0319 / ADR-0330 / ADR-0369)
"""

from pathlib import Path
import pytest

from src.utils.blueprints import BlueprintLoader, BlueprintNotFoundError


def test_blueprint_loader_resolves_official_blueprints():
    required_blueprints = [
        "project_readme_template.md",
        "project_agents_template.md",
        "project_opencode_template.json",
        "project_gitignore_template.gitignore",
        "project_index_template.md",
        "project_sprint_backlog_template.md",
        "project_open_questions_template.md",
        "project_spec_template.md",
        "project_adr_template.md",
        "story_draft_template.md",
        "story_template.md",
        "tshirt_size_template.md",
        "project_fact_dossier_template.md",
        "git_pre_commit_hook.sh",
    ]
    for bp in required_blueprints:
        path = BlueprintLoader.get_blueprint_path(bp)
        assert path.exists(), f"Blueprint {bp} does not exist on disk"
        raw = BlueprintLoader.load_raw(bp)
        assert len(raw) > 0


def test_blueprint_loader_renders_variables():
    rendered = BlueprintLoader.render(
        "project_readme_template.md",
        {"PROJECT_NAME": "AlphaProject"},
    )
    assert "# 🚀 AlphaProject" in rendered
    assert "{{PROJECT_NAME}}" not in rendered


def test_blueprint_loader_raises_on_missing():
    with pytest.raises(BlueprintNotFoundError):
        BlueprintLoader.get_blueprint_path("non_existent_template_xyz123.md")


def test_ticket_pipeline_uses_blueprints(tmp_path):
    from src.pipelines.ticket_pipeline import TicketPipelineEngine

    engine = TicketPipelineEngine(tmp_path)
    spec_path = engine.create_spec(
        title="Payment Service",
        overview="Processes card payments",
        scope="Frontend and backend checkout",
        architecture="Stripe Gateway seam",
        acceptance_criteria="Tokenized cards only",
    )
    assert spec_path.exists()
    spec_text = spec_path.read_text(encoding="utf-8")
    assert "Payment Service" in spec_text
    assert "Stripe Gateway seam" in spec_text

    stories = [
        {
            "title": "Authorize Card",
            "type": "BE",
            "given": "card is valid",
            "when": "auth is called",
            "then": "token is returned",
        }
    ]
    created = engine.decompose_to_tickets(spec_path, stories)
    assert len(created) == 1
    story_text = created[0].read_text(encoding="utf-8")
    assert "Authorize Card" in story_text
    assert "REC-001" in story_text
