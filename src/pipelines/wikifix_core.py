import json
import logging
import re
from pathlib import Path
from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole
from src.pipelines.wikifix_auditors import WikiFixAuditMixin
from src.pipelines._wikifix_heal import WikiFixHealMixin, os_relative_path

logger = logging.getLogger(__name__)

__all__ = ["WikiFixAgent", "os_relative_path"]


class WikiFixAgent(WikiFixAuditMixin, WikiFixHealMixin):
    """Linter sémantique actif et mécanique (Système 1)."""

    def __init__(self):
        self.name = "WikiFix"
        self.supported_callouts = {"NOTE", "TIP", "WARNING", "IMPORTANT", "CAUTION"}
        self.callout_mapping = {
            "note": "NOTE",
            "info": "NOTE",
            "tip": "TIP",
            "hint": "TIP",
            "warning": "WARNING",
            "danger": "WARNING",
            "error": "WARNING",
            "important": "IMPORTANT",
            "caution": "CAUTION",
        }

    def _normalize_callout(self, callout_type: str) -> str | None:
        return self.callout_mapping.get(callout_type.lower().strip(), None)

    def _collect_markdown_files(self, project_path: Path, interest_dirs: list[str]) -> list[Path]:
        files = []
        for d in interest_dirs:
            dir_path = project_path / d
            if dir_path.exists():
                try:
                    for md_file in dir_path.rglob("*.md"):
                        try:
                            if md_file.is_file():
                                files.append(md_file)
                        except (OSError, ValueError) as e:
                            logger.debug(
                                "Entrée Markdown inutilisable, ignorée",
                                exc_info=True,
                                extra={
                                    "component": "pipelines.wikifix_core",
                                    "operation": "collect_markdown_files",
                                    "error": str(e),
                                },
                            )
                except (OSError, PermissionError) as e:
                    logger.debug(
                        "Répertoire d'intérêt inaccessible lors du scan Markdown",
                        exc_info=True,
                        extra={
                            "component": "pipelines.wikifix_core",
                            "operation": "collect_markdown_files",
                            "error": str(e),
                        },
                    )
        return files

    def _stream_markdown_files(self, project_path: Path, interest_dirs: list[str]):
        for md_file in self._collect_markdown_files(project_path, interest_dirs):
            try:
                yield md_file, md_file.read_text(encoding="utf-8")
            except Exception as e:
                ZeroFluffConsole.error(f"Erreur lecture {md_file}: {e}")

    def _validate_state_machine_and_ttl(
        self, project_path: Path, state: LoopState, story_filter: str = None
    ) -> None:
        import yaml
        from src.pipelines.state_machine import (
            StateMachineEngine,
            StateTransitionError,
            ContentTamperingError,
        )

        engine = StateMachineEngine(str(project_path))
        engine.validate_single_in_analyze()
        stories_dir = project_path / ProjectLayout.BACKLOG / "stories"
        if not stories_dir.exists():
            return
        for sf in stories_dir.glob("**/*.md"):
            if story_filter and story_filter not in sf.name:
                continue
            try:
                txt = sf.read_text(encoding="utf-8")
                if txt.startswith("---"):
                    parts = txt.split("---", 2)
                    if len(parts) >= 3:
                        data = yaml.safe_load(parts[1])
                        if isinstance(data, dict):
                            status = data.get("status", "")
                            if status in (
                                "READY_FOR_GROOMING",
                                "READY_FOR_DEV",
                                "IN_DEV",
                                "IN_QA",
                                "DONE",
                                "ACCEPTED",
                            ):
                                engine.validate_content_integrity(sf)
                            if status in (
                                "READY_FOR_GROOMING",
                                "READY_FOR_DEV",
                                "IN_DEV",
                                "IN_QA",
                                "DONE",
                                "ACCEPTED",
                                "COMPLETED",
                            ):
                                engine.validate_sentinel_approval(sf)
                            if status in (
                                "READY_FOR_GROOMING",
                                "READY_FOR_DEV",
                                "IN_DEV",
                                "IN_QA",
                                "DONE",
                                "ACCEPTED",
                            ):
                                engine.validate_fact_dossier_gate(
                                    sf, strict=getattr(state, "strict", False)
                                )
                            if status in ("IN_ANALYZE", "IN_BUILD", "IN_VALIDATE"):
                                engine.check_ttl(sf)
            except (StateTransitionError, ContentTamperingError):
                raise
            except Exception as exc:
                logger.debug(f"Erreur guardrails {sf}: {exc}", exc_info=True)

    # _heal_line_callout / _heal_line_links / _audit_and_heal_files :
    # hérités de WikiFixHealMixin (src/pipelines/_wikifix_heal.py, ADR-0202).

    def _save_cache(self, project_path: Path, cache_data: dict) -> None:
        try:
            cache_file = project_path / ProjectLayout.MEMORY / "cache" / "wikifix_cache.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(
                json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as exc:
            logger.debug(f"Erreur cache wikifix: {exc}", exc_info=True)

    def _detect_orphans(
        self, project_path: Path, markdown_files: list[Path], referenced: set
    ) -> list[str]:
        resolved = {p.resolve() for p in referenced if p.exists()}
        orphans = []
        for f in markdown_files:
            if f.name.lower() in ("readme.md", "index.md"):
                continue
            try:
                if f.resolve() not in resolved:
                    orphans.append(str(f.relative_to(project_path)))
            except Exception as exc:
                logger.debug(f"Erreur détection orphelin {f}: {exc}", exc_info=True)
        return orphans

    def _write_report_and_assert(
        self,
        project_path: Path,
        state: LoopState,
        md_files: list[Path],
        healed_links: list,
        healed_callouts: list,
        orphans: list,
        biz_errs: list,
        tech_errs: list,
        struct_errs: list,
    ) -> None:
        report_path = project_path / ProjectLayout.MEMORY / "wikifix_report.md"
        lines = [
            f"# 🛡️ Rapport de Santé Sémantique (WikiFix) - Projet '{state.project_name}'\n",
            "## 📊 Statut Global",
            f"- **Fichiers markdown audités** : {len(md_files)}",
            f"- **Liens brisés corrigés** : {len(healed_links)}",
            f"- **Pages orphelines** : {len(orphans)}",
            f"- **Violations Directives** : {len(biz_errs)}",
            f"- **Fuites Techniques** : {len(tech_errs)}",
            f"- **Défauts Structurels** : {len(struct_errs)}\n",
        ]
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text("\n".join(lines), encoding="utf-8")
            ZeroFluffConsole.success(
                f"Rapport WikiFix rédigé sous {ProjectLayout.MEMORY}/wikifix_report.md"
            )
        except Exception as e:
            ZeroFluffConsole.error(f"Échec écriture rapport: {e}")

        if struct_errs:
            blocking, tolerated = [], []
            # ADR-0385: Statuts legacy tolérés (rétrocompatibilité — pas de blocage
            # INVEST sur les récits déjà livrés ou en cours d'analyse).
            _tolerated = r"(?:IN_ANALYZE|IN_REVIEW|READY_FOR_GROOMING|READY_FOR_DEV|IN_DEV|IN_QA|DONE|DONE_TESTED|ACCEPTED|SHIPPED|TOMBSTONE|DRAFT|OPEN|ON_HOLD|CLOSED|SUPERSEDED|BACKLOG)"
            for sf in struct_errs:
                p = project_path / sf["file"]
                is_tol = False
                if p.exists():
                    try:
                        if re.search(
                            rf"(?m)^status:\s*{_tolerated}\b",
                            p.read_text(encoding="utf-8"),
                        ):
                            is_tol = True
                    except Exception as exc:
                        logger.debug(f"Erreur statut {p}: {exc}", exc_info=True)
                (tolerated if is_tol else blocking).append(sf)
            if tolerated:
                ZeroFluffConsole.warning(
                    f"[WikiFix Rétrocompatibilité] {len(tolerated)} récit(s) toléré(s) "
                    f"(statut terminal ou en cours — audit INVEST non bloquant)."
                )
            if blocking:
                raise ValueError(f"[ÉCHEC INVEST] {len(blocking)} récit(s) non-conformes.")

    def execute(
        self, state: LoopState, verbose: bool = False, story_filter: str = None
    ) -> LoopState:
        ZeroFluffConsole.step_s1(self.name, "Démarrage de l'audit de cohérence...")
        project_path = Path("Projects") / state.project_name
        if not project_path.exists():
            ZeroFluffConsole.error(f"Le dossier '{state.project_name}' n'existe pas.")
            return state

        self._validate_state_machine_and_ttl(project_path, state, story_filter=story_filter)
        dirs = [
            ProjectLayout.DOCS,
            ProjectLayout.DIRECTIVES,
            ProjectLayout.BACKLOG,
            ProjectLayout.REFERENCE,
        ]
        all_md = self._collect_markdown_files(project_path, dirs)
        if not all_md:
            ZeroFluffConsole.step_s1(self.name, "Aucun fichier markdown trouvé.")
            return state

        base_map = {}
        for f in all_md:
            base_map.setdefault(f.name.lower(), []).append(f)
        md_files = [
            f for f in all_md if not any(part == ProjectLayout.REFERENCE for part in f.parts)
        ]

        cache_p = project_path / ProjectLayout.MEMORY / "cache" / "wikifix_cache.json"
        cache_data = {}
        if cache_p.exists():
            try:
                cache_data = json.loads(cache_p.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.debug(f"Erreur cache: {exc}", exc_info=True)

        b_alerts, h_links, c_alerts, h_callouts, ref_files, new_cache = self._audit_and_heal_files(
            project_path, md_files, base_map, cache_data, verbose
        )
        self._save_cache(project_path, new_cache)
        orphans = self._detect_orphans(project_path, md_files, ref_files)
        biz_errs = self._audit_business_exclusions(project_path)
        tech_errs = self._audit_technical_leakage(project_path, md_files)
        struct_errs = self._audit_structural_compliance(
            project_path, md_files, story_filter=story_filter
        )

        from src.core.rule_engine import RuleEngine

        rule_eng = RuleEngine()
        adr_dir = project_path / "docs" / "01-architecture"
        if adr_dir.exists():
            rule_eng.load_from_adr_dir(adr_dir)
        for fpath in md_files:
            if "backlog" in fpath.parts and "stories" in fpath.parts:
                if story_filter and story_filter not in fpath.name:
                    continue
                content = fpath.read_text(encoding="utf-8")
                for v in rule_eng.validate_all(content, target="backlog_stories"):
                    if v.severity == "BLOCKING":
                        struct_errs.append(
                            {
                                "file": str(fpath.relative_to(project_path)),
                                "missing": [f"[{v.check_id}] {v.message}"],
                            }
                        )

        self._generate_master_index(project_path, md_files)
        self._write_report_and_assert(
            project_path,
            state,
            md_files,
            h_links,
            h_callouts,
            orphans,
            biz_errs,
            tech_errs,
            struct_errs,
        )
        ZeroFluffConsole.success(f"Audit WikiFix terminé : {len(md_files)} fichier(s) analysé(s).")
        return state
