"""
mLoop Framework Focus Pipeline Submodule
Gestionnaire CLI du verrou d'attention et des transitions de la State Machine (Frontmatter Metadata).
"""

import os
import yaml
from pathlib import Path
from src.state import StoryStatus
from src.pipelines.state_machine import StateMachineEngine, StateTransitionError

def set_focus(project_name: str, story_rel_path: str, base_projects_dir: str = "Projects"):
    """
    Bascule le statut frontmatter de la story ciblée à IN_ANALYZE,
    normalise les autres stories non-terminées à OPEN/ON-HOLD,
    et valide l'unicité du focus via le moteur StateMachineEngine.
    """
    project_path = Path(base_projects_dir) / project_name
    if not project_path.exists():
        raise FileNotFoundError(f"Projet introuvable : {project_path}")

    backlog_path = project_path / "backlog"
    stories_dir = backlog_path / "stories"

    # Auto-nettoyage du chemin si l'agent transmet 'Projects/.../stories/CODEBASE/US-XX.md'
    clean_rel_path = story_rel_path.replace("\\", "/")
    if "stories/" in clean_rel_path:
        clean_rel_path = clean_rel_path.split("stories/", 1)[-1]
    story_rel_path = clean_rel_path

    target_story_file = stories_dir / story_rel_path
    if not target_story_file.exists() and not story_rel_path.endswith(".md"):
        target_story_file = stories_dir / f"{story_rel_path}.md"

    if not target_story_file.exists():
        # Auto-résolution récursive par nom de fichier/ID si le sous-dossier n'est pas spécifié
        story_name = Path(story_rel_path).name
        if not story_name.endswith(".md"):
            story_name = f"{story_name}.md"
        matches = list(stories_dir.glob(f"**/{story_name}"))
        if not matches:
            # Recherche par ID logique (id:) ou clé Jira (jira_key:) dans le frontmatter
            target_query = Path(story_rel_path).stem.strip()
            for f in stories_dir.rglob("*.md"):
                try:
                    c = f.read_text(encoding="utf-8", errors="ignore")
                    if (f"id: {target_query}" in c 
                        or f"jira_key: {target_query}" in c 
                        or f"id: US-{target_query}" in c):
                        matches.append(f)
                        break
                except Exception:
                    pass

        if matches:
            target_story_file = matches[0]
            story_rel_path = target_story_file.relative_to(stories_dir).as_posix()
        else:
            # 2. Résolution sémantique par mot-clé métier ou numéro (ex: 'casse', '14', 'repack')
            from src.utils.lexicon_resolver import SemanticLexiconResolver
            resolved_semantic = SemanticLexiconResolver.resolve_story_query(story_rel_path, stories_dir)
            if resolved_semantic and resolved_semantic.exists():
                target_story_file = resolved_semantic
                story_rel_path = target_story_file.relative_to(stories_dir).as_posix()
            else:
                raise FileNotFoundError(f"Story introuvable sous backlog/stories/ : {story_rel_path}")

    engine = StateMachineEngine(str(project_path))

    # 1. Normalisation des métadonnées Frontmatter YAML
    for file in stories_dir.glob("**/*.md"):
        try:
            rel_p = file.relative_to(stories_dir).as_posix()
            text = file.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue

            data = yaml.safe_load(parts[1])
            if not isinstance(data, dict):
                continue

            current_raw = data.get("status", "OPEN")
            current_status = StoryStatus.from_raw(current_raw)
            status_changed = False

            if rel_p == story_rel_path:
                if current_status != StoryStatus.IN_ANALYZE:
                    engine.validate_transition(current_status, StoryStatus.IN_ANALYZE)
                    data["status"] = StoryStatus.IN_ANALYZE.value
                    status_changed = True
            elif current_status == StoryStatus.IN_ANALYZE:
                # Relâcher le focus : remettre en OPEN ou ON_HOLD
                target = StoryStatus.ON_HOLD if rel_p.startswith("SANTE/") else StoryStatus.OPEN
                engine.validate_transition(current_status, target)
                data["status"] = target.value
                status_changed = True

            if status_changed:
                new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True).strip()
                new_text = f"---\n{new_yaml}\n---" + parts[2]
                file.write_text(new_text, encoding="utf-8")
        except StateTransitionError:
            raise
        except Exception as e:
            print(f"Warning normalizing {file}: {e}")

    # 2. Validation déterministe par le moteur State Machine
    engine.validate_single_in_analyze()

    print(f"[FOCUS STATE MACHINE] Récit '{story_rel_path}' positionné au statut IN_ANALYZE.")
    return True

