"""
Moteur de sonde déterministe des runtimes d'agents aval (ADR-0377).

Inspiré du pattern catalogue d'AgentManager (agentmgr), mais 100% natif Python,
souverain, hors-ligne et conforme aux standards de robustesse senior (ADR-0369).
Vérifie la présence et la version des agents CLI utilisés pour le Dev Handoff et Herdr.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger("mloop.agent_probe")


class AgentAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    OUTDATED = "OUTDATED"
    MISSING = "MISSING"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


@dataclass(frozen=True)
class AgentDefinition:
    """Définition déclarative d'un agent CLI du catalogue."""
    id: str
    name: str
    bin_name: str
    version_args: list[str] = field(default_factory=lambda: ["--version"])
    version_regex: str = r"(\d+\.\d+(?:\.\d+)?)"
    min_version: str = "0.1.0"
    role: str = ""
    critical_in_stages: tuple[str, ...] = ("STAGE_BUILD",)


@dataclass
class AgentStatus:
    """Résultat de la sonde pour un agent donné."""
    definition: AgentDefinition
    availability: AgentAvailability
    installed_path: str | None = None
    detected_version: str | None = None
    error_message: str | None = None

    @property
    def is_usable(self) -> bool:
        return self.availability in (AgentAvailability.AVAILABLE, AgentAvailability.OUTDATED)


# SSOT du catalogue des agents aval mLoop (ADR-0377)
AGENT_CATALOG: dict[str, AgentDefinition] = {
    "herdr": AgentDefinition(
        id="herdr",
        name="Herdr PTY Orchestrator",
        bin_name="herdr",
        version_args=["--version"],
        min_version="0.4.0",
        role="PTY Worker Isolation (ADR-0346)",
        critical_in_stages=("STAGE_PLAN_GRILL", "STAGE_BUILD", "STAGE_VALIDATE", "STAGE_RUN"),
    ),
    "opencode": AgentDefinition(
        id="opencode",
        name="OpenCode",
        bin_name="opencode",
        version_args=["--version"],
        min_version="1.0.0",
        role="Universal Code Generator (ADR-0375)",
        critical_in_stages=("STAGE_BUILD",),
    ),
    "claude-code": AgentDefinition(
        id="claude-code",
        name="Claude Code",
        bin_name="claude",
        version_args=["--version"],
        min_version="1.0.0",
        role="Deep Refactoring & Spike",
        critical_in_stages=(),
    ),
    "cline": AgentDefinition(
        id="cline",
        name="Cline CLI",
        bin_name="cline",
        version_args=["--version"],
        min_version="3.0.0",
        role="Build Worker Délégué (ADR-0346)",
        critical_in_stages=("STAGE_BUILD",),
    ),
    "aider": AgentDefinition(
        id="aider",
        name="Aider",
        bin_name="aider",
        version_args=["--version"],
        min_version="0.50.0",
        role="Pair Programming CLI",
        critical_in_stages=(),
    ),
    "cursor-cli": AgentDefinition(
        id="cursor-cli",
        name="Cursor CLI",
        bin_name="cursor",
        version_args=["--version"],
        min_version="2024.0.0",
        role="IDE Headless Agent",
        critical_in_stages=(),
    ),
}


class AgentProbeProtocol(Protocol):
    """Typage structurel pour la sonde d'agents (ADR-0369 Standard 1)."""
    def probe(self, agent_id: str) -> AgentStatus: ...
    def probe_all(self) -> list[AgentStatus]: ...
    def check_readiness(self, stage: str) -> tuple[bool, list[str]]: ...


class AgentProbe:
    """Moteur de sonde des runtimes d'agents locaux (ADR-0377)."""

    def __init__(self, catalog: dict[str, AgentDefinition] | None = None, probe_timeout: float = 2.0):
        self.catalog = catalog or AGENT_CATALOG
        self.timeout = probe_timeout

    def probe(self, agent_id: str) -> AgentStatus:
        """Sonde un agent par son identifiant de catalogue."""
        defn = self.catalog.get(agent_id)
        if not defn:
            return AgentStatus(
                definition=AgentDefinition(id=agent_id, name=agent_id, bin_name=agent_id),
                availability=AgentAvailability.ERROR,
                error_message=f"Agent '{agent_id}' inconnu du catalogue mLoop",
            )

        resolved_path = shutil.which(defn.bin_name)
        if not resolved_path:
            logger.debug(
                f"Agent '{defn.id}' non trouvé dans le PATH.",
                extra={"agent_id": defn.id, "bin": defn.bin_name},
            )
            return AgentStatus(
                definition=defn,
                availability=AgentAvailability.MISSING,
                error_message="Binaire introuvable dans le PATH",
            )

        cmd = [resolved_path] + defn.version_args
        try:
            # Deadline d'exécution stricte (ADR-0369 Standard 3)
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
            output = f"{res.stdout}\n{res.stderr}".strip()
            match = re.search(defn.version_regex, output)
            detected_ver = match.group(1) if match else "inconnue"

            # Évaluation de la version minimale
            availability = AgentAvailability.AVAILABLE
            if detected_ver != "inconnue" and self._is_version_older(detected_ver, defn.min_version):
                availability = AgentAvailability.OUTDATED

            return AgentStatus(
                definition=defn,
                availability=availability,
                installed_path=resolved_path,
                detected_version=detected_ver,
            )
        except subprocess.TimeoutExpired:
            logger.warning(
                f"Timeout lors de l'exécution de '{cmd}' (> {self.timeout}s).",
                extra={"agent_id": defn.id, "timeout": self.timeout},
            )
            return AgentStatus(
                definition=defn,
                availability=AgentAvailability.TIMEOUT,
                installed_path=resolved_path,
                error_message=f"Exécution suspendue (timeout {self.timeout}s)",
            )
        except Exception as exc:
            logger.error(
                f"Erreur inattendue lors de la sonde de '{defn.id}': {exc}",
                exc_info=True,
                extra={"agent_id": defn.id},
            )
            return AgentStatus(
                definition=defn,
                availability=AgentAvailability.ERROR,
                installed_path=resolved_path,
                error_message=str(exc),
            )

    def probe_all(self) -> list[AgentStatus]:
        """Sonde l'ensemble des agents répertoriés dans le catalogue."""
        return [self.probe(agent_id) for agent_id in self.catalog]

    def check_readiness(self, stage: str) -> tuple[bool, list[str]]:
        """
        Vérifie si les agents requis pour une étape du cycle sont opérationnels.
        Utilisé par le 16e contrôle Vibe-Check (ADR-0377).
        """
        norm_stage = stage.upper().replace("-", "_")
        statuses = self.probe_all()
        violations: list[str] = []

        for st in statuses:
            defn = st.definition
            # Si l'agent est requis dans cette étape
            if any(req in norm_stage for req in defn.critical_in_stages):
                if not st.is_usable:
                    violations.append(
                        f"Agent requis '{defn.name}' ({defn.bin_name}) manquant ou inaccessible pour l'étape {stage} : {st.error_message or st.availability.value}"
                    )

        # Règle spéciale Dev Handoff en Phase BUILD : au moins UN agent de génération de code doit être présent
        if "BUILD" in norm_stage:
            code_agents = [st for st in statuses if st.definition.id in ("opencode", "claude-code", "aider") and st.is_usable]
            if not code_agents:
                violations.append("Aucun agent de dev aval utilisable (opencode, claude-code ou aider) pour la Phase BUILD.")

        is_ready = len(violations) == 0
        return is_ready, violations

    @staticmethod
    def _is_version_older(current: str, target: str) -> bool:
        """Compare deux chaînes semver simples a.b.c."""
        try:
            curr_parts = [int(p) for p in re.findall(r"\d+", current)]
            target_parts = [int(p) for p in re.findall(r"\d+", target)]
            return curr_parts < target_parts
        except Exception:
            return False


def render_agent_report(statuses: list[AgentStatus], json_format: bool = False) -> str:
    """Formate le rapport d'audit des agents locaux avec esthétique CLI épurée."""
    if json_format:
        import json
        payload = [
            {
                "id": st.definition.id,
                "name": st.definition.name,
                "bin": st.definition.bin_name,
                "availability": st.availability.value,
                "version": st.detected_version,
                "path": st.installed_path,
                "role": st.definition.role,
                "error": st.error_message,
            }
            for st in statuses
        ]
        return json.dumps(payload, indent=2, ensure_ascii=False)

    lines = [
        "AGENT                 BINAIRE     STATUT         VERSION      RÔLE ARCHITECTURAL",
        "───────────────────── ─────────── ────────────── ──────────── ──────────────────────────────────────────",
    ]
    for st in statuses:
        name_pad = st.definition.name[:21].ljust(21)
        bin_pad = st.definition.bin_name[:11].ljust(11)
        ver_pad = (st.detected_version or "-")[:12].ljust(12)
        role_pad = st.definition.role

        if st.availability == AgentAvailability.AVAILABLE:
            stat_pad = "● DISPONIBLE  "
        elif st.availability == AgentAvailability.OUTDATED:
            stat_pad = "⬆ OBSOLÈTE    "
        elif st.availability == AgentAvailability.MISSING:
            stat_pad = "○ INTROUVABLE "
        elif st.availability == AgentAvailability.TIMEOUT:
            stat_pad = "⏱ TIMEOUT     "
        else:
            stat_pad = "✖ ERREUR      "

        lines.append(f"{name_pad} {bin_pad} {stat_pad} {ver_pad} {role_pad}")

    lines.append("───────────────────── ─────────── ────────────── ──────────── ──────────────────────────────────────────")
    lines.append("Légende : ● Disponible et conforme | ⬆ Mise à jour recommandée | ○ Absent du PATH")
    return "\n".join(lines)
