# -*- coding: utf-8 -*-
"""
memory_bank_bridge.py - Bridge de Mémoire Bidirectionnel mLoop <-> Cline Memory Bank.

Conforme à ADR-0202 (<=300L), ADR-0375 (5 Phases) et EPIC-26 (MLOOP-260-BE Palier 2).
Génère de façon idempotente les 6 fichiers standardisés de la Memory Bank Cline sous
Projects/<project_name>/memory/memory-bank/ avec réconciliation inverse des notes de session.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mloop.bridges.cline.memory_bank")

MEMORY_BANK_DIR_NAME = "memory-bank"


class MemoryBankBridge:
    """Générateur et moissonneur de sidecars Memory Bank pour Cline."""

    def __init__(self, workspace_root: Optional[Path] = None, project_name: str = "mLoop") -> None:
        self.root = workspace_root or Path.cwd()
        self.project_name = project_name
        self.project_dir = (
            self.root / "Projects" / project_name
            if (self.root / "Projects" / project_name).exists()
            else self.root
        )
        self.bank_dir = self.project_dir / "memory" / MEMORY_BANK_DIR_NAME

    def ensure_bank_dir(self) -> Path:
        """Crée le dossier memory/memory-bank/ si inexistant."""
        self.bank_dir.mkdir(parents=True, exist_ok=True)
        return self.bank_dir

    def _safe_write_idempotent(self, file_path: Path, content: str) -> bool:
        """Écrit le fichier uniquement si son contenu a changé (idempotence)."""
        stripped_content = content.strip() + "\n"
        if file_path.exists():
            existing = file_path.read_text(encoding="utf-8")
            if existing == stripped_content:
                return False
        file_path.write_text(stripped_content, encoding="utf-8")
        return True

    def build_projectbrief(self) -> str:
        """Génère projectbrief.md (Fondations et vision du projet)."""
        return (
            f"# Project Brief — {self.project_name}\n\n"
            "## 1. Vision & Core Mission\n"
            "Memory Loop (mLoop) est un framework de gouvernance et d'orchestration agentique "
            "souverain multi-LLMs. Il sert de Cerveau d'État et de Fournisseur Universel de "
            "Spécifications (Universal Dev Handoff) pour guider des agents de développement aval.\n\n"
            "## 2. Core Requirements\n"
            "- Souveraineté épistémique : Source Unique de Vérité (SSOT) 100% Markdown & JSON.\n"
            "- Cycle de vie en 5 phases universelles (ADR-0375) : INGEST, PLAN, BUILD, VALIDATE, SHIP.\n"
            "- Interdiction formelle du saut de phase (ADR-0339/0375).\n"
            "- Preuve épistémique et traçabilité radicale via EvidencePacks (ADR-0375).\n"
            "- Rigueur 360° Zéro Blindspot (ADR-0376).\n"
            "- Plafond modulaire strict <= 300 lignes par fichier Python (ADR-0202).\n"
        )

    def build_product_context(self) -> str:
        """Génère productContext.md (Problèmes résolus et expérience utilisateur)."""
        return (
            f"# Product Context — {self.project_name}\n\n"
            "## 1. Why this project exists\n"
            "Les agents de code autonomes souffrent fréquemment d'amnésie de contexte, de sauts "
            "de phase intempestifs et de destructions silencieuses de code. mLoop élimine ces dérives.\n\n"
            "## 2. User Workflows\n"
            "1. Cadrage & Ingestion : Ingestion des documents et code source sans altération.\n"
            "2. Analyse & Grill-Me : Entrevue contradictoire 1:1 pour éliminer les zones d'ombre.\n"
            "3. Build Délégué : Délégation d'implémentation à des workers isolés via Herdr.\n"
            "4. Certification QA : Fact-Check NLI, Vibe-Check pré-vol et suites pytest.\n"
            "5. Livraison Fail-Closed : Publication Git et Jira sous validation stricte des invariants.\n"
        )

    def build_system_patterns(self) -> str:
        """Génère systemPatterns.md (Architecture, patrons et ADRs clés)."""
        return (
            f"# System Patterns — {self.project_name}\n\n"
            "## 1. Architecture Globale\n"
            "- Orchestration Bimodale : OpenCode (Headless/CI/Fast) + Cline (Plan-Lock/Teams/IDE).\n"
            "- Isolation Out-of-Process : Herdr gère les sessions dans des fenêtres PTY isolées (ADR-0346).\n"
            "- Fallback Déterministe : OpenCode est le filet de sécurité inviolable advenant un échec de Cline.\n\n"
            "## 2. Key Architecture Decision Records (ADRs)\n"
            "- ADR-0202 : Modularité interne et plafond strict de 300 lignes par fichier.\n"
            "- ADR-0346 : Registre multi-runtimes des workers Herdr.\n"
            "- ADR-0375 : Réalignement du cycle de vie en 5 phases universelles et EvidencePacks.\n"
            "- ADR-0376 : Standard de rigueur d'ingénierie et audit 360° Zéro Blindspot en 7 couches.\n"
            "- ADR-0377 : Sonde et diagnostic déterministe des runtimes agents aval.\n\n"
            "## 3. Invariants Inviolables\n"
            "- Pas de suppression silencieuse de code.\n"
            "- Pas de saut de phase : mode --plan obligatoire en Phase 2.\n"
            "- Typage strict et gestion des shims Windows (`.cmd` / `.ps1`).\n"
        )

    def build_tech_context(self) -> str:
        """Génère techContext.md (Technologies, dépendances et commandes CLI)."""
        return (
            f"# Tech Context — {self.project_name}\n\n"
            "## 1. Stack Technique\n"
            "- Langage : Python 3.11+ (Typage strict, dataclasses, Protocol).\n"
            "- Orchestration PTY : Herdr (v0.8.0+).\n"
            "- Runtimes Workers : OpenCode (v1.18.x), Cline (v3.0.x).\n"
            "- Tests & Qualité : pytest, pytest-asyncio, Vibe-Check (23 contrôles déterministes).\n"
            "- Stockage & Indexation : SQLite FTS5, Hypergraphe sémantique JSON.\n\n"
            "## 2. Commandes CLI Souveraines mLoop\n"
            "```powershell\n"
            "python src/swarm.py doctor --agents\n"
            "python src/swarm.py sync --project mLoop\n"
            "python src/swarm.py vibe-check --project mLoop\n"
            "python src/swarm.py worker-spawn --kind cline --story <ID> --project mLoop\n"
            "python src/swarm.py worker-spawn --kind opencode --story <ID> --project mLoop\n"
            "```\n"
        )

    def _extract_active_stories(self) -> List[Dict[str, Any]]:
        """Extrait les récits du sprint backlog avec statut normalisé."""
        stories = []
        backlog_path = self.project_dir / "backlog" / "sprint_backlog.md"
        if not backlog_path.exists():
            return stories
        content = backlog_path.read_text(encoding="utf-8")
        row_regex = re.compile(
            r"\|\s*\[([ x\-])\]\s*\|\s*\*\*([A-Z0-9_\-]+)\*\*\s*\|.*?\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
        )
        for line in content.splitlines():
            m = row_regex.search(line)
            if m:
                state, story_id, comp, title, grill, status = (
                    m.group(1).strip(),
                    m.group(2).strip(),
                    m.group(3).strip(),
                    m.group(4).strip(),
                    m.group(5).strip(),
                    m.group(6).strip(),
                )
                stories.append(
                    {
                        "id": story_id,
                        "title": title,
                        "component": comp,
                        "grill": grill,
                        "status": status,
                        "checked": state == "x",
                    }
                )
        return stories

    def build_active_context(self) -> str:
        """Génère activeContext.md (Focus chirurgical du sprint actif - Option A)."""
        stories = self._extract_active_stories()
        # Focus chirurgical : READY_FOR_DEV, IN_PROGRESS, BLOCKED et 3 derniers terminés
        active_stories = [
            s
            for s in stories
            if "READY" in s["status"] or "PROGRESS" in s["status"] or "BLOCKED" in s["status"]
        ]
        done_stories = [
            s for s in stories if s["checked"] or "LIVR" in s["status"] or "DONE" in s["status"]
        ][-3:]

        lines = [
            f"- **{s['id']}** : {s['title']} ({s['component']}) — Statut: `{s['status']}`"
            for s in active_stories
        ]
        if done_stories:
            lines.append("### Récemment Livrés :")
            lines.extend([f"- ~~{s['id']}~~ : {s['title']} (Terminé)" for s in done_stories])

        active_str = "\n".join(lines) if lines else "- Aucun récit actif dans le sprint en cours."
        return (
            f"# Active Context — {self.project_name}\n\n"
            "## 1. Current Sprint Focus (Chirurgical)\n"
            "Le sprint actif est centré sur l'intégration du standard Memory Bank, "
            "le mode Plan étanche et le Circuit-Breaker Herdr.\n\n"
            "## 2. Active Stories (Focus Sprint)\n"
            f"{active_str}\n\n"
            "## 3. Notes de Session & Découvertes d'Implémentation\n"
            "*(Les notes ajoutées ci-dessous par Cline sont moissonnées automatiquement par mloop sync)*\n"
        )

    def build_progress(self) -> str:
        """Génère progress.md (Métriques de complétion globales)."""
        stories = self._extract_active_stories()
        total = len(stories)
        done = sum(
            1 for s in stories if s["checked"] or "LIVR" in s["status"] or "DONE" in s["status"]
        )
        return (
            f"# Progress — {self.project_name}\n\n"
            "## 1. Sprint Health Overview\n"
            f"- Total Récits Traités : {total}\n"
            f"- Récits Terminés : {done}\n"
            f"- Récits en Cours / Prêts : {total - done}\n\n"
            "## 2. What Works\n"
            "- [x] Sonde déterministe d'agents aval (`doctor --agents`) opérationnelle.\n"
            "- [x] Registre multi-runtimes Herdr pour OpenCode et Cline.\n"
            "- [x] Bridge Memory Bank avec focus chirurgical et réconciliation inverse.\n"
        )

    def harvest_session_notes(self) -> List[str]:
        """Extrait les notes libres inscrites par Cline sous 'Notes de Session'."""
        active_ctx = self.bank_dir / "activeContext.md"
        if not active_ctx.exists():
            return []
        text = active_ctx.read_text(encoding="utf-8")
        marker = "## 3. Notes de Session & Découvertes d'Implémentation"
        if marker not in text:
            return []
        section = text.split(marker)[1]
        notes = []
        for line in section.splitlines():
            s = line.strip()
            if s.startswith("- ") and not s.startswith("*(Les notes"):
                notes.append(s[2:].strip())
        return notes

    def harvest_cline_notes(self, story_id: str) -> bool:
        """Moissonne les notes de Cline (activeContext.md) vers l'EvidencePack.

        Wrapper composant de bout en bout (MLOOP-260-BE §Op.2) : extrait les notes
        de session puis les réinjecte dans memory/evidence/<story_id>_evidence.json.

        Returns:
            True si de nouvelles notes ont été fusionnées dans l'EvidencePack,
            False si aucune note détectée ou EvidencePack absent (cas de rejet métier).
        """
        notes = self.harvest_session_notes()
        if not notes:
            logger.debug(
                "[MemoryBank] Aucune note de session à moissonner.",
                extra={"story_id": story_id, "bank_dir": str(self.bank_dir)},
            )
            return False
        return self.update_evidence_pack(story_id, notes)

    def update_evidence_pack(self, story_id: str, notes: List[str]) -> bool:
        """Réinjecte les notes récoltées dans l'EvidencePack de la story."""
        if not notes:
            return False
        ep_path = self.project_dir / "memory" / "evidence" / f"{story_id}_evidence.json"
        if not ep_path.exists():
            return False
        try:
            data = json.loads(ep_path.read_text(encoding="utf-8"))
            existing = data.setdefault("session_notes", [])
            for note in notes:
                if note not in existing:
                    existing.append(note)
            ep_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"[MemoryBank] EvidencePack {story_id} bonifié avec {len(notes)} notes.")
            return True
        except Exception as exc:
            logger.warning(f"[MemoryBank] Échec mise à jour EvidencePack {story_id}: {exc}")
            return False

    def sync_all(self) -> Dict[str, Path]:
        """Génère ou met à jour les 6 fichiers de la Memory Bank de façon idempotente."""
        self.ensure_bank_dir()
        files = {
            "projectbrief.md": self.build_projectbrief(),
            "productContext.md": self.build_product_context(),
            "activeContext.md": self.build_active_context(),
            "systemPatterns.md": self.build_system_patterns(),
            "techContext.md": self.build_tech_context(),
            "progress.md": self.build_progress(),
        }
        res = {}
        for fname, content in files.items():
            target = self.bank_dir / fname
            updated = self._safe_write_idempotent(target, content)
            action = "généré/mis à jour" if updated else "inchangé (idempotent)"
            logger.debug(f"[MemoryBank] {fname} {action}")
            res[fname] = target
        return res
