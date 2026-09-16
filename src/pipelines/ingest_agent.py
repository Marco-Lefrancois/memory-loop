import hashlib
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole
from src.core.lod_generator import LODGenerator


class IngestAgent:
    """
    Système 1 : Ingest Agent.
    Analyse le répertoire reference/ pour parser les PDF, DOCX, XLSX, TXT, SVG, etc.
    et les consolider de manière déterministe avec Source Manifest canonique,
    extraction adaptative de vocabulaire (Length-Aware) et auto-alimentation du lexique (ADR-0335).
    """

    def __init__(self):
        self.name = "Ingest Engine"
        self.anomalies: list[dict] = []

    # ─── Résolution des racines de sortie (Voie B — routage par initiative) ───
    def _project_root(self, state: LoopState) -> Path:
        return Path("Projects") / state.project_name

    def _ref_root(self, state: LoopState) -> Path:
        """Racine de scan. Scopée à reference/<initiative>/ si une initiative est fournie."""
        base = self._project_root(state) / ProjectLayout.REFERENCE
        initiative = getattr(state, "ingest_initiative", None)
        return (base / initiative) if initiative else base

    def _ingested_root(self, state: LoopState) -> Path:
        """
        Racine d'écriture des documents ingérés.
        - Avec initiative : docs/<initiative>/00-ingested/ (projets à structure par module).
        - Sans initiative : docs/00-ingested/ (modèle plat ADR-0102).
        """
        docs = self._project_root(state) / ProjectLayout.DOCS
        initiative = getattr(state, "ingest_initiative", None)
        base = (docs / initiative) if initiative else docs
        return base / ProjectLayout.DOCS_INGESTED

    def _initiative_docs_root(self, state: LoopState) -> Path:
        """Racine docs de l'initiative (ou docs/ à plat si non scopé)."""
        docs = self._project_root(state) / ProjectLayout.DOCS
        initiative = getattr(state, "ingest_initiative", None)
        return (docs / initiative) if initiative else docs

    def execute(self, state: LoopState) -> LoopState:
        initiative = getattr(state, "ingest_initiative", None)
        scope_label = f"reference/{initiative}/" if initiative else f"{ProjectLayout.REFERENCE}/"
        ZeroFluffConsole.step_s1(self.name, f"Démarrage du scan du répertoire {scope_label}...")
        self.anomalies = []
        ref_path = self._ref_root(state)

        if not ref_path.exists():
            ref_path.mkdir(parents=True, exist_ok=True)

        supported_extensions = [
            ".pdf",
            ".docx",
            ".xlsx",
            ".csv",
            ".txt",
            ".md",
            ".cs",
            ".pptx",
            ".ppt",
            ".svg",
            ".vtt",
            ".jpg",
            ".jpeg",
            ".png",
        ]

        for file in ref_path.rglob("*"):
            if file.is_file() and file.suffix.lower() in supported_extensions:
                state = self._process_file(file, state)

        # Post-traitement déterministe (ADR-0102 & ADR-0335)
        self._write_source_manifest(state)
        self._update_domain_lexicon(state)
        self._write_anomalies_manifest(state)
        self._generate_maquettes_index(state)
        self._generate_ingested_index(state)
        # La carte d'orientation racine docs/index.md décrit le projet entier :
        # ne pas la (re)générer lors d'une ingestion scopée à une seule initiative.
        if not getattr(state, "ingest_initiative", None):
            self._generate_docs_root_index(state)
        self._generate_lod_sidecars(state)

        return state

    def _extract_sections(self, text: str) -> list[str]:
        """Extrait la liste hiérarchique des titres Markdown (#, ##, ###)."""
        sections = []
        for line in text.splitlines():
            line_str = line.strip()
            if line_str.startswith("#"):
                clean_title = line_str.lstrip("#").strip()
                if clean_title and clean_title not in sections:
                    sections.append(clean_title)
        return sections

    def _extract_length_aware_terms(self, text: str) -> list[str]:
        """
        Extrait les entités nommées et termes techniques avec plafonnement adaptatif
        selon la volumétrie textuelle (Standard DeepPaperNote / paper-glossary - ADR-0335).
        """
        char_count = len(text)
        if char_count < 10000:
            max_terms = 10
        elif char_count < 30000:
            max_terms = 18
        elif char_count < 60000:
            max_terms = 25
        else:
            max_terms = 35

        # Recherche de motifs terminologiques (Acronymes, PascalCase, CamelCase, [Termes])
        candidates = []

        # 1. Termes explicites entre crochets ou backticks
        bracketed = re.findall(r"`([A-Za-z0-9_\-\.\s]{2,40})`|\[([A-Za-z0-9_\-\.\s]{2,40})\]", text)
        for b1, b2 in bracketed:
            val = (b1 or b2).strip()
            if len(val) >= 2 and not val.startswith("http") and not val.startswith("/"):
                candidates.append(val)

        # 2. Acronymes (2 à 8 lettres majuscules consécutives)
        acronyms = re.findall(r"\b[A-Z]{2,8}\b", text)
        stopwords_acronyms = {
            "LE",
            "LA",
            "LES",
            "DES",
            "DU",
            "UN",
            "UNE",
            "ET",
            "OU",
            "PAR",
            "POUR",
            "SUR",
            "DANS",
            "NON",
            "OUI",
            "PAS",
            "EST",
            "SONT",
            "QUE",
            "QUI",
            "CE",
            "CET",
            "CETTE",
        }
        candidates.extend([a for a in acronyms if a not in stopwords_acronyms])

        # 3. Mots en PascalCase / CamelCase (ex: IngestAgent, ZeroFluffConsole, OAuth2)
        camel_pascal = re.findall(r"\b[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*\b", text)
        candidates.extend(camel_pascal)

        # Filtrage et dédoublonnage avec conservation de la fréquence
        counts = Counter(candidates)
        # Supprimer les candidats trop courts ou parasites
        filtered = [
            term for term, count in counts.most_common() if len(term) >= 2 and not term.isdigit()
        ]

        return filtered[:max_terms]

    def _process_file(self, filepath: Path, state: LoopState) -> LoopState:
        try:
            file_content_raw = filepath.read_bytes()
            sha256_val = hashlib.sha256(file_content_raw).hexdigest()
        except Exception as e:
            ZeroFluffConsole.error(f"Impossible de lire le fichier {filepath.name} : {e}")
            self.anomalies.append(
                {
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "error": f"Erreur I/O: {e}",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return state

        # Vérification si déjà ingéré
        for source in state.ingested_sources:
            if source.get("filepath") == str(filepath) and source.get("sha256") == sha256_val:
                return state

        ZeroFluffConsole.step_s1(
            self.name, f"Parsing du fichier {filepath.name} ({filepath.suffix.upper()})..."
        )
        extracted_text = ""

        # Ingestion multimodale Microsoft MarkItDown & Parsers Déterministes
        ext = filepath.suffix.lower()
        if ext == ".svg":
            from src.converters.svg_to_md import parse_svg_to_md_text

            try:
                raw_svg = filepath.read_text(encoding="utf-8", errors="replace")
                extracted_text = parse_svg_to_md_text(raw_svg, filepath.name)
            except Exception as e:
                extracted_text = f"[Erreur parsing SVG : {e}]"
        elif ext == ".vtt":
            extracted_text = self._parse_vtt(filepath)
        elif ext in [".jpg", ".jpeg", ".png"]:
            extracted_text = self._process_image_asset(filepath, state)
        else:
            extracted_text = self._try_markitdown(filepath)

        if not extracted_text:
            if ext == ".txt" or ext == ".md" or ext == ".cs":
                try:
                    extracted_text = filepath.read_text(encoding="utf-8")
                except Exception:
                    try:
                        extracted_text = filepath.read_text(encoding="cp1252")
                    except Exception as e:
                        extracted_text = f"[Erreur de lecture texte : {e}]"
            elif ext == ".pdf":
                extracted_text = self._parse_pdf(filepath)
            elif ext == ".xlsx":
                extracted_text = self._parse_xlsx(filepath)
            elif ext == ".docx":
                extracted_text = self._parse_docx(filepath)
            elif ext in [".pptx", ".ppt"]:
                extracted_text = self._parse_pptx(filepath)
            elif ext == ".csv":
                try:
                    from src.converters.csv_engine import csv_to_markdown_summary

                    extracted_text = csv_to_markdown_summary(filepath, max_preview_rows=25)
                except Exception as e:
                    extracted_text = f"[Erreur de lecture CSV : {e}]"

        # Sauvegarde automatique de la version Markdown (racine dynamique selon initiative)
        ingested_dir = self._ingested_root(state)
        ingested_dir.mkdir(parents=True, exist_ok=True)
        ref_root = self._ref_root(state)

        if ext == ".svg":
            target_dir = ingested_dir / "05-maquettes-notes"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_md = target_dir / f"{filepath.stem}.md"

            # Synchronisation de l'actif visuel sous docs/[<initiative>/]05-assets/maquettes/ (ADR-0332)
            assets_maquettes = self._initiative_docs_root(state) / "05-assets" / "maquettes"
            assets_maquettes.mkdir(parents=True, exist_ok=True)
            target_svg = assets_maquettes / filepath.name
            if not target_svg.exists() or target_svg.resolve() != filepath.resolve():
                import shutil

                shutil.copy2(filepath, target_svg)
        else:
            subfolder = self._determine_target_subfolder(filepath, ref_root, ext)
            target_dir = ingested_dir / subfolder if subfolder else ingested_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            target_md = target_dir / f"{filepath.stem}.md"

        if (
            extracted_text
            and len(extracted_text.strip()) > 0
            and not extracted_text.startswith("[Erreur")
        ):
            sections = self._extract_sections(extracted_text)
            terms = self._extract_length_aware_terms(extracted_text)
            enriched_text = self._enrich_markdown(
                extracted_text, filepath, state.project_name, terms=terms
            )
            try:
                target_md.write_text(enriched_text, encoding="utf-8")
                ZeroFluffConsole.info(f"Copie Markdown enrichie enregistrée dans : {target_md}")
            except Exception as e:
                ZeroFluffConsole.warning(f"Note: Écriture du Markdown dans 00-ingested : {e}")

            # Ajout à l'état consolidé uniquement en cas de succès
            source_meta = {
                "filename": filepath.name,
                "filepath": str(filepath),
                "file_type": ext.upper()[1:],
                "sha256": sha256_val,
                "char_count": len(extracted_text),
                "word_count": len(extracted_text.split()),
                "sections": sections,
                "terms": terms,
                "extracted_text_summary": extracted_text[
                    :1000
                ],  # Résumé tronqué pour préserver l'espace d'état
                "timestamp": datetime.now().isoformat(),
            }
            state.ingested_sources.append(source_meta)
            ZeroFluffConsole.success(
                f"Fichier {filepath.name} ingéré avec succès ({len(terms)} termes, {len(sections)} sections)."
            )
        else:
            # En cas d'erreur ou d'extraction vide, ne PAS ajouter au cache des sources ingérées
            if target_md.exists() and target_md.stat().st_size == 0:
                try:
                    target_md.unlink()
                    ZeroFluffConsole.warning(
                        f"Fichier vide (0 octet) supprimé sous 00-ingested : {target_md.name}"
                    )
                except Exception:
                    pass

            err_detail = (
                extracted_text
                if extracted_text and extracted_text.startswith("[Erreur")
                else "Aucun texte extrait"
            )
            ZeroFluffConsole.error(f"ÉCHEC D'INGESTION pour {filepath.name} : {err_detail}")
            self.anomalies.append(
                {
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "error": err_detail,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return state

    def _write_source_manifest(self, state: LoopState) -> None:
        """Génère le manifeste de source canonique sous docs/00-ingested/source_manifest.json (ADR-0335)."""
        ingested_dir = self._ingested_root(state)
        ingested_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = ingested_dir / "source_manifest.json"

        manifest_data = {
            "manifest_version": "1.0.0",
            "project_name": state.project_name,
            "generated_at": datetime.now().isoformat(),
            "total_sources": len(state.ingested_sources),
            "sources": [
                {
                    "filename": s.get("filename", Path(s.get("filepath", "")).name),
                    "filepath": s.get("filepath"),
                    "file_type": s.get("file_type"),
                    "sha256": s.get("sha256"),
                    "char_count": s.get("char_count", len(s.get("extracted_text_summary", ""))),
                    "word_count": s.get("word_count", 0),
                    "sections_count": len(s.get("sections", [])),
                    "sections": s.get("sections", []),
                    "terms": s.get("terms", []),
                    "ingested_at": s.get("timestamp"),
                }
                for s in state.ingested_sources
            ],
        }

        try:
            manifest_file.write_text(
                json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            ZeroFluffConsole.info(f"Source Manifest canonique synchronisé : {manifest_file}")
        except Exception as e:
            ZeroFluffConsole.warning(f"Impossible d'écrire source_manifest.json : {e}")

    def _write_anomalies_manifest(self, state: LoopState) -> None:
        """Enregistre le registre d'anomalies d'ingestion sous docs/00-ingested/ingest_anomalies.json (Fail-Closed)."""
        ingested_dir = self._ingested_root(state)
        anomalies_file = ingested_dir / "ingest_anomalies.json"

        if self.anomalies:
            data = {
                "project_name": state.project_name,
                "recorded_at": datetime.now().isoformat(),
                "total_anomalies": len(self.anomalies),
                "anomalies": self.anomalies,
            }
            try:
                anomalies_file.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                ZeroFluffConsole.warning(
                    f"Registre des anomalies d'ingestion consigné : {anomalies_file}"
                )
            except Exception as e:
                ZeroFluffConsole.warning(f"Impossible d'écrire ingest_anomalies.json : {e}")
        else:
            if anomalies_file.exists():
                try:
                    anomalies_file.unlink()
                except Exception:
                    pass

    def _update_domain_lexicon(self, state: LoopState) -> None:
        """
        Auto-alimente le Dictionnaire de Lexique Métier sous docs/04-transverse/lexique_domaine.md
        en agrégeant les termes extraits des documents ingérés (ADR-0335 / paper-glossary).
        """
        if not state.ingested_sources:
            return

        term_sources: dict[str, list[str]] = {}
        term_counts: Counter = Counter()

        for source in state.ingested_sources:
            source_name = source.get("filename", Path(source.get("filepath", "")).name)
            for t in source.get("terms", []):
                term_counts[t] += 1
                if t not in term_sources:
                    term_sources[t] = []
                if source_name not in term_sources[t]:
                    term_sources[t].append(source_name)

        if not term_counts:
            return

        transverse_dir = self._initiative_docs_root(state) / ProjectLayout.DOCS_TRANSVERSE
        transverse_dir.mkdir(parents=True, exist_ok=True)
        lexicon_file = transverse_dir / "lexique_domaine.md"

        lines = [
            "# Lexique & Vocabulaire du Domaine Métier (SSOT ADR-0335)",
            "",
            "> **Statut :** Auto-consolidé par le Moteur d'Ingestion mLoop | **Dernière mise à jour :** "
            + datetime.now().strftime("%Y-%m-%d %H:%M"),
            "",
            "Ce document recense les entités nommées, acronymes et concepts techniques découverts dans les documents sources de référence (`reference/`). Il constitue le vocabulaire officiel du projet.",
            "",
            "| Terme / Concept Métier | Fréquence d'Apparition | Documents Sources Associés |",
            "| :--- | :---: | :--- |",
        ]

        for term, freq in term_counts.most_common():
            docs = ", ".join(term_sources.get(term, []))
            lines.append(f"| **`{term}`** | {freq} | `{docs}` |")

        lines.append("")
        try:
            lexicon_file.write_text("\n".join(lines), encoding="utf-8")
            ZeroFluffConsole.info(
                f"Dictionnaire de Lexique du Domaine synchronisé : {lexicon_file}"
            )
        except Exception as e:
            ZeroFluffConsole.warning(f"Impossible d'écrire lexique_domaine.md : {e}")

    def _determine_target_subfolder(self, filepath: Path, ref_root: Path, ext: str) -> str:
        """
        Détermine le sous-dossier thématique cible sous docs/00-ingested/ (ADR-0102).
        1. Si le fichier est dans un sous-dossier de reference/, préserve et mappe l'arborescence.
        2. Sinon, utilise une heuristique typologique basée sur le nom de fichier et l'extension.
        """
        try:
            rel_parent = filepath.parent.relative_to(ref_root)
            if str(rel_parent) != ".":
                p_str = str(rel_parent).lower()
                if any(k in p_str for k in ["sow", "contrat", "brief", "kickoff"]):
                    return "01-sow-et-contrats"
                elif any(k in p_str for k in ["guide", "spec", "fonctionnel", "exigences"]):
                    return "02-guides-et-specs"
                elif any(k in p_str for k in ["scan", "inventaire", "onetrust", "audit"]):
                    return "03-scans-et-inventaires"
                elif any(k in p_str for k in ["api", "technique", "swagger", "openapi", "sdk"]):
                    return "04-api-et-techniques"
                elif any(k in p_str for k in ["maquette", "ecran", "ui", "ux", "svg"]):
                    return "05-maquettes-notes"
                else:
                    return str(rel_parent).replace("\\", "/")
        except Exception:
            pass

        name_lower = filepath.stem.lower()
        if ext == ".svg":
            return "05-maquettes-notes"
        elif any(k in name_lower for k in ["sow", "contrat", "brief", "kickoff"]):
            return "01-sow-et-contrats"
        elif any(k in name_lower for k in ["guide", "spec", "fonctionnel", "requirement"]):
            return "02-guides-et-specs"
        elif any(k in name_lower for k in ["scan", "inventaire", "onetrust", "audit", "rapport"]):
            return "03-scans-et-inventaires"
        elif any(
            k in name_lower for k in ["api", "technique", "swagger", "openapi", "sdk", "schema"]
        ):
            return "04-api-et-techniques"
        elif ext in [".xlsx", ".csv"]:
            return "03-scans-et-inventaires"

        return "02-guides-et-specs"

    def _generate_ingested_index(self, state: LoopState) -> None:
        """Génère un index sémantique complet des documents sous docs/00-ingested/index.md (ADR-0102)."""
        ingested_dir = self._ingested_root(state)
        if not ingested_dir.exists():
            return

        index_file = ingested_dir / "index.md"
        lines = [
            f"# 📚 Index des Documents Ingérés — {state.project_name}",
            "",
            "> **Statut :** SSOT Documentaire Ingestion Phase 1 | **Généré le :** "
            + datetime.now().strftime("%Y-%m-%d %H:%M"),
            "",
            "Ce document répertorie l'ensemble des sources brutes ingérées depuis `reference/` et converties en Markdown normalisé selon l'ADR-0102 et l'ADR-0335.",
            "",
            "## 🗂️ Sommaire par Catégorie Thématique",
            "",
        ]

        categories = {
            "01-sow-et-contrats": "📄 01. Énoncés des Travaux & Contrats (SOW)",
            "02-guides-et-specs": "📘 02. Guides d'Implémentation & Spécifications",
            "03-scans-et-inventaires": "📊 03. Scans, Inventaires & Audits",
            "04-api-et-techniques": "🔌 04. Références API & Architecture Technique",
            "05-maquettes-notes": "🎨 05. Maquettes & Transcriptions d'Écrans",
            "maquettes": "🎨 05. Maquettes & Transcriptions d'Écrans",
        }

        # Découverte dynamique de tout autre sous-dossier (ex: T-Shirt Size - Initiatives)
        for sub in sorted(ingested_dir.iterdir(), key=lambda d: d.name):
            if sub.is_dir() and sub.name not in categories and not sub.name.startswith("."):
                categories[sub.name] = f"📦 {sub.name.replace('-', ' ').title()}"

        found_any = False
        for cat_dir_name, cat_title in categories.items():
            cat_path = ingested_dir / cat_dir_name
            md_files = list(cat_path.glob("*.md")) if cat_path.exists() else []
            if md_files:
                found_any = True
                lines.append(f"### {cat_title}")
                lines.append("")
                lines.append(
                    "| Document Markdown | Fichier Source Original | Termes Clés Identifiés |"
                )
                lines.append("| :--- | :--- | :--- |")
                for mf in sorted(md_files, key=lambda f: f.name):
                    matching = [
                        s
                        for s in state.ingested_sources
                        if Path(s.get("filepath", "")).stem == mf.stem
                    ]
                    orig_file = matching[0].get("filename", "N/A") if matching else "reference/"
                    terms_str = (
                        ", ".join(f"`{t}`" for t in (matching[0].get("terms", [])[:5]))
                        if matching
                        else "—"
                    )
                    rel_link = f"[{mf.name}]({cat_dir_name}/{mf.name})"
                    lines.append(f"| {rel_link} | `{orig_file}` | {terms_str} |")
                lines.append("")

        root_mds = [f for f in ingested_dir.glob("*.md") if f.name not in ["index.md", "README.md"]]
        if root_mds:
            found_any = True
            lines.append("### 📁 Autres Documents Ingérés")
            lines.append("")
            for mf in sorted(root_mds, key=lambda f: f.name):
                lines.append(f"- [{mf.name}]({mf.name})")
            lines.append("")

        if not found_any:
            lines.append("*(Aucun document ingéré pour le moment)*\n")

        try:
            index_file.write_text("\n".join(lines), encoding="utf-8")
            ZeroFluffConsole.info(f"Index SSOT 00-ingested généré : {index_file}")
        except Exception as e:
            ZeroFluffConsole.warning(f"Impossible d'écrire 00-ingested/index.md : {e}")

    def _generate_docs_root_index(self, state: LoopState) -> None:
        """Génère ou met à jour la carte d'orientation SSOT racine sous docs/index.md (ADR-0102)."""
        docs_dir = Path("Projects") / state.project_name / ProjectLayout.DOCS
        if not docs_dir.exists():
            return

        index_file = docs_dir / "index.md"
        if not index_file.exists() or "<!-- MLOOP_AUTO_GENERATED -->" in index_file.read_text(
            encoding="utf-8", errors="ignore"
        ):
            content = f"""<!-- MLOOP_AUTO_GENERATED -->
# 🧭 Carte d'Orientation SSOT & Architecture — {state.project_name}

> **Source Unique de Vérité (SSOT)** conforme à l'[ADR-0102](standards/adr-system/0102-structure-ssot-dossier-docs.md).
> **Dernière synchronisation :** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 🗺️ Arborescence Canonique du Projet

| Dossier | Description & Rôle SSOT | Accès |
| :--- | :--- | :---: |
| **`00-ingested/`** | Matière première ingérée depuis `reference/` (SOW, specs, audits, APIs, maquettes). | [Explorer](00-ingested/index.md) |
| **`01-architecture/`** | Décisions d'architecture (ADRs), Énoncé des travaux (SOW), schémas techniques. | [Explorer](01-architecture/) |
| **`02-business-rules/`** | Catalogue vivant des règles d'affaires du domaine (`RM-XXX`). | [Explorer](02-business-rules/) |
| **`03-models/`** | Modèles de données, dictionnaires d'entités, schémas DrawDB / SQL. | [Explorer](03-models/) |
| **`04-transverse/`** | Questions ouvertes client/dev (`Q-XXX`), journal de bord et lexique métier. | [Explorer](04-transverse/) |
| **`05-assets/`** | Actifs visuels versionnés (Maquettes SVG, diagrammes, images). | [Explorer](05-assets/) |

---

## 📌 Raccourcis Clés du Projet
- 📋 **Sprint Backlog Maître** : [`backlog/sprint_backlog.md`](../backlog/sprint_backlog.md)
- 📖 **Lexique du Domaine** : [`docs/04-transverse/lexique_domaine.md`](04-transverse/lexique_domaine.md)
- ❓ **Questions Ouvertes Client** : [`docs/04-transverse/00-questions-ouvertes-client.md`](04-transverse/00-questions-ouvertes-client.md)
"""
            try:
                index_file.write_text(content, encoding="utf-8")
                ZeroFluffConsole.info(
                    f"Carte d'orientation SSOT racine synchronisée : {index_file}"
                )
            except Exception as e:
                ZeroFluffConsole.warning(f"Impossible d'écrire docs/index.md : {e}")

    def _generate_maquettes_index(self, state: LoopState) -> None:
        """Génère l'index et cartographie globale des maquettes sous docs/00-ingested/05-maquettes-notes/00-index-maquettes.md."""
        maquettes_dir = self._ingested_root(state) / "05-maquettes-notes"
        if not maquettes_dir.exists():
            maquettes_dir = self._ingested_root(state) / "maquettes"
        if maquettes_dir.exists() and any(maquettes_dir.glob("*.md")):
            try:
                from src.converters.svg_to_md import generate_maquettes_index

                index_path = generate_maquettes_index(maquettes_dir)
                ZeroFluffConsole.info(
                    f"Index et Cartographie des Maquettes synchronisé : {index_path}"
                )
            except Exception as e:
                ZeroFluffConsole.warning(f"Impossible de générer 00-index-maquettes.md : {e}")

    def _generate_lod_sidecars(self, state: LoopState) -> None:
        """Génère les sidecars LOD .abstract.md et .overview.md pour docs/00-ingested/ et ses sous-dossiers (ADR-0335)."""
        ingested_dir = self._ingested_root(state)
        if not ingested_dir.exists():
            return

        # 1. Générer pour chaque sous-dossier de 00-ingested
        for sub_dir in ingested_dir.iterdir():
            if sub_dir.is_dir() and not sub_dir.name.startswith("."):
                if any(
                    f.is_file() and f.suffix.lower() == ".md" and not f.name.startswith(".")
                    for f in sub_dir.iterdir()
                ):
                    try:
                        LODGenerator.generate_lod_sidecars(
                            directory_path=sub_dir,
                            source_info={"kind": "ingested_category", "category": sub_dir.name},
                            project_name=state.project_name,
                        )
                    except Exception as e:
                        ZeroFluffConsole.warning(f"Erreur sidecar LOD pour {sub_dir.name} : {e}")

        # 2. Générer pour la racine 00-ingested si des fichiers y sont présents
        try:
            LODGenerator.generate_lod_sidecars(
                directory_path=ingested_dir,
                source_info={
                    "kind": "ingested_root",
                    "uri": f"mloop://docs/{ProjectLayout.DOCS_INGESTED}",
                },
                project_name=state.project_name,
            )
            ZeroFluffConsole.info("Sidecars LOD (L0/L1) synchronisés sous docs/00-ingested/")
        except Exception as e:
            ZeroFluffConsole.warning(f"Erreur sidecar LOD racine 00-ingested : {e}")

    def _parse_pdf(self, path: Path) -> str:
        try:
            import pypdf

            reader = pypdf.PdfReader(path)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        except ImportError:
            msg = "[Erreur : pypdf n'est pas installé. Extraction brute impossible]"
            ZeroFluffConsole.error(f"Dépendance manquante pour PDF ({path.name}) : pypdf")
            return msg
        except Exception as e:
            msg = f"[Erreur lors du parsing PDF : {e}]"
            ZeroFluffConsole.error(f"Erreur parsing PDF ({path.name}) : {e}")
            return msg

    def _parse_xlsx(self, path: Path) -> str:
        try:
            import openpyxl

            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheets_text = []
            for sheetname in wb.sheetnames:
                sheet = wb[sheetname]
                sheets_text.append(f"## Feuille : {sheetname}")
                rows_text = []
                for row in sheet.iter_rows(values_only=True):
                    row_vals = [str(val) if val is not None else "" for val in row]
                    if any(row_vals):
                        rows_text.append(", ".join(row_vals))
                sheets_text.append("\n".join(rows_text))
            return "\n\n".join(sheets_text)
        except ImportError:
            msg = "[Erreur : openpyxl n'est pas installé. Lecture XLSX impossible]"
            ZeroFluffConsole.error(f"Dépendance manquante pour XLSX ({path.name}) : openpyxl")
            return msg
        except Exception as e:
            msg = f"[Erreur lors du parsing XLSX : {e}]"
            ZeroFluffConsole.error(f"Erreur parsing XLSX ({path.name}) : {e}")
            return msg

    def _parse_docx(self, path: Path) -> str:
        try:
            import docx

            doc = docx.Document(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(paragraphs)
        except ImportError:
            msg = "[Erreur : python-docx n'est pas installé. Lecture DOCX impossible]"
            ZeroFluffConsole.error(f"Dépendance manquante pour DOCX ({path.name}) : python-docx")
            return msg
        except Exception as e:
            msg = f"[Erreur lors du parsing DOCX : {e}]"
            ZeroFluffConsole.error(f"Erreur parsing DOCX ({path.name}) : {e}")
            return msg

    def _parse_pptx(self, path: Path) -> str:
        try:
            from pptx import Presentation

            prs = Presentation(path)
            slides_text = []
            for i, slide in enumerate(prs.slides, start=1):
                slides_text.append(f"## Slide {i}")
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        slides_text.append(shape.text)
            return "\n\n".join(slides_text)
        except ImportError:
            msg = "[Erreur : python-pptx n'est pas installé. Lecture PPTX impossible]"
            ZeroFluffConsole.error(f"Dépendance manquante pour PPTX ({path.name}) : python-pptx")
            return msg
        except Exception as e:
            msg = f"[Erreur lors du parsing PPTX : {e}]"
            ZeroFluffConsole.error(f"Erreur parsing PPTX ({path.name}) : {e}")
            return msg

    def _try_markitdown(self, path: Path) -> str:
        """
        Ingestion universelle Microsoft MarkItDown.
        """
        try:
            from markitdown import MarkItDown

            md = MarkItDown()
            res = md.convert(str(path))
            return res.text_content if hasattr(res, "text_content") else str(res)
        except Exception:
            return ""

    def _enrich_markdown(
        self, raw_text: str, filepath: Path, project_name: str, terms: list[str] = None
    ) -> str:
        """
        Enrichit le document Markdown avec un Frontmatter YAML normatif (Pattern pdf-brain & DeepPaperNote).
        """
        if raw_text.lstrip().startswith("---"):
            return raw_text

        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        title = filepath.stem.replace("_", " ").replace("-", " ").title()
        for line in lines[:5]:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        summary_lines = [l for l in lines if not l.startswith("#") and len(l) > 20][:3]
        summary = (
            " ".join(summary_lines)[:300]
            if summary_lines
            else f"Document de référence pour {filepath.name}."
        )

        doc_type = "general_doc"
        fname_lower = filepath.name.lower()
        if "api" in fname_lower or "reference" in fname_lower:
            doc_type = "api_reference"
        elif "adr" in fname_lower or "arch" in fname_lower or "design" in fname_lower:
            doc_type = "architecture_doc"
        elif "story" in fname_lower or "us-" in fname_lower or "rec-" in fname_lower:
            doc_type = "user_story"
        elif "spec" in fname_lower or "req" in fname_lower:
            doc_type = "spec"

        concepts = []
        full_lower = raw_text.lower() + " " + fname_lower
        taxonomy_file = Path("docs") / "05-knowledge" / "taxonomy.json"
        if taxonomy_file.exists():
            try:
                tax_data = json.loads(taxonomy_file.read_text(encoding="utf-8"))
                for c in tax_data.get("concepts", []):
                    c_id = c.get("id")
                    label = c.get("prefLabel", "").lower()
                    alts = [a.lower() for a in c.get("altLabels", [])]
                    if label in full_lower or any(a in full_lower for a in alts):
                        concepts.append(c_id)
            except Exception:
                pass

        if not concepts:
            concepts = ["general/reference"]

        tags = [filepath.suffix.lstrip(".").lower(), doc_type]
        if project_name.lower() not in tags:
            tags.append(project_name.lower())

        terms_list = terms or []

        frontmatter = (
            "---\n"
            f'title: "{title}"\n'
            f'summary: "{summary}"\n'
            f'document_type: "{doc_type}"\n'
            f"tags: {json.dumps(tags, ensure_ascii=False)}\n"
            f"concepts: {json.dumps(concepts, ensure_ascii=False)}\n"
            f"terms: {json.dumps(terms_list, ensure_ascii=False)}\n"
            f'ingested_at: "{datetime.now().isoformat()}"\n'
            "---\n\n"
        )
        return frontmatter + raw_text

    def _parse_vtt(self, path: Path) -> str:
        """Parse un fichier WebVTT de transcription de réunion en Markdown lisible."""
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            lines = raw.splitlines()
            dialogue = []
            title = path.stem.replace("_", " ")
            dialogue.append(f"# 🎙️ Transcription : {title}\n")

            seen_cues = set()
            for line in lines:
                l = line.strip()
                if not l or l == "WEBVTT" or "-->" in l or l.isdigit():
                    continue
                # Nettoyer les balises <v Nom>
                speaker_match = re.match(r"<v\s+([^>]+)>(.*)", l)
                if speaker_match:
                    speaker, text = speaker_match.groups()
                    text = text.replace("</v>", "").strip()
                    cue_key = f"{speaker}:{text}"
                    if cue_key not in seen_cues:
                        seen_cues.add(cue_key)
                        dialogue.append(f"- **{speaker}** : {text}")
                else:
                    if l not in seen_cues:
                        seen_cues.add(l)
                        dialogue.append(f"- {l}")
            return "\n".join(dialogue)
        except Exception as e:
            return f"[Erreur lors du parsing VTT ({path.name}) : {e}]"

    def _process_image_asset(self, filepath: Path, state: LoopState) -> str:
        """Synchronise l'image dans docs/05-assets/ et génère une note d'artefact."""
        try:
            import shutil

            rel_parent = filepath.parent.name
            target_assets = self._initiative_docs_root(state) / "05-assets"
            if rel_parent in ["01-reception", "02-incubation", "03-ventes"]:
                target_assets = target_assets / rel_parent
            target_assets.mkdir(parents=True, exist_ok=True)
            target_img = target_assets / filepath.name
            shutil.copy2(filepath, target_img)

            return f"# 🖼️ Capture / Maquette : {filepath.stem}\n\n![{filepath.stem}](../05-assets/{rel_parent}/{filepath.name})\n\n- **Fichier source** : `{filepath.name}`\n- **Module associé** : `{rel_parent}`\n"
        except Exception as e:
            return f"[Erreur lors du traitement de l'image ({filepath.name}) : {e}]"
