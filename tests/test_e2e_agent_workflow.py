"""
Test E2E Simulation Agent — mLoop Workflow Guardrail & Boot Sequence Test.

Ce test simule un agent IA effectuant la Boot Sequence complète :
1. resume (Anti-Amnésie)
2. vibe-check (Guardrail pré-vol)
3. focus (Verrouillage d'attention sur une story valide)

Il valide également qu'une tentative de focus sur un mauvais nom/chemin déclenche l'erreur attendue sans planter le système.
"""
import pytest
import subprocess
import sys
from pathlib import Path

PROJECT_NAME = "Metro_COMMERCE"
VALID_STORY = "Projects/Metro_COMMERCE/backlog/stories/OneTrust_COMMERCE/MMA-4692.md"
INVALID_STORY = "backlog/stories/NONEXISTENT_STORY_99999.md"

def run_swarm_cmd(args_list):
    """Exécute une commande CLI python src/swarm.py et retourne stdout, stderr, exit_code."""
    cmd = [sys.executable, "src/swarm.py"] + args_list
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
    return res.returncode, res.stdout, res.stderr

class TestAgentE2ESimulation:

    def test_boot_sequence_step1_resume(self):
        """Étape 1 : Simulation 'python src/swarm.py resume --project Metro_COMMERCE'"""
        code, stdout, stderr = run_swarm_cmd(["resume", "--project", PROJECT_NAME])
        assert code == 0, f"Resume a échoué avec stderr: {stderr}"
        assert "Session restaurée avec succès" in stdout or "Restauration" in stdout

    def test_boot_sequence_step2_vibe_check(self):
        """Étape 2 : Simulation 'python src/swarm.py vibe-check --project Metro_COMMERCE'"""
        code, stdout, stderr = run_swarm_cmd(["vibe-check", "--project", PROJECT_NAME])
        assert code == 0, f"Vibe-check a échoué avec stderr: {stderr}"
        assert "Guardrail" in stdout or "Vibe-Check" in stdout

    def test_boot_sequence_step3_focus_invalid_story_intercepted(self):
        """Étape 3a : Simulation d'une erreur d'agent (mauvais chemin de story). Le guardrail doit intercepter proprement."""
        code, stdout, stderr = run_swarm_cmd(["focus", "--project", PROJECT_NAME, "--story", INVALID_STORY])
        assert code != 0 or "FileNotFoundError" in stdout or "introuvable" in stdout, "L'erreur de story introuvable aurait dû être levée !"

    def test_boot_sequence_step3_focus_valid_story(self):
        """Étape 3b : Simulation d'un focus valide sur le bon chemin de la story MMA-4692."""
        code, stdout, stderr = run_swarm_cmd(["focus", "--project", PROJECT_NAME, "--story", VALID_STORY])
        assert code == 0, f"Focus valide a échoué avec stderr: {stderr}"
        assert "MMA-4692" in stdout or "IN_ANALYZE" in stdout or "FOCUS STATE MACHINE" in stdout or "Focus" in stdout

    def test_full_agent_boot_sequence_end_to_end(self):
        """Test E2E complet enchaîné (Sequence complète d'amorçage sans interruption)."""
        # 1. Resume
        c1, out1, _ = run_swarm_cmd(["resume", "--project", PROJECT_NAME])
        assert c1 == 0

        # 2. Vibe Check
        c2, out2, _ = run_swarm_cmd(["vibe-check", "--project", PROJECT_NAME])
        assert c2 == 0

        # 3. Focus
        c3, out3, _ = run_swarm_cmd(["focus", "--project", PROJECT_NAME, "--story", VALID_STORY])
        assert c3 == 0

        print("\n✅ Simulation E2E Agent terminée avec succès : La Boot Sequence complète est 100% fonctionnelle.")
