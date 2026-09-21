import json
import logging
import os
import re
import urllib.parse
from pathlib import Path
from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole
from src.pipelines.wikifix_auditors import WikiFixAuditMixin

logger = logging.getLogger(__name__)


def os_relative_path(from_dir: Path, to_file: Path) -> str:
    return os.path.relpath(str(to_file), start=str(from_dir)).replace("\\", "/")


class WikiFixAgent(WikiFixAuditMixin):
    """Linter sémantique actif et mécanique (Système 1)."""

    def __init__(self):
        self.name = "WikiFix"
        self.supported_callouts = {"NOTE", "TIP", "WARNING", "IMPORTANT", "CAUTION"}
        self.callout_mapping = {
            "note": "NOTE", "info": "NOTE", "tip": "TIP", "hint": "TIP",
            "warning": "WARNING", "danger": "WARNING", "error": "WARNING",
            "important": "IMPORTANT", "caution": "CAUTION",
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
                        except (OSError, ValueError):
                            continue
                except (OSError, PermissionError):
                    continue
        return files

    def _stream_markdown_files(self, project_path: Path, interest_dirs: list[str]):
        for md_file in self._collect_markdown_files(project_path, interest_dirs):
            try:
                yield md_file, md_file.read_text(encoding="utf-8")
            except Exception as e:
                ZeroFluffConsole.error(f"Erreur lecture {md_file}: {e}")

    def _validate_state_machine_and_ttl(self, project_path: Path, state: LoopState, story_filter: str = None) -> None:
        import yaml
        from src.pipelines.state_machine import StateMachineEngine, StateTransitionError, ContentTamperingError
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
                            if status in ("READY_FOR_GROOMING", "READY_FOR_DEV", "IN_DEV", "IN_QA", "DONE", "ACCEPTED"):
                                engine.validate_content_integrity(sf)
                            if status in ("READY_FOR_GROOMING", "READY_FOR_DEV", "IN_DEV", "IN_QA", "DONE", "ACCEPTED", "COMPLETED"):
                                engine.validate_sentinel_approval(sf)
                            if status in ("READY_FOR_GROOMING", "READY_FOR_DEV", "IN_DEV", "IN_QA", "DONE", "ACCEPTED"):
                                engine.validate_fact_dossier_gate(sf, strict=getattr(state, "strict", False))
                            if status in ("IN_ANALYZE", "IN_BUILD", "IN_VALIDATE"):
                                engine.check_ttl(sf)
            except (StateTransitionError, ContentTamperingError):
                raise
            except Exception as exc:
                logger.debug(f"Erreur guardrails {sf}: {exc}", exc_info=True)

    def _heal_line_callout(self, line: str, line_idx: int, file_rel: str, healed_callouts: list, callouts_alerts: list) -> tuple[str, bool]:
        match = re.search(r"^\s*>\s*\[!([^\]]+)\](.*)$", line)
        if not match:
            return line, False
        raw_type = match.group(1)
        if raw_type not in self.supported_callouts:
            normalized = self._normalize_callout(raw_type)
            if normalized:
                new_line = re.sub(r"\[![^\]]+\]", f"[!{normalized}]", line)
                healed_callouts.append({"file": file_rel, "line": line_idx, "from": raw_type, "to": normalized})
                ZeroFluffConsole.success(f"Callout auto-corrigé dans {file_rel}:{line_idx} ({raw_type} -> {normalized})")
                return new_line, True
            callouts_alerts.append({"file": file_rel, "line": line_idx, "type": raw_type, "msg": f"Callout non standard '{raw_type}'."})
        return line, False

    def _heal_line_links(self, line: str, line_idx: int, file_path: Path, file_rel: str, basename_map: dict,
                         referenced_files: set, healed_links: list, broken_links_alerts: list) -> tuple[str, bool]:
        matches = list(re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line))
        if not matches:
            return line, False
        line_offset = 0
        file_modified = False
        for match in matches:
            link_target = match.group(2).strip()
            if link_target.startswith(("http://", "https://", "mailto:")) or link_target.startswith("#"):
                continue
            decoded = urllib.parse.unquote(link_target)
            target_str = decoded.split("#")[0]
            if not target_str:
                continue
            target_path = Path(target_str.replace("file:///", "")) if target_str.startswith("file:///") else (file_path.parent / target_str).resolve()
            if target_path.exists():
                referenced_files.add(target_path.resolve())
            else:
                target_name = Path(target_str).name.lower()
                if target_name in basename_map and len(basename_map[target_name]) == 1:
                    resolved = basename_map[target_name][0]
                    referenced_files.add(resolved.resolve())
                    try:
                        rel = os_relative_path(file_path.parent, resolved)
                    except Exception:
                        rel = resolved.resolve().as_uri()
                    anchor = ("#" + decoded.split("#")[1]) if "#" in decoded else ""
                    new_target = f"{rel}{anchor}"
                    sp, ep = match.start(2) + line_offset, match.end(2) + line_offset
                    line = line[:sp] + new_target + line[ep:]
                    line_offset += len(new_target) - len(link_target)
                    file_modified = True
                    healed_links.append({"file": file_rel, "line": line_idx, "broken": link_target, "healed": new_target})
                    ZeroFluffConsole.success(f"Lien auto-corrigé dans {file_rel}:{line_idx}")
                else:
                    broken_links_alerts.append({"file": file_rel, "line": line_idx, "target": link_target, "msg": "Lien brisé."})
        return line, file_modified

    def _audit_and_heal_files(self, project_path: Path, markdown_files: list[Path], basename_map: dict,
                              cache_data: dict, verbose: bool) -> tuple:
        b_alerts, h_links, c_alerts, h_callouts, ref_files, new_cache = [], [], [], [], set(), {}
        for file_path in markdown_files:
            file_rel = str(file_path.relative_to(project_path))
            mtime = os.path.getmtime(file_path)
            cached = cache_data.get(file_rel, {})
            if cached.get("mtime") == mtime and not verbose:
                new_cache[file_rel] = cached
                for ref in cached.get("referenced_files", []):
                    if Path(ref).exists():
                        ref_files.add(Path(ref).resolve())
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                ZeroFluffConsole.error(f"Impossible de lire {file_rel}: {e}")
                continue
            file_mod = False
            new_lines = []
            for idx, line in enumerate(content.splitlines(), 1):
                line, c_mod = self._heal_line_callout(line, idx, file_rel, h_callouts, c_alerts)
                line, l_mod = self._heal_line_links(line, idx, file_path, file_rel, basename_map, ref_files, h_links, b_alerts)
                file_mod = file_mod or c_mod or l_mod
                new_lines.append(line)
            if file_mod:
                try:
                    file_path.write_text("\n".join(new_lines), encoding="utf-8")
                    mtime = os.path.getmtime(file_path)
                except Exception as e:
                    ZeroFluffConsole.error(f"Échec écriture {file_rel}: {e}")
            new_cache[file_rel] = {"mtime": mtime, "referenced_files": [str(p) for p in ref_files if p.exists()]}
        return b_alerts, h_links, c_alerts, h_callouts, ref_files, new_cache

    def _save_cache(self, project_path: Path, cache_data: dict) -> None:
        try:
            cache_file = project_path / ProjectLayout.MEMORY / "cache" / "wikifix_cache.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Erreur cache wikifix: {exc}", exc_info=True)

    def _detect_orphans(self, project_path: Path, markdown_files: list[Path], referenced: set) -> list[str]:
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

    def _write_report_and_assert(self, project_path: Path, state: LoopState, md_files: list[Path],
                                 healed_links: list, healed_callouts: list, orphans: list,
                                 biz_errs: list, tech_errs: list, struct_errs: list) -> None:
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
            ZeroFluffConsole.success(f"Rapport WikiFix rédigé sous {ProjectLayout.MEMORY}/wikifix_report.md")
        except Exception as e:
            ZeroFluffConsole.error(f"Échec écriture rapport: {e}")

        if struct_errs:
            blocking, in_analyze = [], []
            for sf in struct_errs:
                p = project_path / sf["file"]
                is_an = False
                if p.exists():
                    try:
                        if re.search(r"(?m)^status:\s*(?:IN_ANALYZE|IN_REVIEW)\b", p.read_text(encoding="utf-8")):
                            is_an = True
                    except Exception as exc:
                        logger.debug(f"Erreur statut {p}: {exc}", exc_info=True)
                (in_analyze if is_an else blocking).append(sf)
            if in_analyze:
                ZeroFluffConsole.warning(f"[WikiFix IN_ANALYZE] {len(in_analyze)} récit(s) toléré(s).")
            if blocking:
                raise ValueError(f"[ÉCHEC INVEST] {len(blocking)} récit(s) non-conformes.")

    def execute(self, state: LoopState, verbose: bool = False, story_filter: str = None) -> LoopState:
        ZeroFluffConsole.step_s1(self.name, "Démarrage de l'audit de cohérence...")
        project_path = Path("Projects") / state.project_name
        if not project_path.exists():
            ZeroFluffConsole.error(f"Le dossier '{state.project_name}' n'existe pas.")
            return state

        self._validate_state_machine_and_ttl(project_path, state, story_filter=story_filter)
        dirs = [ProjectLayout.DOCS, ProjectLayout.DIRECTIVES, ProjectLayout.BACKLOG, ProjectLayout.REFERENCE]
        all_md = self._collect_markdown_files(project_path, dirs)
        if not all_md:
            ZeroFluffConsole.step_s1(self.name, "Aucun fichier markdown trouvé.")
            return state

        base_map = {}
        for f in all_md:
            base_map.setdefault(f.name.lower(), []).append(f)
        md_files = [f for f in all_md if not any(part == ProjectLayout.REFERENCE for part in f.parts)]

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
        struct_errs = self._audit_structural_compliance(project_path, md_files, story_filter=story_filter)

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
                        struct_errs.append({"file": str(fpath.relative_to(project_path)), "missing": [f"[{v.check_id}] {v.message}"]})

        self._generate_master_index(project_path, md_files)
        self._write_report_and_assert(project_path, state, md_files, h_links, h_callouts, orphans, biz_errs, tech_errs, struct_errs)
        ZeroFluffConsole.success(f"Audit WikiFix terminé : {len(md_files)} fichier(s) analysé(s).")
        return state
