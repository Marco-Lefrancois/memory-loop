import re
import os
import json
import time
from pathlib import Path
from src.state import LoopState, JournalEntry
from src.pipelines.wikifix import WikiFixAgent
from src.pipelines.graphify.agent import GraphifyAgent
from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("pipelines.sync")


def load_sync_cache(project_path: Path) -> dict:
    cache_file = project_path / "memory" / "cache" / "sync_state.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(
                f"Erreur de lecture du cache de synchronisation '{cache_file}'.",
                exc_info=True,
                extra={"subsystem": "cache", "project": project_path.name},
            )
    return {"stories": {}, "questions": {}}


def save_sync_cache(project_path: Path, cache: dict) -> None:
    cache_dir = project_path / "memory" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "sync_state.json"
    cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def sync_project_directives(project_name: str, project_path: Path) -> None:
    """Synchronise automatiquement les directives et le journal de mémoire à partir des ADRs."""
    directives_dir = project_path / "directives"
    architecture_dir = project_path / "docs" / "01-architecture"
    # Création systématique de la structure canonique de memory (ADR-0100)
    memory_base = project_path / "memory"
    memory_subdirs = ["sessions", "debates", "sync", "reports", "cache", "tmp"]
    for sdir in memory_subdirs:
        (memory_base / sdir).mkdir(parents=True, exist_ok=True)

    # Vérification et consolidation des directives
    bus_file = directives_dir / "business.md"
    if architecture_dir.exists() and bus_file.exists():
        adrs = list(architecture_dir.glob("ADR-*.md"))
        if adrs:
            content = bus_file.read_text(encoding="utf-8")

            # Nettoyage et régénération du bloc ADR
            start_marker = "<!-- BEGIN_ADR_LIST -->"
            end_marker = "<!-- END_ADR_LIST -->"

            new_adr_block = start_marker + "\n"
            for adr in adrs:
                new_adr_block += f"- **Référence ADR ({adr.stem})** : Décision enregistrée sous [{adr.name}](file:///{adr.as_posix()}).\n"
            new_adr_block += end_marker

            if start_marker in content and end_marker in content:
                content = re.sub(
                    rf"{start_marker}.*?{end_marker}", new_adr_block, content, flags=re.DOTALL
                )
            else:
                content += "\n\n" + new_adr_block

            bus_file.write_text(content, encoding="utf-8")


def sync_open_questions(project_name: str, project_path: Path) -> None:
    """Synchronise automatiquement l'état des questions ouvertes vers le wayfinder."""
    transverse_dir = project_path / "docs" / "04-transverse"
    wayfinder_file = project_path / "backlog" / "wayfinder_map.md"

    if not transverse_dir.exists() or not wayfinder_file.exists():
        return

    resolved_qs = set()
    open_qs = set()

    cache = load_sync_cache(project_path)

    for md_file in transverse_dir.glob("00-questions-ouvertes-*.md"):
        mtime = os.path.getmtime(md_file)
        file_key = md_file.as_posix()

        file_cache = cache["questions"].get(file_key, {})
        if file_cache.get("mtime") == mtime:
            resolved_qs.update(file_cache.get("resolved", []))
            open_qs.update(file_cache.get("open", []))
            continue

        content = md_file.read_text(encoding="utf-8")
        file_resolved = set()
        file_open = set()

        # 1. Parsing Section Format: ### Q-XXX ou ### QD-XXX ... - **Décision** :
        sections = re.split(r"(?m)^###\s+((?:Q|QD)-\d+)", content)
        for i in range(1, len(sections), 2):
            q_id = sections[i]
            body = sections[i + 1] if i + 1 < len(sections) else ""
            if re.search(r"-\s*\*\*(?:Décision|Decision)\*\*\s*:", body, re.IGNORECASE):
                file_resolved.add(q_id)
            else:
                file_open.add(q_id)

        # 2. Parsing Table Format: | Q-XXX | QD-XXX | ... | Décision/Archivé/CLOSED | ...
        for match in re.finditer(r"(?m)^\|\s*((?:Q|QD)-\d+)\s*\|.*?\|\s*([^|]+)\s*\|", content):
            q_id = match.group(1)
            status_text = match.group(2).lower()
            if any(
                k in status_text
                for k in [
                    "décision",
                    "decision",
                    "validé",
                    "valide",
                    "archivé",
                    "archive",
                    "closed",
                ]
            ):
                file_resolved.add(q_id)
            else:
                if q_id not in file_resolved:
                    file_open.add(q_id)

        cache["questions"][file_key] = {
            "mtime": mtime,
            "resolved": list(file_resolved),
            "open": list(file_open),
        }
        resolved_qs.update(file_resolved)
        open_qs.update(file_open)

    save_sync_cache(project_path, cache)

    if not resolved_qs and not open_qs:
        return

    # Mettre à jour wayfinder_map.md
    wf_content = wayfinder_file.read_text(encoding="utf-8")
    original_wf = wf_content

    # Coche (RESOLVED)
    for q_id in resolved_qs:
        wf_content = re.sub(rf"(?m)^(\s*-\s*)\[\s\](.*?\b{q_id}\b.*)$", r"\1[x]\2", wf_content)

    # Décoche (OPEN)
    for q_id in open_qs:
        wf_content = re.sub(rf"(?m)^(\s*-\s*)\[x\](.*?\b{q_id}\b.*)$", r"\1[ ]\2", wf_content)

    if wf_content != original_wf:
        wayfinder_file.write_text(wf_content, encoding="utf-8")
        ZeroFluffConsole.info(
            f"[Sync] Mise à jour automatique de l'état des OQs dans wayfinder_map.md."
        )

    # Déblocage automatique des stories
    stories_dir = project_path / "backlog" / "stories"
    if stories_dir.exists() and resolved_qs:
        for story_file in stories_dir.rglob("*.md"):
            content = story_file.read_text(encoding="utf-8")
            original_content = content
            for q_id in resolved_qs:
                content = re.sub(
                    rf"(?m)^(>.*?⚠️\s*BLOQUÉ.*?\b{q_id}\b.*)$",
                    rf"> ✅ DÉBLOQUÉ : {q_id} (Décision actée)",
                    content,
                    flags=re.IGNORECASE,
                )
            if content != original_content:
                story_file.write_text(content, encoding="utf-8")
                ZeroFluffConsole.info(f"[Sync] Story {story_file.stem} débloquée (OQ {q_id}).")


def sync_sprint_backlog(project_name: str, project_path: Path) -> None:
    """
    Synchronise sprint_backlog.md (SSOT Master) et les en-têtes YAML des fichiers de récits.
    Supporte tout découpage en modules (01-reception, 02-incubation, etc.) et tout préfixe (REC, INC, US, Jira).
    """
    stories_dir = project_path / "backlog" / "stories"
    backlog_file = project_path / "backlog" / "sprint_backlog.md"

    if not stories_dir.exists() or not backlog_file.exists():
        return

    import unicodedata

    def norm(txt):
        return unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("utf-8").upper()

    backlog_content = backlog_file.read_text(encoding="utf-8")
    status_map = {}
    direct_id_status_map = {}

    current_cat = None
    for line in backlog_content.splitlines():
        nline = norm(line)
        # Détection dynamique des sections de modules / codebases (ex: ## Module : Incubation, ### CODEBASE : FOOD)
        if (
            "CODEBASE :" in nline
            or "MODULE :" in nline
            or nline.startswith("## ")
            or nline.startswith("### ")
        ):
            current_cat = (
                nline.replace("#", "").replace("MODULE :", "").replace("CODEBASE :", "").strip()
            )
        elif (
            line.strip().startswith("|")
            and not line.strip().startswith("|---")
            and not line.strip().startswith("| :---")
        ):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                row_text = line
                # Extraction de l'ID ou clé du récit (ex: REC-001-FE, INC-001, US-012, COUVBOIRE-990)
                m_ids = re.findall(r"\b([A-Z0-9]+(?:-[A-Z0-9]+)+)\b", row_text)
                m_statut = re.search(
                    r"\b(ACCEPTED|DONE|IN_QA|IN_DEV|READY_FOR_DEV|READY_FOR_GROOMING|IN_REVIEW|IN-REVIEW|IN_VALIDATE|IN_PLAN|IN_ANALYZE|OPEN|ON_HOLD|ON-HOLD|CLOSED|BACKLOG)\b",
                    row_text,
                    re.IGNORECASE,
                )

                if m_ids and m_statut:
                    st_val = m_statut.group(1).upper().replace("-", "_")
                    for s_id in m_ids:
                        direct_id_status_map[s_id.upper()] = st_val
                        if current_cat:
                            status_map[(current_cat, s_id.upper())] = st_val

    # 1. Aligner les en-têtes YAML des stories d'après sprint_backlog.md (SSOT)
    updated_files = 0
    for f in stories_dir.rglob("*.md"):
        category = f.parent.name
        fc = f.read_text(encoding="utf-8")
        m_yaml = re.search(r"^---\n(.*?)\n---", fc, re.DOTALL)
        if not m_yaml:
            continue
        yaml_text = m_yaml.group(1)

        # Récupération de l'ID depuis le frontmatter ou le nom de fichier
        m_id_yaml = re.search(r"(?m)^id:\s*(.+)$", yaml_text)
        story_id = m_id_yaml.group(1).strip().strip("'\"") if m_id_yaml else f.stem

        target_status = (
            direct_id_status_map.get(story_id.upper())
            or status_map.get((category, story_id.upper()))
            or direct_id_status_map.get(f.stem.upper())
        )
        if target_status:
            m_curr = re.search(r"(?m)^status:\s*(.+)$", yaml_text)
            curr_status = m_curr.group(1).strip() if m_curr else None
            if curr_status != target_status:
                new_yaml = re.sub(r"(?m)^status:\s*.+$", f"status: {target_status}", yaml_text)
                f.write_text(fc.replace(yaml_text, new_yaml, 1), encoding="utf-8")
                updated_files += 1

    if updated_files > 0:
        ZeroFluffConsole.info(
            f"[Sync] {updated_files} fichier(s) de récit(s) réaligné(s) sur le statut de sprint_backlog.md (SSOT)."
        )


def sync_live_reference_wikis(project_name: str, project_path: Path) -> None:
    """
    Rapatrie automatiquement les dernières modifications Git des wikis dans reference/
    (Pattern Live Git-Sync ADR-0327).
    """
    ref_dir = project_path / "reference"
    if not ref_dir.exists():
        return

    import subprocess

    for wiki_p in ref_dir.rglob("*.wiki"):
        if (wiki_p / ".git").exists():
            try:
                proc = subprocess.run(
                    ["git", "-C", str(wiki_p), "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                if proc.returncode == 0:
                    out = proc.stdout.strip()
                    if "Already up to date" in out or "Déjà à jour" in out:
                        ZeroFluffConsole.info(f"[Live Git-Sync] {wiki_p.name} est à jour.")
                    else:
                        ZeroFluffConsole.success(
                            f"[Live Git-Sync] {wiki_p.name} synchronisé avec succès : {out.splitlines()[0]}"
                        )
                else:
                    ZeroFluffConsole.warning(
                        f"[Live Git-Sync] Avertissement pull sur {wiki_p.name} : {proc.stderr.strip()[:100]}"
                    )
            except Exception as e:
                ZeroFluffConsole.warning(
                    f"[Live Git-Sync] Synchronisation live ignorée pour {wiki_p.name} : {e}"
                )
                logger.error(
                    f"Échec du pull Git live pour le wiki '{wiki_p.name}'.",
                    exc_info=True,
                    extra={"subsystem": "wikifix", "project": project_name, "wiki": wiki_p.name},
                )


def sync_hypergraph(
    project_name: str, project_path: Path, incremental: bool = False, verbose: bool = False
) -> None:
    """
    Construit ou met à jour l'hypergraphe des récits et entités (Standard ADR-0343).
    Stocké sous memory/hypergraph.json.
    """
    try:
        from src.core.hypergraph_engine import HypergraphKnowledgeAbstract
        import yaml

        hypergraph_file = project_path / "memory" / "hypergraph.json"
        existing_ka = None
        if incremental and hypergraph_file.exists():
            try:
                existing_ka = HypergraphKnowledgeAbstract.load_from_file(hypergraph_file)
            except Exception as e:
                existing_ka = None
                logger.error(
                    f"Impossible de charger l'hypergraphe existant '{hypergraph_file}'.",
                    exc_info=True,
                    extra={"subsystem": "hypergraph", "project": project_name},
                )

        ka = HypergraphKnowledgeAbstract(project_name=project_name)
        story_dir = project_path / "backlog" / "stories"
        if story_dir.exists():
            for story_file in story_dir.rglob("*.md"):
                try:
                    fc = story_file.read_text(encoding="utf-8")
                    m_yaml = re.search(r"^---\s*\n(.*?)\n---", fc, re.DOTALL)
                    if not m_yaml:
                        continue
                    yaml_text = m_yaml.group(1)
                    data = yaml.safe_load(yaml_text) or {}
                    story_id = str(data.get("id") or data.get("jira_key") or story_file.stem)
                    title = str(data.get("title") or story_file.stem)
                    status = str(data.get("status") or "DRAFT")

                    adrs = [m.group(1) for m in re.finditer(r"\b(ADR-\d{4})\b", fc)]
                    business_rules = [
                        m.group(1) for m in re.finditer(r"\b(BR-\d{3}|RM-\d{3})\b", fc)
                    ]
                    apis = [
                        m.group(1)
                        for m in re.finditer(
                            r"\b(API-\d{3}|GET\s+/[^\s]+|POST\s+/[^\s]+|PUT\s+/[^\s]+|DELETE\s+/[^\s]+)\b",
                            fc,
                        )
                    ]
                    data_models = [m.group(1) for m in re.finditer(r"\b(MDL-\d{3})\b", fc)]
                    gherkin_tests = [
                        m.group(1).strip()
                        for m in re.finditer(
                            r"(?i)^\s*(?:Scénario|Scenario):\s*(.+)$", fc, re.MULTILINE
                        )
                    ]

                    ka.create_story_unit(
                        story_id=story_id,
                        title=title,
                        persona=data.get("persona") or data.get("role"),
                        api_contracts=sorted(list(set(apis))) if apis else None,
                        business_rules=sorted(list(set(business_rules)))
                        if business_rules
                        else None,
                        data_models=sorted(list(set(data_models))) if data_models else None,
                        adrs=sorted(list(set(adrs))) if adrs else None,
                        gherkin_scenarios=sorted(list(set(gherkin_tests)))
                        if gherkin_tests
                        else None,
                        status=status,
                    )
                except Exception as e:
                    logger.error(
                        f"Erreur de traitement du fichier de story '{story_file}' pour l'hypergraphe.",
                        exc_info=True,
                        extra={
                            "subsystem": "hypergraph",
                            "project": project_name,
                            "file_path": str(story_file),
                        },
                    )

        if existing_ka and incremental:
            report = existing_ka.merge_with(ka)
            existing_ka.save_to_file(hypergraph_file)
            if verbose or report.has_changes:
                ZeroFluffConsole.info(
                    f"[Hypergraph Sync] Fusion incrémentale : {len(report.added_nodes)} nœuds ajoutés, {len(report.updated_nodes)} mis à jour, {len(report.added_edges)} arêtes ajoutées."
                )
        else:
            ka.save_to_file(hypergraph_file)
            if verbose or len(ka.edges) > 0:
                ZeroFluffConsole.info(
                    f"[Hypergraph Sync] Hypergraphe généré ({len(ka.nodes)} nœuds, {len(ka.edges)} hyper-arêtes) -> {hypergraph_file.name}"
                )
    except Exception as _hg_err:
        ZeroFluffConsole.warning(f"[Hypergraph Sync] Erreur non-bloquante : {_hg_err}")
        logger.error(
            "Erreur non-bloquante lors de la construction de l'hypergraphe.",
            exc_info=True,
            extra={"subsystem": "hypergraph", "project": project_name},
        )


def run_sync(
    project_name: str,
    state: LoopState,
    project_path: Path,
    details_msg: str = None,
    fast_mode: bool = False,
    verbose: bool = False,
    incremental: bool = False,
    story_filter: str = None,
) -> LoopState:
    ZeroFluffConsole.section(f"Synchronisation et Validation - {project_name}")
    t_total = time.perf_counter()
    logger.info(
        f"[SYNC] Début de la synchronisation pour '{project_name}'.",
        extra={"subsystem": "orchestrator", "project": project_name, "fast_mode": fast_mode},
    )

    # [Live Git-Sync] Rapatriement en direct des wikis distants dans reference/
    sync_live_reference_wikis(project_name, project_path)

    # [Directives Sync] Auto-population des directives et de la mémoire
    sync_project_directives(project_name, project_path)

    # [Backlog Sync] Alignement du sprint backlog avec les YAML des stories
    sync_sprint_backlog(project_name, project_path)

    # [Questions Sync] Auto-résolution des questions ouvertes vers le wayfinder et déblocage stories
    sync_open_questions(project_name, project_path)

    # [Hypergraph Sync] Modélisation Hyper-Story Units & Knowledge Abstracts (ADR-0343)
    sync_hypergraph(project_name, project_path, incremental=incremental, verbose=verbose)

    # [S2b] Gatekeeper Structurel (struct-check) — consultatif, non-bloquant par défaut (ADR-0338)
    try:
        from src.pipelines.struct_checker import StructCheckEngine

        struct_engine = StructCheckEngine(project_path)
        story_files = sorted(project_path.glob("backlog/stories/**/*.md"))
        struct_violations_found = False
        for sf in story_files:
            if story_filter and story_filter not in sf.name:
                continue
            report = struct_engine.check_file(sf, strict=False)
            for v in report.violations:
                if v.severity == "BLOCKING":
                    ZeroFluffConsole.warning(
                        f"[struct-check] {sf.name} : [{v.check_id}] {v.message}"
                    )
                    struct_violations_found = True
        if struct_violations_found:
            ZeroFluffConsole.warning(
                "[struct-check] Violations structurelles détectées. Exécuter 'python src/swarm.py struct-check --verbose' pour le détail."
            )
    except Exception as _struct_err:
        ZeroFluffConsole.warning(f"[struct-check] Ignoré (erreur non-bloquante) : {_struct_err}")
        logger.error(
            "Erreur non-bloquante lors du struct-check consultatif.",
            exc_info=True,
            extra={"subsystem": "struct", "project": project_name},
        )

    # [Fact-Search 2.0 & Lexicon Sync] Indexation SQLite FTS5 des chunks documentaires et du lexique
    try:
        from src.loop_mem.db import sync_project_lexicon_from_disk, index_project_docs_to_fts5

        lex_count = sync_project_lexicon_from_disk(project_name)
        chunks_count = index_project_docs_to_fts5(project_name)
        if verbose or not fast_mode:
            ZeroFluffConsole.info(
                f"[Fact-Search FTS5] {chunks_count} chunks documentaires et {lex_count} termes du lexique indexés."
            )
    except Exception as _fs_err:
        ZeroFluffConsole.warning(f"[Fact-Search FTS5] Indexation ignorée : {_fs_err}")
        logger.error(
            "Erreur non-bloquante lors de l'indexation FTS5.",
            exc_info=True,
            extra={"subsystem": "fts5", "project": project_name},
        )

    # [S1] Audit sémantique et génération des EvidencePacks
    try:
        state = WikiFixAgent().execute(state, verbose=verbose, story_filter=story_filter)
    except Exception as _wf_err:
        ZeroFluffConsole.warning(f"[WikiFix] Erreur non-bloquante lors de l'audit : {_wf_err}")
        logger.error(
            "Erreur non-bloquante lors de l'audit WikiFix.",
            exc_info=True,
            extra={"subsystem": "wikifix", "project": project_name},
        )

    if not fast_mode:
        # [Sync] Mise à jour du graphe sémantique pour refléter les derniers changements du code
        try:
            state = GraphifyAgent().execute(state)
        except Exception as _gf_err:
            ZeroFluffConsole.warning(
                f"[Graphify] Erreur non-bloquante lors de la modélisation : {_gf_err}"
            )
            logger.error(
                "Erreur non-bloquante lors de la modélisation Graphify.",
                exc_info=True,
                extra={"subsystem": "graphify", "project": project_name},
            )

    try:
        state.save_to_audit(project_path)
    except Exception as _audit_err:
        ZeroFluffConsole.warning(f"[Audit] Impossible de sauvegarder l'audit : {_audit_err}")
        logger.error(
            "Impossible de sauvegarder l'audit de session (save_to_audit).",
            exc_info=True,
            extra={"subsystem": "audit", "project": project_name},
        )

    duration_ms = round((time.perf_counter() - t_total) * 1000, 2)
    logger.info(
        f"[SYNC] Fin de la synchronisation pour '{project_name}'.",
        extra={
            "subsystem": "orchestrator",
            "project": project_name,
            "duration_ms": duration_ms,
            "fast_mode": fast_mode,
        },
    )

    return state
