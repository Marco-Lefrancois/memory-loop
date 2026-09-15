from pathlib import Path
from src.state import LoopState
from src.pipelines.ingest_agent import IngestAgent
from src.pipelines.crawler import WebCrawlerAgent
from src.pipelines.graphify.agent import GraphifyAgent
from src.pipelines.wikifix import WikiFixAgent
from src.pipelines.handoff import HandoffAgent
from src.cli import ZeroFluffConsole


def run_ingest(
    project_name: str, state: LoopState, project_path: Path, initiative: str | None = None
):
    ZeroFluffConsole.section(f"Cycle INGEST - Initialisation - {project_name}")

    if not project_path.exists():
        ZeroFluffConsole.error(f"Le projet {project_name} n'existe pas dans Projects/")
        return

    state.project_name = project_name
    state.ingest_initiative = initiative

    if initiative:
        ref_scope = project_path / "reference" / initiative
        if not ref_scope.exists():
            ZeroFluffConsole.error(
                f"Initiative '{initiative}' introuvable sous reference/ : {ref_scope}"
            )
            return
        ZeroFluffConsole.info(
            f"Ingestion scopée à l'initiative '{initiative}' → docs/{initiative}/00-ingested/"
        )

    # Phase 1: Ingestion Cognitive Local MarkItDown (RHO/Graphe)
    state = IngestAgent().execute(state)

    # Phase 2: Vérification de Surcharge (Handoff)
    state = HandoffAgent(threshold=15).execute(state)
    ZeroFluffConsole.success(f"Documentation moissonnée pour le projet '{project_name}'.")

    # Synthèse Télémétrie Source Manifest & Lexique (ADR-0335)
    total_sources = len(state.ingested_sources)
    total_terms = sum(len(s.get("terms", [])) for s in state.ingested_sources)
    total_sections = sum(len(s.get("sections", [])) for s in state.ingested_sources)
    ZeroFluffConsole.info(
        f"📊 [Source Manifest] {total_sources} source(s) consolidée(s) | {total_sections} sections répertoriées | {total_terms} termes extraits"
    )

    graphify = GraphifyAgent()
    state = graphify.execute(state)
    ZeroFluffConsole.success(f"Graphe sémantique généré.")

    state = WikiFixAgent().execute(state)

    state.save_to_audit(project_path)
    return state
