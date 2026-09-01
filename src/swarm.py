import sys
import json
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

load_dotenv(override=True)

from src.state import LoopState, ProjectLayout

from src.cli import ZeroFluffConsole

def _canonical_key(name: str) -> str:
    import re
    import unicodedata
    if not name:
        return ""
    normalized = unicodedata.normalize('NFD', name)
    clean = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-zA-Z0-9]', '', clean).lower()

def resolve_project_name(raw_name: str, create_if_missing: bool = False) -> str:
    """
    Résout le nom de projet canonique en vérifiant :
    1. L'existence d'un dossier physique sous Projects/ (ex: Metro_OneTrust).
    2. L'existence du projet dans le graphe ou les métadonnées (active_project.json).
    Si create_if_missing est True et que le projet n'existe pas, crée le squelette canonique (3 Piliers).
    """
    if not raw_name:
        raise ValueError("Le nom du projet ne peut pas être vide.")

    clean_name = raw_name.replace("Projects/", "").replace("Projects\\", "").strip()

    # 0-pré. Correspondance exacte case-insensitive sur le dossier physique (avant résolution sémantique)
    # Priorité absolue sur les projets non archivés pour éviter les collisions avec _DEPRECATED
    _direct_projects_dir = Path("Projects")
    if _direct_projects_dir.exists():
        # Construire un index {nom_lower: nom_réel} en excluant les archives
        _physical_index = {
            _p.name.lower(): _p.name
            for _p in _direct_projects_dir.iterdir()
            if _p.is_dir() and not _p.name.startswith(".") and not _p.name.endswith("_DEPRECATED")
        }
        _exact_match = _physical_index.get(clean_name.lower())
        if _exact_match:
            return _exact_match

    # 0. Résolution sémantique par table d'alias métiers
    from src.utils.lexicon_resolver import SemanticLexiconResolver
    semantic_resolved = SemanticLexiconResolver.resolve_project_alias(clean_name)
    if semantic_resolved:
        ZeroFluffConsole.info(f"Projet '{raw_name}' résolu sémantiquement vers '{semantic_resolved}'.")
        return semantic_resolved

    target_key = _canonical_key(clean_name)

    projects_dir = Path("Projects")
    existing_projects = {}

    if projects_dir.exists():
        for p in projects_dir.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                existing_projects[_canonical_key(p.name)] = p.name

    active_project_json = Path(ProjectLayout.ACTIVE_PROJECT_FILE)
    known_graph_names = set()
    if active_project_json.exists():
        try:
            data = json.loads(active_project_json.read_text(encoding="utf-8"))
            if "active_project" in data:
                known_graph_names.add(data["active_project"])
        except Exception:
            pass

    if clean_name in existing_projects.values():
        return clean_name

    if target_key in existing_projects:
        official_name = existing_projects[target_key]
        ZeroFluffConsole.info(f"Projet '{raw_name}' résolu automatiquement vers le nom officiel '{official_name}'.")
        return official_name

    target_canon = _canonical_key(clean_name)
    if target_canon:
        for official_name in existing_projects.values():
            off_canon = _canonical_key(official_name)
            if target_canon == off_canon or sorted(target_canon) == sorted(off_canon):
                ZeroFluffConsole.info(f"Projet '{raw_name}' résolu automatiquement vers le nom officiel '{official_name}'.")
                return official_name

        # Résolution par sous-chaîne ou préfixe (ex: "Boire" -> "BoireFrere_Reception")
        matching_projects = [
            official_name for official_name in existing_projects.values()
            if target_canon in _canonical_key(official_name)
        ]
        if len(matching_projects) == 1:
            official_name = matching_projects[0]
            ZeroFluffConsole.info(f"Projet '{raw_name}' résolu automatiquement vers le nom officiel '{official_name}'.")
            return official_name
        elif len(matching_projects) > 1:
            # Si plusieurs candidats matchent (ex: Boire vs BoireFrere_Reception), prioriser celui avec SSOT valide
            valid_ssot = [
                m for m in matching_projects
                if (projects_dir / m / "backlog" / "sprint_backlog.md").exists() or (projects_dir / m / "AGENTS.md").exists()
            ]
            if len(valid_ssot) == 1:
                official_name = valid_ssot[0]
                ZeroFluffConsole.info(f"Projet '{raw_name}' résolu automatiquement vers le nom officiel '{official_name}'.")
                return official_name

    for gname in known_graph_names:
        if _canonical_key(gname) == target_key and gname in existing_projects.values():
            return gname

    if create_if_missing:
        return clean_name

    raise ValueError(
        f"Le projet '{raw_name}' n'existe NI physiquement sous Projects/ NI dans le graphe. "
        f"Projets connus disponibles : {list(existing_projects.values())}"
    )

def get_project_context(project_name: str, create_if_missing: bool = False):
    """Charge l'état du projet et enregistre le projet actif."""
    resolved_name = resolve_project_name(project_name, create_if_missing=create_if_missing)

    active_json = Path(ProjectLayout.ACTIVE_PROJECT_FILE)
    try:
        active_json.parent.mkdir(parents=True, exist_ok=True)
        with open(active_json, "w", encoding="utf-8") as f:
            json.dump({"active_project": resolved_name}, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not write active_project.json: {e}")

    project_path = Path("Projects") / resolved_name
    state = LoopState(project_name=resolved_name)
    if project_path.exists():
        try:
            state.load_from_audit(project_path)
        except Exception:
            state.load_from_graph(project_path)
    state.project_name = resolved_name
    return state, project_path


def main():
    from src.commands.router import execute_cli
    try:
        execute_cli()
    except KeyboardInterrupt:
        ZeroFluffConsole.error("\nExécution interrompue par l'utilisateur.")
        sys.exit(130)

if __name__ == "__main__":
    from src.core.safe_exec import safe_run_entrypoint
    safe_run_entrypoint(main)
