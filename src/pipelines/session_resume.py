from pathlib import Path
import json
import time
from src.cli import ZeroFluffConsole


def run_session_resume(project_name: str):
    """
    Axe 1 Joe Njenga / Vibe Code Common Sense (ADR-0310) : Moteur de Restauration de Session Anti-Amnésie.
    Restaure instantanément l'état complet du projet au réveil de l'agent.
    """
    ZeroFluffConsole.section(f"Restauration de Session Anti-Amnésie - mLoop ({project_name})")
    
    project_dir = Path("Projects") / project_name
    
    # 0. Lecture de l'état officiel du cycle de vie (ADR-0339)
    from src.core.lifecycle import ProjectLifecycleManager, STAGE_NAMES
    l_state = ProjectLifecycleManager.get_state(project_dir)
    stage_desc = STAGE_NAMES.get(l_state.current_stage, l_state.current_stage.value)
    next_gate = l_state.stage_index if l_state.stage_index < 5 else 5
    lifecycle_banner = (
        f"## 🚦 État du Cycle de Vie Projet (ADR-0339)\n"
        f"- **Étape Active** : `{l_state.current_stage.value}` ({stage_desc})\n"
        f"- **Prochaine Porte de Sortie** : Gate {next_gate}\n"
    )

    # 1. Lecture de sprint_backlog.md et STORY_MAPPING.md (Vertical Slicing SSOT)
    backlog_file = project_dir / "backlog" / "sprint_backlog.md"
    story_mapping_file = project_dir / "backlog" / "STORY_MAPPING.md"
    
    backlog_summary = "Sprint backlog non disponible"
    if backlog_file.exists():
        backlog_content = backlog_file.read_text(encoding="utf-8")
        lines = [l for l in backlog_content.splitlines() if l.strip().startswith("|") or l.strip().startswith("#")]
        backlog_summary = "\n".join(lines[:15])

    mapping_summary = "Story mapping non disponible"
    if story_mapping_file.exists():
        mapping_content = story_mapping_file.read_text(encoding="utf-8")
        lines = [l for l in mapping_content.splitlines() if l.strip().startswith("|") or l.strip().startswith("#")]
        mapping_summary = "\n".join(lines[:35])
    else:
        mapping_summary = "[Consolidé dans sprint_backlog.md (SSOT Master Unifiée)]"

        
    # 2. Lecture du dernier rapport d'état Self-Dev
    self_dev_file = Path("memory") / "SELF_DEV_STATUS.md"
    self_dev_summary = "Aucun état self-dev consigné"
    if self_dev_file.exists():
        self_dev_summary = self_dev_file.read_text(encoding="utf-8")[:300] + "..."
        
    # 3. Extraction des 5 dernières observations FTS5
    from src.loop_mem.db import get_session_timeline
    timeline = get_session_timeline(project_name=project_name) or []
    recent_obs = timeline[:5]
    obs_summary = "\n".join([f"- [{o.get('timestamp')}] ({o.get('type')}) {o.get('content')[:100]}..." for o in recent_obs])
    
    # 4. Consignation du rapport de santé de mémoire (Dédié par Projet ET Global mLoop)
    proj_health_file = project_dir / "memory" / "SESSION_MEMORY_HEALTH.md"
    global_health_file = Path("memory") / "SESSION_MEMORY_HEALTH.md"
    
    health_content = f"""# Diagnostic de Santé & Restauration de Mémoire mLoop

**Projet**: {project_name}
**Timestamp Restauration**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Statut Rétention Contextuelle**: 100% (Anti-Amnesia Active)

{lifecycle_banner}
## Découpage Vertical (Story Mapping SSOT)
{mapping_summary}

## Backlog en Cours
{backlog_summary}

## Dernier État Self-Dev / Calibration
{self_dev_summary}

## 5 Derniers Souvenirs Extraits (Auto-Recall FTS5)
{obs_summary or 'Aucune observation enregistrée'}
"""
    # Garde-fou constitutionnel : forcer strictement <= 200 lignes (ADR-0362)
    health_lines = health_content.strip().splitlines()
    if len(health_lines) > 200:
        health_lines = health_lines[:198] + ["", "*[Tronqué pour respecter le plafond strict de 200 lignes ADR-0362]*"]
        health_content = "\n".join(health_lines) + "\n"

    # Écriture dans le dossier du projet métier
    proj_health_file.parent.mkdir(parents=True, exist_ok=True)
    proj_health_file.write_text(health_content, encoding="utf-8")

    # Écriture dans la racine globale mLoop
    global_health_file.parent.mkdir(parents=True, exist_ok=True)
    global_health_file.write_text(health_content, encoding="utf-8")
    
    ZeroFluffConsole.success(f"Session restaurée avec succès pour '{project_name}' ! Diagnostic consigné sous {proj_health_file} et {global_health_file}")
    return {
        "status": "resumed",
        "project": project_name,
        "backlog_present": backlog_file.exists(),
        "recent_observations_count": len(recent_obs)
    }
