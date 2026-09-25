"""
src/pipelines/bridge_certifier — Harnais de certification & conformité des
ponts MCP (MLOOP-215-FULL).

Deux familles de symboles cohabitent ici :

- le **lecteur de rapport** (``read_certification_report``,
  ``surface_state_of``, modèles) : import léger, sans dépendance au pont —
  c'est le seul chemin utilisé par le Vibe-Check, qui ne doit jamais payer le
  coût d'import des ponts ni lancer de navigateur ;
- le **moteur d'exécution** (``run_certification``, ``certify``) : import
  lourd, réservé à la commande ``certify-bridges``.

Garder cette frontière est une exigence de performance **et** de sécurité : un
contrôleur qui importerait le moteur pour lire un fichier JSON exposerait le
pré-vol aux ruptures du pont qu'il est censé évaluer.
"""

from src.pipelines.bridge_certifier._bc_models import (
    LEVEL_INTEGRATION,
    LEVEL_IN_PROCESS,
    LEVEL_MANUAL,
    MODULE_MAX_BYTES,
    MODULE_MAX_LINES,
    SCHEMA_ID,
    STATUS_FAIL,
    STATUS_PASS,
    STORY_ID,
    SURFACE_CHARGEMENT,
    SURFACE_ERREUR,
    SURFACE_INITIAL_VIDE,
    SURFACE_SUCCES,
    VERDICT_CONFORME,
    VERDICT_NON_CONFORME,
    CertificationError,
    CertificationReport,
    ControlResult,
    JournalEntry,
    default_report_dir,
    utc_now_iso,
)
from src.pipelines.bridge_certifier._bc_persist import (
    REPORT_FILENAME,
    REPORT_MARKDOWN_FILENAME,
    dynamic_counters,
    read_certification_report,
    render_markdown,
    report_paths,
    surface_state_of,
    write_certification_report,
)
from src.pipelines.bridge_certifier._bc_runner import (
    FULL_SCOPES,
    LIMIT_IDE_AUDIT,
    CertificationConfig,
    certify,
    run_certification,
)

__all__ = [
    "CertificationConfig",
    "CertificationError",
    "CertificationReport",
    "ControlResult",
    "FULL_SCOPES",
    "JournalEntry",
    "LEVEL_INTEGRATION",
    "LEVEL_IN_PROCESS",
    "LEVEL_MANUAL",
    "LIMIT_IDE_AUDIT",
    "MODULE_MAX_BYTES",
    "MODULE_MAX_LINES",
    "REPORT_FILENAME",
    "REPORT_MARKDOWN_FILENAME",
    "SCHEMA_ID",
    "STATUS_FAIL",
    "STATUS_PASS",
    "STORY_ID",
    "SURFACE_CHARGEMENT",
    "SURFACE_ERREUR",
    "SURFACE_INITIAL_VIDE",
    "SURFACE_SUCCES",
    "VERDICT_CONFORME",
    "VERDICT_NON_CONFORME",
    "certify",
    "default_report_dir",
    "dynamic_counters",
    "read_certification_report",
    "render_markdown",
    "report_paths",
    "run_certification",
    "surface_state_of",
    "utc_now_iso",
    "write_certification_report",
]
