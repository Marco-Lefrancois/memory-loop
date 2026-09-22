"""
src/dashboard/routers/archify.py — Router FastAPI pour l'inventaire et la restitution des
diagrammes Archify dans le Dashboard Cockpit (MLOOP-150-BE, ADR-0369).

Expose deux endpoints :
  - GET /api/archify/list?project=<nom>   : Inventaire multi-tenant (framework + projet résolu)
  - GET /api/archify/html?file=<nom>&project=<nom> : Restitution HTML standalone

Sécurité : anti path-traversal strict sur allowlist de racines (OQ-150-01).
Compilation : subprocess à la volée avec timeout explicite (60s) + verrou threading (OQ-150-04).
Conforme ADR-0202 (<300 lignes), ADR-0369 (robustesse Python senior) et OQ-150-01 à OQ-150-05.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from src.dashboard.project_utils import resolve_project_canonical_name, resolve_project_path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/archify", tags=["Archify Diagrams"])

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ── Artefacts discriminants (OQ-150-05) ──────────────────────────────────────
_ARCHITECTURE_SUFFIX = ".architecture.html"
_LIFECYCLE_SUFFIX = ".lifecycle.html"
_KNOWN_SUFFIXES = (_ARCHITECTURE_SUFFIX, _LIFECYCLE_SUFFIX)
_JSON_SUFFIX = ".json"

# ── Verrous anti-rebond par chemin d'artefact (OQ-150-04) ────────────────────
_compile_locks: Dict[str, threading.Lock] = {}
_compile_locks_guard = threading.Lock()


def _get_compile_lock(artifact_key: str) -> threading.Lock:
    """Retourne (ou crée) le verrou de compilation pour un artefact donné."""
    with _compile_locks_guard:
        if artifact_key not in _compile_locks:
            _compile_locks[artifact_key] = threading.Lock()
        return _compile_locks[artifact_key]


# ── Allowlist des racines autorisées (OQ-150-01 amendée multi-tenant) ────────


def _get_allowed_roots(project_name: Optional[str] = None) -> List[Path]:
    """
    Calcule la liste des racines autorisées pour l'accès aux artefacts Archify.
    Racines framework fixes + racine projet résolu (multi-tenant).
    """
    roots: List[Path] = [
        REPO_ROOT / "tools" / "archify" / "showcase",
        REPO_ROOT / "docs" / "05-assets",
    ]
    if project_name:
        proj_root = resolve_project_path(project_name)
        if proj_root != REPO_ROOT:
            roots.append(proj_root)
        # Inclure aussi le sous-dossier docs/05-assets du projet si présent
        proj_assets = proj_root / "docs" / "05-assets"
        if proj_assets.exists() and proj_assets not in roots:
            roots.append(proj_assets)
    return roots


def _assert_within_allowlist(candidate: Path, allowed_roots: List[Path]) -> None:
    """
    Lève HTTPException(403) si le chemin résolu n'est sous aucune racine allowlistée.
    Anti path-traversal : compare les chemins résolus (.resolve()).
    """
    resolved = candidate.resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return  # chemin sécurisé
        except ValueError:
            continue
    raise HTTPException(
        status_code=403,
        detail=(
            f"Accès interdit : le chemin demandé est hors des racines autorisées. "
            f"Seules les racines Archify framework et du projet résolu sont accessibles."
        ),
    )


def _classify_artifact_type(filename: str) -> str:
    """Discrimine le type d'artefact depuis le nom de fichier (OQ-150-05)."""
    if filename.endswith(".architecture.html"):
        return "architecture"
    if filename.endswith(".lifecycle.html"):
        return "lifecycle"
    # Extensions supplémentaires tolérées (sequence, workflow, dataflow)
    for seg in (".sequence.", ".workflow.", ".dataflow."):
        if seg in filename:
            return seg.strip(".")
    return "architecture"


def _scan_artifacts(allowed_roots: List[Path]) -> List[Dict[str, Any]]:
    """
    Parcourt récursivement toutes les racines allowlistées et retourne la liste
    des artefacts HTML Archify avec leurs métadonnées.
    Lecture disque directe, zéro cache (OQ-150-03).
    """
    artifacts: List[Dict[str, Any]] = []
    seen_paths: set = set()

    for root in allowed_roots:
        if not root.exists() or not root.is_dir():
            continue
        try:
            for f in root.rglob("*.html"):
                if not f.is_file():
                    continue
                # Filtre : seuls les fichiers avec suffixe Archify reconnu
                name = f.name
                if not any(
                    name.endswith(s)
                    for s in (
                        ".architecture.html",
                        ".lifecycle.html",
                        ".sequence.html",
                        ".workflow.html",
                        ".dataflow.html",
                    )
                ):
                    continue
                real = f.resolve()
                if real in seen_paths:
                    continue
                seen_paths.add(real)
                try:
                    rel = f.relative_to(REPO_ROOT).as_posix()
                except ValueError:
                    rel = f.name

                artifacts.append(
                    {
                        "name": name,
                        "type": _classify_artifact_type(name),
                        "size_bytes": f.stat().st_size,
                        "relative_path": rel,
                    }
                )
        except Exception as exc:
            logger.debug(
                "Erreur lors du scan des artefacts Archify dans une racine",
                exc_info=True,
                extra={
                    "component": "dashboard.archify",
                    "operation": "scan_artifacts",
                    "root": str(root),
                    "error": str(exc),
                },
            )

    # Tri déterministe par chemin relatif
    artifacts.sort(key=lambda a: a["relative_path"])
    return artifacts


def _find_html_file(file_name: str, allowed_roots: List[Path]) -> Optional[Path]:
    """
    Cherche le fichier HTML dans toutes les racines allowlistées (récursif).
    Retourne le premier chemin trouvé, ou None si absent.
    """
    for root in allowed_roots:
        if not root.exists():
            continue
        try:
            for candidate in root.rglob(file_name):
                if candidate.is_file():
                    _assert_within_allowlist(candidate, allowed_roots)  # lève 403 si hors allowlist
                    return candidate
        except HTTPException:
            raise
        except Exception as exc:
            logger.debug(
                "Erreur de scan lors de la recherche d'un artefact HTML",
                exc_info=True,
                extra={
                    "component": "dashboard.archify",
                    "operation": "find_html_file",
                    "root": str(root),
                    "file_name": file_name,
                    "error": str(exc),
                },
            )
    return None


def _find_json_spec(html_name: str, allowed_roots: List[Path]) -> Optional[Path]:
    """
    Cherche un fichier JSON de spec Archify correspondant au HTML attendu.
    Exemple : foo.architecture.html -> foo.architecture.json
    """
    # Déduire le nom JSON depuis le nom HTML
    json_name = None
    for suffix in (
        ".architecture.html",
        ".lifecycle.html",
        ".sequence.html",
        ".workflow.html",
        ".dataflow.html",
    ):
        if html_name.endswith(suffix):
            base = html_name[: -len(suffix)]
            type_part = suffix.lstrip(".").replace(".html", "")
            json_name = f"{base}.{type_part}.json"
            break
    if not json_name:
        return None

    for root in allowed_roots:
        if not root.exists():
            continue
        try:
            for candidate in root.rglob(json_name):
                if candidate.is_file():
                    return candidate
        except Exception as exc:
            logger.debug(
                "Erreur scan JSON spec Archify",
                exc_info=True,
                extra={
                    "component": "dashboard.archify",
                    "operation": "find_json_spec",
                    "root": str(root),
                    "json_name": json_name,
                    "error": str(exc),
                },
            )
    return None


def _compile_on_the_fly(json_spec: Path, html_name: str) -> Optional[Path]:
    """
    Lance archify_runner.py en subprocess avec timeout=60s pour compiler le HTML manquant.
    Verrou threading par artifact_key pour éviter les compilations parallèles (Pilier 3).
    Retourne le chemin HTML si la compilation réussit, None sinon.
    Lève HTTPException(500) si la compilation échoue ou dépasse le timeout.
    """
    artifact_key = str(json_spec.resolve())
    lock = _get_compile_lock(artifact_key)

    runner = REPO_ROOT / "tools" / "archify" / "archify_runner.py"
    output_dir = json_spec.parent
    expected_html = output_dir / html_name

    with lock:
        # Double-check : le HTML a peut-être été compilé pendant l'attente du verrou
        if expected_html.exists():
            return expected_html

        logger.info(
            "Compilation Archify à la volée déclenchée",
            extra={
                "component": "dashboard.archify",
                "operation": "compile_on_the_fly",
                "json_spec": str(json_spec),
                "output_dir": str(output_dir),
            },
        )
        try:
            result = subprocess.run(
                [sys.executable, str(runner), str(json_spec), "--output-dir", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            logger.error(
                "Timeout compilation Archify à la volée (60s dépassées)",
                exc_info=True,
                extra={
                    "component": "dashboard.archify",
                    "operation": "compile_on_the_fly",
                    "json_spec": str(json_spec),
                    "timeout": 60,
                    "error": str(exc),
                },
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Timeout lors de la compilation Archify pour '{html_name}' "
                    f"(limite : 60s). Exécutez manuellement : python src/swarm.py archify"
                ),
            )
        except Exception as exc:
            logger.error(
                "Erreur inattendue lors de la compilation Archify à la volée",
                exc_info=True,
                extra={
                    "component": "dashboard.archify",
                    "operation": "compile_on_the_fly",
                    "json_spec": str(json_spec),
                    "error": str(exc),
                },
            )
            raise HTTPException(
                status_code=500,
                detail=f"Erreur interne lors de la compilation Archify : {exc}",
            )

        if result.returncode != 0:
            logger.error(
                "Compilation Archify échouée (code de sortie non nul)",
                extra={
                    "component": "dashboard.archify",
                    "operation": "compile_on_the_fly",
                    "json_spec": str(json_spec),
                    "returncode": result.returncode,
                    "stderr": result.stderr[:500],
                },
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Échec de la compilation Archify pour '{html_name}' "
                    f"(code {result.returncode}). Stderr : {result.stderr[:200]}"
                ),
            )

        if expected_html.exists():
            logger.info(
                "Compilation Archify réussie",
                extra={
                    "component": "dashboard.archify",
                    "operation": "compile_on_the_fly",
                    "output": str(expected_html),
                },
            )
            return expected_html

        logger.error(
            "Compilation Archify terminée sans erreur mais HTML absent",
            extra={
                "component": "dashboard.archify",
                "operation": "compile_on_the_fly",
                "expected_html": str(expected_html),
                "returncode": result.returncode,
            },
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"Compilation Archify terminée mais le fichier '{html_name}' est introuvable. "
                f"Exécutez : python src/swarm.py archify"
            ),
        )


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────


@router.get("/list")
def list_archify_artifacts(
    project: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Inventaire multi-tenant des diagrammes Archify disponibles sur disque.

    Agrège les artefacts du framework (tools/archify/showcase/, docs/05-assets/)
    et du projet résolu (Projects/<projet>/) avec lecture disque directe (zéro cache).
    Chaque artefact expose : name, type, size_bytes, relative_path.
    Si aucun artefact n'est trouvé, suggère la commande CLI de compilation.
    """
    proj_name = resolve_project_canonical_name(project)
    allowed_roots = _get_allowed_roots(proj_name)
    artifacts = _scan_artifacts(allowed_roots)

    response: Dict[str, Any] = {
        "project": proj_name,
        "total_artifacts": len(artifacts),
        "artifacts": artifacts,
    }
    if len(artifacts) == 0:
        response["message"] = (
            "Aucun diagramme Archify trouvé pour ce projet. "
            "Lancez : python src/swarm.py archify --project " + proj_name
        )
    return response


@router.get("/html", response_class=HTMLResponse)
def get_archify_html(
    file: str = Query(
        ..., description="Nom du fichier HTML Archify (ex: mloop-framework.architecture.html)"
    ),
    project: Optional[str] = Query(None),
) -> HTMLResponse:
    """
    Restitue un diagramme HTML Archify standalone (200).

    - 403 : chemin hors allowlist (anti path-traversal)
    - 404 : fichier absent de toutes les racines (commande CLI suggérée)
    - 500 : échec ou timeout de la compilation à la volée
    - Compilation subprocess à la volée si JSON de spec présent mais HTML absent (OQ-150-04)
    """
    proj_name = resolve_project_canonical_name(project)
    allowed_roots = _get_allowed_roots(proj_name)

    # Rejet immédiat des tentatives de path-traversal sur le paramètre brut
    if ".." in file or "/" in file or "\\" in file:
        raise HTTPException(
            status_code=403,
            detail="Accès interdit : le nom de fichier contient des séquences de traversal interdites.",
        )

    # Recherche du HTML dans l'allowlist
    html_path = _find_html_file(file, allowed_roots)

    if html_path is None:
        # Tentative de compilation à la volée si un JSON de spec existe
        json_spec = _find_json_spec(file, allowed_roots)
        if json_spec is not None:
            html_path = _compile_on_the_fly(json_spec, file)
        else:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Diagramme Archify '{file}' introuvable dans les racines autorisées. "
                    f"Compilez-le avec : python src/swarm.py archify --project {proj_name}"
                ),
            )

    if html_path is None:
        # Garde de sécurité statique : ne devrait jamais être atteint (compile_on_the_fly lève 500)
        raise HTTPException(status_code=500, detail="Compilation Archify sans résultat inattendu.")

    try:
        content = html_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        logger.error(
            "Erreur lecture du fichier HTML Archify",
            exc_info=True,
            extra={
                "component": "dashboard.archify",
                "operation": "get_archify_html",
                "html_path": str(html_path),
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture du diagramme '{file}'.",
        ) from exc

    return HTMLResponse(
        content=content,
        media_type="text/html; charset=utf-8",
    )
