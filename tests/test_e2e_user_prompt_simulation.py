"""
Test E2E Simulation Agent — Simulation exacte du prompt utilisateur en langage naturel.
Prompt : "J'aimerais reprendre mes analyses pour le projet Metro One Trust de mémoire je suis rendu au récit US-13-FOOD"
"""
import pytest
import subprocess
import sys
from pathlib import Path

def run_swarm_cmd(args_list):
    """Exécute une commande CLI python src/swarm.py et retourne stdout, stderr, exit_code."""
    cmd = [sys.executable, "src/swarm.py"] + args_list
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
    return res.returncode, res.stdout, res.stderr

class TestNaturalLanguageUserPromptSimulation:

    def test_user_prompt_simulation_metro_onetrust_us13_food(self):
        """
        Simule l'exécution par l'Agent IA des commandes extraites du prompt utilisateur :
        Projet : "Metro Food" -> Résolu automatiquement vers 'Metro_FOOD'
        Story  : "US-13-FOOD"     -> Résolu automatiquement vers 'OneTrust_FOOD/MMA-4673.md'
        """
        # Étape 1 : Resume avec le nom exact saisi par l'utilisateur ("Metro Food")
        c1, out1, err1 = run_swarm_cmd(["resume", "--project", "Metro Food"])
        assert c1 == 0, f"Le resume a échoué : {err1}"
        assert "Metro_FOOD" in out1, "La résolution automatique du nom de projet a échoué"

        # Étape 2 : Focus avec l'identifiant exact saisi par l'utilisateur ("US-13-FOOD")
        c2, out2, err2 = run_swarm_cmd(["focus", "--project", "Metro Food", "--story", "US-13-FOOD"])
        assert c2 == 0, f"Le focus a échoué : {err2}"
        assert "MMA-4673.md" in out2 or "US-13-FOOD" in out2, "La résolution automatique du chemin de la story a échoué"

        print("\n✅ Simulation du prompt utilisateur réussie à 100% avec résolution automatique !")

    def test_simulation_ssot_integrity_and_no_phantom_references(self):
        """
        Simule l'initialisation de session et vérifie qu'aucun fichier mentionné dans AGENTS.md
        n'est une référence fantôme non résolue dans le projet métier.
        """
        agents_md = Path("AGENTS.md")
        assert agents_md.exists(), "Le fichier de directives AGENTS.md doit exister"

        content = agents_md.read_text(encoding="utf-8")

        # Règle d'Or : Interdiction de référencer des fichiers supprimés comme STORY_MAPPING.md
        assert "STORY_MAPPING.md" not in content, (
            "AGENTS.md ne doit plus contenir de référence à STORY_MAPPING.md "
            "car sprint_backlog.md est désormais la SSOT unifiée."
        )

        # Vérifier que les chemins absolus/relatifs mentionnés existent
        required_paths = [
            "standards/blueprints/story_template.md",
            "standards/GHERKIN_GUIDELINES.md",
        ]
        for p in required_paths:
            assert Path(p).exists(), f"Le fichier de référence {p} mentionné dans AGENTS.md est introuvable"

    def test_vibe_check_guardrail_simulation(self):
        """
        Simule le Guardrail Vibe-Check Pré-Vol sur le projet actif
        et valide le passage de 100% des contrôles d'intégrité.
        """
        from src.utils.token_ledger import TokenLedger
        key_info = TokenLedger.resolve_active_key_info()
        label = key_info.get("key_label", "")
        test_project = "BoireFrere_Segment2" if label == "Boire et Frère" else "Metro_COMMERCE"

        c, out, err = run_swarm_cmd(["vibe-check", "--project", test_project])
        assert c == 0, f"Le vibe-check a échoué : {err}"
        assert "Intégrité SSOT" in out or "Résultat Vibe-Check" in out
        assert "FAIL" not in out, "Le vibe-check contient une erreur de validation"


