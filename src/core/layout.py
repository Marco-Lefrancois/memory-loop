"""
mLoop Framework Project Layout (ADR-0100, ADR-0102, ADR-0103)
Source unique de vérité pour la structure des répertoires des projets clients et mLoop.
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_adr_contracts() -> Dict[str, Any]:
    """
    Charge les contrats d'architecture depuis StandardsGraphStore (ADR-0379),
    avec repli résilient sur standards/adr-contracts.json.
    """
    try:
        from src.core.standards_graph import StandardsGraphStore
        contracts = StandardsGraphStore.get_instance().get_layout_contracts()
        if contracts:
            return contracts
    except Exception:
        pass

    contracts_path = Path(__file__).resolve().parent.parent.parent / "standards" / "adr-contracts.json"
    if contracts_path.exists():
        try:
            return json.loads(contracts_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARNING] Impossible de lire adr-contracts.json : {e}. Fallback activé.")
    return {
        "ADR-0100": {
            "client_layout": ["reference", "docs", "backlog", "memory", "graphify-out"],
            "forbidden_in_client": ["src", "openspec"]
        },
        "ADR-0102": {
            "docs_subdirs": ["00-ingested", "01-architecture", "02-business-rules",
                             "03-models", "04-transverse", "05-assets/maquettes",
                             "05-assets/diagrams", "05-assets/images"],
            "required_files_in_docs": ["index.md"],
            "ssot_files": {
                "sprint_backlog": "sprint_backlog.md",
                "story_mapping": "STORY_MAPPING.md",
                "open_questions": "00-questions-ouvertes.md"
            }
        },
        "ADR-0103": {
            "mloop_only_dirs": ["directives", "journal", "src", "openspec"],
            "mloop_layout": ["reference", "docs", "backlog", "memory", "graphify-out",
                             "directives", "journal", "src", "openspec"]
        },
        "ADR-0375": {
            "stage_order": [
                "STAGE_1_INGEST", "STAGE_2_PLAN_ANALYSE", "STAGE_3_BUILD",
                "STAGE_4_VALIDATE", "STAGE_5_SHIP"
            ]
        },
        "ADR-0378": {
            "gate_definitions": {
                "1": {
                    "name": "Gate 1 : Ingestion & Cadrage Initial Prêt",
                    "from_stage": "STAGE_1_INGEST",
                    "to_stage": "STAGE_2_PLAN_ANALYSE"
                }
            }
        }
    }


class ProjectLayout:
    """
    Layout des répertoires du projet — chargé dynamiquement depuis standards/adr-contracts.json.

    NE PAS MODIFIER LES CONSTANTES ICI DIRECTEMENT.
    Modifier l'ADR source correspondante, puis mettre à jour standards/adr-contracts.json,
    puis relancer `python src/swarm.py calibrate` (Règle ADR-Sync — AGENTS.md).

    Source ADRs :
      ADR-0100 : Loi des 3 Piliers (client_layout, forbidden_in_client)
      ADR-0102 : Arborescence docs/ (docs_subdirs, ssot_files)
      ADR-0103 : Segmentation mLoop/OpenSpec (mloop_layout, mloop_only_dirs)
    """
    _c = load_adr_contracts()

    # Piliers Universels — ADR-0100
    CLIENT_LAYOUT = _c["ADR-0100"]["client_layout"]
    FORBIDDEN_CLIENT = _c["ADR-0100"]["forbidden_in_client"]
    MEMORY_SUBDIRS = _c["ADR-0100"].get("memory_subdirs", ["sessions", "debates", "sync", "reports", "cache", "tmp"])

    REFERENCE = CLIENT_LAYOUT[0]   # "reference"
    DOCS = CLIENT_LAYOUT[1]        # "docs"
    BACKLOG = CLIENT_LAYOUT[2]     # "backlog"
    MEMORY = CLIENT_LAYOUT[3]      # "memory"
    GRAPHIFY_OUT = CLIENT_LAYOUT[4]# "graphify-out"
    MEMO_ARCHIVE = "memo_archive"

    ACTIVE_PROJECT_FILE = "memory/active_project.json"

    PROJECTS_DIR = Path("Projects")
    SOURCE_MANIFEST = "source_manifest.json"
    INGEST_ANOMALIES = "ingest_anomalies.json"

    # Sous-dossiers docs/ — ADR-0102
    DOCS_SUBDIRS = _c["ADR-0102"]["docs_subdirs"]
    DOCS_INGESTED = DOCS_SUBDIRS[0]      # "00-ingested"
    DOCS_ARCHITECTURE = DOCS_SUBDIRS[1]  # "01-architecture"
    DOCS_RULES = DOCS_SUBDIRS[2]         # "02-business-rules"
    DOCS_MODELS = DOCS_SUBDIRS[3]        # "03-models"
    DOCS_TRANSVERSE = DOCS_SUBDIRS[4]    # "04-transverse"
    DOCS_ASSETS = "05-assets"            # "05-assets" (ADR-0332)
    DOCS_ASSETS_MAQUETTES = "05-assets/maquettes"
    DOCS_ASSETS_DIAGRAMS = "05-assets/diagrams"
    DOCS_ASSETS_IMAGES = "05-assets/images"

    # Fichiers SSOT canoniques — ADR-0102
    SSOT_FILES = _c["ADR-0102"]["ssot_files"]
    SPRINT_BACKLOG_FILE = SSOT_FILES["sprint_backlog"]   # "sprint_backlog.md"
    STORY_MAPPING_FILE = SSOT_FILES["story_mapping"]     # "STORY_MAPPING.md"
    OPEN_QUESTIONS_CLIENT_FILE = SSOT_FILES.get("open_questions_client", "00-questions-ouvertes-client.md")
    OPEN_QUESTIONS_DEVTEAM_FILE = SSOT_FILES.get("open_questions_devteam", "00-questions-ouvertes-devteam.md")
    OPEN_QUESTIONS_FILE = OPEN_QUESTIONS_DEVTEAM_FILE   # Alias pour compatibilité ascendante

    # Piliers MLOOP uniquement — ADR-0103
    MLOOP_ONLY_DIRS = _c["ADR-0103"]["mloop_only_dirs"]
    MLOOP_LAYOUT = _c["ADR-0103"]["mloop_layout"]

    DIRECTIVES = MLOOP_ONLY_DIRS[0]   # "directives"
    JOURNAL = MLOOP_ONLY_DIRS[1]      # "journal"
    SRC = MLOOP_ONLY_DIRS[2]          # "src"
    OPENSPEC = MLOOP_ONLY_DIRS[3]     # "openspec"
