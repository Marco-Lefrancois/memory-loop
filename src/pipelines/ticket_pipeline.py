"""
Ticket Pipeline - mLoop
Gestion de la distillation de conversations/analyses en spécification (to-spec)
et du découpage en stories tracer-bullet (to-tickets).
"""

from pathlib import Path
from typing import Dict, List, Optional
import datetime
from src.state import ProjectLayout

SPEC_TEMPLATE = """# 📋 Technical Specification: {title}

## Overview
{overview}

## Scope & Target Components
{scope}

## Technical Architecture & Seams
{architecture}

## Acceptance Criteria & Edge Cases
{acceptance_criteria}

---
*Distillé par mLoop to-spec engine le {date}.*
"""

class TicketPipelineEngine:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.backlog_dir = project_path / ProjectLayout.BACKLOG
        self.stories_dir = self.backlog_dir / "stories"

    def create_spec(self, title: str, overview: str, scope: str, architecture: str, acceptance_criteria: str) -> Path:
        """Génère un fichier de spécification technique dans docs/01-architecture/."""
        docs_dir = self.project_path / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"spec_{title.lower().replace(' ', '_')}.md"
        spec_path = docs_dir / filename
        
        date_str = datetime.date.today().isoformat()
        content = SPEC_TEMPLATE.format(
            title=title,
            overview=overview,
            scope=scope,
            architecture=architecture,
            acceptance_criteria=acceptance_criteria,
            date=date_str
        )
        spec_path.write_text(content, encoding="utf-8")
        return spec_path

    def decompose_to_tickets(self, spec_path: Path, stories: List[Dict[str, str]]) -> List[Path]:
        """Découpe une spécification en récits tracer-bullet dans backlog/stories/."""
        self.stories_dir.mkdir(parents=True, exist_ok=True)
        created_paths = []

        # blueprint backend/frontend templates
        blueprint_be = self.project_path / "standards" / "blueprints" / "story_template_BE.md"
        for idx, story in enumerate(stories, 1):
            story_id = f"REC-{idx:03d}"
            filename = f"{story_id}_{story['title'].lower().replace(' ', '_')}.md"
            story_path = self.stories_dir / filename
            
            blockers = story.get("blocked_by", [])
            blockers_yaml = f"[{', '.join(blockers)}]" if blockers else "[]"
            
            story_content = f"""---
id: {story_id}
title: "{story['title']}"
status: IN_ANALYZE
type: {story.get('type', 'BE')}
blocked_by: {blockers_yaml}
created_at: "{datetime.date.today().isoformat()}"
---

# 📖 {story_id} : {story['title']}

## Description
**En tant que** Système,  
**je veux** {story['title']},  
**afin d'** assurer l'exécution tracer-bullet du projet.

## Contexte
Récit vertique tracer-bullet généré via mLoop to-tickets.

---

## Critères d'acceptation
* **Contrat** : {story['title']}
* **Performance** : Traitement déterministe mLoop

---

## Règles d'affaires
* **Règle-01 (Exécution) :** Validation synchrone du contrat de service.

---

## Scénarios de test (Gherkin)
```gherkin
Fonctionnalité: {story['title']} ({story_id})

  Scénario: Validation du récit {story_id} - Chemin Nominal
    Étant donné {story.get('given', 'un état initial valide et des pré-conditions respectées')}
    Quand {story.get('when', 'la transaction métier est exécutée')}
    Alors {story.get('then', 'le résultat est sauvegardé avec succès et la réponse est confirmée')}

  Scénario: Gestion des exceptions et rejets métier - {story_id}
    Étant donné une règle d'affaires RM-001 violée ou des paramètres invalides
    Quand la demande est soumise au service
    Alors le système rejette la requête avec un code HTTP 400/409 et un message explicite

  Scénario: Résilience technique et mode dégradé - {story_id}
    Étant donné une interruption temporaire de la base de données ou du réseau
    Quand la tentative d'accès est initiée
    Alors le mécanisme de retry avec exponential backoff s'active et préserve l'idempotence

  Scénario: Comportement UX et observabilité - {story_id}
    Étant donné une action utilisateur en cours de traitement
    Quand la réponse est retournée par le backend
    Alors une notification toast s'affiche et une métrique d'audit est consignée dans le journal
```
"""
            story_path.write_text(story_content, encoding="utf-8")
            created_paths.append(story_path)
            
        # Mise à jour du sprint backlog
        self._update_sprint_backlog(created_paths)
        return created_paths

    def _update_sprint_backlog(self, new_stories: List[Path]):
        sprint_file = self.backlog_dir / "sprint_backlog.md"
        if not sprint_file.exists():
            sprint_file.write_text("# 🏃 Sprint Backlog\n\n## Stories\n", encoding="utf-8")
            
        content = sprint_file.read_text(encoding="utf-8")
        for s in new_stories:
            rel_link = f"- [ ] [{s.name}](./stories/{s.name})"
            if rel_link not in content:
                content += f"\n{rel_link}"
        sprint_file.write_text(content, encoding="utf-8")
