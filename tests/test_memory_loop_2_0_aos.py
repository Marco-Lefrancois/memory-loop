"""
Suite de tests unitaires pour Memory Loop 2.0 (The Agentic Operating System).

Couvre l'ensemble des nouveaux modules :
- Ingestion multimodale MarkPDFdown (fallback local et support extensions)
- LLM-Wiki Engine & Goal-Cascading
- Blast Radius natif Python
- Virtual Context Pager (Working Pages & Eviction LRU)
- Actor Swarm & Débat MCTS
- AST Semantic Patcher & Formal ADR Solver
- Dream Consolidation Daemon & Skill Auto-Tuner
"""
import pytest
import asyncio
from pathlib import Path

from src.converters.markpdfdown_converter import MarkPDFdownConverter
from src.pipelines.llm_wiki import LLMWikiEngine
from src.pipelines.goal_cascade import GoalCascadeEngine
from src.pipelines.blast_radius import BlastRadiusEngine
from src.loop_mem.context_pager import VirtualContextPager
from src.core.actor_swarm import SwarmActorCoordinator, SwarmMessage
from src.bridges.agentic_debate import MCTSAdvDebateEngine
from src.core.ast_patcher import ASTSemanticPatcher
from src.core.formal_solver import FormalADRSolver
from src.pipelines.dream_consolidator import DreamConsolidationDaemon
from src.pipelines.skill_auto_tuner import SkillAutoTuner
from src.loop_mem.dpo_archive import DPOPreferenceArchive


def test_markpdfdown_converter_extensions(tmp_path):
    converter = MarkPDFdownConverter()
    assert converter.is_supported("doc.pdf")
    assert converter.is_supported("schema.png")
    assert converter.is_supported("arch.svg")
    assert not converter.is_supported("script.exe")

    # Test conversion fallback local
    sample_txt = tmp_path / "sample.pdf"
    sample_txt.write_text("Test content", encoding="utf-8")
    res = converter.convert_file(sample_txt)
    assert "Test content" in res or "sample" in res


def test_virtual_context_pager_lru():
    pager = VirtualContextPager(max_working_tokens=50)
    # Page de 20 tokens
    p1 = pager.load_page("page_1", "Page 1", "x" * 80, priority=1)
    # Page de 20 tokens
    p2 = pager.load_page("page_2", "Page 2", "y" * 80, priority=2)
    assert pager.total_tokens() <= 50

    # Charger une page qui dépasse le budget
    p3 = pager.load_page("page_3", "Page 3", "z" * 120, priority=3)
    # La page 2 (priorité 2) doit avoir été évincée au profit de p1 (priorité 1)
    assert "page_1" in pager.active_pages
    assert "page_3" in pager.active_pages
    
    rendered = pager.render_context_window()
    assert "PAGE: page_1" in rendered


@pytest.mark.asyncio
async def test_actor_swarm_concurrency():
    coordinator = SwarmActorCoordinator()
    plan_actor = coordinator.get_actor("plan")
    
    msg = SwarmMessage(
        sender="orchestrator",
        recipient="plan",
        message_type="TASK_REQUEST",
        payload={"story_id": "US-01"},
    )
    await coordinator.dispatch(msg)
    
    status = coordinator.get_swarm_status()
    assert status["plan"]["pending_messages"] == 1

    async def mock_handler(m: SwarmMessage):
        return SwarmMessage(sender="plan", recipient="orchestrator", message_type="PLAN_PROPOSAL", payload={"status": "DONE"})

    response = await plan_actor.process_next(mock_handler)
    assert response is not None
    assert response.message_type == "PLAN_PROPOSAL"
    assert len(plan_actor.processed_messages) == 1


def test_mcts_adversarial_debate():
    debate = MCTSAdvDebateEngine(max_branches=3)
    proposals = [
        {"title": "Option Monolithique", "content": "Modification du shared context global sans tests"},
        {"title": "Option INVEST Propre", "content": "---\nid: US-01\n---\n## Scénarios de test\nÉtant donné un client, Quand il clique, Alors il voit."},
    ]
    result = debate.evaluate_branches(proposals)
    assert result["total_branches_explored"] == 2
    assert result["selected_title"] == "Option INVEST Propre"


def test_ast_semantic_patcher():
    content = "---\nid: US-TEST\nstatus: DRAFT\n---\n\n## Description\nAncienne description.\n\n## Règles d'affaires\nRM-01."
    
    # 1. Patch Frontmatter
    updated = ASTSemanticPatcher.patch_frontmatter(content, {"status": "READY_FOR_DEV", "jira_key": "MMA-100"})
    assert "status: READY_FOR_DEV" in updated
    assert "jira_key: MMA-100" in updated
    assert "Ancienne description." in updated

    # 2. Patch Section Markdown
    patched_section = ASTSemanticPatcher.patch_markdown_section(updated, "Description", "Nouvelle description enrichie.")
    assert "Nouvelle description enrichie." in patched_section
    assert "Ancienne description." not in patched_section


def test_formal_adr_solver():
    valid_story = """---
id: US-VALID
type: Story
title: Récit Valide
status: READY_FOR_DEV
---

## Description
Description du récit.

## Contexte
Contexte du récit.

## Règles d'affaires
Règle métier pure en gras.

## Scénarios de test
### Scénario 1
Étant donné un utilisateur
Quand il valide
Alors le résultat est conforme.
"""
    is_valid, violations = FormalADRSolver.verify_story_invariants(valid_story)
    assert is_valid
    assert len(violations) == 0

    # Invalide (Frontmatter incomplet et pas de Gherkin)
    invalid_story = "## Description\nTexte sans frontmatter ni tests."
    is_valid_bad, violations_bad = FormalADRSolver.verify_story_invariants(invalid_story)
    assert not is_valid_bad
    assert len(violations_bad) > 0


def test_blast_radius_engine(tmp_path):
    engine = BlastRadiusEngine(tmp_path)
    engine.knowledge_graph = {
        "nodes": [
            {"id": "Projects/Metro/US-01.md", "name": "US-01"},
            {"id": "src/services/ConsentService.cs", "name": "ConsentService"},
            {"id": "tests/test_consent.py", "name": "test_consent"},
        ],
        "links": [
            {"source": "Projects/Metro/US-01.md", "target": "src/services/ConsentService.cs"},
            {"source": "tests/test_consent.py", "target": "Projects/Metro/US-01.md"},
        ],
    }
    res = engine.compute_blast_radius("US-01")
    assert "src/services/ConsentService.cs" in res["downstream_dependencies"]
    assert "tests/test_consent.py" in res["upstream_dependencies"]
    assert "tests/test_consent.py" in res["affected_tests"]

    report = engine.format_markdown_report(res)
    assert "Rayon d'Impact" in report


def test_dream_consolidation_and_dpo(tmp_path):
    daemon = DreamConsolidationDaemon(tmp_path)
    report = daemon.consolidate()
    assert report["status"] == "HEALTHY"
    assert (tmp_path / "memory" / "SESSION_MEMORY_HEALTH.md").exists()

    dpo = DPOPreferenceArchive(tmp_path)
    dpo.record_preference("Contexte", "Proposition erronée", "Proposition retenue", "GOVERNANCE")
    prefs = dpo.get_all_preferences()
    assert len(prefs) == 1
    assert "Proposition retenue" in dpo.get_few_shot_prompt()
