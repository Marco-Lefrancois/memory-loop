from pathlib import Path
import pytest
from src.pipelines.skill_doctor import SkillDoctor, run_skill_doctor


def test_estimate_tokens():
    assert SkillDoctor.estimate_tokens("") == 0
    assert SkillDoctor.estimate_tokens("   ") == 0
    text = "Hello world! This is a test of deterministic token estimation."
    tokens = SkillDoctor.estimate_tokens(text)
    assert tokens > 5
    assert tokens < 30


def test_parse_skill_manifest(tmp_path: Path):
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    content = """---
name: test_skill
description: A mock skill for unit testing purposes.
version: 1.0.0
---

# Test Skill Instructions
Here are detailed instructions for this skill.
"""
    skill_file.write_text(content, encoding="utf-8")
    
    doctor = SkillDoctor(workspace_root=tmp_path, individual_threshold=50)
    parsed = doctor.parse_skill_manifest(skill_file)
    
    assert parsed["name"] == "test_skill"
    assert parsed["description"] == "A mock skill for unit testing purposes."
    assert parsed["total_tokens"] > 0
    assert parsed["description_tokens"] > 0
    assert parsed["valid"] is True


def test_audit_with_mock_skills(tmp_path: Path):
    skills_root = tmp_path / ".agents" / "skills"
    skills_root.mkdir(parents=True)
    
    # Skill 1: small
    s1_dir = skills_root / "small_skill"
    s1_dir.mkdir()
    (s1_dir / "SKILL.md").write_text("---\nname: small_skill\ndescription: Small skill.\n---\nBody.", encoding="utf-8")
    
    # Skill 2: oversized (> 50 tokens)
    s2_dir = skills_root / "large_skill"
    s2_dir.mkdir()
    large_body = "word " * 100
    (s2_dir / "SKILL.md").write_text(f"---\nname: large_skill\ndescription: Large skill.\n---\n{large_body}", encoding="utf-8")
    
    doctor = SkillDoctor(workspace_root=tmp_path, individual_threshold=50)
    report = doctor.audit(suggest_tombstone=True)
    
    assert report["success"] is True
    summary = report["summary"]
    assert summary["total_skills"] == 2
    assert summary["oversized_skills_count"] == 1
    assert "large_skill" in report["oversized_skills"]
    assert summary["context_rot_risk"] in ("LOW", "MEDIUM", "HIGH")
    
    # Check skills array
    assert len(report["skills"]) == 2


def test_audit_live_workspace():
    workspace_root = Path(__file__).resolve().parent.parent
    report = run_skill_doctor(workspace_root=workspace_root, threshold=2000, output_json=False)
    assert report["success"] is True
    summary = report["summary"]
    assert summary["total_skills"] >= 30
    assert summary["total_boot_description_tokens"] > 0
    assert len(report["skills"]) == summary["total_skills"]
