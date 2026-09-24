"""
_sync_graph.py — Sous-module Sync : synchronisation Git wikis & hypergraphe.

Responsabilités :
  - sync_live_reference_wikis : git pull --ff-only sur les wikis dans reference/
  - sync_hypergraph           : construction / fusion incrémentale HypergraphKnowledgeAbstract

ADR-0202 (RULE-AST-01) : ≤ 300 L / 15 Ko.
ADR-0369              : subprocess.run(git pull, timeout=8) — seul appel réseau, déjà borné.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("pipelines.sync.graph")


# ---------------------------------------------------------------------------
# Synchronisation Git wikis locaux
# ---------------------------------------------------------------------------


def sync_live_reference_wikis(project_name: str, project_path: Path) -> None:
    """
    Rapatrie automatiquement les dernières modifications Git des wikis dans reference/
    (Pattern Live Git-Sync ADR-0327).

    ADR-0369 : subprocess.run avec timeout=8 (borné).
    """
    ref_dir = project_path / "reference"
    if not ref_dir.exists():
        return

    for wiki_p in ref_dir.rglob("*.wiki"):
        if (wiki_p / ".git").exists():
            try:
                proc = subprocess.run(
                    ["git", "-C", str(wiki_p), "pull", "--ff-only"],
                    capture_output=True,
                    text=True,
                    timeout=8,  # ADR-0369 : borné
                )
                if proc.returncode == 0:
                    out = proc.stdout.strip()
                    if "Already up to date" in out or "Déjà à jour" in out:
                        ZeroFluffConsole.info(f"[Live Git-Sync] {wiki_p.name} est à jour.")
                    else:
                        ZeroFluffConsole.success(
                            f"[Live Git-Sync] {wiki_p.name} synchronisé avec succès :"
                            f" {out.splitlines()[0]}"
                        )
                else:
                    ZeroFluffConsole.warning(
                        f"[Live Git-Sync] Avertissement pull sur {wiki_p.name} :"
                        f" {proc.stderr.strip()[:100]}"
                    )
            except Exception as e:
                ZeroFluffConsole.warning(
                    f"[Live Git-Sync] Synchronisation live ignorée pour {wiki_p.name} : {e}"
                )
                logger.error(
                    f"Échec du pull Git live pour le wiki '{wiki_p.name}'.",
                    exc_info=True,
                    extra={
                        "subsystem": "wikifix",
                        "project": project_name,
                        "wiki": wiki_p.name,
                    },
                )


# ---------------------------------------------------------------------------
# Hypergraphe
# ---------------------------------------------------------------------------


def sync_hypergraph(
    project_name: str,
    project_path: Path,
    incremental: bool = False,
    verbose: bool = False,
) -> None:
    """
    Construit ou met à jour l'hypergraphe des récits et entités (Standard ADR-0343).
    Stocké sous memory/hypergraph.json.
    Aucun appel réseau — traitement 100% FS local.
    """
    try:
        from src.core.hypergraph_engine import HypergraphKnowledgeAbstract
        import yaml

        hypergraph_file = project_path / "memory" / "hypergraph.json"
        existing_ka = None

        if incremental and hypergraph_file.exists():
            try:
                existing_ka = HypergraphKnowledgeAbstract.load_from_file(hypergraph_file)
            except Exception:
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
                            r"\b(API-\d{3}|GET\s+/[^\s]+|POST\s+/[^\s]+|PUT\s+/[^\s]+"
                            r"|DELETE\s+/[^\s]+)\b",
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
                        business_rules=(
                            sorted(list(set(business_rules))) if business_rules else None
                        ),
                        data_models=(sorted(list(set(data_models))) if data_models else None),
                        adrs=sorted(list(set(adrs))) if adrs else None,
                        gherkin_scenarios=(
                            sorted(list(set(gherkin_tests))) if gherkin_tests else None
                        ),
                        status=status,
                    )
                except Exception:
                    logger.error(
                        f"Erreur de traitement du fichier de story '{story_file}'"
                        " pour l'hypergraphe.",
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
                    f"[Hypergraph Sync] Fusion incrémentale : {len(report.added_nodes)} nœuds"
                    f" ajoutés, {len(report.updated_nodes)} mis à jour,"
                    f" {len(report.added_edges)} arêtes ajoutées."
                )
        else:
            ka.save_to_file(hypergraph_file)
            if verbose or len(ka.edges) > 0:
                ZeroFluffConsole.info(
                    f"[Hypergraph Sync] Hypergraphe généré ({len(ka.nodes)} nœuds,"
                    f" {len(ka.edges)} hyper-arêtes) -> {hypergraph_file.name}"
                )

    except Exception as _hg_err:
        ZeroFluffConsole.warning(f"[Hypergraph Sync] Erreur non-bloquante : {_hg_err}")
        logger.error(
            "Erreur non-bloquante lors de la construction de l'hypergraphe.",
            exc_info=True,
            extra={"subsystem": "hypergraph", "project": project_name},
        )
