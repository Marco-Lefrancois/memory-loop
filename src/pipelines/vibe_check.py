# Shim de rétrocompatibilité (MLOOP-170-BE, ADR-0202).
# Ce fichier délègue vers le package src/pipelines/vibe_check/ refactoré.
# Les 19 fichiers callers existants n'ont PAS besoin d'être modifiés.
from src.pipelines.vibe_check import run_vibe_check, detect_project_lifecycle_stage  # noqa: F401

__all__ = ["run_vibe_check", "detect_project_lifecycle_stage"]
