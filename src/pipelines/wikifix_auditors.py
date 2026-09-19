"""
wikifix_auditors.py — WikiFix Audit Mixin (ADR-0202)
Contient les méthodes d'audit extraites de WikiFixAgent :
  - _audit_business_exclusions
  - _audit_technical_leakage
  - _audit_structural_compliance
  - _generate_master_index
Ne pas modifier ce fichier directement : façade via wikifix.py.
"""
import logging
import os
import re
from pathlib import Path

from src.state import ProjectLayout
from src.cli import ZeroFluffConsole

logger = logging.getLogger(__name__)


class WikiFixAuditMixin:
    """Mixin portant toute la logique d'audit sémantique de WikiFixAgent."""

    # ------------------------------------------------------------------
    # 4. Linter de conformité d'affaires
    # ------------------------------------------------------------------
    def _audit_business_exclusions(self, project_path: Path) -> list[dict]:
        import yaml

        violations = []
        exclusions = {
            "stripe": "Intégration Stripe détectée.",
            "paypal": "Intégration PayPal détectée.",
            "checkout": "Tunnel d'achat détecté.",
            "prescription": "Santé clinique détectée.",
            "ordonnance": "Santé clinique détectée.",
        }

        # Load dynamic RHO rules (Global and Project)
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
                    logger.debug("Erreur chargement rho_file %s", rho_file, exc_info=True)

        src_dir = project_path / ProjectLayout.SRC
        if not src_dir.exists():
            return violations

        for file_path in src_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in (
                ".ts",
                ".tsx",
                ".py",
                ".js",
            ):
                try:
                    content = file_path.read_text(encoding="utf-8").lower()
                except Exception:
                    continue

                for keyword, msg in exclusions.items():
                    if keyword in content:
                        violations.append(
                            {
                                "file": str(file_path.relative_to(project_path)),
                                "keyword": keyword,
                                "msg": msg,
                            }
                        )
        return violations

    # ------------------------------------------------------------------
    # 4.5 Linter d'Isolation Technique (Backlog)
    # ------------------------------------------------------------------
    def _audit_technical_leakage(
        self, project_path: Path, markdown_files: list[Path]
    ) -> list[dict]:
        """
        Vérifie que les fichiers du backlog ne contiennent pas de spécifications techniques.
        (ex: noms de librairies, blocs de code typescript/javascript, etc.)
        """
        leakages = []
        # Mots-clés qui ne devraient jamais être dans un backlog purement fonctionnel
        tech_keywords = [
            "npm install",
            "yarn add",
            "expo install",
            "import {",
            "import *",
            "```typescript",
            "```javascript",
            "```tsx",
            "```ts",
            "zustand",
            "redux",
            "axios",
            "fetch(",
            "(voir rec-",
            "(voir st-",
            "(selon pt-",
            "state-bound",
            "isjustificationvalid",
            "isformvalid",
        ]

        for fpath in markdown_files:
            # Ne vérifier que les fichiers du backlog
            if "backlog" in fpath.parts:
                try:
                    content = fpath.read_text(encoding="utf-8")
                    content_lower = content.lower()
                except Exception:
                    continue

                for kw in tech_keywords:
                    if kw in content_lower:
                        leakages.append(
                            {
                                "file": str(fpath.relative_to(project_path)),
                                "keyword": kw,
                            }
                        )

                # Règle #9 : Interdiction des parenthèses de renvoi interne (ex: (REC-001-FE), (ST-001)) hors URLs markdown
                raw_refs = re.findall(
                    r"(?<!\])\([^)\n]*\b(?:REC|ST|PT)-\d+[^)\n]*\)",
                    content,
                    re.IGNORECASE,
                )
                parenthetical_refs = [
                    ref
                    for ref in raw_refs
                    if not any(
                        proto in ref.lower()
                        for proto in ["http://", "https://", "file://", "mailto:"]
                    )
                ]
                if parenthetical_refs:
                    for pref in set(parenthetical_refs):
                        leakages.append(
                            {
                                "file": str(fpath.relative_to(project_path)),
                                "keyword": f"Parenthèse de renvoi interne interdite (Règle #9): {pref}",
                            }
                        )
        return leakages

    # ------------------------------------------------------------------
    # 4.6 Linter de Conformité Structurelle (INVEST)
    # ------------------------------------------------------------------
    def _audit_structural_compliance(
        self, project_path: Path, markdown_files: list[Path], story_filter: str = None
    ) -> list[dict]:
        """
        Vérifie que les fichiers du backlog contiennent les sections structurelles obligatoires (INVEST)
        et respectent la Règle du Blindage Gherkin (4 Piliers obligatoires).
        """
        structural_failures = []
        required_sections = [
            (r"## Scénarios de test", "Section 'Scénarios de test' manquante"),
            (r"## Règles d", "Section 'Règles d'affaires' manquante"),
        ]

        for fpath in markdown_files:
            if "backlog" in fpath.parts and "stories" in fpath.parts:
                if "reference" in fpath.parts or "archive_deprecated" in fpath.parts:
                    continue
                if story_filter and story_filter not in fpath.name:
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8")
                except Exception:
                    continue

                missing = []
                for req_pattern, label in required_sections:
                    if not re.search(req_pattern, content, re.IGNORECASE):
                        missing.append(label)

                # Contrôle strict du Blindage Gherkin (ADR-0301 - 4 Piliers)
                scenarios = re.findall(
                    r"(?:Scénario|Scenario)\s*:", content, re.IGNORECASE
                )
                if len(scenarios) < 4:
                    missing.append(
                        f"Gherkin 4-Piliers Incomplet ({len(scenarios)}/4 scénarios exigés par ADR-0301 : Nominal, Exceptions, Résilience, UX)"
                    )

                # Contrôle 1 : Visual Gate (Section Maquettes : Liens Figma, Captures Visuelles ou Mermaid)
                has_visual = bool(
                    re.search(
                        r"(?:figma\.com|!\[|```mermaid|## Maquettes)",
                        content,
                        re.IGNORECASE,
                    )
                )
                if not has_visual:
                    missing.append(
                        "Section Maquettes (liens Figma ou visuels UI) manquante (Visual Gate)"
                    )

                # Contrôle 0 : Auto-Healing et Enforcing des Séparateurs '---' entre les sections H2 (ADR-0303)
                h2_matches = list(re.finditer(r"(?m)^(##\s+.+)$", content))
                if len(h2_matches) > 1:
                    content_modified = False
                    new_content = content
                    for match in h2_matches[1:]:  # Ignorer le tout premier H2 si proche du YAML
                        header_str = match.group(1)
                        pos = match.start()
                        # Vérifier si les 20 caractères précédant le H2 contiennent un ---
                        prefix_window = new_content[max(0, pos - 25) : pos]
                        if "---" not in prefix_window:
                            # Auto-correction : insérer \n---\n avant le header H2
                            replacement = f"\n---\n\n{header_str}"
                            new_content = (
                                new_content[:pos]
                                + replacement
                                + new_content[pos + len(header_str) :]
                            )
                            content_modified = True
                    if content_modified:
                        fpath.write_text(new_content, encoding="utf-8")
                        content = new_content
                        ZeroFluffConsole.success(
                            f"[WikiFix Auto-Healing] Séparateurs '---' auto-insérés entre les sections H2 pour {fpath.name}"
                        )

                # Contrôle 2 : Requis UI / API Backend / Data Model
                has_ui_api = bool(
                    re.search(
                        r"(?:UI|Interface|Composants|Maquette|Contrats UI|Endpoints|Data Model|API)",
                        content,
                        re.IGNORECASE,
                    )
                )
                if not has_ui_api:
                    missing.append(
                        "Contrats UI & API Backend manquants (Chaque récit doit décrire l'interface UI et/ou les endpoints API/Data Model)"
                    )

                # Contrôle 3 : Anti-Fluff / Rejet des Vagues Formulations (Gold Standard Quality)
                fluff_terms = [
                    "affiché clairement",
                    "affichée clairement",
                    "l'écran s'ouvre",
                    "si nécessaire",
                ]
                found_fluff = [term for term in fluff_terms if term in content.lower()]
                if found_fluff:
                    missing.append(
                        f"Formulations évasives non-conformes au Gold Standard détectées: {', '.join(found_fluff)}. Préciser le composant visuel ou la règle exacte."
                    )

                # Contrôle 4 : Interdiction des commentaires d'échafaudage Gherkin (ADR-0301) et bruits de titres IA
                scaffold_comments = re.findall(
                    r"#\s*PILIER\s*\d+", content, re.IGNORECASE
                )
                if scaffold_comments:
                    missing.append(
                        "Commentaires d'échafaudage '# PILIER X' interdits dans le bloc Gherkin final (ADR-0301 Anti-Pollution)"
                    )

                # Contrôle 4b : Interdiction des marqueurs éphémères et bruits de titres ((IA Only), (Standard D-A-F-E))
                title_noise = re.findall(
                    r"\(Standard D-A-F-E\)", content, re.IGNORECASE
                )
                if title_noise:
                    missing.append(
                        f"Marqueurs d'échafaudage ou bruits de titres interdits détectés ({', '.join(set(title_noise))}). Utiliser des titres standard propres."
                    )

                # Contrôle 5 : Interdiction des préfixes d'identifiants éphémères dans les Règles d'affaires (ADR-0301 Amendement 2026-09)
                ephemeral_rm = re.findall(
                    r"(?:^|\n)\s*[-*]\s*\*\*\s*(?:RM-(?:TEMP|TODO|FIXME|WIP)|TODO|FIXME|WIP)\b",
                    content,
                    re.IGNORECASE,
                )
                if ephemeral_rm:
                    missing.append(
                        f"Identifiants éphémères interdits dans les règles d'affaires ({', '.join(set(s.strip() for s in ephemeral_rm))}). Utiliser le standard 'RM-XXX [Titre Métier Pur]'."
                    )
                bare_rm = re.findall(
                    r"(?:^|\n)\s*[-*]\s*\*\*\s*RM-[A-Z0-9-]+\s*\*\*\s*:",
                    content,
                )
                if bare_rm:
                    missing.append(
                        f"Règle d'affaires sans titre fonctionnel ({', '.join(set(s.strip() for s in bare_rm))}). Suivre le standard 'RM-XXX [Nom de la Règle]'."
                    )

                # Contrôle 6 : Dualité Stricte Read/Write Model (Récits Frontend)
                is_frontend = bool(
                    re.search(r"layer:\s*frontend", content, re.IGNORECASE)
                ) or fpath.name.upper().endswith("-FE.MD")
                if is_frontend:
                    has_read_model = bool(
                        re.search(
                            r"(?:Périmètre de Consultation|Read Model|Inventaire visualisé|Composants de Lecture|Consultation|jauge)",
                            content,
                            re.IGNORECASE,
                        )
                    )
                    if not has_read_model:
                        missing.append(
                            "Périmètre de Consultation (Read Model) manquant dans le récit Frontend. Expliciter ce qui est visualisé à l'écran (jauges, listes, métadonnées, résumé)."
                        )

                # Contrôle 7 : Verrou Confirmation Gate (Statut READY_FOR_DEV / READY_FOR_GROOMING avec OQ non résolues)
                is_ready = bool(
                    re.search(
                        r"status:\s*(?:READY_FOR_DEV|READY_FOR_GROOMING)",
                        content,
                        re.IGNORECASE,
                    )
                )
                if is_ready:
                    unresolved_oq = re.findall(r"\bOQ-\d+\b", content)
                    if unresolved_oq:
                        missing.append(
                            f"Statut READY_FOR_DEV / READY_FOR_GROOMING invalide car des questions ouvertes non résolues sont présentes ({', '.join(set(unresolved_oq))}). Franchir la Confirmation Gate avant clôture."
                        )

                # Contrôle 8 : Ordre Visuel Spatial Top-to-Bottom (Récits Frontend - Règle #13)
                if is_frontend:
                    header_pos = (
                        content.find("En-tête")
                        if "En-tête" in content
                        else content.find("Top Bar")
                    )
                    footer_pos = (
                        content.find("Pied de Page")
                        if "Pied de Page" in content
                        else content.find("Footer")
                    )
                    if (
                        header_pos != -1
                        and footer_pos != -1
                        and header_pos > footer_pos
                    ):
                        missing.append(
                            "Non-respect de la Règle #13 d'Ordre Visuel Spatial : l'En-tête (Header) doit apparaître AVANT le Pied de Page (Footer) dans les critères UI/UX."
                        )

                # Contrôle 9 : Fact-Search & Validation Déterministe des Sources Physiques (ADR-0326)
                cited_sources = re.findall(
                    r"\b([a-zA-Z0-9_\-/\\]+\.(?:md|xlsx|pdf|docx|plist|cs|csproj|xml|yml|json))\b",
                    content,
                )
                ghost_sources = []
                for src in set(cited_sources):
                    if (
                        src.startswith("<")
                        or src.endswith(">")
                        or "template" in src.lower()
                        or src
                        in [
                            "package.json",
                            "tsconfig.json",
                            "story_template.md",
                            "active_project.json",
                        ]
                    ):
                        continue
                    src_clean = src.replace("\\", "/").lstrip("/")
                    cand1 = project_path / src_clean
                    cand2 = project_path / "docs" / src_clean
                    cand3 = Path(src_clean)
                    cand4 = Path("standards") / src_clean
                    cand5 = project_path / "memory" / "evidence" / Path(src_clean).name
                    cand6 = project_path / "memory" / "evidence" / src_clean
                    cand7 = project_path / "backlog" / src_clean
                    cand8 = project_path / "reference" / src_clean
                    cand9 = (fpath.parent / src_clean).resolve()
                    if not (
                        cand1.exists()
                        or cand2.exists()
                        or cand3.exists()
                        or cand4.exists()
                        or cand5.exists()
                        or cand6.exists()
                        or cand7.exists()
                        or cand8.exists()
                        or cand9.exists()
                    ):
                        matches = []
                        fname = Path(src_clean).name
                        for sub in ["docs", "backlog", "reference"]:
                            sub_p = project_path / sub
                            if sub_p.exists():
                                matches.extend(list(sub_p.glob(f"**/{fname}")))
                        if not matches:
                            ghost_sources.append(src)

                if ghost_sources and is_ready:
                    missing.append(
                        f"[GUARDRAIL FACT-SEARCH] Source(s) citée(s) introuvable(s) physiquement sur disque ({', '.join(set(ghost_sources))}). Vérifier l'existence sous docs/ ou corriger la référence."
                    )

                # Contrôle 11 : Validation Canonique des Liens Wiki Azure DevOps (ADR-0327)
                azure_wiki_links = re.findall(
                    r"https://dev\.azure\.com/[^\s)]+_wiki/wikis/[^\s)]+", content
                )
                for wlink in azure_wiki_links:
                    if "friendlyName=" in wlink:
                        missing.append(
                            f"[ADR-0327] Paramètre conflictuel 'friendlyName=' interdit dans le lien Wiki Azure DevOps. Utiliser le paramètre 'pagePath=' exclusif ou un Permalink officiel avec pageId ({wlink})."
                        )
                    if "pagePath=" in wlink and "---" in wlink:
                        missing.append(
                            f"[ADR-0327] Encodage défectueux du tiret littéral dans le 'pagePath' ({wlink}). Remplacer '---' par '%20-%20' ou utiliser le Permalink officiel avec pageId."
                        )

                # Contrôle 10 : Génération du sidecar EvidencePack (ADR-0326)
                # PRINCIPE : vérifier et générer le fichier JSON sidecar UNIQUEMENT.
                # JAMAIS injecter de bloc texte dans le fichier Story .md.
                # Les agents consultent memory/evidence/<ID>_evidence.json directement.
                try:
                    ev_base = project_path / "memory" / "evidence"
                    existing_eps = (
                        list(ev_base.rglob(f"{fpath.stem}_evidence.json"))
                        if ev_base.exists()
                        else []
                    )
                    ep_file = (
                        existing_eps[0]
                        if existing_eps
                        else (ev_base / f"{fpath.stem}_evidence.json")
                    )
                    needs_ep = not (
                        ep_file.exists()
                        and os.path.getmtime(ep_file) >= os.path.getmtime(fpath)
                    )
                    if needs_ep:
                        from src.pipelines.evidence_pack import EvidencePackEngine

                        ep_engine = EvidencePackEngine(project_path)
                        ep_pack = ep_engine.extract_evidence(fpath)
                        ep_engine.save_evidence_pack(ep_pack)
                        ZeroFluffConsole.success(
                            f"[WikiFix] EvidencePack sidecar mis à jour : memory/evidence/{fpath.stem}_evidence.json"
                        )
                    # Zéro injection de texte dans le fichier .md — les agents lisent le JSON sidecar directement
                except Exception as e_ep:
                    ZeroFluffConsole.error(
                        f"[WikiFix Evidence Error] Erreur génération EvidencePack pour {fpath.name} : {e_ep}"
                    )

                if missing:
                    structural_failures.append(
                        {
                            "file": str(fpath.relative_to(project_path)),
                            "missing": missing,
                        }
                    )

        # Contrôle des récits orphelins absents de sprint_backlog.md
        sprint_backlog_file = (
            project_path / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
        )
        if sprint_backlog_file.exists():
            try:
                sb_content = sprint_backlog_file.read_text(encoding="utf-8")
                stories_dir = project_path / ProjectLayout.BACKLOG / "stories"
                if stories_dir.exists():
                    for sfile in stories_dir.rglob("*.md"):
                        story_key = sfile.stem
                        if story_key not in sb_content:
                            structural_failures.append(
                                {
                                    "file": str(sfile.relative_to(project_path)),
                                    "missing": [
                                        f"Récit orphelin '{story_key}' absent du sprint_backlog.md (SSOT non synchronisée)"
                                    ],
                                }
                            )
            except Exception as exc:
                logger.debug("Erreur lecture sprint_backlog", exc_info=True)

        return structural_failures

    # ------------------------------------------------------------------
    # 4.8 OpenWiki Dynamic Master Index Generation
    # ------------------------------------------------------------------
    def _generate_master_index(self, project_path: Path, markdown_files: list[Path]):
        """
        Génère automatiquement la table des matières dynamique 'docs/index.md'
        (OpenWiki / Karpathy Self-Healing Wiki Engine).
        """
        docs_dir = project_path / ProjectLayout.DOCS
        if not docs_dir.exists():
            return

        index_file = docs_dir / "index.md"
        doc_files = sorted(
            [f for f in docs_dir.rglob("*.md") if f.name.lower() != "index.md"]
        )

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

        index_file.write_text("\n".join(lines), encoding="utf-8")
