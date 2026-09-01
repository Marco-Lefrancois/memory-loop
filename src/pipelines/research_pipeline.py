from pathlib import Path
from src.state import LoopState
from src.cli import ZeroFluffConsole
from src.pipelines.crawler import WebCrawlerAgent

def run_research(project_name: str, state: LoopState, project_path: Path, query: str = "", explicit_url: str = None):
    ZeroFluffConsole.section(f"Cycle Research & Développement - {project_name}")
    
    if not project_path.exists():
        project_path.mkdir(parents=True, exist_ok=True)

    # 1. Create directory structures
    research_dir = project_path / "reference" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    ZeroFluffConsole.step_s1("Research Init", "Dossier : reference/research/ prêt.")

    target_query = query or explicit_url or "R&D mLoop"
    ZeroFluffConsole.info(f"Target/URL reçue : '{target_query}'")
    
    # 2. Exécution du crawler si une URL est transmise
    if explicit_url:
        ZeroFluffConsole.step_s1("Research Crawl", f"Aspiration directe de {explicit_url}...")
        crawler = WebCrawlerAgent()
        crawler.execute(state, explicit_url=explicit_url)
        ZeroFluffConsole.success(f"Crawl terminé pour {explicit_url}")
        
    # 3. Create a scratchpad for the IDE agent to pick up
    scratchpad_path = research_dir / "CURRENT_RESEARCH.md"
    scratchpad_content = f"""# Current Research Task: {target_query}

**Topic/URL**: {target_query}
**Status**: In Progress

## Instructions pour l'Agent IDE (Deep Research Pipeline)
1. **Source aspirée** : Consultez `memory/crawler/cache/` pour les fichiers ingérés.
2. **Skill Agentique** : Exécutez les 5 étapes du skill `research-and-develop` (`.agents/skills/research-and-develop/SKILL.md`).
3. **Formalisation ADR** : Rédigez la décision d'architecture dans `docs/01-architecture/ADR-XXX.md`.
4. **Indexation** : Lancez `python src/swarm.py sync --project {project_name}` pour indexer les nouveaux artefacts.
"""
    scratchpad_path.write_text(scratchpad_content, encoding="utf-8")
    
    # 4. Initialize SOURCES.md
    sources_path = research_dir / "SOURCES.md"
    sources_content = f"# Sources for Crawling\n\n- {explicit_url or 'Ajoutez ici les URLs à aspirer.'}\n"
    sources_path.write_text(sources_content, encoding="utf-8")
    ZeroFluffConsole.success("Fichier SOURCES.md et CURRENT_RESEARCH.md mis à jour.")

    ZeroFluffConsole.success("Pipeline Research initialisée avec succès.")
