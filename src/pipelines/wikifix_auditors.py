import logging
import os
import re
from pathlib import Path
import yaml
from src.state import ProjectLayout
from src.cli import ZeroFluffConsole

logger = logging.getLogger(__name__)


class WikiFixAuditMixin:
    """Mixin regroupant les règles d'audit déterministe pour WikiFix."""

    def _audit_business_exclusions(self, project_path: Path) -> list[dict]:
        violations = []
        exclusions = {
            "stripe": "Intégration Stripe détectée.",
            "paypal": "Intégration PayPal détectée.",
            "checkout": "Tunnel d'achat détecté.",
            "prescription": "Santé clinique détectée.",
            "ordonnance": "Santé clinique détectée.",
        }
        rho_files = [
            Path("standards") / "rho_rules.yaml",
            project_path / "memory" / "rho_rules.yaml",
        ]
        for rho_file in rho_files:
            if rho_file.exists():
                try:
                    with open(rho_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        for rule in data.get("rules", []):
                            kw = rule.get("keyword")
                            msg = rule.get("msg")
                            if kw and msg:
                                exclusions[kw.lower()] = msg
                except Exception as exc:
                    logger.debug(f"Erreur lecture RHO {rho_file}: {exc}", exc_info=True)

        src_dir = project_path / ProjectLayout.SRC
        if not src_dir.exists():
            return violations

        for file_path in src_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in (".ts", ".tsx", ".py", ".js"):
                try:
                    content = file_path.read_text(encoding="utf-8").lower()
                except Exception as exc:
                    logger.debug(f"Erreur lecture code {file_path}: {exc}", exc_info=True)
                    continue
                for keyword, msg in exclusions.items():
                    if keyword in content:
                        violations.append({
                            "file": str(file_path.relative_to(project_path)),
                            "keyword": keyword,
                            "msg": msg,
                        })
        return violations

    def _audit_technical_leakage(self, project_path: Path, markdown_files: list[Path]) -> list[dict]:
        leakages = []
        tech_keywords = [
            "npm install", "yarn add", "expo install", "import {", "import *",
            "```typescript", "```javascript", "```tsx", "```ts", "zustand",
            "redux", "axios", "fetch(", "(voir rec-", "(voir st-", "(selon pt-",
            "state-bound", "isjustificationvalid", "isformvalid",
        ]
        for fpath in markdown_files:
            if "backlog" in fpath.parts:
                try:
                    content = fpath.read_text(encoding="utf-8")
                    content_lower = content.lower()
                except Exception as exc:
                    logger.debug(f"Erreur lecture backlog {fpath}: {exc}", exc_info=True)
                    continue

                for kw in tech_keywords:
                    if kw in content_lower:
                        leakages.append({"file": str(fpath.relative_to(project_path)), "keyword": kw})

                raw_refs = re.findall(r"(?<!\])\([^)\n]*\b(?:REC|ST|PT)-\d+[^)\n]*\)", content, re.IGNORECASE)
                parenthetical_refs = [
                    ref for ref in raw_refs
                    if not any(proto in ref.lower() for proto in ["http://", "https://", "file://", "mailto:"])
                ]
                for pref in set(parenthetical_refs):
                    leakages.append({
                        "file": str(fpath.relative_to(project_path)),
                        "keyword": f"Parenthèse de renvoi interne interdite (Règle #9): {pref}",
                    })
        return leakages

    def _check_story_invest(self, fpath: Path, content: str, project_path: Path, is_ready: bool) -> list[str]:
        missing = []
        required_sections = [
            (r"## Scénarios de test", "Section 'Scénarios de test' manquante"),
            (r"## Règles d", "Section 'Règles d'affaires' manquante"),
        ]
        for req_pattern, label in required_sections:
            if not re.search(req_pattern, content, re.IGNORECASE):
                missing.append(label)

        scenarios = re.findall(r"(?:Scénario|Scenario)\s*:", content, re.IGNORECASE)
        if len(scenarios) < 4:
            missing.append(f"Gherkin 4-Piliers Incomplet ({len(scenarios)}/4 scénarios exigés par ADR-0301)")

        if not re.search(r"(?:figma\.com|!\[|```mermaid|## Maquettes)", content, re.IGNORECASE):
            missing.append("Section Maquettes (liens Figma ou visuels UI) manquante (Visual Gate)")

        if not re.search(r"(?:UI|Interface|Composants|Maquette|Contrats UI|Endpoints|Data Model|API)", content, re.IGNORECASE):
            missing.append("Contrats UI & API Backend manquants")

        fluff_terms = ["affiché clairement", "affichée clairement", "l'écran s'ouvre", "si nécessaire"]
        found_fluff = [term for term in fluff_terms if term in content.lower()]
        if found_fluff:
            missing.append(f"Formulations évasives détectées: {', '.join(found_fluff)}")

        if re.findall(r"#\s*PILIER\s*\d+", content, re.IGNORECASE):
            missing.append("Commentaires d'échafaudage '# PILIER X' interdits (ADR-0301)")

        if re.findall(r"\(Standard D-A-F-E\)", content, re.IGNORECASE):
            missing.append("Marqueurs d'échafaudage interdits (Standard D-A-F-E)")

        if re.findall(r"(?:^|\n)\s*[-*]\s*\*\*\s*(?:RM-(?:TEMP|TODO|FIXME|WIP)|TODO|FIXME|WIP)\b", content, re.IGNORECASE):
            missing.append("Identifiants éphémères interdits dans les règles d'affaires")

        if re.findall(r"(?:^|\n)\s*[-*]\s*\*\*\s*RM-[A-Z0-9-]+\s*\*\*\s*:", content):
            missing.append("Règle d'affaires sans titre fonctionnel standard")

        is_frontend = bool(re.search(r"layer:\s*frontend", content, re.IGNORECASE)) or fpath.name.upper().endswith("-FE.MD")
        if is_frontend:
            if not re.search(r"(?:Périmètre de Consultation|Read Model|Inventaire visualisé|Composants de Lecture|Consultation|jauge)", content, re.IGNORECASE):
                missing.append("Périmètre de Consultation (Read Model) manquant dans le récit Frontend")
            h_pos = content.find("En-tête") if "En-tête" in content else content.find("Top Bar")
            f_pos = content.find("Pied de Page") if "Pied de Page" in content else content.find("Footer")
            if h_pos != -1 and f_pos != -1 and h_pos > f_pos:
                missing.append("Règle #13: l'En-tête (Header) doit apparaître AVANT le Pied de Page (Footer)")

        if is_ready:
            unresolved_oq = re.findall(r"\bOQ-\d+\b", content)
            if unresolved_oq:
                missing.append(f"Statut READY avec questions ouvertes non résolues: {', '.join(set(unresolved_oq))}")
            ghosts = self._check_ghost_sources(content, project_path, fpath)
            if ghosts:
                missing.append(f"[GUARDRAIL FACT-SEARCH] Source(s) citée(s) introuvable(s): {', '.join(set(ghosts))}")

        for wlink in re.findall(r"https://dev\.azure\.com/[^\s)]+_wiki/wikis/[^\s)]+", content):
            if "friendlyName=" in wlink:
                missing.append(f"[ADR-0327] Paramètre conflictuel 'friendlyName=' interdit: {wlink}")
            if "pagePath=" in wlink and "---" in wlink:
                missing.append(f"[ADR-0327] Encodage défectueux du tiret littéral: {wlink}")

        return missing

    def _check_ghost_sources(self, content: str, project_path: Path, fpath: Path) -> list[str]:
        cited_sources = re.findall(r"\b([a-zA-Z0-9_\-/\\]+\.(?:md|xlsx|pdf|docx|plist|cs|csproj|xml|yml|json))\b", content)
        ghost_sources = []
        ignored = {"package.json", "tsconfig.json", "story_template.md", "active_project.json"}
        for src in set(cited_sources):
            if src.startswith("<") or src.endswith(">") or "template" in src.lower() or src in ignored:
                continue
            src_clean = src.replace("\\", "/").lstrip("/")
            candidates = [
                project_path / src_clean, project_path / "docs" / src_clean, Path(src_clean),
                Path("standards") / src_clean, project_path / "memory" / "evidence" / Path(src_clean).name,
                project_path / "memory" / "evidence" / src_clean, project_path / "backlog" / src_clean,
                project_path / "reference" / src_clean, (fpath.parent / src_clean).resolve(),
            ]
            if not any(c.exists() for c in candidates):
                fname = Path(src_clean).name
                found = False
                for sub in ["docs", "backlog", "reference"]:
                    sub_p = project_path / sub
                    if sub_p.exists() and list(sub_p.glob(f"**/{fname}")):
                        found = True
                        break
                if not found:
                    ghost_sources.append(src)
        return ghost_sources

    def _auto_heal_h2_separators(self, fpath: Path, content: str) -> str:
        h2_matches = list(re.finditer(r"(?m)^(##\s+.+)$", content))
        if len(h2_matches) <= 1:
            return content
        content_modified = False
        new_content = content
        for match in h2_matches[1:]:
            header_str = match.group(1)
            pos = match.start()
            prefix_window = new_content[max(0, pos - 25) : pos]
            if "---" not in prefix_window:
                replacement = f"\n---\n\n{header_str}"
                new_content = new_content[:pos] + replacement + new_content[pos + len(header_str) :]
                content_modified = True
        if content_modified:
            try:
                fpath.write_text(new_content, encoding="utf-8")
                ZeroFluffConsole.success(f"[WikiFix Auto-Healing] Séparateurs '---' auto-insérés pour {fpath.name}")
            except Exception as exc:
                logger.debug(f"Erreur écriture séparateurs {fpath}: {exc}", exc_info=True)
            return new_content
        return content

    def _sync_evidence_pack_sidecar(self, fpath: Path, project_path: Path) -> None:
        try:
            ev_base = project_path / "memory" / "evidence"
            existing_eps = list(ev_base.rglob(f"{fpath.stem}_evidence.json")) if ev_base.exists() else []
            ep_file = existing_eps[0] if existing_eps else (ev_base / f"{fpath.stem}_evidence.json")
            if not (ep_file.exists() and os.path.getmtime(ep_file) >= os.path.getmtime(fpath)):
                from src.pipelines.evidence_pack import EvidencePackEngine
                ep_engine = EvidencePackEngine(project_path)
                ep_pack = ep_engine.extract_evidence(fpath)
                ep_engine.save_evidence_pack(ep_pack)
                ZeroFluffConsole.success(f"[WikiFix] EvidencePack sidecar mis à jour: {ep_file.name}")
        except Exception as e_ep:
            logger.debug(f"Erreur génération EvidencePack pour {fpath.name}: {e_ep}", exc_info=True)

    def _audit_structural_compliance(self, project_path: Path, markdown_files: list[Path], story_filter: str = None) -> list[dict]:
        structural_failures = []
        for fpath in markdown_files:
            if "backlog" in fpath.parts and "stories" in fpath.parts:
                if any(p in ("reference", "archive_deprecated", "archive", "_archive") for p in fpath.parts):
                    continue
                if story_filter and story_filter not in fpath.name:
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8")
                except Exception as exc:
                    logger.debug(f"Erreur lecture story {fpath}: {exc}", exc_info=True)
                    continue

                content = self._auto_heal_h2_separators(fpath, content)
                is_ready = bool(re.search(r"status:\s*(?:READY_FOR_DEV|READY_FOR_GROOMING)", content, re.IGNORECASE))
                missing = self._check_story_invest(fpath, content, project_path, is_ready)
                self._sync_evidence_pack_sidecar(fpath, project_path)

                if missing:
                    structural_failures.append({"file": str(fpath.relative_to(project_path)), "missing": missing})

        sprint_backlog_file = project_path / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
        if sprint_backlog_file.exists():
            try:
                sb_content = sprint_backlog_file.read_text(encoding="utf-8")
                stories_dir = project_path / ProjectLayout.BACKLOG / "stories"
                if stories_dir.exists():
                    for sfile in stories_dir.rglob("*.md"):
                        if any(p in ("reference", "archive_deprecated", "archive", "_archive") for p in sfile.parts):
                            continue
                        if sfile.stem not in sb_content:
                            structural_failures.append({
                                "file": str(sfile.relative_to(project_path)),
                                "missing": [f"Récit orphelin '{sfile.stem}' absent du sprint_backlog.md"],
                            })
            except Exception as exc:
                logger.debug(f"Erreur lecture sprint_backlog: {exc}", exc_info=True)
        return structural_failures

    def _generate_master_index(self, project_path: Path, markdown_files: list[Path]) -> None:
        docs_dir = project_path / ProjectLayout.DOCS
        if not docs_dir.exists():
            return
        index_file = docs_dir / "index.md"
        doc_files = sorted([f for f in docs_dir.rglob("*.md") if f.name.lower() != "index.md"])
        lines = [
            f"# 📚 Table des Matières Dynamique - SSOT Projet '{project_path.name}'\n",
            "- **Statut Wiki** : AUTO-MAINTENU & HEALED",
            f"- **Fichiers Documentés** : {len(doc_files)}\n",
            "## 🗂️ Sommaire de la Base de Connaissances\n",
        ]
        for doc in doc_files:
            rel_path = doc.relative_to(docs_dir).as_posix()
            title = doc.stem.replace("_", " ").replace("-", " ").title()
            lines.append(f"- [{title}]({rel_path})")
        try:
            index_file.write_text("\n".join(lines), encoding="utf-8")
        except Exception as exc:
            logger.debug(f"Erreur écriture index.md: {exc}", exc_info=True)
