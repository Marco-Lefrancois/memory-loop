import os
import re
import urllib.parse
from pathlib import Path
from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole

class WikiFixAgent:
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
            "note": "NOTE", "info": "NOTE",
            "tip": "TIP", "hint": "TIP",
            "warning": "WARNING", "danger": "WARNING", "error": "WARNING",
            "important": "IMPORTANT",
            "caution": "CAUTION"
        }

    def _normalize_callout(self, callout_type: str) -> str:
        """Normalise un type de callout en standard ou retourne None si inconnu."""
        lower_type = callout_type.lower().strip()
        return self.callout_mapping.get(lower_type, None)

    def _stream_markdown_files(self, project_path: Path, interest_dirs: list[str]):
        """Générateur 'Lazy Evaluation' qui cède les fichiers markdown et leur contenu un par un."""
        for d in interest_dirs:
            dir_path = project_path / d
            if dir_path.exists():
                for md_file in dir_path.rglob("*.md"):
                    try:
                        content = md_file.read_text(encoding="utf-8")
                        yield md_file, content
                    except Exception as e:
                        ZeroFluffConsole.error(f"Erreur de lecture sur {md_file}: {e}")

    def execute(self, state: LoopState, verbose: bool = False) -> LoopState:
        ZeroFluffConsole.step_s1(self.name, "Démarrage de l'audit de cohérence de la base de connaissances...")
        project_path = Path("Projects") / state.project_name
        
        if not project_path.exists():
            ZeroFluffConsole.error(f"Le dossier du projet '{state.project_name}' n'existe pas.")
            return state

        # Validation déterministe de la Machine à États mLoop & Guardrail Sentinel
        from src.pipelines.state_machine import StateMachineEngine, StateTransitionError, ContentTamperingError
        engine = StateMachineEngine(str(project_path))
        engine.validate_single_in_analyze()

        # Validation de l'approbation Sentinel, intégrité anti-tampering et TTL
        import yaml
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
                                # Garde-fou Anti-Tampering : vérifier l'intégrité du contenu validé
                                if status in ("READY_FOR_GROOMING", "READY_FOR_DEV", "IN_DEV", "IN_QA", "DONE", "ACCEPTED"):
                                    engine.validate_content_integrity(sf)
                                # Garde-fou Sentinel : vérifier l'approbation Rubber Duck
                                if status in ("READY_FOR_GROOMING", "READY_FOR_DEV", "IN_DEV", "IN_QA", "DONE", "ACCEPTED", "COMPLETED"):
                                    engine.validate_sentinel_approval(sf)
                                # Garde-fou TTL : vérifier que le récit n'a pas épuisé ses cycles
                                if status in ("IN_ANALYZE", "IN_BUILD", "IN_VALIDATE"):
                                    engine.check_ttl(sf)
                except (StateTransitionError, ContentTamperingError) as ste:
                    ZeroFluffConsole.error(str(ste))
                    raise ste
                except Exception:
                    pass

        # 1. Collecter tous les fichiers Markdown du projet cible via le générateur paresseux
        interest_dirs = [ProjectLayout.DOCS, ProjectLayout.DIRECTIVES, ProjectLayout.REFERENCE, ProjectLayout.BACKLOG]
        markdown_files = [f for f, _ in self._stream_markdown_files(project_path, interest_dirs)]

        if not markdown_files:
            ZeroFluffConsole.step_s1(self.name, "Aucun fichier markdown trouvé dans les répertoires cibles.")
            return state

        # Charger le cache mtime de WikiFix
        import os, json
        cache_dir = project_path / ProjectLayout.MEMORY / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "wikifix_cache.json"
        cache_data = {}
        if cache_file.exists():
            try:
                cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Construire une map de tous les basenames pour l'Auto-Healing
        basename_map = {}
        for fpath in markdown_files:
            bname = fpath.name.lower()
            if bname not in basename_map:
                basename_map[bname] = []
            basename_map[bname].append(fpath)

        broken_links_alerts = []
        healed_links = []
        callouts_alerts = []
        healed_callouts = []
        referenced_files = set()
        new_cache_data = {}

        # 2. Auditer chaque fichier
        for file_path in markdown_files:
            file_rel = str(file_path.relative_to(project_path))
            mtime = os.path.getmtime(file_path)

            if verbose:
                ZeroFluffConsole.info(f"Audit de [highlight]{file_rel}[/highlight]...")

            # Utiliser le cache si le fichier n'a pas changé
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
                callout_match = re.search(r'^\s*>\s*\[!([^\]]+)\](.*)$', line)
                if callout_match:
                    raw_type = callout_match.group(1)
                    if raw_type not in self.supported_callouts:
                        normalized = self._normalize_callout(raw_type)
                        if normalized:
                            new_line = re.sub(r'\[![^\]]+\]', f"[!{normalized}]", line)
                            line = new_line
                            file_modified = True
                            healed_callouts.append({"file": str(file_rel), "line": line_idx, "from": raw_type, "to": normalized})
                            ZeroFluffConsole.success(f"Callout auto-corrigé dans {file_rel}:{line_idx} ({raw_type} -> {normalized})")
                        else:
                            callouts_alerts.append({"file": str(file_rel), "line": line_idx, "type": raw_type, "msg": f"Le type de callout '{raw_type}' n'est pas standard."})

                # B. Traitement et correction des Liens Markdown
                link_matches = list(re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line))
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
                            except Exception: pass
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
                                healed_links.append({"file": str(file_rel), "line": line_idx, "broken": link_target, "healed": new_target})
                                ZeroFluffConsole.success(f"Lien brisé auto-corrigé dans {file_rel}:{line_idx} ({link_target} -> {new_target})")
                            else:
                                broken_links_alerts.append({"file": str(file_rel), "line": line_idx, "target": link_target, "msg": f"Lien brisé (fichier introuvable)."})

                new_lines.append(line)

            if file_modified:
                try:
                    file_path.write_text("\n".join(new_lines), encoding="utf-8")
                    mtime = os.path.getmtime(file_path)
                except Exception as e:
                    ZeroFluffConsole.error(f"Échec de l'écriture du fichier corrigé {file_rel} : {e}")

            new_cache_data[file_rel] = {
                "mtime": mtime,
                "referenced_files": [str(p) for p in referenced_files if p.exists()]
            }

        try:
            cache_file.write_text(json.dumps(new_cache_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

        # 3. Détecter les pages orphelines
        orphan_files = []
        resolved_referenced_paths = {p.resolve() for p in referenced_files if p.exists()}
        
        for fpath in markdown_files:
            if fpath.name.lower() in ("readme.md", "index.md"):
                continue
            try:
                if fpath.resolve() not in resolved_referenced_paths:
                    orphan_files.append(str(fpath.relative_to(project_path)))
            except Exception: pass

        # 4. Linter de conformité d'affaires
        business_violations = self._audit_business_exclusions(project_path)

        # 4.5 Linter d'Isolation Technique (Backlog)
        technical_leakages = self._audit_technical_leakage(project_path, markdown_files)

        # 4.6 Linter de Conformité Structurelle (INVEST)
        structural_failures = self._audit_structural_compliance(project_path, markdown_files)
        
        # 4.7 Intégration Dynamique RuleEngine (ADR-0329)
        from src.core.rule_engine import RuleEngine
        rule_engine = RuleEngine()
        # Charger les ADRs du projet
        adr_dir = project_path / "docs" / "01-architecture"
        if adr_dir.exists():
            rule_engine.load_from_adr_dir(adr_dir)
            
        for fpath in markdown_files:
            if "backlog" in fpath.parts and "stories" in fpath.parts:
                content = fpath.read_text(encoding="utf-8")
                violations = rule_engine.validate_all(content, target="backlog_stories")
                for v in violations:
                    if v.severity == "BLOCKING":
                        structural_failures.append({
                            "file": str(fpath.relative_to(project_path)),
                            "missing": [f"[{v.check_id}] {v.message}"]
                        })

        # 4.8 OpenWiki Dynamic Master Index Generation
        self._generate_master_index(project_path, markdown_files)

        # 5. Rédiger le rapport
        report_path = project_path / ProjectLayout.MEMORY / "wikifix_report.md"
        report_lines = [
            f"# 🛡️ Rapport de Santé Sémantique (WikiFix) - Projet '{state.project_name}'\n",
            f"## 📊 Statut Global",
            f"- **Fichiers markdown audités** : {len(markdown_files)} fichier(s)",
            f"- **Liens brisés corrigés (Auto-Healing)** : {len(healed_links)} correction(s)",
            f"- **Pages orphelines identifiées** : {len(orphan_files)} page(s)",
            f"- **Violations de Directives d'Affaires** : {len(business_violations)} alerte(s)",
            f"- **Fuites Techniques (Backlog)** : {len(technical_leakages)} alerte(s)",
            f"- **Défauts Structurels (INVEST)** : {len(structural_failures)} alerte(s)\n"
        ]

        if business_violations:
            report_lines.append("## 🛑 ALERTE CRITIQUE : Non-Conformité d'Affaires")
            for violation in business_violations:
                report_lines.append(f"- **Fichier** : [{violation['file']}](file:///{project_path / violation['file']}) (Keyword: `{violation['keyword']}`)")
            ZeroFluffConsole.error(f"[GUARDRAIL BUSINESS] Détecté {len(business_violations)} violations !")

        if technical_leakages:
            report_lines.append("## ⚠️ AVERTISSEMENT : Fuites Techniques (Isolation Backlog rompue)")
            for leak in technical_leakages:
                report_lines.append(f"- **Fichier** : [{leak['file']}](file:///{project_path / leak['file']}) (Terme: `{leak['keyword']}`)")
            ZeroFluffConsole.error(f"[GUARDRAIL TECH] Détecté {len(technical_leakages)} fuites techniques dans le backlog !")

        if structural_failures:
            report_lines.append("## ❌ ERREUR FATALE : Conformité Structurelle du Backlog (INVEST)")
            for sf in structural_failures:
                report_lines.append(f"- **Fichier** : [{sf['file']}](file:///{project_path / sf['file']}) (Manquant: `{', '.join(sf['missing'])}`)")
            ZeroFluffConsole.error(f"[GUARDRAIL INVEST] Détecté {len(structural_failures)} fichiers non-conformes au gabarit !")

        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text("\n".join(report_lines), encoding="utf-8")
            ZeroFluffConsole.success(f"Rapport WikiFix rédigé sous {ProjectLayout.MEMORY}/wikifix_report.md")
        except Exception as e:
            ZeroFluffConsole.error(f"Échec de l'écriture du rapport : {e}")

        ZeroFluffConsole.success(f"Audit WikiFix terminé : {len(markdown_files)} fichier(s) analysé(s) ({len(healed_links) + len(healed_callouts)} correction(s)).")
        
        if structural_failures:
            # Séparer les échecs sur récits en cours de cadrage (IN_ANALYZE) des échecs sur récits engagés/clôturés
            blocking_failures = []
            in_analyze_failures = []
            for sf in structural_failures:
                sf_p = project_path / sf["file"]
                is_in_analyze = False
                if sf_p.exists():
                    try:
                        txt_content = sf_p.read_text(encoding="utf-8")
                        if re.search(r'(?m)^status:\s*(?:IN_ANALYZE|IN_REVIEW)\b', txt_content):
                            is_in_analyze = True
                    except Exception:
                        pass
                if is_in_analyze:
                    in_analyze_failures.append(sf)
                else:
                    blocking_failures.append(sf)

            if in_analyze_failures:
                ZeroFluffConsole.warning(f"[WikiFix IN_ANALYZE / IN_REVIEW] {len(in_analyze_failures)} récit(s) en cours de cadrage/révision toléré(s) avant la session Grill-me.")

            if blocking_failures:
                raise ValueError(f"[ÉCHEC DE VALIDATION INVEST] {len(blocking_failures)} récit(s) ne respectent pas le gabarit officiel (Gherkin/INVEST manquant).\nCe n'est pas un crash système, mais une validation métier ! Lisez memory/wikifix_report.md, corrigez les fichiers, et relancez la validation.")
            
        return state

    def _audit_business_exclusions(self, project_path: Path) -> list[dict]:
        import yaml
        violations = []
        exclusions = {
            "stripe": "Intégration Stripe détectée.",
            "paypal": "Intégration PayPal détectée.",
            "checkout": "Tunnel d'achat détecté.",
            "prescription": "Santé clinique détectée.",
            "ordonnance": "Santé clinique détectée."
        }
        
        # Load dynamic RHO rules (Global and Project)
        rho_files = [
            Path("standards") / "rho_rules.yaml",
            project_path / "memory" / "rho_rules.yaml"
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
                except Exception:
                    pass
        
        src_dir = project_path / ProjectLayout.SRC
        if not src_dir.exists():
            return violations
            
        for file_path in src_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in (".ts", ".tsx", ".py", ".js"):
                try:
                    content = file_path.read_text(encoding="utf-8").lower()
                except Exception: continue
                        
                for keyword, msg in exclusions.items():
                    if keyword in content:
                        violations.append({"file": str(file_path.relative_to(project_path)), "keyword": keyword, "msg": msg})
        return violations

    def _audit_technical_leakage(self, project_path: Path, markdown_files: list[Path]) -> list[dict]:
        """
        Vérifie que les fichiers du backlog ne contiennent pas de spécifications techniques.
        (ex: noms de librairies, blocs de code typescript/javascript, etc.)
        """
        leakages = []
        # Mots-clés qui ne devraient jamais être dans un backlog purement fonctionnel
        tech_keywords = [
            "npm install", "yarn add", "expo install", "import {", "import *", 
            "```typescript", "```javascript", "```tsx", "```ts", 
            "zustand", "redux", "axios", "fetch(",
            "(voir rec-", "(voir st-", "(selon pt-", "state-bound", "isjustificationvalid", "isformvalid"
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
                        leakages.append({
                            "file": str(fpath.relative_to(project_path)),
                            "keyword": kw
                        })

                # Règle #9 : Interdiction des parenthèses de renvoi interne (ex: (REC-001-FE), (ST-001)) hors URLs markdown
                raw_refs = re.findall(r"(?<!\])\([^)\n]*\b(?:REC|ST|PT)-\d+[^)\n]*\)", content, re.IGNORECASE)
                parenthetical_refs = [
                    ref for ref in raw_refs
                    if not any(proto in ref.lower() for proto in ["http://", "https://", "file://", "mailto:"])
                ]
                if parenthetical_refs:
                    for pref in set(parenthetical_refs):
                        leakages.append({
                            "file": str(fpath.relative_to(project_path)),
                            "keyword": f"Parenthèse de renvoi interne interdite (Règle #9): {pref}"
                        })
        return leakages

    def _audit_structural_compliance(self, project_path: Path, markdown_files: list[Path]) -> list[dict]:
        """
        Vérifie que les fichiers du backlog contiennent les sections structurelles obligatoires (INVEST)
        et respectent la Règle du Blindage Gherkin (4 Piliers obligatoires).
        """
        structural_failures = []
        required_sections = [
            (r"## Scénarios de test", "Section 'Scénarios de test' manquante"),
            (r"## Règles d", "Section 'Règles d'affaires' manquante")
        ]
        
        for fpath in markdown_files:
            if "backlog" in fpath.parts and "stories" in fpath.parts:
                try:
                    content = fpath.read_text(encoding="utf-8")
                except Exception:
                    continue
                
                missing = []
                for req_pattern, label in required_sections:
                    if not re.search(req_pattern, content, re.IGNORECASE):
                        missing.append(label)
                
                # Contrôle strict du Blindage Gherkin (ADR-0301 - 4 Piliers)
                scenarios = re.findall(r"(?:Scénario|Scenario)\s*:", content, re.IGNORECASE)
                if len(scenarios) < 4:
                    missing.append(f"Gherkin 4-Piliers Incomplet ({len(scenarios)}/4 scénarios exigés par ADR-0301 : Nominal, Exceptions, Résilience, UX)")
                
                # Contrôle 1 : Visual Gate (Section Maquettes : Liens Figma, Captures Visuelles ou Mermaid)
                has_visual = bool(re.search(r"(?:figma\.com|!\[|```mermaid|## Maquettes)", content, re.IGNORECASE))
                if not has_visual:
                    missing.append("Section Maquettes (liens Figma ou visuels UI) manquante (Visual Gate)")

                # Contrôle 0 : Auto-Healing et Enforcing des Séparateurs '---' entre les sections H2 (ADR-0303)
                h2_matches = list(re.finditer(r"(?m)^(##\s+.+)$", content))
                if len(h2_matches) > 1:
                    content_modified = False
                    new_content = content
                    for match in h2_matches[1:]: # Ignorer le tout premier H2 si proche du YAML
                        header_str = match.group(1)
                        pos = match.start()
                        # Vérifier si les 20 caractères précédant le H2 contiennent un ---
                        prefix_window = new_content[max(0, pos - 25):pos]
                        if "---" not in prefix_window:
                            # Auto-correction : insérer \n---\n avant le header H2
                            replacement = f"\n---\n\n{header_str}"
                            new_content = new_content[:pos] + replacement + new_content[pos + len(header_str):]
                            content_modified = True
                    if content_modified:
                        fpath.write_text(new_content, encoding="utf-8")
                        content = new_content
                        ZeroFluffConsole.success(f"[WikiFix Auto-Healing] Séparateurs '---' auto-insérés entre les sections H2 pour {fpath.name}")

                # Contrôle 2 : Requis UI / API Backend / Data Model
                has_ui_api = bool(re.search(r"(?:UI|Interface|Composants|Maquette|Contrats UI|Endpoints|Data Model|API)", content, re.IGNORECASE))
                if not has_ui_api:
                    missing.append("Contrats UI & API Backend manquants (Chaque récit doit décrire l'interface UI et/ou les endpoints API/Data Model)")

                # Contrôle 3 : Anti-Fluff / Rejet des Vagues Formulations (Gold Standard Quality)
                fluff_terms = ["affiché clairement", "affichée clairement", "l'écran s'ouvre", "si nécessaire"]
                found_fluff = [term for term in fluff_terms if term in content.lower()]
                if found_fluff:
                    missing.append(f"Formulations évasives non-conformes au Gold Standard détectées: {', '.join(found_fluff)}. Préciser le composant visuel ou la règle exacte.")

                # Contrôle 4 : Interdiction des commentaires d'échafaudage Gherkin (ADR-0301) et bruits de titres IA
                scaffold_comments = re.findall(r"#\s*PILIER\s*\d+", content, re.IGNORECASE)
                if scaffold_comments:
                    missing.append("Commentaires d'échafaudage '# PILIER X' interdits dans le bloc Gherkin final (ADR-0301 Anti-Pollution)")

                # Contrôle 4b : Interdiction des marqueurs éphémères et bruits de titres ((IA Only), (Standard D-A-F-E))
                title_noise = re.findall(r"\(Standard D-A-F-E\)", content, re.IGNORECASE)
                if title_noise:
                    missing.append(f"Marqueurs d'échafaudage ou bruits de titres interdits détectés ({', '.join(set(title_noise))}). Utiliser des titres standard propres.")

                # Contrôle 5 : Interdiction des préfixes d'identifiants éphémères dans les Règles d'affaires (ADR-0301 Rule #7)
                ephemeral_rm = re.findall(r"\*\s*\*\*\s*RM-[A-Z0-9-]+", content)
                if ephemeral_rm:
                    missing.append(f"Identifiants éphémères interdits dans les titres de règles d'affaires ({', '.join(set(ephemeral_rm))}). Utiliser un titre fonctionnel métier pur en gras.")

                # Contrôle 6 : Dualité Stricte Read/Write Model (Récits Frontend)
                is_frontend = bool(re.search(r"layer:\s*frontend", content, re.IGNORECASE)) or fpath.name.upper().endswith("-FE.MD")
                if is_frontend:
                    has_read_model = bool(re.search(r"(?:Périmètre de Consultation|Read Model|Inventaire visualisé|Composants de Lecture|Consultation|jauge)", content, re.IGNORECASE))
                    if not has_read_model:
                        missing.append("Périmètre de Consultation (Read Model) manquant dans le récit Frontend. Expliciter ce qui est visualisé à l'écran (jauges, listes, métadonnées, résumé).")

                # Contrôle 7 : Verrou Confirmation Gate (Statut READY_FOR_DEV / READY_FOR_GROOMING avec OQ non résolues)
                is_ready = bool(re.search(r"status:\s*(?:READY_FOR_DEV|READY_FOR_GROOMING)", content, re.IGNORECASE))
                if is_ready:
                    unresolved_oq = re.findall(r"\bOQ-\d+\b", content)
                    if unresolved_oq:
                        missing.append(f"Statut READY_FOR_DEV / READY_FOR_GROOMING invalide car des questions ouvertes non résolues sont présentes ({', '.join(set(unresolved_oq))}). Franchir la Confirmation Gate avant clôture.")

                # Contrôle 8 : Ordre Visuel Spatial Top-to-Bottom (Récits Frontend - Règle #13)
                if is_frontend:
                    header_pos = content.find("En-tête") if "En-tête" in content else content.find("Top Bar")
                    footer_pos = content.find("Pied de Page") if "Pied de Page" in content else content.find("Footer")
                    if header_pos != -1 and footer_pos != -1 and header_pos > footer_pos:
                        missing.append("Non-respect de la Règle #13 d'Ordre Visuel Spatial : l'En-tête (Header) doit apparaître AVANT le Pied de Page (Footer) dans les critères UI/UX.")

                # Contrôle 9 : Fact-Search & Validation Déterministe des Sources Physiques (ADR-0326)
                cited_sources = re.findall(r"\b([a-zA-Z0-9_\-/\\]+\.(?:md|xlsx|pdf|docx|plist|cs|csproj|xml|yml|json))\b", content)
                ghost_sources = []
                for src in set(cited_sources):
                    if src.startswith("<") or src.endswith(">") or "template" in src.lower() or src in ["package.json", "tsconfig.json", "story_template.md", "active_project.json"]:
                        continue
                    src_clean = src.replace("\\", "/").lstrip("/")
                    cand1 = project_path / src_clean
                    cand2 = project_path / "docs" / src_clean
                    cand3 = Path(src_clean)
                    cand4 = Path("standards") / src_clean
                    cand5 = project_path / "memory" / "evidence" / Path(src_clean).name
                    cand6 = project_path / "memory" / "evidence" / src_clean
                    if not (cand1.exists() or cand2.exists() or cand3.exists() or cand4.exists() or cand5.exists() or cand6.exists()):
                        ingested_matches = list((project_path / "docs").glob(f"**/{Path(src_clean).name}")) if (project_path / "docs").exists() else []
                        if not ingested_matches:
                            ghost_sources.append(src)
                
                if ghost_sources and is_ready:
                    missing.append(f"[GUARDRAIL FACT-SEARCH] Source(s) citée(s) introuvable(s) physiquement sur disque ({', '.join(set(ghost_sources))}). Vérifier l'existence sous docs/ ou corriger la référence.")

                # Contrôle 11 : Validation Canonique des Liens Wiki Azure DevOps (ADR-0327)
                azure_wiki_links = re.findall(r'https://dev\.azure\.com/[^\s)]+_wiki/wikis/[^\s)]+', content)
                for wlink in azure_wiki_links:
                    if "friendlyName=" in wlink:
                        missing.append(f"[ADR-0327] Paramètre conflictuel 'friendlyName=' interdit dans le lien Wiki Azure DevOps. Utiliser le paramètre 'pagePath=' exclusif ou un Permalink officiel avec pageId ({wlink}).")
                    if "pagePath=" in wlink and "---" in wlink:
                        missing.append(f"[ADR-0327] Encodage défectueux du tiret littéral dans le 'pagePath' ({wlink}). Remplacer '---' par '%20-%20' ou utiliser le Permalink officiel avec pageId.")

                # Contrôle 10 : Génération du sidecar EvidencePack (ADR-0326)
                # PRINCIPE : vérifier et générer le fichier JSON sidecar UNIQUEMENT.
                # JAMAIS injecter de bloc texte dans le fichier Story .md.
                # Les agents consultent memory/evidence/<ID>_evidence.json directement.
                try:
                    ev_base = project_path / "memory" / "evidence"
                    existing_eps = list(ev_base.rglob(f"{fpath.stem}_evidence.json")) if ev_base.exists() else []
                    ep_file = existing_eps[0] if existing_eps else (ev_base / f"{fpath.stem}_evidence.json")
                    needs_ep = not (ep_file.exists() and os.path.getmtime(ep_file) >= os.path.getmtime(fpath))
                    if needs_ep:
                        from src.pipelines.evidence_pack import EvidencePackEngine
                        ep_engine = EvidencePackEngine(project_path)
                        ep_pack = ep_engine.extract_evidence(fpath)
                        ep_engine.save_evidence_pack(ep_pack)
                        ZeroFluffConsole.success(f"[WikiFix] EvidencePack sidecar mis à jour : memory/evidence/{fpath.stem}_evidence.json")
                    # Zéro injection de texte dans le fichier .md — les agents lisent le JSON sidecar directement
                except Exception as e_ep:
                    ZeroFluffConsole.error(f"[WikiFix Evidence Error] Erreur génération EvidencePack pour {fpath.name} : {e_ep}")

                if missing:


                    structural_failures.append({
                        "file": str(fpath.relative_to(project_path)),
                        "missing": missing
                    })
        
        # Contrôle des récits orphelins absents de sprint_backlog.md
        sprint_backlog_file = project_path / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
        if sprint_backlog_file.exists():
            try:
                sb_content = sprint_backlog_file.read_text(encoding="utf-8")
                stories_dir = project_path / ProjectLayout.BACKLOG / "stories"
                if stories_dir.exists():
                    for sfile in stories_dir.rglob("*.md"):
                        story_key = sfile.stem
                        if story_key not in sb_content:
                            structural_failures.append({
                                "file": str(sfile.relative_to(project_path)),
                                "missing": [f"Récit orphelin '{story_key}' absent du sprint_backlog.md (SSOT non synchronisée)"]
                            })
            except Exception:
                pass

        return structural_failures

    def _generate_master_index(self, project_path: Path, markdown_files: list[Path]):
        """
        Génère automatiquement la table des matières dynamique 'docs/index.md'
        (OpenWiki / Karpathy Self-Healing Wiki Engine).
        """
        docs_dir = project_path / ProjectLayout.DOCS
        if not docs_dir.exists():
            return

        index_file = docs_dir / "index.md"
        doc_files = sorted([f for f in docs_dir.rglob("*.md") if f.name.lower() != "index.md"])

        lines = [
            f"# 📚 Table des Matières Dynamique - SSOT Projet '{project_path.name}'\n",
            "- **Statut Wiki** : AUTO-MAINTENU & HEALED",
            f"- **Fichiers Documentés** : {len(doc_files)}\n",
            "## 🗂️ Sommaire de la Base de Connaissances\n"
        ]

        for doc in doc_files:
            rel_path = doc.relative_to(docs_dir).as_posix()
            title = doc.stem.replace("_", " ").replace("-", " ").title()
            lines.append(f"- [{title}]({rel_path})")

        index_file.write_text("\n".join(lines), encoding="utf-8")

def os_relative_path(from_dir: Path, to_file: Path) -> str:
    import os
    return os.path.relpath(str(to_file), start=str(from_dir)).replace("\\", "/")
