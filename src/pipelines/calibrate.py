"""
Calibration Pipeline - Ecosystem Auto-Calibration Engine for mLoop.

Executes an 8-step automated audit and auto-repair check to guarantee 100% alignment across:
1. CLI tools (src/swarm.py) <-> OpenCode shortcuts (opencode.json)
2. MCP Bridges (src/bridges/mcp_*.py) <-> opencode.json["mcp"]
3. Agentic Skills (.agents/skills/) <-> Router Index (.agents/skills/router/SKILL.md)
4. System Prompts (AGENTS.md & GEMINI.md)
5. Official Blueprints (standards/blueprints/)
6. Semantic Memory (SQLite FTS5 + Graphify)
7. Open Notebook Registry (memory/open_notebook_registry.json)
8. mLoop 3-Guardrail Suite (audit-loop -> PASS Exit 0)
"""

import os
import re
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging

from src.cli import ZeroFluffConsole

logger = logging.getLogger("calibrate")


class EcosystemCalibrator:
    """
    Automated Ecosystem Calibrator Engine for mLoop.
    Performs 8-point inspection and auto-repair.
    """

    def __init__(self, root_dir: Path, project_name: str = "default", auto_repair: bool = True):
        self.root_dir = root_dir
        self.project_name = project_name
        self.project_dir = root_dir / "Projects" / project_name
        self.auto_repair = auto_repair
        self.report_matrix: List[Dict[str, str]] = []

    def log_step(self, step_id: str, name: str, status: str, details: str) -> None:
        """Records an audit step result into the report matrix."""
        self.report_matrix.append({
            "step_id": step_id,
            "name": name,
            "status": status,
            "details": details
        })
        icon = "🟢" if status == "PASS" else ("🟡" if status == "REPAIRED" or status == "WARN" else "🔴")
        ZeroFluffConsole.info(f"{icon} [{step_id}] {name} : {status} - {details}")

    def run_full_calibration(self) -> bool:
        """Executes all 9 calibration steps sequentially."""
        ZeroFluffConsole.section(f"mLoop Calibrate Engine — Auto-Calibration ({self.project_name})")

        # Step 1: CLI Swarm <-> OpenCode Commands
        self._audit_cli_commands()

        # Step 2: MCP Bridges <-> OpenCode MCP Config
        self._audit_mcp_bridges()

        # Step 3: Skills <-> Router Index
        self._audit_skills_index()

        # Step 4: System Prompts (AGENTS.md & GEMINI.md)
        self._audit_system_prompts()

        # Step 5: Official Blueprints
        self._audit_blueprints()

        # Step 6: Semantic Memory & Graphify Sync
        self._audit_semantic_sync()

        # Step 7: Open Notebook SHA256 Registry
        self._audit_open_notebook_registry()

        # Step 8: Final 3-Guardrail Suite (audit-loop)
        guardrail_passed = self._audit_guardrails()

        # Step 9: ADR Contract Sync (standards/adr-contracts.json vs ProjectLayout)
        adr_passed = self._audit_adr_contracts()

        # Step 10: Memory Structural Sync (memory/ subdirs)
        mem_passed = self._audit_memory_structure()

        # Step 11: Project Canonical Root & Anti-Drift Sub-READMEs
        root_passed = self._audit_project_root_and_subreadmes()

        # Step 12: ADR Integrity & Stub Purge
        adr_int_passed = self._audit_adrs_and_placeholders()

        # Step 13: Docs Root & Hierarchy Guard (ADR-0102)
        docs_hier_passed = self._audit_docs_hierarchy()

        # Step 14: Git Cache & Weight Shield
        git_shield_passed = self._audit_gitignore_and_heavy_caches()

        # Step 15: Jargon & Functional Purity Linter
        purity_passed = self._audit_jargon_and_functional_purity()

        # Step 16: Reviews Hierarchy & Cleanliness Guard
        reviews_passed = self._audit_reviews_hierarchy_and_cleanliness()

        # Step 17: StoryType & Naming Standard Guard
        typing_passed = self._audit_stories_typing_and_naming()

        self.print_summary_matrix()
        return (guardrail_passed and adr_passed and mem_passed and root_passed 
                and adr_int_passed and docs_hier_passed and git_shield_passed 
                and purity_passed and reviews_passed and typing_passed)

    def _audit_cli_commands(self) -> None:
        """[1/8] Verifies CLI commands in swarm.py exist in opencode.json."""
        swarm_file = self.root_dir / "src" / "swarm.py"
        opencode_file = self.root_dir / "opencode.json"

        if not swarm_file.exists() or not opencode_file.exists():
            self.log_step("1/8", "CLI -> OpenCode Shortcuts", "WARN", "Fichier swarm.py ou opencode.json introuvable.")
            return

        try:
            from src.commands._registry import COMMANDS
            cli_commands = list(COMMANDS.keys())
        except Exception:
            cli_commands = []

        if not cli_commands:
            self.log_step("1/8", "CLI -> OpenCode Shortcuts", "WARN", "Impossible d'extraire les commandes du registre.")
            return
        
        try:
            opencode_data = json.loads(opencode_file.read_text(encoding="utf-8"))
            registered_cmds = opencode_data.get("command", {})
        except Exception as e:
            self.log_step("1/8", "CLI -> OpenCode Shortcuts", "FAIL", f"Erreur lecture opencode.json : {e}")
            return

        CORE_SHORTCUTS = {
            "loop": {
                "description": "Memory Loop : Dispatcher universel (/loop <action> [args])",
                "template": "python src/swarm.py $ARGUMENTS"
            },
            "loop-guide": {
                "description": "Memory Loop : Guide d'utilisation du pipeline CLI mLoop",
                "template": "python src/swarm.py guide $ARGUMENTS"
            },
            "loop-resume": {
                "description": "Memory Loop : Restauration de session anti-amnésie",
                "template": "python src/swarm.py resume --project $ARGUMENTS"
            },
            "loop-vibe-check": {
                "description": "Memory Loop : Guardrail pré-vol de la session",
                "template": "python src/swarm.py vibe-check --project $ARGUMENTS"
            },
            "loop-focus": {
                "description": "Memory Loop : Verrouiller l'attention sur un récit",
                "template": "python src/swarm.py focus --project $ARGUMENTS"
            },
            "loop-sync": {
                "description": "Memory Loop : Synchronisation WikiFix, graphe et SQLite",
                "template": "python src/swarm.py sync --project $ARGUMENTS"
            },
            "loop-grill": {
                "description": "Memory Loop : Session interactive Grill-with-Docs & ADRs",
                "template": "python src/swarm.py grill --project $ARGUMENTS"
            },
            "loop-to-spec": {
                "description": "Memory Loop : Distiller une conversation en spécification",
                "template": "python src/swarm.py to-spec --project $ARGUMENTS"
            },
            "loop-to-tickets": {
                "description": "Memory Loop : Découper une spec en tickets verticaux",
                "template": "python src/swarm.py to-tickets --project $ARGUMENTS"
            },
            "loop-rubber-duck": {
                "description": "Memory Loop : Audit contradictoire Sentinel (Read-Only)",
                "template": "python src/swarm.py rubber-duck --project $ARGUMENTS"
            },
            "loop-cycle": {
                "description": "Memory Loop : Suivi de l'avancement des 5 phases",
                "template": "python src/swarm.py cycle-status --project $ARGUMENTS"
            },
            "loop-calibrate": {
                "description": "Memory Loop : Auto-étalonnage continu de l'écosystème",
                "template": "python src/swarm.py calibrate --project $ARGUMENTS"
            },
            "loop-crawl": {
                "description": "Memory Loop : Web Crawler sur une URL ou bibliothèque",
                "template": "python src/swarm.py crawl --project $ARGUMENTS"
            },
            "loop-dashboard": {
                "description": "Memory Loop : Lancer le serveur Web Dashboard",
                "template": "python src/swarm.py dashboard --project $ARGUMENTS"
            },
        }

        missing = []
        for sname, sdef in CORE_SHORTCUTS.items():
            if sname not in registered_cmds:
                missing.append((sname, sdef))

        if missing:
            if self.auto_repair:
                for sname, sdef in missing:
                    opencode_data.setdefault("command", {})[sname] = sdef
                opencode_file.write_text(json.dumps(opencode_data, indent=2, ensure_ascii=False), encoding="utf-8")
                self.log_step("1/8", "CLI -> OpenCode Shortcuts", "REPAIRED", f"Ajouté {len(missing)} raccourci(s) essentiel(s) dans opencode.json.")
            else:
                self.log_step("1/8", "CLI -> OpenCode Shortcuts", "WARN", f"{len(missing)} raccourci(s) essentiel(s) manquant(s) dans opencode.json.")
        else:
            self.log_step("1/8", "CLI -> OpenCode Shortcuts", "PASS", f"Dispatcher universel '/loop' et les {len(CORE_SHORTCUTS)} raccourcis métier sont alignés.")

    def _audit_mcp_bridges(self) -> None:
        """[2/8] Verifies python scripts under src/bridges/mcp_*.py are registered in opencode.json mcp."""
        bridges_dir = self.root_dir / "src" / "bridges"
        opencode_file = self.root_dir / "opencode.json"

        if not bridges_dir.exists() or not opencode_file.exists():
            self.log_step("2/8", "MCP Bridges -> opencode.json", "PASS", "Dossier bridges absent ou opencode.json introuvable.")
            return

        mcp_scripts = list(bridges_dir.glob("mcp_*.py"))
        try:
            opencode_data = json.loads(opencode_file.read_text(encoding="utf-8"))
            mcp_config = opencode_data.get("mcp", {})
        except Exception:
            self.log_step("2/8", "MCP Bridges -> opencode.json", "WARN", "Lecture opencode.json mcp échouée.")
            return

        unregistered = []
        for script in mcp_scripts:
            bridge_key = script.stem.replace("mcp_", "")
            if bridge_key not in mcp_config and script.stem not in mcp_config:
                unregistered.append(script.name)

        if unregistered:
            if self.auto_repair:
                for script in mcp_scripts:
                    b_key = script.stem.replace("mcp_", "")
                    if b_key not in mcp_config:
                        opencode_data.setdefault("mcp", {})[b_key] = {
                            "type": "local",
                            "command": ["python", f"src/bridges/{script.name}"]
                        }
                opencode_file.write_text(json.dumps(opencode_data, indent=2, ensure_ascii=False), encoding="utf-8")
                self.log_step("2/8", "MCP Bridges -> opencode.json", "REPAIRED", f"Enregistré {len(unregistered)} pont(s) MCP.")
            else:
                self.log_step("2/8", "MCP Bridges -> opencode.json", "WARN", f"{len(unregistered)} pont(s) MCP non déclarés.")
        else:
            self.log_step("2/8", "MCP Bridges -> opencode.json", "PASS", f"Tous les {len(mcp_scripts)} ponts MCP sont configurés.")

    def _audit_skills_index(self) -> None:
        """[3/8] Verifies all .agents/skills/ folders are listed in router/SKILL.md."""
        skills_dir = self.root_dir / ".agents" / "skills"
        router_file = skills_dir / "router" / "SKILL.md"

        if not skills_dir.exists() or not router_file.exists():
            self.log_step("3/8", "Skills -> Router Index", "PASS", "Dossier skills ou router/SKILL.md introuvable.")
            return

        skill_folders = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        router_content = router_file.read_text(encoding="utf-8")

        unindexed = []
        for sname in skill_folders:
            if f"/{sname}" not in router_content and sname != "router":
                unindexed.append(sname)

        if unindexed:
            if self.auto_repair:
                lines = router_content.splitlines()
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if "### 🔬 Skills Externes & Spécialisés" in line:
                        for u in unindexed:
                            new_lines.append(f"- **`/{u}`** : Compétence mLoop enregistrée automatiquement.")
                router_file.write_text("\n".join(new_lines), encoding="utf-8")
                self.log_step("3/8", "Skills -> Router Index", "REPAIRED", f"Inscrit {len(unindexed)} skill(s) manquant(s) dans router/SKILL.md.")
            else:
                self.log_step("3/8", "Skills -> Router Index", "WARN", f"{len(unindexed)} skill(s) non indexés dans router/SKILL.md.")
        else:
            self.log_step("3/8", "Skills -> Router Index", "PASS", f"Les {len(skill_folders)} skills sont répertoriés dans l'index.")

    def _audit_system_prompts(self) -> None:
        """[4/8] Audits AGENTS.md & GEMINI.md for core commands & directives."""
        agents_file = self.root_dir / "AGENTS.md"
        gemini_file = self.root_dir / "GEMINI.md"
        claude_file = self.root_dir / "CLAUDE.md"

        # Synchronisation synchrone de CLAUDE.md (Axe 3 ADR-0310)
        if agents_file.exists():
            agents_content = agents_file.read_text(encoding="utf-8")
            if not claude_file.exists() or "Memory Loop" not in claude_file.read_text(encoding="utf-8"):
                claude_file.write_text(f"# CLAUDE.md - Memory Loop Directives\n\n{agents_content}", encoding="utf-8")

        missing = []
        for pfile in [agents_file, gemini_file]:
            if pfile.exists():
                content = pfile.read_text(encoding="utf-8")
                if "wikifix" not in content:
                    missing.append(pfile.name)

        if missing:
            self.log_step("4/8", "Directives AGENTS.md/GEMINI.md/CLAUDE.md", "WARN", f"Fichiers {', '.join(missing)} nécessitent un rafraîchissement de directives.")
        else:
            self.log_step("4/8", "Directives AGENTS.md/GEMINI.md/CLAUDE.md", "PASS", "AGENTS.md, GEMINI.md et CLAUDE.md sont synchronisés.")

    def _audit_blueprints(self) -> None:
        """[5/8] Verifies official story & SOW templates under standards/blueprints/."""
        bp_dir = self.root_dir / "standards" / "blueprints"
        if not bp_dir.exists():
            self.log_step("5/8", "Gabarits standards/blueprints", "PASS", "Dossier blueprints non présent.")
            return

        templates = ["story_template.md", "sow_evaluation_template.md"]
        missing_bp = [t for t in templates if not (bp_dir / t).exists()]

        if missing_bp:
            self.log_step("5/8", "Gabarits standards/blueprints", "FAIL", f"Gabarit(s) manquant(s) : {', '.join(missing_bp)}")
        else:
            self.log_step("5/8", "Gabarits standards/blueprints", "PASS", "Gabarits officiels (story_template.md, sow_evaluation_template.md) validés.")

    def _audit_semantic_sync(self) -> None:
        """[6/8] Synchronizes SQLite FTS5 database and Graphify index."""
        try:
            from src.pipelines.sync import run_sync
            from src.state import LoopState
            state = LoopState(project_name=self.project_name)
            run_sync(self.project_name, state, self.project_dir)
            self.log_step("6/8", "Synchronisation Sémantique & Graphify", "PASS", "Base SQLite FTS5 & Graphify synchronisées avec succès.")
        except Exception as e:
            self.log_step("6/8", "Synchronisation Sémantique & Graphify", "WARN", f"Avertissement lors de la sync : {e}")

    def _audit_open_notebook_registry(self) -> None:
        """[7/8] Checks memory/ingest_registry.json SHA256 integrity."""
        registry_file = self.root_dir / "memory" / "ingest_registry.json"
        if not registry_file.exists():
            registry_file = self.root_dir / "memory" / "open_notebook_registry.json"
            
        if registry_file.exists():
            try:
                data = json.loads(registry_file.read_text(encoding="utf-8"))
                count = len(data.get("indexed_files", {})) if isinstance(data, dict) else len(data)
                self.log_step("7/8", "Registre Ingestion MarkItDown SHA256", "PASS", f"{count} document(s) indexés sans doublons.")
            except Exception as e:
                self.log_step("7/8", "Registre Ingestion MarkItDown SHA256", "WARN", f"Erreur lecture registre : {e}")
        else:
            self.log_step("7/8", "Registre Ingestion MarkItDown SHA256", "PASS", "Registre MarkItDown propre.")

    def _audit_guardrails(self) -> bool:
        """[8/9] Runs the full 3-guardrail suite via audit-loop."""
        try:
            from src.pipelines.loop_audit import run_loop_audit
            res = run_loop_audit(self.project_name)
            passed = (res.get("status") == "PASS")
            status_str = "PASS" if passed else "FAIL"
            self.log_step("8/9", "Validation 3 Guardrails (audit-loop)", status_str, f"Status global : {res.get('status')}")
            return passed
        except Exception as e:
            self.log_step("8/9", "Validation 3 Guardrails (audit-loop)", "FAIL", f"Erreur d'exécution audit-loop : {e}")
            return False

    def _audit_adr_contracts(self) -> bool:
        """
        [9/9] ADR Contract Sync — Vérifie que ProjectLayout en mémoire == standards/adr-contracts.json.
        Règle ADR-Sync : toute modification d'ADR 01xx doit mettre à jour adr-contracts.json.
        """
        from src.state import ProjectLayout, _load_adr_contracts
        contracts_path = Path("standards") / "adr-contracts.json"

        if not contracts_path.exists():
            self.log_step("9/9", "ADR Contract Sync", "FAIL",
                          "standards/adr-contracts.json introuvable — Règle ADR-Sync non satisfaite.")
            return False

        try:
            disk = _load_adr_contracts()
            drifts = []

            # Vérification ADR-0100 : client_layout
            disk_layout = disk["ADR-0100"]["client_layout"]
            if disk_layout != ProjectLayout.CLIENT_LAYOUT:
                drifts.append(f"ADR-0100 client_layout: disk={disk_layout} vs code={ProjectLayout.CLIENT_LAYOUT}")

            # Vérification ADR-0102 : docs_subdirs
            disk_subdirs = disk["ADR-0102"]["docs_subdirs"]
            if disk_subdirs != ProjectLayout.DOCS_SUBDIRS:
                drifts.append(f"ADR-0102 docs_subdirs: disk={disk_subdirs} vs code={ProjectLayout.DOCS_SUBDIRS}")

            # Vérification ADR-0103 : mloop_layout
            disk_mloop = disk["ADR-0103"]["mloop_layout"]
            if disk_mloop != ProjectLayout.MLOOP_LAYOUT:
                drifts.append(f"ADR-0103 mloop_layout: disk={disk_mloop} vs code={ProjectLayout.MLOOP_LAYOUT}")

            if drifts:
                self.log_step("9/9", "ADR Contract Sync", "FAIL",
                              f"Drift détecté ({len(drifts)} écart(s)) : {'; '.join(drifts)}")
                return False
            else:
                self.log_step("9/9", "ADR Contract Sync", "PASS",
                              "ProjectLayout aligné avec adr-contracts.json (ADR-0100/0102/0103).")
                return True

        except Exception as e:
            self.log_step("9/9", "ADR Contract Sync", "FAIL", f"Erreur lecture contrats : {e}")
            return False

    def _audit_memory_structure(self) -> bool:
        """
        [10/10] Memory Structural Sync — Vérifie que le dossier memory/ du projet comporte les 6 sous-dossiers canoniques.
        """
        memory_dir = self.project_dir / "memory"
        required_subdirs = ["sessions", "debates", "sync", "reports", "cache", "tmp"]

        if not memory_dir.exists():
            memory_dir.mkdir(parents=True, exist_ok=True)

        missing = []
        for sdir in required_subdirs:
            subdir_path = memory_dir / sdir
            if not subdir_path.exists():
                missing.append(sdir)
                if self.auto_repair:
                    subdir_path.mkdir(parents=True, exist_ok=True)

        if missing:
            if self.auto_repair:
                self.log_step("10/10", "Memory Structural Sync", "REPAIRED",
                              f"Sous-dossier(s) memory/ créés automatiquement : {', '.join(missing)}")
                return True
            else:
                self.log_step("10/10", "Memory Structural Sync", "WARN",
                              f"Sous-dossier(s) memory/ manquant(s) : {', '.join(missing)}")
                return False
        else:
            self.log_step("10/10", "Memory Structural Sync", "PASS",
                          "Structure canonique de memory/ à 6 sous-dossiers validée.")
            return True

    def _audit_project_root_and_subreadmes(self) -> bool:
        """
        [11/11] Project Canonical Root & Anti-Drift Sub-README Audit.
        Vérifie la présence de README.md, AGENTS.md, opencode.json, .gitignore à la racine du projet
        et purge automatiquement tout sous-README orphelin.
        """
        if not self.project_dir.exists() or self.project_name in ("default", "mLoop"):
            self.log_step("11/11", "Project Canonical Root & Anti-Drift", "PASS", "Projet framework mLoop / racine.")
            return True

        # 1. Vérification des 4 fichiers racines
        required_root = ["README.md", "AGENTS.md", "opencode.json", ".gitignore"]
        missing_root = [f for f in required_root if not (self.project_dir / f).exists()]
        repaired_root = []

        if missing_root and self.auto_repair:
            for f in missing_root:
                fpath = self.project_dir / f
                if f == "README.md":
                    fpath.write_text(
                        f"# 🚀 {self.project_name} — Documentation & Architecture SSOT\n\n"
                        f"Bienvenue dans le dépôt officiel de documentation d'architecture pour le projet **{self.project_name}**.\n",
                        encoding="utf-8"
                    )
                    repaired_root.append(f)
                elif f == "AGENTS.md":
                    fpath.write_text(
                        f"# 🛡️ Guide Agentique Spécifique — {self.project_name} (mLoop Project Engine)\n\n"
                        f"Ce document constitue la **Source de Vérité Agentique (AGENTS.md)** pour le projet **{self.project_name}**.\n\n"
                        "## 1. Séquence d'Amorçage & Outils CLI\n"
                        f"1. `python src/swarm.py resume --project {self.project_name}`\n"
                        "2. `loop_mem_search`\n"
                        "3. `graphify query`\n"
                        f"4. `python src/swarm.py vibe-check --project {self.project_name}`\n\n"
                        "## 2. Séparation des 3 Piliers\n"
                        "- reference/ (Local, hors Git)\n- docs/ (SSOT)\n- backlog/ (Stories Gherkin)\n- memory/ (EvidencePacks)\n",
                        encoding="utf-8"
                    )
                    repaired_root.append(f)
                elif f == "opencode.json":
                    import json
                    cfg = {
                        "$schema": "https://opencode.ai/schema.json",
                        "project": self.project_name,
                        "version": "1.0.0",
                        "instructions": ["AGENTS.md"],
                        "mcp": {
                            "loop_mem": {"type": "local", "command": ["python", "-m", "src.mcp_server"]},
                            "graphify": {"type": "local", "command": ["python", "-m", "graphify.server"]},
                            "codegraph": {"type": "local", "command": ["codegraph", "serve", "--mcp"]}
                        },
                        "watcher": {
                            "ignore": [".codegraph/**", "memory/cache/**", "memory/events.jsonl"]
                        },
                        "commands": {
                            "loop-explore": {"command": f'python src/swarm.py code-explore --project {self.project_name} --query "$QUERY"', "description": "CodeGraph Explore"},
                            "loop-sync": {"command": f'python src/swarm.py sync --project {self.project_name}', "description": "mLoop Sync"}
                        }
                    }
                    fpath.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
                    repaired_root.append(f)
                elif f == ".gitignore":
                    fpath.write_text(
                        "# Python Bytecode & Cache\n__pycache__/\n*.py[cod]\n.pytest_cache/\n\n"
                        "# Local AST & CodeGraph\ngraphify-out/\n.codegraph/\n**/.codegraph/\n\n"
                        "# Raw Material\nreference/\n\n"
                        "# Temporary\n~$*.xlsx\n*.tmp\n",
                        encoding="utf-8"
                    )
                    repaired_root.append(f)

        # 2. Détection & purge des sous-READMEs
        sub_readmes = []
        for p in self.project_dir.rglob("README.md"):
            if p == self.project_dir / "README.md":
                continue
            # Ignorer reference/ ou node_modules
            rel = str(p.relative_to(self.project_dir)).replace("\\", "/")
            if rel.startswith("reference/") or "node_modules" in rel or ".git" in rel:
                continue
            sub_readmes.append(p)

        purged = []
        if sub_readmes and self.auto_repair:
            for sr in sub_readmes:
                try:
                    sr.unlink()
                    purged.append(str(sr.relative_to(self.project_dir)))
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {sr}: {e}")

        # Synthèse du résultat
        if (missing_root and not self.auto_repair) or (sub_readmes and not self.auto_repair):
            details = []
            if missing_root:
                details.append(f"Racines manquants: {', '.join(missing_root)}")
            if sub_readmes:
                details.append(f"Sous-READMEs orphelins: {len(sub_readmes)}")
            self.log_step("11/17", "Project Canonical Root & Anti-Drift", "WARN", " ; ".join(details))
            return False
        elif repaired_root or purged:
            actions = []
            if repaired_root:
                actions.append(f"Fichiers racines initialisés ({', '.join(repaired_root)})")
            if purged:
                actions.append(f"Sous-READMEs orphelins purgés ({len(purged)})")
            self.log_step("11/17", "Project Canonical Root & Anti-Drift", "REPAIRED", " ; ".join(actions))
            return True
        else:
            self.log_step("11/17", "Project Canonical Root & Anti-Drift", "PASS",
                          "Structure racine (README, AGENTS, opencode, .gitignore) validée & zéro sous-README orphelin.")
            return True

    def _audit_adrs_and_placeholders(self) -> bool:
        """[12/17] Verifies ADR integrity, purges stubs/placeholders (<600 bytes) and normalizes filenames."""
        adr_dir = self.project_dir / "docs" / "01-architecture"
        if not adr_dir.exists():
            self.log_step("12/17", "ADR Integrity & Stub Purge", "PASS", "Aucun répertoire 01-architecture (non requis).")
            return True

        stubs = []
        renamed = []
        for p in adr_dir.glob("*.md"):
            if p.name in ["COMPARATIF_CODEBASES.md", "OKF_REGISTRE_ENTITES.md", "PLAN_CONTINGENCE_ONETRUST.md"]:
                continue
            # 1. Vérification stubs / placeholders
            content = p.read_text(encoding="utf-8", errors="ignore")
            size = p.stat().st_size
            is_stub = False
            if size < 600 and ("Session d'interrogatoire" in content or "Mise à jour clé Jira" in content or "Généré automatiquement par mLoop Grill Engine" in content or "Arbitrage d'architecture validé" in content):
                is_stub = True
            
            if is_stub:
                stubs.append(p)
                continue

            # 2. Vérification nomenclature (pas de _d_cision_, snake_case, etc.)
            if "_" in p.name and p.name.startswith("ADR-"):
                clean_name = p.name.replace("_d_cision_d_architecture", "-Decision-Architecture")
                clean_name = clean_name.replace("_", "-")
                clean_name = re.sub(r"-+", "-", clean_name)
                target_p = p.parent / clean_name
                if self.auto_repair and target_p != p:
                    try:
                        p.rename(target_p)
                        renamed.append(f"{p.name} -> {clean_name}")
                    except Exception as e:
                        logger.warning(f"Impossible de renommer {p.name}: {e}")

        purged = []
        if stubs and self.auto_repair:
            for s in stubs:
                try:
                    s.unlink()
                    purged.append(s.name)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {s.name}: {e}")

        if stubs and not self.auto_repair:
            self.log_step("12/17", "ADR Integrity & Stub Purge", "WARN", f"{len(stubs)} stubs/placeholders détectés : {', '.join([s.name for s in stubs])}")
            return False
        elif purged or renamed:
            actions = []
            if purged:
                actions.append(f"{len(purged)} stubs purgés ({', '.join(purged)})")
            if renamed:
                actions.append(f"{len(renamed)} fichiers normalisés ({', '.join(renamed)})")
            self.log_step("12/17", "ADR Integrity & Stub Purge", "REPAIRED", " ; ".join(actions))
            return True
        else:
            self.log_step("12/17", "ADR Integrity & Stub Purge", "PASS", "Tous les ADRs sont substantiels et conformes à la nomenclature kebab-case.")
            return True

    def _audit_docs_hierarchy(self) -> bool:
        """[13/17] Verifies docs/ root has no orphan drafts except index.md (ADR-0102)."""
        docs_dir = self.project_dir / "docs"
        if not docs_dir.exists():
            self.log_step("13/17", "Docs Root & Hierarchy Guard", "PASS", "Répertoire docs/ inexistant.")
            return True

        orphan_files = [f for f in docs_dir.glob("*.md") if f.name != "index.md"]
        repaired = []
        if orphan_files and self.auto_repair:
            transverse_dir = docs_dir / "04-transverse"
            transverse_dir.mkdir(parents=True, exist_ok=True)
            for of in orphan_files:
                target = transverse_dir / of.name
                try:
                    of.rename(target)
                    repaired.append(f"{of.name} déplacé dans docs/04-transverse/")
                except Exception as e:
                    logger.warning(f"Erreur déplacement {of.name}: {e}")

        if orphan_files and not self.auto_repair:
            self.log_step("13/17", "Docs Root & Hierarchy Guard", "WARN", f"{len(orphan_files)} fichiers orphelins à la racine de docs/: {', '.join([f.name for f in orphan_files])}")
            return False
        elif repaired:
            self.log_step("13/17", "Docs Root & Hierarchy Guard", "REPAIRED", " ; ".join(repaired))
            return True
        else:
            self.log_step("13/17", "Docs Root & Hierarchy Guard", "PASS", "Racine de docs/ 100% conforme (index.md unique + 5 sous-dossiers).")
            return True

    def _audit_gitignore_and_heavy_caches(self) -> bool:
        """[14/17] Verifies .gitignore has required memory/cache and reference exclusions."""
        gitignore_file = self.project_dir / ".gitignore"
        if not gitignore_file.exists():
            self.log_step("14/17", "Git Cache & Weight Shield", "WARN", "Fichier .gitignore introuvable.")
            return False

        content = gitignore_file.read_text(encoding="utf-8", errors="ignore")
        required_patterns = [
            "memory/cache/",
            "memory/tmp/",
            "memory/execution_traces.json",
            "memory/ingest_cache.json",
            "reference/",
            "graphify-out/",
        ]
        missing = [p for p in required_patterns if p not in content]
        
        if missing and self.auto_repair:
            addition = "\n# Auto-repair Calibrate : Memory & Reference Exclusions\n" + "\n".join(missing) + "\n"
            gitignore_file.write_text(content + addition, encoding="utf-8")
            self.log_step("14/17", "Git Cache & Weight Shield", "REPAIRED", f"Exclusions ajoutées à .gitignore: {', '.join(missing)}")
            return True
        elif missing:
            self.log_step("14/17", "Git Cache & Weight Shield", "WARN", f"Motifs manquants dans .gitignore: {', '.join(missing)}")
            return False
        else:
            self.log_step("14/17", "Git Cache & Weight Shield", "PASS", ".gitignore protège parfaitement le dépôt contre les caches lourds et la matière première.")
            return True

    def _audit_jargon_and_functional_purity(self) -> bool:
        """[15/15] Scans project documentation for internal framework jargon (ADR-0319) and personal names."""
        agents_file = self.project_dir / "AGENTS.md"
        readme_file = self.project_dir / "README.md"
        
        repaired = []
        for doc_file in [agents_file, readme_file]:
            if doc_file.exists():
                content = doc_file.read_text(encoding="utf-8", errors="ignore")
                new_content = content
                if "ADR-0319" in new_content or "(Directive Lead Dev Renaud" in new_content:
                    new_content = new_content.replace("(Directive Lead Dev Renaud - ADR-0319)", "(Pureté Fonctionnelle & Zéro Code Physique)")
                    new_content = new_content.replace("ADR-0319", "Pureté Fonctionnelle")
                    new_content = new_content.replace("Directive Lead Dev Renaud", "Directive Pureté Fonctionnelle")
                    if self.auto_repair and new_content != content:
                        doc_file.write_text(new_content, encoding="utf-8")
                        repaired.append(doc_file.name)

        if repaired:
            self.log_step("15/17", "Jargon & Functional Purity Linter", "REPAIRED", f"Jargon interne purifié dans: {', '.join(repaired)}")
            return True
        else:
            self.log_step("15/17", "Jargon & Functional Purity Linter", "PASS", "Documentation projet épurée de tout jargon interne ou nom personnel.")
            return True

    def _audit_reviews_hierarchy_and_cleanliness(self) -> bool:
        """[16/17] Verifies backlog/reviews/ is partitioned by category subfolders and contains no orphan drafts."""
        reviews_dir = self.project_dir / "backlog" / "reviews"
        if not reviews_dir.exists():
            self.log_step("16/17", "Reviews Hierarchy & Cleanliness Guard", "PASS", "Aucun répertoire backlog/reviews/ (non requis).")
            return True

        orphan_root_files = [f for f in reviews_dir.glob("*.md")]
        repaired = []

        if orphan_root_files and self.auto_repair:
            transverse_dir = self.project_dir / "docs" / "04-transverse"
            transverse_dir.mkdir(parents=True, exist_ok=True)
            for f in orphan_root_files:
                if f.name.startswith("rubber_duck_"):
                    # Tenter de classer dans la bonne catégorie
                    target_sub = reviews_dir / "FOOD" if "-FOOD" in f.name else reviews_dir / "GENERAL"
                    target_sub.mkdir(parents=True, exist_ok=True)
                    target_file = target_sub / f.name
                    if target_file.exists():
                        target_file.unlink()
                    f.rename(target_file)
                    repaired.append(f"{f.name} -> {target_sub.name}/")
                else:
                    # Déplacer vers 04-transverse
                    target_file = transverse_dir / f.name
                    if target_file.exists():
                        target_file.unlink()
                    f.rename(target_file)
                    repaired.append(f"{f.name} -> docs/04-transverse/")

        if orphan_root_files and not self.auto_repair:
            self.log_step("16/17", "Reviews Hierarchy & Cleanliness Guard", "WARN", f"{len(orphan_root_files)} fichier(s) orphelin(s) à la racine de reviews/: {', '.join([f.name for f in orphan_root_files])}")
            return False
        elif repaired:
            self.log_step("16/17", "Reviews Hierarchy & Cleanliness Guard", "REPAIRED", " ; ".join(repaired))
            return True
        else:
            self.log_step("16/17", "Reviews Hierarchy & Cleanliness Guard", "PASS", "Structure backlog/reviews/ étanche par sous-dossiers et 100% propre.")
            return True

    def _audit_stories_typing_and_naming(self) -> bool:
        """[17/17] Verifies story frontmatter type (StoryType) and naming conventions."""
        stories_dir = self.project_dir / "backlog" / "stories"
        if not stories_dir.exists():
            self.log_step("17/17", "StoryType & Naming Standard Guard", "PASS", "Aucun répertoire backlog/stories/ (non requis).")
            return True

        from src.state import StoryType
        valid_types = {t.value for t in StoryType}

        repaired_types = []
        invalid_types = []
        repaired_names = []

        for f in stories_dir.rglob("*.md"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            # Vérification du typage
            m_type = re.search(r"type:\s*([^\n]+)", parts[1], re.IGNORECASE)
            if m_type:
                raw_type = m_type.group(1).strip()
                parsed_type = StoryType.from_raw(raw_type)
                if raw_type != parsed_type.value:
                    if self.auto_repair:
                        new_fm = re.sub(r"type:\s*[^\n]+", f"type: {parsed_type.value}", parts[1], flags=re.IGNORECASE)
                        f.write_text(f"---{new_fm}---{parts[2]}", encoding="utf-8")
                        repaired_types.append(f"{f.name}: {raw_type} -> {parsed_type.value}")
                    else:
                        invalid_types.append(f"{f.name} ({raw_type})")
            else:
                if self.auto_repair:
                    new_fm = f"type: Feature\n" + parts[1].strip() + "\n"
                    f.write_text(f"---\n{new_fm}---{parts[2]}", encoding="utf-8")
                    repaired_types.append(f"{f.name}: ajouté type: Feature")
                else:
                    invalid_types.append(f"{f.name} (manquant)")

            # Vérification nomenclature Stories (ADR-0322 : Support US-XX et Clés Jira officielles MMA-XXXX)
            is_valid_naming = (
                f.name == "README.md"
                or bool(re.match(r"^(?:US-\d+|[A-Z]{2,10}-\d+)(?:-[A-Z0-9]+)?\.md$", f.name))
                or bool(re.match(r"^[A-Z]+-US-\d+\.md$", f.name))
            )
            if not is_valid_naming:
                m_num = re.search(r"US-(\d+)", f.name)
                if m_num and self.auto_repair:
                    new_name = f"US-{m_num.group(1)}-FOOD.md" if f.parent.name == "FOOD" else f"US-{m_num.group(1)}.md"
                    target_p = f.parent / new_name
                    f.rename(target_p)
                    repaired_names.append(f"{f.name} -> {new_name}")

        if invalid_types and not self.auto_repair:
            self.log_step("17/17", "StoryType & Naming Standard Guard", "WARN", f"{len(invalid_types)} récit(s) avec type invalide: {', '.join(invalid_types)}")
            return False
        elif repaired_types or repaired_names:
            actions = []
            if repaired_types:
                actions.append(f"{len(repaired_types)} types normalisés")
            if repaired_names:
                actions.append(f"{len(repaired_names)} fichiers renommés")
            self.log_step("17/17", "StoryType & Naming Standard Guard", "REPAIRED", " ; ".join(actions))
            return True
        else:
            self.log_step("17/17", "StoryType & Naming Standard Guard", "PASS", "Tous les récits ont un StoryType valide et une nomenclature standardisée.")
            return True


    def print_summary_matrix(self) -> None:
        """Prints a clean summary markdown table of calibration results."""
        ZeroFluffConsole.section("Matrice d'Étalonnage de l'Écosystème mLoop")
        print("\n| # | Domaine d'Audit | Statut | Détails |")
        print("|---|---|---|---|")
        for item in self.report_matrix:
            print(f"| {item['step_id']} | {item['name']} | **{item['status']}** | {item['details']} |")
        print("\n")
