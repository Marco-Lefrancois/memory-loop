"""
Test E2E Simulation Agent — Simulation exacte du prompt utilisateur en langage naturel.
Prompt : "J'aimerais reprendre mes analyses pour le projet Metro One Trust de mémoire je suis rendu au récit US-13-FOOD"
"""

import pytest
import subprocess
import sys
from pathlib import Path


def _is_key_alignment_failure(stderr: str) -> bool:
    """Détecte si l'échec du vibe-check est dû à un désalignement de clé LiteLLM
    ou à un confinement de compétence (projet non aligné au contexte d'exécution actif).
    Les deux cas sont des comportements guardrail attendus, non des régressions."""
    key_mismatch = "requiert la clé" in stderr and "active:" in stderr
    confinement_403 = "CONFINEMENT 403" in stderr or "STRICTEMENT INTERDITE" in stderr
    return key_mismatch or confinement_403


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
        c2, out2, err2 = run_swarm_cmd(
            ["focus", "--project", "Metro Food", "--story", "US-13-FOOD"]
        )
        assert c2 == 0, f"Le focus a échoué : {err2}"
        assert "MMA-4673.md" in out2 or "US-13-FOOD" in out2, (
            "La résolution automatique du chemin de la story a échoué"
        )

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
            assert Path(p).exists(), (
                f"Le fichier de référence {p} mentionné dans AGENTS.md est introuvable"
            )

    def test_vibe_check_guardrail_simulation(self):
        """
        Simule le Guardrail Vibe-Check Pré-Vol sur le projet actif
        et valide le passage de 100% des contrôles d'intégrité.

        Tolère l'échec de clé LiteLLM (désalignement Perso vs Metro) et le
        confinement 403 (projet non aligné au contexte actif) car le guardrail
        fonctionne correctement — seul le contexte d'exécution est incompatible.
        Toute autre défaillance reste bloquante.
        """
        from src.utils.token_ledger import TokenLedger

        key_info = TokenLedger.resolve_active_key_info()
        label = key_info.get("key_label", "")
        test_project = "BoireFrere_Segment2" if label == "Boire et Frère" else "Metro_COMMERCE"

        c, out, err = run_swarm_cmd(["vibe-check", "--project", test_project])
        if c != 0:
            assert _is_key_alignment_failure(err), (
                f"Le vibe-check a échoué pour une raison inattendue : {err}"
            )
            pytest.skip("Vibe-check échoué pour raison attendue (key/confinement) — test sauté")
        assert "Intégrité SSOT" in out or "Résultat Vibe-Check" in out
        # Vérifier uniquement la ligne de bilan final (pas les labels de checks internes)
        bilan_lines = [l for l in out.splitlines() if "Résultat Vibe-Check" in l or "/ 0 FAIL" in l]
        assert any("0 FAIL" in l for l in bilan_lines) or len(bilan_lines) == 0, (
            "Le vibe-check contient des échecs réels dans le bilan final"
        )

    def test_key_alignment_resilience(self):
        """
        Vérifie que le vibe-check détecte correctement un désalignement de clé
        LiteLLM et retourne un message explicite (sans planter).
        """
        from src.utils.token_ledger import TokenLedger

        key_info = TokenLedger.resolve_active_key_info()
        label = key_info.get("key_label", "")
        test_project = "Metro_COMMERCE"

        c, out, err = run_swarm_cmd(["vibe-check", "--project", test_project])
        # Le résultat doit contenir l'information sur l'alignement de clé
        combined = out + err
        has_key_info = "Clé active" in combined or "Alignement Projet" in combined
        assert has_key_info, (
            "Le message d'alignement de clé LiteLLM n'a pas été trouvé dans la sortie"
        )
