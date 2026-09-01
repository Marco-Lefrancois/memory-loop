from pathlib import Path
from src.state import LoopState
from src.cli import ZeroFluffConsole

def run_teach(project_name: str, state: LoopState, project_path: Path):
    ZeroFluffConsole.section(f"Cycle Teach - Initialisation - {project_name}")
    
    # Check project path exists
    if not project_path.exists():
        project_path.mkdir(parents=True, exist_ok=True)

    # 1. Create directory structures
    dirs = ["lessons", "learning-records", "reference"]
    for d in dirs:
        dir_path = project_path / d
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            ZeroFluffConsole.step_s1("Teach Init", f"Création du dossier : {d}/")
        else:
            ZeroFluffConsole.step_s1("Teach Init", f"Le dossier {d}/ existe déjà.")

    # 2. Setup MISSION.md
    mission_path = project_path / "MISSION.md"
    if not mission_path.exists():
        mission_content = """# Mission: {Saisir le sujet d'apprentissage ici}

## Why
{1-3 sentences. Le but concret dans le monde réel que vous poursuivez. Qu'est-ce qui change dans votre vie ou votre travail une fois ce skill acquis ?}

## Success looks like
- {Une compétence spécifique et observable que vous serez capable de mettre en œuvre}
- {Un autre élément mesurable}

## Constraints
- {Temps, budget, préférences d'apprentissage, limites de l'approche}

## Out of scope
- {Sujets adjacents exclus pour le moment pour protéger la zone proximale de développement}
"""
        mission_path.write_text(mission_content, encoding="utf-8")
        ZeroFluffConsole.success(f"Fichier MISSION.md initialisé.")
    else:
        ZeroFluffConsole.info("Fichier MISSION.md déjà existant.")

    # 3. Setup RESOURCES.md
    resources_path = project_path / "RESOURCES.md"
    if not resources_path.exists():
        resources_content = """# {Sujet} Resources

## Knowledge

- [Lien vers ressource de confiance](https://example.com)
  Description courte : ce qu'elle couvre et quand s'y référer.

## Wisdom (Communautés)

- [Communauté ou Forum](https://example.com)
  Description de la communauté pour obtenir des retours réels.
"""
        resources_path.write_text(resources_content, encoding="utf-8")
        ZeroFluffConsole.success(f"Fichier RESOURCES.md initialisé.")
    else:
        ZeroFluffConsole.info("Fichier RESOURCES.md déjà existant.")

    # 4. Setup GLOSSARY.md
    glossary_path = project_path / "GLOSSARY.md"
    if not glossary_path.exists():
        glossary_content = """# {Sujet} Glossary

Nomenclature et vocabulaire de référence pour ce sujet.

## Terms

**Terme**:
Définition concise du concept (1-2 phrases).
_Eviter_ : Synonymes ou termes ambigus.
"""
        glossary_path.write_text(glossary_content, encoding="utf-8")
        ZeroFluffConsole.success(f"Fichier GLOSSARY.md initialisé.")
    else:
        ZeroFluffConsole.info("Fichier GLOSSARY.md déjà existant.")

    # 5. Setup NOTES.md
    notes_path = project_path / "NOTES.md"
    if not notes_path.exists():
        notes_content = """# Notes d'Enseignement

- Préférences d'apprentissage :
- Expérience déclarée :
- Journal de bord / Notes de travail :
"""
        notes_path.write_text(notes_content, encoding="utf-8")
        ZeroFluffConsole.success(f"Fichier NOTES.md initialisé.")
    else:
        ZeroFluffConsole.info("Fichier NOTES.md déjà existant.")

    ZeroFluffConsole.success("Espace d'apprentissage Teach initialisé avec succès !")
