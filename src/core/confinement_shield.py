"""
mLoop Confinement Shield (ADR-0379)
Bouclier déterministe au runtime interdisant tout outrepassage par les modèles paresseux (Lazy LLMs).

Verrous d'exécution :
1. Tool Whitelisting : Interception bloquante si l'outil n'est pas dans skills: [...]
2. Filesystem Write-Jail : Interception bloquante sur tentative d'écriture dans des dossiers interdits (Check 13)
3. Proof-of-Work Validator : Vérification SHA-256 et ancrage épistémique du source_manifest.json
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import logging
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from src.core.standards_graph import StandardsGraphStore

logger = logging.getLogger("mLoop.ConfinementShield")

_THREAD_LOCAL = threading.local()


# ─── Exceptions Métier de Sécurité (ADR-0369 / ADR-0379) ────────────────────

class ConfinementSecurityError(PermissionError):
    """Classe de base pour toutes les violations de confinement runtime."""


class PermissionDeniedError(ConfinementSecurityError):
    """Levée lorsqu'un agent tente d'invoquer une compétence ou un outil non autorisé."""


class SandboxViolationError(ConfinementSecurityError):
    """Levée lorsqu'un agent tente d'écrire en dehors de son périmètre de système de fichiers autorisé."""


class ProofOfWorkError(ConfinementSecurityError):
    """Levée lorsque les preuves cryptographiques ou documentaires d'une phase sont invalides."""


# ─── Gestionnaire de Contexte d'Exécution Agentique ─────────────────────────

class AgentContext:
    """
    Gestionnaire de contexte thread-safe définissant l'identité de l'agent actif.
    Exemple d'utilisation :
        with AgentContext("explorer", project_path=Path("Projects/MonProjet")):
            # Toute écriture ou appel d'outil est strictement surveillé et confiné
            ...
    """

    def __init__(self, agent_name: str, project_path: Optional[Path] = None):
        self.agent_name = agent_name
        self.project_path = project_path
        self._prev_agent = getattr(_THREAD_LOCAL, "active_agent", None)
        self._prev_project = getattr(_THREAD_LOCAL, "active_project", None)

    def __enter__(self) -> AgentContext:
        _THREAD_LOCAL.active_agent = self.agent_name
        _THREAD_LOCAL.active_project = self.project_path
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        _THREAD_LOCAL.active_agent = self._prev_agent
        _THREAD_LOCAL.active_project = self._prev_project

    @classmethod
    def get_current_agent_name(cls) -> Optional[str]:
        return getattr(_THREAD_LOCAL, "active_agent", None)

    @classmethod
    def get_current_project_path(cls) -> Optional[Path]:
        return getattr(_THREAD_LOCAL, "active_project", None)


# ─── Bouclier Déterministe : ConfinementShield ───────────────────────────────

class ConfinementShield:
    """
    Bouclier de protection et de confinement déterministe pour le runtime mLoop.
    """

    @classmethod
    def verify_skill_access(
        cls,
        skill_name: str,
        agent_name: Optional[str] = None,
        project_path: Optional[Path] = None,
    ) -> bool:
        """
        Vérifie si la compétence demandée est explicitement autorisée pour l'agent actif.
        Si l'agent n'est pas dans sa whitelist, consigne une anomalie et lève PermissionDeniedError.
        """
        active_agent_name = agent_name or AgentContext.get_current_agent_name()
        if not active_agent_name:
            # Aucun agent spécifique actif (ex: script CLI direct sans contexte agent) : autorisé
            return True

        store = StandardsGraphStore.get_instance()
        agent = store.get_agent(active_agent_name)
        if not agent:
            # Si le profil agent n'est pas trouvé dans les standards
            logger.warning(f"Agent '{active_agent_name}' non répertorié dans StandardsGraph.")
            return True

        # Normaliser le nom de la compétence
        clean_skill = skill_name.lower().replace("skill://", "").strip()

        # Si l'agent a une liste de skills vide, il n'a droit à aucun outil spécialisé
        allowed_skills = {s.lower() for s in agent.skills}

        if clean_skill not in allowed_skills:
            msg = (
                f"[CONFINEMENT 403] La compétence '{clean_skill}' est STRICTEMENT INTERDITE "
                f"pour l'agent '{active_agent_name}'. "
                f"Compétences déclarées dans {agent.file_path} : {sorted(list(allowed_skills))}"
            )
            # Consigner l'anomalie
            p_path = project_path or AgentContext.get_current_project_path()
            if p_path:
                cls.record_anomaly(
                    p_path,
                    anomaly_type="UNAUTHORIZED_SKILL_INVOCATION",
                    details=f"Agent '{active_agent_name}' a tenté d'invoquer '{clean_skill}'.",
                )
            logger.error(msg)
            raise PermissionDeniedError(msg)

        return True

    @classmethod
    def verify_write_path(
        cls,
        target_path: Path,
        agent_name: Optional[str] = None,
        project_path: Optional[Path] = None,
    ) -> bool:
        """
        Vérifie si le chemin d'écriture visé est autorisé pour l'agent actif.
        Lève SandboxViolationError si le chemin est interdit ou non autorisé.
        """
        active_agent_name = agent_name or AgentContext.get_current_agent_name()
        if not active_agent_name:
            return True

        store = StandardsGraphStore.get_instance()
        agent = store.get_agent(active_agent_name)
        if not agent:
            return True

        p_root = project_path or AgentContext.get_current_project_path()
        try:
            rel_path_str = (
                str(target_path.relative_to(p_root)).replace("\\", "/")
                if p_root and target_path.is_relative_to(p_root)
                else str(target_path).replace("\\", "/")
            )
        except Exception:
            rel_path_str = str(target_path).replace("\\", "/")

        # 1. Vérifier les interdictions explicites (forbidden_write_paths)
        for pattern in agent.forbidden_write_paths:
            norm_pattern = pattern.replace("\\", "/")
            if fnmatch.fnmatch(rel_path_str, norm_pattern) or fnmatch.fnmatch(
                rel_path_str, norm_pattern.rstrip("/*")
            ):
                msg = (
                    f"[CONFINEMENT 403] Écriture STRICTEMENT INTERDITE dans '{rel_path_str}' "
                    f"pour l'agent '{active_agent_name}' (Motif interdit : '{pattern}')."
                )
                if p_root:
                    cls.record_anomaly(
                        p_root,
                        anomaly_type="FORBIDDEN_FILESYSTEM_WRITE",
                        details=f"Agent '{active_agent_name}' a tenté d'écrire dans '{rel_path_str}'.",
                    )
                logger.error(msg)
                raise SandboxViolationError(msg)

        # 2. Vérifier les autorisations positives (allowed_write_paths)
        if agent.allowed_write_paths:
            allowed = False
            for pattern in agent.allowed_write_paths:
                norm_pattern = pattern.replace("\\", "/")
                if fnmatch.fnmatch(rel_path_str, norm_pattern) or fnmatch.fnmatch(
                    rel_path_str, norm_pattern.rstrip("/*")
                ):
                    allowed = True
                    break
            if not allowed:
                msg = (
                    f"[CONFINEMENT 403] Écriture hors périmètre dans '{rel_path_str}' "
                    f"pour l'agent '{active_agent_name}'. "
                    f"Chemins autorisés : {agent.allowed_write_paths}"
                )
                if p_root:
                    cls.record_anomaly(
                        p_root,
                        anomaly_type="OUT_OF_BOUNDS_WRITE",
                        details=f"Agent '{active_agent_name}' a tenté d'écrire hors périmètre dans '{rel_path_str}'.",
                    )
                logger.error(msg)
                raise SandboxViolationError(msg)

        return True

    @classmethod
    def verify_phase_1_proof_of_work(cls, project_path: Path) -> Tuple[bool, List[str]]:
        """
        Vérifie de façon déterministe que la Phase 1 (INGEST & EXPLORE) dispose de ses preuves de travail :
        1. Le source_manifest.json existe et est valide.
        2. 100% des fichiers de reference/ sont référencés avec le bon hash SHA-256.
        3. Le champ what_it_actually_proves est renseigné.
        """
        violations: List[str] = []
        manifest_file = project_path / "docs" / "00-ingested" / "source_manifest.json"
        ref_dir = project_path / "reference"

        if not ref_dir.exists():
            return True, []

        ref_files = [f for f in ref_dir.rglob("*") if f.is_file() and f.name.lower() != "readme.md"]
        if not ref_files:
            return True, []  # Aucun document source à ingérer

        if not manifest_file.exists():
            violations.append("Fichier docs/00-ingested/source_manifest.json manquant.")
            return False, violations

        try:
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            sources = manifest_data.get("sources", [])
            manifest_by_path = {s.get("source_path"): s for s in sources if isinstance(s, dict)}

            for rf in ref_files:
                rel_str = str(rf.relative_to(project_path)).replace("\\", "/")
                entry = manifest_by_path.get(rel_str)
                if not entry:
                    violations.append(f"Document source non répertorié dans le manifeste : {rel_str}")
                    continue

                actual_sha = hashlib.sha256(rf.read_bytes()).hexdigest()
                manifest_sha = entry.get("sha256")
                if manifest_sha != actual_sha:
                    violations.append(
                        f"Empreinte SHA-256 divergente pour {rel_str} (Attendu: {manifest_sha}, Réel: {actual_sha})"
                    )

                proves = entry.get("what_it_actually_proves", "").strip()
                if not proves or proves.lower().startswith("[à documenter"):
                    violations.append(f"Preuve épistémique non documentée pour {rel_str} (what_it_actually_proves vide)")

        except Exception as e:
            violations.append(f"Erreur de parsing du source_manifest.json : {e}")

        return (len(violations) == 0), violations

    @classmethod
    def record_anomaly(cls, project_path: Path, anomaly_type: str, details: str) -> None:
        """Enregistre une anomalie d'outrepassage dans docs/00-ingested/ingest_anomalies.json."""
        try:
            anomalies_file = project_path / "docs" / "00-ingested" / "ingest_anomalies.json"
            anomalies_file.parent.mkdir(parents=True, exist_ok=True)
            existing = []
            if anomalies_file.exists():
                try:
                    existing = json.loads(anomalies_file.read_text(encoding="utf-8"))
                    if not isinstance(existing, list):
                        existing = []
                except Exception:
                    existing = []

            existing.append({
                "timestamp": datetime.now().isoformat(),
                "agent": AgentContext.get_current_agent_name() or "unknown",
                "anomaly_type": anomaly_type,
                "details": details,
            })
            anomalies_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Impossible de consigner l'anomalie : {e}")
