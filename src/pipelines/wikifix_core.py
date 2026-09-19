"""
wikifix_core.py — WikiFixAgent principal (ADR-0202)
Contient la classe WikiFixAgent avec la logique d'orchestration execute().
Les méthodes d'audit sont héritées de WikiFixAuditMixin (wikifix_auditors.py).
Ne pas modifier ce fichier directement : façade via wikifix.py.
"""
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
    """
    Système 1 : Agent WikiFix.
    Linter sémantique actif et mécanique.
    Parcourt le projet pour valider les liens hypertextes internes,
    auditer et normaliser les callouts Obsidian/GitHub, identifier les pages
    orphelines, et appliquer des résolutions automatiques (Auto-Healing).
    """

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

    def _normalize_callout(self, callout_type: str) -> str:
        """Normalise un type de callout en standard ou retourne None si inconnu."""
        lower_type = callout_type.lower().strip()
        return self.callout_mapping.get(lower_type, None)

    def _collect_markdown_files(self, project_path: Path, interest_dirs: list[str]) -> list[Path]:
        """Collecte les chemins de fichiers markdown sans chargement I/O inutile du contenu (Zero-I/O Discovery)."""
        files = []
        for d in interest_dirs:
            dir_path = project_path / d
            if dir_path.exists():
                try:
                    for md_file in dir_path.rglob("*.md"):
                        try:
                            # Protection Windows MAX_PATH : test d'accès rapide
                            if md_file.is_file():
                                files.append(md_file)
                        except (OSError, ValueError):
                            continue
                except (OSError, PermissionError):
                    continue
        return files

    def _stream_markdown_files(self, project_path: Path, interest_dirs: list[str]):
        """Générateur 'Lazy Evaluation' qui cède les fichiers markdown et leur contenu un par un."""
        for md_file in self._collect_markdown_files(project_path, interest_dirs):
            try:
                content = md_file.read_text(encoding="utf-8")
                yield md_file, content
            except Exception as e:
                ZeroFluffConsole.error(f"Erreur de lecture sur {md_file}: {e}")

    # ------------------------------------------------------------------
    # Helpers d'orchestration
    # ------------------------------------------------------------------
    def _setup_project_paths(self, state: LoopState):
        """Vérifie project_path, initialise StateMachineEngine, valide les stories."""
        import yaml
        from src.pipelines.state_machine import (
            StateMachineEngine,
            StateTransitionError,
            ContentTamperingError,
        )

        project_path = Path("Projects") / state.project_name
        if not project_path.exists():
            ZeroFluffConsole.error(
                f"Le dossier du projet '{state.project_name}' n'existe pas."
            )
            return None

        engine = StateMachineEngine(str(project_path))
        engine.validate_single_in_analyze()

        stories_dir = project_path / ProjectLayout.BACKLOG / "stories"
        if stories_dir.exists():
            for sf in stories_dir.glob("**/*.md"):
                try:
                    txt = sf.read_text(encoding="utf-8")
                    if txt.startswith("---"):
                        parts = txt.split("---", 2)
                        if len(parts) >= 3:
                            data = yaml.safe_load(parts[1])
                            if isinstance(data, dict):
                                status = data.get("status", "")
                                if status in (
                                    "READY_FOR_GROOMING", "READY_FOR_DEV",
                                    "IN_DEV", "IN_QA", "DONE", "ACCEPTED",
                                ):
                                    engine.validate_content_integrity(sf)
                                if status in (
                                    "READY_FOR_GROOMING", "READY_FOR_DEV",
                                    "IN_DEV", "IN_QA", "DONE", "ACCEPTED", "COMPLETED",
                                ):
                                    engine.validate_sentinel_approval(sf)
                                if status in (
                                    "READY_FOR_GROOMING", "READY_FOR_DEV",
                                    "IN_DEV", "IN_QA", "DONE", "ACCEPTED",
                                ):
                                    engine.validate_fact_dossier_gate(
                                        sf, strict=getattr(state, "strict", False)
                                    )
                                if status in ("IN_ANALYZE", "IN_BUILD", "IN_VALIDATE"):
                                    engine.check_ttl(sf)
                except (StateTransitionError, ContentTamperingError) as ste:
                    ZeroFluffConsole.error(str(ste))
                    raise ste
                except Exception as exc:
                    logger.debug("Erreur validation stories %s", sf, exc_info=True)

        return project_path

    def _collect_and_filter_files(self, project_path: Path):
        """Collecte tous les fichiers markdown, construit basename_map, exclut reference/."""
        all_markdown_files = self._collect_markdown_files(
            project_path,
            [
                ProjectLayout.DOCS,
                ProjectLayout.DIRECTIVES,
                ProjectLayout.BACKLOG,
                ProjectLayout.REFERENCE,
            ],
        )
        basename_map = {}
        for fpath in all_markdown_files:
            bname = fpath.name.lower()
            if bname not in basename_map:
                basename_map[bname] = []
            basename_map[bname].append(fpath)

        # Les fichiers sous reference/ sont des miroirs Git distants en lecture seule (SSOT)
        markdown_files = [
            f
            for f in all_markdown_files
            if not any(part == ProjectLayout.REFERENCE for part in f.parts)
        ]
        return all_markdown_files, markdown_files, basename_map

    def _load_wikifix_cache(self, project_path: Path):
        """Charge le cache mtime WikiFix depuis wikifix_cache.json."""
        cache_dir = project_path / ProjectLayout.MEMORY / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "wikifix_cache.json"
        cache_data = {}
        if cache_file.exists():
            try:
                cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.debug("Erreur chargement cache wikifix", exc_info=True)
        return cache_file, cache_data

    def _audit_files_loop(self, project_path, markdown_files, basename_map, cache_data, verbose):
        """Boucle principale d'audit fichier par fichier. Retourne les résultats et le nouveau cache."""
        broken_links_alerts = []
        healed_links = []
        callouts_alerts = []
        healed_callouts = []
        referenced_files = set()
        new_cache_data = {}

        for file_path in markdown_files:
            file_rel = str(file_path.relative_to(project_path))
            mtime = os.path.getmtime(file_path)

            if verbose:
                ZeroFluffConsole.info(f"Audit de [highlight]{file_rel}[/highlight]...")

            cached_entry = cache_data.get(file_rel, {})
            if cached_entry.get("mtime") == mtime and not verbose:
                new_cache_data[file_rel] = cached_entry
                for ref in cached_entry.get("referenced_files", []):
                    ref_p = Path(ref)
                    if ref_p.exists():
                        referenced_files.add(ref_p.resolve())
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                ZeroFluffConsole.error(f"Impossible de lire le fichier {file_rel} : {e}")
                continue

            file_modified = False
            lines = content.splitlines()
            new_lines = []

            for line_idx, line in enumerate(lines, 1):
                # A. Traitement et correction des Callouts
                callout_match = re.search(r"^\s*>\s*\[!([^\]]+)\](.*)$", line)
                if callout_match:
                    raw_type = callout_match.group(1)
                    if raw_type not in self.supported_callouts:
                        normalized = self._normalize_callout(raw_type)
                        if normalized:
                            new_line = re.sub(r"\[![^\]]+\]", f"[!{normalized}]", line)
                            line = new_line
                            file_modified = True
                            healed_callouts.append(
                                {"file": str(file_rel), "line": line_idx, "from": raw_type, "to": normalized}
                            )
                            ZeroFluffConsole.success(
                                f"Callout auto-corrigé dans {file_rel}:{line_idx} ({raw_type} -> {normalized})"
                            )
                        else:
                            callouts_alerts.append(
                                {"file": str(file_rel), "line": line_idx, "type": raw_type,
                                 "msg": f"Le type de callout '{raw_type}' n'est pas standard."}
                            )

                # B. Traitement et correction des Liens Markdown
                link_matches = list(re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line))
                if link_matches:
                    line_offset = 0
                    for match in link_matches:
                        link_target = match.group(2).strip()
                        if link_target.startswith(("http://", "https://", "mailto:")) or link_target.startswith("#"):
                            continue

                        decoded_target = urllib.parse.unquote(link_target)
                        target_path_str = decoded_target.split("#")[0]
                        if not target_path_str:
                            continue

                        if target_path_str.startswith("file:///"):
                            target_path = Path(target_path_str.replace("file:///", ""))
                        else:
                            target_path = (file_path.parent / target_path_str).resolve()

                        if target_path.exists():
                            try:
                                referenced_files.add(target_path.resolve())
                            except Exception as exc:
                                logger.debug("Erreur referenced_files.add", exc_info=True)
                        else:
                            target_name = Path(target_path_str).name.lower()
                            if target_name in basename_map and len(basename_map[target_name]) == 1:
                                resolved_file = basename_map[target_name][0]
                                referenced_files.add(resolved_file.resolve())
                                try:
                                    rel_path = os_relative_path(file_path.parent, resolved_file)
                                except Exception:
                                    rel_path = resolved_file.resolve().as_uri()

                                anchor = ""
                                if "#" in decoded_target:
                                    anchor = "#" + decoded_target.split("#")[1]

                                new_target = f"{rel_path}{anchor}"
                                start_pos = match.start(2) + line_offset
                                end_pos = match.end(2) + line_offset

                                line = line[:start_pos] + new_target + line[end_pos:]
                                line_offset += len(new_target) - len(link_target)

                                file_modified = True
                                healed_links.append(
                                    {"file": str(file_rel), "line": line_idx, "broken": link_target, "healed": new_target}
                                )
                                ZeroFluffConsole.success(
                                    f"Lien brisé auto-corrigé dans {file_rel}:{line_idx} ({link_target} -> {new_target})"
                                )
                            else:
                                broken_links_alerts.append(
                                    {"file": str(file_rel), "line": line_idx, "target": link_target,
                                     "msg": "Lien brisé (fichier introuvable)."}
                                )

                new_lines.append(line)

            if file_modified:
                try:
                    file_path.write_text("\n".join(new_lines), encoding="utf-8")
                    mtime = os.path.getmtime(file_path)
                except Exception as e:
                    ZeroFluffConsole.error(f"Échec de l'écriture du fichier corrigé {file_rel} : {e}")

            new_cache_data[file_rel] = {
                "mtime": mtime,
                "referenced_files": [str(p) for p in referenced_files if p.exists()],
            }

        return broken_links_alerts, healed_links, callouts_alerts, healed_callouts, referenced_files, new_cache_data

    def _detect_orphans(self, project_path, markdown_files, referenced_files):
        """Détecte les pages orphelines (non référencées)."""
        orphan_files = []
        resolved_referenced_paths = {p.resolve() for p in referenced_files if p.exists()}
        for fpath in markdown_files:
            if fpath.name.lower() in ("readme.md", "index.md"):
                continue
            try:
                if fpath.resolve() not in resolved_referenced_paths:
                    orphan_files.append(str(fpath.relative_to(project_path)))
            except Exception as exc:
                logger.debug("Erreur détection orphelin %s", fpath, exc_info=True)
        return orphan_files

    def _write_report(self, project_path, state, markdown_files, healed_links, healed_callouts,
                      orphan_files, business_violations, technical_leakages, structural_failures):
        """Génère et écrit le rapport wikifix_report.md."""
        report_path = project_path / ProjectLayout.MEMORY / "wikifix_report.md"
        report_lines = [
            f"# 🛡️ Rapport de Santé Sémantique (WikiFix) - Projet '{state.project_name}'\n",
            f"## 📊 Statut Global",
            f"- **Fichiers markdown audités** : {len(markdown_files)} fichier(s)",
            f"- **Liens brisés corrigés (Auto-Healing)** : {len(healed_links)} correction(s)",
            f"- **Pages orphelines identifiées** : {len(orphan_files)} page(s)",
            f"- **Violations de Directives d'Affaires** : {len(business_violations)} alerte(s)",
            f"- **Fuites Techniques (Backlog)** : {len(technical_leakages)} alerte(s)",
            f"- **Défauts Structurels (INVEST)** : {len(structural_failures)} alerte(s)\n",
        ]

        if business_violations:
            report_lines.append("## 🛑 ALERTE CRITIQUE : Non-Conformité d'Affaires")
            for violation in business_violations:
                report_lines.append(
                    f"- **Fichier** : [{violation['file']}](file:///{project_path / violation['file']}) (Keyword: `{violation['keyword']}`)"
                )
            ZeroFluffConsole.error(
                f"[GUARDRAIL BUSINESS] Détecté {len(business_violations)} violations !"
            )

        if technical_leakages:
            report_lines.append(
                "## ⚠️ AVERTISSEMENT : Fuites Techniques (Isolation Backlog rompue)"
            )
            for leak in technical_leakages:
                report_lines.append(
                    f"- **Fichier** : [{leak['file']}](file:///{project_path / leak['file']}) (Terme: `{leak['keyword']}`)"
                )
            ZeroFluffConsole.error(
                f"[GUARDRAIL TECH] Détecté {len(technical_leakages)} fuites techniques dans le backlog !"
            )

        if structural_failures:
            report_lines.append(
                "## ❌ ERREUR FATALE : Conformité Structurelle du Backlog (INVEST)"
            )
            for sf in structural_failures:
                report_lines.append(
                    f"- **Fichier** : [{sf['file']}](file:///{project_path / sf['file']}) (Manquant: `{', '.join(sf['missing'])}`)"
                )
            ZeroFluffConsole.error(
                f"[GUARDRAIL INVEST] Détecté {len(structural_failures)} fichiers non-conformes au gabarit !"
            )

        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text("\n".join(report_lines), encoding="utf-8")
            ZeroFluffConsole.success(
                f"Rapport WikiFix rédigé sous {ProjectLayout.MEMORY}/wikifix_report.md"
            )
        except Exception as e:
            ZeroFluffConsole.error(f"Échec de l'écriture du rapport : {e}")

    def execute(self, state: LoopState, verbose: bool = False, story_filter: str = None) -> LoopState:
        ZeroFluffConsole.step_s1(
            self.name,
            "Démarrage de l'audit de cohérence de la base de connaissances...",
        )

        project_path = self._setup_project_paths(state)
        if project_path is None:
            return state

        all_markdown_files, markdown_files, basename_map = self._collect_and_filter_files(project_path)
        if not all_markdown_files:
            ZeroFluffConsole.step_s1(self.name, "Aucun fichier markdown trouvé dans les répertoires cibles.")
            return state

        cache_file, cache_data = self._load_wikifix_cache(project_path)

        broken_links_alerts, healed_links, callouts_alerts, healed_callouts, referenced_files, new_cache_data = (
            self._audit_files_loop(project_path, markdown_files, basename_map, cache_data, verbose)
        )

        try:
            cache_file.write_text(
                json.dumps(new_cache_data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as exc:
            logger.debug("Erreur écriture cache wikifix", exc_info=True)

        orphan_files = self._detect_orphans(project_path, markdown_files, referenced_files)

        # 4. Linter de conformité d'affaires
        business_violations = self._audit_business_exclusions(project_path)
        # 4.5 Linter d'Isolation Technique (Backlog)
        technical_leakages = self._audit_technical_leakage(project_path, markdown_files)
        # 4.6 Linter de Conformité Structurelle (INVEST)
        structural_failures = self._audit_structural_compliance(
            project_path, markdown_files, story_filter=story_filter
        )

        # 4.7 Intégration Dynamique RuleEngine (ADR-0329)
        from src.core.rule_engine import RuleEngine

        rule_engine = RuleEngine()
        adr_dir = project_path / "docs" / "01-architecture"
        if adr_dir.exists():
            rule_engine.load_from_adr_dir(adr_dir)

        for fpath in markdown_files:
            if "backlog" in fpath.parts and "stories" in fpath.parts:
                if story_filter and story_filter not in fpath.name:
                    continue
                content = fpath.read_text(encoding="utf-8")
                violations = rule_engine.validate_all(content, target="backlog_stories")
                for v in violations:
                    if v.severity == "BLOCKING":
                        structural_failures.append(
                            {"file": str(fpath.relative_to(project_path)), "missing": [f"[{v.check_id}] {v.message}"]}
                        )

        # 4.8 OpenWiki Dynamic Master Index Generation
        self._generate_master_index(project_path, markdown_files)

        # 5. Rédiger le rapport
        self._write_report(
            project_path, state, markdown_files, healed_links, healed_callouts,
            orphan_files, business_violations, technical_leakages, structural_failures
        )

        ZeroFluffConsole.success(
            f"Audit WikiFix terminé : {len(markdown_files)} fichier(s) analysé(s) ({len(healed_links) + len(healed_callouts)} correction(s))."
        )

        if structural_failures:
            blocking_failures = []
            in_analyze_failures = []
            for sf in structural_failures:
                sf_p = project_path / sf["file"]
                is_in_analyze = False
                if sf_p.exists():
                    try:
                        txt_content = sf_p.read_text(encoding="utf-8")
                        if re.search(r"(?m)^status:\s*(?:IN_ANALYZE|IN_REVIEW)\b", txt_content):
                            is_in_analyze = True
                    except Exception as exc:
                        logger.debug("Erreur vérification statut in_analyze %s", sf_p, exc_info=True)
                if is_in_analyze:
                    in_analyze_failures.append(sf)
                else:
                    blocking_failures.append(sf)

            if in_analyze_failures:
                ZeroFluffConsole.warning(
                    f"[WikiFix IN_ANALYZE / IN_REVIEW] {len(in_analyze_failures)} récit(s) en cours de cadrage/révision toléré(s) avant la session Grill-me."
                )

            if blocking_failures:
                raise ValueError(
                    f"[ÉCHEC DE VALIDATION INVEST] {len(blocking_failures)} récit(s) ne respectent pas le gabarit officiel (Gherkin/INVEST manquant).\nCe n'est pas un crash système, mais une validation métier ! Lisez memory/wikifix_report.md, corrigez les fichiers, et relancez la validation."
                )

        return state
