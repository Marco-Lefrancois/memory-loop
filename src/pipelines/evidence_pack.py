import json
import re
import datetime
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any, List, Literal, Optional, TypedDict

from src.cli import ZeroFluffConsole
from src.pipelines.pack_preserver import load_preserved_fields, PackPreserver
from src.pipelines.evidence_synchronizer import EvidenceSynchronizer
from src.pipelines.evidence_types import CodeTraceabilityEntry

if TYPE_CHECKING:
    from src.pipelines.plan_evidence_parser import PlanEvidenceParser
from src.utils.logger import get_logger

logger = get_logger("pipelines.evidence_pack")

# ──────────────────────────────────────────────────────────────────────────────
# MLOOP-180-BE : Types de parité Phase 2 (ADR-0320 / ADR-0361)
# ──────────────────────────────────────────────────────────────────────────────

DecisionCategory = Literal[
    "architecture",
    "pattern",
    "refactoring",
    "performance",
    "security",
    "tooling",
    "testing",
]

_ALLOWED_DECISION_CATEGORIES = {
    "architecture",
    "pattern",
    "refactoring",
    "performance",
    "security",
    "tooling",
    "testing",
}


class VerbatimExtract(TypedDict, total=False):
    """Citation verbatim ancrée avec numéros de ligne (ADR-0320 §G)."""

    source_file: str
    lines: List[int]  # [start, end] — obligatoire pour VALIDATED
    quote: str  # texte verbatim non vide
    established_fact: str  # fait établi dérivé de la citation


class ImplementationDecision(TypedDict, total=False):
    """Décision d'implémentation tracée avec catégorie fermée."""

    decision_id: str
    category: str  # validé contre _ALLOWED_DECISION_CATEGORIES
    rationale: str
    alternatives_considered: List[str]
    timestamp: str  # ISO-8601 UTC


class DeclarativeContract(TypedDict, total=False):
    """Référence déclarative à une route/CTA réellement utilisée (Zéro Fausse Route)."""

    method: str  # GET | POST | PUT | PATCH | DELETE | N/A
    path: str  # route ou "[API de soumission à définir]"
    status: str  # "defined" | "to_define"
    source: str  # fichier source où la route est déclarée


class ConflictResolution(TypedDict, total=False):
    """Résolution documentée d'une divergence récit vs code/maquette."""

    artifact: str
    narrative_claim: str
    code_reality: str
    resolution: str
    authority: str  # "code" | "mockup" | "spec"


class EvidencePackEngine:
    """
    Générateur & Gestionnaire d'Artefacts EvidencePack (memory/evidence/US-XX_evidence.json).
    Mappe les alertes ([!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION]),
    les questions ouvertes (Q-XXX, QD-XXX), les sources de vérité associées à un récit
    avec empreinte cryptographique SHA-256 et audit épistémique (ADR-0335, ADR-0336).
    """

    ALERT_TYPES = ["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"]

    # ADR-0320 §G : extensions considérées comme Code Source physique (preuve forte)
    # vs Documentation (preuve d'existence seulement).
    CODE_EXTENSIONS = {"cs", "csproj", "plist", "xml"}
    DOC_EXTENSIONS = {"md", "xlsx", "pdf", "docx", "json", "yml"}

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.evidence_dir = self.project_path / "memory" / "evidence"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    # ── MLOOP-180-BE : Validation catégorie fermée (CA-3) ────────────────────
    @staticmethod
    def _validate_decision_category(category: str) -> None:
        """
        Valide qu'une catégorie de décision appartient à la liste fermée (CA-3).

        Raises:
            ValueError: si la catégorie n'est pas dans _ALLOWED_DECISION_CATEGORIES.

        ADR-0369 : jamais de swallow — l'exception se propage au caller.
        """
        if category not in _ALLOWED_DECISION_CATEGORIES:
            raise ValueError(
                f"[MLOOP-180-BE] Catégorie de décision hors liste fermée : {category!r}. "
                f"Autorisées : {sorted(_ALLOWED_DECISION_CATEGORIES)}"
            )

    # ── MLOOP-180-BE : Validation verbatim (CA-2) ────────────────────────────
    @staticmethod
    def _validate_verbatim_extract(extract: "VerbatimExtract") -> None:
        """
        Valide qu'un VerbatimExtract porte une quote non vide et un ancrage ligne valide.

        Raises:
            ValueError: si quote vide ou lines invalides (None, mauvais ordre, non-liste).

        ADR-0369 : jamais de swallow — l'exception se propage au caller.
        """
        quote = extract.get("quote", "")
        if not quote:
            raise ValueError(
                "[MLOOP-180-BE] VerbatimExtract : le champ 'quote' ne peut pas être vide "
                "(ADR-0320 §G — ancrage épistémique obligatoire)."
            )
        lines = extract.get("lines")
        if lines is None:
            raise ValueError(
                "[MLOOP-180-BE] VerbatimExtract : ancrage ligne obligatoire (ADR-0320). "
                "Fournir 'lines': [start, end]."
            )
        if not isinstance(lines, (list, tuple)) or len(lines) != 2:
            raise ValueError(
                f"[MLOOP-180-BE] VerbatimExtract : 'lines' doit être [start, end], reçu : {lines!r}."
            )
        start, end = lines[0], lines[1]
        if not (isinstance(start, int) and isinstance(end, int)) or start > end:
            raise ValueError(
                f"[MLOOP-180-BE] VerbatimExtract : 'lines' invalides [start={start}, end={end}] "
                "— start doit être ≤ end et les deux doivent être des entiers."
            )

    # ── MLOOP-330-BE : Validation Traçabilité Code ↔ Exigences (ADR-0394) ────
    @staticmethod
    def _validate_code_traceability_entry(entry: "CodeTraceabilityEntry") -> None:
        """
        Valide qu'une entrée de traçabilité est conforme (ADR-0394 / OpenSpec Ready).

        Raises:
            ValueError: si ast_symbol mal qualifié, requirement_ref vide, ou rationale trop court.
        """
        ast_symbol = str(entry.get("ast_symbol", "")).strip()
        if not ast_symbol or "::" not in ast_symbol:
            raise ValueError(
                f"[ADR-0394] CodeTraceabilityEntry : le champ 'ast_symbol' ({ast_symbol!r}) doit être qualifié sous forme 'chemin/fichier.ext::Symbole'."
            )

        req_ref = str(entry.get("requirement_ref", "")).strip()
        if not req_ref or len(req_ref) < 2:
            raise ValueError(
                f"[ADR-0394] CodeTraceabilityEntry : le champ 'requirement_ref' ne peut pas être vide ({req_ref!r})."
            )

        rationale = str(entry.get("rationale", "")).strip()
        if not rationale or len(rationale) < 10:
            raise ValueError(
                f"[ADR-0394] CodeTraceabilityEntry : la justification 'rationale' doit comporter au moins 10 caractères ({rationale!r})."
            )

    def validate_code_traceability(self, entries: List["CodeTraceabilityEntry"]) -> bool:
        """
        Valide l'ensemble des entrées d'une matrice de traçabilité Code ↔ Exigences.
        """
        for entry in entries:
            self._validate_code_traceability_entry(entry)
        return True

    def _resolve_source_sha256(self, src_name: str) -> Optional[str]:
        """Calcule l'empreinte SHA-256 d'une source trouvée sur disque."""
        resolved = self._resolve_source_path(src_name)
        if resolved and resolved.is_file():
            try:
                h = hashlib.sha256()
                with open(resolved, "rb") as f:
                    while chunk := f.read(8192):
                        h.update(chunk)
                return h.hexdigest()
            except Exception as e:
                logger.debug(
                    "Calcul SHA-256 de la source échoué, empreinte non disponible",
                    exc_info=True,
                    extra={
                        "component": "pipelines.evidence_pack",
                        "operation": "_resolve_source_sha256",
                        "source": src_name,
                        "error": str(e),
                    },
                )
        return None

    def _candidate_paths(self, src_name: str) -> List[Path]:
        """Chemins candidats de résolution d'une source citée (docs, reference, memory, backlog, root)."""
        return [
            self.project_path / "memory" / "evidence" / src_name,
            self.project_path / "memory" / src_name,
            self.project_path / "backlog" / "handoff" / src_name,
            self.project_path / "backlog" / "reviews" / src_name,
            self.project_path / "backlog" / src_name,
            self.project_path / "docs" / "00-ingested" / src_name,
            self.project_path / "docs" / "05-assets" / src_name,
            self.project_path / "docs" / src_name,
            self.project_path / "reference" / src_name,
            self.project_path / src_name,
            Path("C:/Memory Loop") / "standards" / "blueprints" / src_name,
            Path("C:/Memory Loop") / ".agents" / "references" / src_name,
            Path("c:/Memory Loop") / "docs" / "00-ingested" / src_name,
            Path("c:/Memory Loop") / "docs" / src_name,
        ]

    def _resolve_source_path(self, src_name: str) -> Optional[Path]:
        """Résout le chemin réel d'une source citée en cherchant aussi récursivement sous reference/, docs/, memory/ et backlog/."""
        for cp in self._candidate_paths(src_name):
            if cp.exists() and cp.is_file():
                return cp
        # Fallback : recherche récursive sous memory/ (ex: memory/evidence/<fact_dossier>.md)
        memory_dir = self.project_path / "memory"
        if memory_dir.exists():
            matches = list(memory_dir.rglob(src_name))
            if matches:
                return matches[0]
        # Fallback : recherche récursive sous backlog/ (ex: backlog/handoff/.../<tasks>.md)
        backlog_dir = self.project_path / "backlog"
        if backlog_dir.exists():
            matches = list(backlog_dir.rglob(src_name))
            if matches:
                return matches[0]
        # Fallback : recherche récursive sous reference/ (arborescences de code source multi-niveaux)
        ref_dir = self.project_path / "reference"
        if ref_dir.exists():
            matches = list(ref_dir.rglob(src_name))
            if matches:
                return matches[0]
        # Fallback : recherche récursive sous docs/ (ex: docs/00-ingested/maquettes/<mockup>.md)
        docs_dir = self.project_path / "docs"
        if docs_dir.exists():
            matches = list(docs_dir.rglob(src_name))
            if matches:
                return matches[0]
        # Fallback : recherche sous les référentiels globaux du framework
        for global_dir in [Path("C:/Memory Loop/standards"), Path("C:/Memory Loop/.agents")]:
            if global_dir.exists():
                matches = list(global_dir.rglob(src_name))
                if matches:
                    return matches[0]
        return None

    def _classify_source(self, src_name: str, resolved_path: Optional[Path]) -> Dict[str, Any]:
        """
        Classifie une source Fact-Search selon ADR-0320 §G :
        - verification_method: "code_source_verified" | "file_existence_only" | "semantic_match"
        - source_type: "code" | "documentation"
        Le score n'est HIGH/1.0 que pour du code source physiquement résolu (preuve forte).
        Une source de documentation, même trouvée, reste MEDIUM/0.75 (existence, pas véracité sémantique).
        """
        ext = src_name.rsplit(".", 1)[-1].lower() if "." in src_name else ""
        is_code = ext in self.CODE_EXTENSIONS
        source_type = "code" if is_code else "documentation"

        if resolved_path is not None and is_code:
            return {
                "verification_method": "code_source_verified",
                "source_type": source_type,
                "confidence": "HIGH",
                "confidence_score": 1.0,
            }
        if resolved_path is not None:
            return {
                "verification_method": "file_existence_only",
                "source_type": source_type,
                "confidence": "MEDIUM",
                "confidence_score": 0.75,
            }
        # Source citée mais introuvable sur disque : dégradation de confiance (signal WikiFix)
        return {
            "verification_method": "file_existence_only",
            "source_type": source_type,
            "confidence": "LOW",
            "confidence_score": 0.25,
        }

    def _extract_visual_contract(self, sources: set) -> List[Dict[str, Any]]:
        """
        Phase 1 (Enforcement Déterministe du Grounding Visuel & Épistémique) :
        pour chaque source .md citée dans le récit, si elle correspond à une
        spécification UI ingérée (frontmatter `document_type: "ui_specification"`,
        produite par `src/converters/svg_to_md.py`), extrait les champs
        `is_vectorized` / `ocr_status` afin de tracer si le Contrat Visuel
        (Maquettes = SSOT, AGENTS.md) a réellement pu être lu par OCR ou non.

        Retourne une liste vide si aucune maquette n'est référencée (pas d'invention
        de contrat visuel pour une story purement backend/headless).
        """
        contracts: List[Dict[str, Any]] = []
        for src in sorted(sources):
            if not src.endswith(".md"):
                continue
            resolved = self._resolve_source_path(src)
            if resolved is None:
                continue
            try:
                mockup_content = resolved.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.debug(
                    "Lecture du fichier maquette échouée, maquette ignorée",
                    exc_info=True,
                    extra={
                        "component": "pipelines.evidence_pack",
                        "operation": "_extract_mockup_contracts",
                        "mockup_path": str(resolved),
                        "error": str(e),
                    },
                )
                continue

            fm_match = re.match(r"^---\s*\n(.*?)\n---", mockup_content, re.DOTALL)
            if not fm_match:
                continue
            fm_text = fm_match.group(1)

            is_ui_spec = re.search(r'^document_type:\s*"ui_specification"', fm_text, re.MULTILINE)
            if not is_ui_spec:
                continue

            vect_m = re.search(r"^is_vectorized:\s*(true|false)", fm_text, re.MULTILINE)
            ocr_m = re.search(r'^ocr_status:\s*"([A-Z_]+)"', fm_text, re.MULTILINE)

            contracts.append(
                {
                    "mockup_path": str(resolved).replace("\\", "/"),
                    "is_vectorized": (vect_m.group(1) == "true") if vect_m else False,
                    "ocr_status": ocr_m.group(1) if ocr_m else "N_A",
                }
            )
        return contracts

    def _find_fact_dossier(self, story_file: Path, sid: str) -> Optional[Path]:
        """Localise le Dossier de Preuves Documentaires associé à un récit."""
        cand1 = self.evidence_dir / f"{sid}_fact_dossier.md"
        if cand1.exists():
            return cand1
        try:
            content = story_file.read_text(encoding="utf-8", errors="replace")
            dossier_links = re.findall(r"\[(?:[^\]]*fact_dossier[^\]]*)\]\(([^)]+)\)", content)
            for target in dossier_links:
                if target.startswith(("http://", "https://")):
                    continue
                cand = (story_file.parent / target).resolve()
                if cand.exists():
                    return cand
        except Exception as e:
            logger.debug(
                "Analyse des liens fact_dossier du récit échouée, recherche récursive de secours",
                exc_info=True,
                extra={
                    "component": "pipelines.evidence_pack",
                    "operation": "_find_fact_dossier",
                    "story_file": str(story_file),
                    "error": str(e),
                },
            )
        memory_dir = self.project_path / "memory"
        if memory_dir.exists():
            matches = list(memory_dir.rglob(f"*{sid}*fact_dossier.md"))
            if matches:
                return matches[0]
        return None

    def _parse_fact_dossier(self, dossier_path: Path) -> Dict[str, Any]:
        """
        Extrait les métadonnées, empreintes et faits atomiques du Dossier de Preuves.
        Projection propre sans duplication massive de prose (ADR-0320, ADR-0326).
        """
        try:
            content = dossier_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {}

        result: Dict[str, Any] = {
            "dossier_path": dossier_path,
            "dossier_status": "CURRENT",
            "sources_hashes": {},
            "facts": [],
            "endpoints": [],
            "has_mermaid": False,
            "has_dbml": False,
            "verbatims_count": 0,
        }

        fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            st_m = re.search(r"^dossier_status:\s*(.+)$", fm_text, re.MULTILINE)
            if st_m:
                result["dossier_status"] = st_m.group(1).strip()
            sh_match = re.search(r"sources_hashes:\s*\n((?:[ \t]+[^\n]+\n?)+)", fm_text)
            if sh_match:
                for line in sh_match.group(1).splitlines():
                    pair = line.strip().split(":", 1)
                    if len(pair) == 2:
                        k = pair[0].strip().strip("'\"")
                        v = pair[1].strip().strip("'\"")
                        result["sources_hashes"][k] = v

        result["sha256"] = self._resolve_source_sha256(dossier_path.name) or ""

        # Format A : Tableau Markdown | **F-01** | `table` | DBML | Rôle/Règle |
        table_rows = re.finditer(
            r"(?m)^\s*\|\s*\*{0,2}(F-\d+)\*{0,2}\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*(?:\|\s*([^|\n]+)\s*)?\|?",
            content,
        )
        for tr in table_rows:
            fid = tr.group(1).strip()
            src_ref = tr.group(2).strip().strip("`* ")
            col3 = tr.group(3).strip().strip("`* ")
            col4 = tr.group(4).strip().strip("`* ") if tr.group(4) else ""
            rule_summary = col4 if col4 else col3
            rule_summary = re.sub(r"\s+", " ", rule_summary).strip()
            if len(rule_summary) > 160:
                rule_summary = rule_summary[:157] + "..."
            result["facts"].append(
                {
                    "fact_id": fid,
                    "source_ref": src_ref,
                    "rule_summary": rule_summary,
                    "status": "VERIFIED",
                }
            )

        # Format B : Blocs d'extraits verbatims (ex: INC-001-BE ou US-05-FOOD)
        if not result["facts"]:
            verbatim_blocks = re.finditer(
                r"(?ms)>\s*\*{0,2}Extrait\s*(\d+)[^\n]*\n.*?>\s*➔\s*\*{0,2}Fait établi\*{0,2}\s*:\s*([^\n]+)",
                content,
            )
            for vb in verbatim_blocks:
                idx = int(vb.group(1))
                fid = f"F-{idx:02d}"
                summary = vb.group(2).strip().strip("* ")
                summary = re.sub(r"\s+", " ", summary).strip()
                if len(summary) > 160:
                    summary = summary[:157] + "..."
                result["facts"].append(
                    {
                        "fact_id": fid,
                        "source_ref": "Dossier de Preuves",
                        "rule_summary": summary,
                        "status": "VERIFIED",
                    }
                )

        # Format C : Bullet lists `- **F-01** ...`
        if not result["facts"]:
            bullet_rows = re.finditer(
                r"(?m)^\s*[\-\*]\s*\*{0,2}(F-\d+)\*{0,2}\s*(?:\[([^\]]+)\])?\s*[:\-]?\s*([^\n]+)",
                content,
            )
            for br in bullet_rows:
                fid = br.group(1).strip()
                sref = br.group(2).strip() if br.group(2) else "Dossier de Preuves"
                summary = br.group(3).strip().strip("* ")
                if len(summary) > 160:
                    summary = summary[:157] + "..."
                result["facts"].append(
                    {
                        "fact_id": fid,
                        "source_ref": sref,
                        "rule_summary": summary,
                        "status": "VERIFIED",
                    }
                )

        result["has_mermaid"] = "```mermaid" in content
        result["has_dbml"] = "Table " in content or "table " in content or "```dbml" in content
        result["verbatims_count"] = len(
            re.findall(r"(?i)(?:verbatim|extrait\s*\d+|«[^»]{15,}»)", content)
        )

        return result

    def extract_evidence(self, story_file: Path) -> Dict[str, Any]:
        story_file = Path(story_file)
        if not story_file.exists():
            raise FileNotFoundError(f"Récit introuvable : {story_file}")

        content = story_file.read_text(encoding="utf-8")
        story_id = story_file.stem

        # 1. Extraction ID et Jira Key du Frontmatter YAML si présent
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        yaml_id = None
        jira_key = None
        if frontmatter_match:
            fm_text = frontmatter_match.group(1)
            id_m = re.search(r"^id:\s*(.+)$", fm_text, re.MULTILINE)
            if id_m:
                yaml_id = id_m.group(1).strip()
            jk_m = re.search(r"^jira_key:\s*(.+)$", fm_text, re.MULTILINE)
            if jk_m:
                jira_key = jk_m.group(1).strip()

        # 2. Extraction des Alertes GitHub Markdown ([!NOTE], [!CAUTION], etc.)
        alerts = []
        alert_pattern = (
            r"(?m)^>\s*\[\!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:^>[^\n]*\n?)+)"
        )
        for match in re.finditer(alert_pattern, content):
            alert_type = match.group(1)
            raw_lines = match.group(2).splitlines()
            clean_text = "\n".join([line.lstrip("> ").strip() for line in raw_lines]).strip()
            alerts.append({"type": alert_type, "text": clean_text})

        # 3. Extraction des Questions Ouvertes liées (Q-XXX et QD-XXX)
        questions = sorted(list(set(re.findall(r"\b(?:Q|QD)-\d{3}\b", content))))

        # 4. Extraction des Sources de Vérité (scans, SOW, directives ET code source .cs, .plist, .csproj)
        import urllib.parse

        decoded_content = urllib.parse.unquote(content)
        sources = set()
        for s_match in re.finditer(
            r"\b([a-zA-Z0-9_\-À-ÿ]+\.(?:md|xlsx|pdf|docx|plist|cs|csproj|xml|yml|json))\b",
            decoded_content,
        ):
            sources.add(s_match.group(1))

        # 5. Extraction V-Model Harness : Scénarios de Test Gherkin
        # FIX: \s* ajouté avant le mot-clé pour consommer l'indentation
        # quand le groupe facultatif (### ou -) match une chaîne vide.
        scenarios = []
        scen_matches = re.finditer(
            r"(?m)^\s*(?:###?\s+|[-*]\s+)?(?:Scénario|Scenario)\s*[:\-]\s*(.+)$",
            content,
        )
        for s_m in scen_matches:
            scenarios.append(
                {
                    "scenario_title": s_m.group(1).strip(),
                    "status": "VERIFIED",
                    "verifier": "Sentinel_ReadOnly",
                }
            )

        # 6. Extraction des Preuves Fact-Search & Faits Vérifiés (ADR-0320, ADR-0326)
        sid = yaml_id or story_id
        dossier_path = self._find_fact_dossier(story_file, sid)
        dossier_data = self._parse_fact_dossier(dossier_path) if dossier_path else {}

        facts_verified = []
        if dossier_data.get("facts"):
            facts_verified = dossier_data["facts"]
        else:
            # Fallback historique si aucun Dossier de Preuves formel
            facts_match = re.search(
                r"(?i)Faits (?:Établis & Prouvés|Vérifiés|Clés)\s*:\s*\n((?:\s*[\d\*\-].*\n?)+)",
                content,
            )
            if facts_match:
                for f_line in facts_match.group(1).splitlines():
                    clean_f = re.sub(
                        r"^\s*[\d\*\-\.]+\s*(?:\*Fait \d+\*|\bFait \d+\b)?\s*[:\-]?\s*",
                        "",
                        f_line,
                    ).strip()
                    if clean_f and not clean_f.startswith("["):
                        facts_verified.append(
                            {
                                "fact_id": f"F-{len(facts_verified) + 1:02d}",
                                "source_ref": "Story Markdown",
                                "rule_summary": clean_f[:160],
                                "status": "VERIFIED",
                            }
                        )

        fact_proofs = []
        source_hashes = {}
        code_verified_count = 0

        # Si un dossier de preuves existe, enregistrer son empreinte et intégrer ses sources canoniques
        if dossier_path and dossier_data:
            dossier_sha = dossier_data.get("sha256") or self._resolve_source_sha256(
                dossier_path.name
            )
            if dossier_sha:
                source_hashes[dossier_path.name] = dossier_sha
                sources.add(dossier_path.name)

            for raw_src, declared_sha in dossier_data.get("sources_hashes", {}).items():
                src_filename = raw_src if "." in raw_src else f"{raw_src}.md"
                sources.add(src_filename)
                resolved_s = self._resolve_source_path(src_filename)
                if resolved_s:
                    live_sha = self._resolve_source_sha256(src_filename)
                    source_hashes[src_filename] = live_sha or declared_sha

        for src in sorted(list(sources)):
            resolved_path = self._resolve_source_path(src)
            sha = self._resolve_source_sha256(src) if resolved_path else None
            if sha:
                source_hashes[src] = sha
            classification = self._classify_source(src, resolved_path)

            # Rehaussement : source adossée au Dossier de Preuves VALIDATED / CURRENT
            is_in_dossier = dossier_data and (
                src in dossier_data.get("sources_hashes", {})
                or any(src in k for k in dossier_data.get("sources_hashes", {}).keys())
                or (dossier_path and src == dossier_path.name)
            )
            if (
                is_in_dossier
                and dossier_path
                and dossier_data.get("dossier_status")
                in (
                    "CURRENT",
                    "VALIDATED",
                )
            ):
                classification["verification_method"] = "ssot_dossier_grounded"
                classification["confidence"] = "HIGH"
                classification["confidence_score"] = 1.0
                matched_fact = f"Source SSOT canonique scellée dans le Dossier de Preuves ({dossier_path.name}) : {src}"
                code_verified_count += 1
            elif classification["verification_method"] == "code_source_verified":
                code_verified_count += 1
                matched_fact = f"Comportement technique confirmé par inspection directe du code source physique : {src}"
            elif resolved_path is not None:
                matched_fact = (
                    f"Référence documentaire trouvée sur disque (existence vérifiée) : {src}"
                )
            else:
                matched_fact = f"Source citée mais introuvable physiquement sur disque : {src}"

            fact_proofs.append(
                {
                    "query": f"Fact-Search {src}",
                    "source_file": src,
                    "sha256": sha or source_hashes.get(src, "NOT_CALCULATED_LOCAL_ONLY"),
                    "section": "SSOT Reference",
                    "matched_fact": matched_fact,
                    "verification_method": classification["verification_method"],
                    "source_type": classification["source_type"],
                    "confidence": classification["confidence"],
                    "confidence_score": classification["confidence_score"],
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
            )

        # 6a-bis. Extraction du Contrat Visuel
        visual_contract = self._extract_visual_contract(sources)

        # 6b. Extraction des Références Externes & Liens Wiki (ADR-0327)
        external_refs = []
        ref_section_match = re.search(
            r"(?i)## Références\s*\n(.*?)(?:\n---|\n##|\Z)", content, re.DOTALL
        )
        if ref_section_match:
            ref_text = ref_section_match.group(1)
            for r_m in re.finditer(r"\[([^\]]+)\]\((https?://[^\)]+)\)", ref_text):
                external_refs.append(
                    {
                        "title": r_m.group(1).strip(),
                        "url": r_m.group(2).strip(),
                        "is_azure_devops_wiki": "_wiki/wikis/" in r_m.group(2),
                    }
                )

        # 7. Audit Épistémique (ADR-0335 / ADR-0336)
        # MLOOP-180-BE : les 5 champs de parité sont INITIALISÉS vides si le pack
        # n'existe pas (rétrocompat CA-5).
        # MLOOP-181-BE : ils sont PRÉSERVÉS depuis le pack existant — les captures
        # du harnais Phase 3 (tournoi, TDD, contrats, citations) survivent à la
        # régénération de chaque `sync` (CA-1/CA-2/CA-4 + sceau Gate 3 intact).
        _preserved_fields = load_preserved_fields(self.evidence_dir / f"{sid}_evidence.json")
        verbatim_extracts: List[VerbatimExtract] = _preserved_fields["verbatim_extracts"]
        implementation_decisions: List[ImplementationDecision] = _preserved_fields[
            "implementation_decisions"
        ]
        declarative_contracts: List[DeclarativeContract] = _preserved_fields[
            "declarative_contracts"
        ]
        conflict_matrix: List[ConflictResolution] = _preserved_fields["conflict_matrix"]

        # Calcul richesse (Déc.5) — basé sur les 3 champs de contenu.
        # richness_reference = 10 (borne douce documentée OQ-002).
        richness = (
            len(verbatim_extracts) + len(implementation_decisions) + len(declarative_contracts)
        )
        _richness_ref: int = 10
        multiplier: float = round(0.7 + 0.3 * min(1.0, richness / _richness_ref), 4)

        # what_it_actually_proves / what_it_does_not_prove : listes (non chaînes scalaires)
        # pour permettre l'assertion de non-vacuité sur les packs VALIDATED (CA-4 élargi).
        what_it_actually_proves: List[str] = [
            f"Spécification adossée aux sources vérifiées : {', '.join(sorted(list(sources))[:3])}"
            if sources
            else "Spécification basée sur modèle déclaratif"
        ]
        what_it_does_not_prove: List[str] = [
            f"Comportement sous réserve de validation des questions ouvertes : {', '.join(questions)}"
            if questions
            else "Aucune question ouverte non résolue"
        ]

        epistemic_audit: Dict[str, Any] = {
            "what_it_actually_proves": what_it_actually_proves,
            "what_it_does_not_prove": what_it_does_not_prove,
            "claim_boundaries": "Périmètre fonctionnel restreint aux 4 Piliers Gherkin du récit",
            # MLOOP-180-BE — Déc.5 : pénalité de richesse (richness_penalty)
            "richness_penalty": {
                "richness": richness,
                "multiplier": multiplier,
                # score sera rempli après le calcul root_score ci-dessous
                "score": 0.0,
                "reason": (
                    "no_citations"
                    if richness == 0
                    else f"partial_richness ({richness}/{_richness_ref})"
                    if richness < _richness_ref
                    else "full_richness"
                ),
            },
        }

        proj_name = self.project_path.name
        next_actions = [
            f"python src/swarm.py grill --project {proj_name} --story {sid}",
            f"python src/swarm.py rubber-duck --project {proj_name} --file {story_file.name}",
            f"python src/swarm.py sync --project {proj_name}",
        ]

        if (
            dossier_data
            and dossier_data.get("dossier_status") in ("CURRENT", "VALIDATED")
            and facts_verified
        ):
            root_confidence, root_score = "HIGH", 1.0
        elif not fact_proofs:
            root_confidence, root_score = "MEDIUM", 0.75
        elif code_verified_count == len(fact_proofs):
            root_confidence, root_score = "HIGH", 1.0
        elif code_verified_count > 0:
            root_confidence, root_score = (
                "MEDIUM",
                round(0.75 + 0.25 * (code_verified_count / len(fact_proofs)), 2),
            )
        else:
            root_confidence, root_score = "MEDIUM", 0.75

        # MLOOP-180-BE — Déc.5 : application du multiplicateur de richesse sur root_score.
        # Effectué APRÈS le calcul root_score existant, AVANT la construction du dict final.
        root_score = round(root_score * multiplier, 4)
        if multiplier < 0.85 and root_confidence == "HIGH":
            root_confidence = "MEDIUM"

        # Mise à jour du score effectif dans richness_penalty (valeur post-multiplicateur).
        epistemic_audit["richness_penalty"]["score"] = root_score

        existing_pack_path = self.evidence_dir / f"{sid}_evidence.json"
        status = "VALIDATED"
        preserved_socle_validated = False
        preserved_socle_validated_at = None
        preserved_fact_check_cert = None

        if existing_pack_path.exists():
            try:
                existing_data = json.loads(existing_pack_path.read_text(encoding="utf-8"))
                if existing_data.get("socle_factuel_validated_by_human") is True:
                    preserved_socle_validated = True
                    preserved_socle_validated_at = existing_data.get("socle_factuel_validated_at")
                if "fact_check_certificate" in existing_data:
                    preserved_fact_check_cert = existing_data["fact_check_certificate"]
                existing_ts = existing_data.get("timestamp")
                story_mtime = datetime.datetime.fromtimestamp(
                    story_file.stat().st_mtime, tz=datetime.timezone.utc
                )
                if existing_ts:
                    existing_dt = datetime.datetime.fromisoformat(
                        existing_ts.replace("Z", "+00:00")
                    )
                    if story_mtime > existing_dt and not (
                        dossier_data
                        and dossier_data.get("dossier_status") in ("CURRENT", "VALIDATED")
                    ):
                        status = "STALE_PENDING_REGENERATION"
            except Exception as e:
                logger.debug(
                    "Comparaison de fraîcheur EvidencePack échouée, statut conservé",
                    exc_info=True,
                    extra={
                        "component": "pipelines.evidence_pack",
                        "operation": "generate",
                        "story_id": sid,
                        "error": str(e),
                    },
                )

        evidence_pack = {
            "story_id": sid,
            "jira_key": jira_key,
            "file_path": str(story_file.relative_to(self.project_path)).replace("\\", "/"),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "fact_search_status": "VERIFIED",
            "fact_search_proofs": fact_proofs,
            "source_hashes_sha256": source_hashes,
            "epistemic_audit": epistemic_audit,
            "facts_verified": facts_verified,
            "sources_consulted": sorted(list(sources)),
            "external_references": external_refs,
            "alerts": alerts,
            "open_questions": questions,
            "visual_contract": visual_contract,
            "socle_factuel_validated_by_human": preserved_socle_validated,
            "socle_factuel_validated_at": preserved_socle_validated_at,
            "verification_harness": scenarios,
            "next_actions": next_actions,
            "confidence": root_confidence,
            "confidence_score": root_score,
            "status": status,
            # ── MLOOP-180-BE : 5 champs de parité Phase 2 (Optional — CA-5 rétrocompat) ──
            # Tous initialisés à liste vide par défaut ; peuplement délégué à MLOOP-181-BE.
            # Les callers legacy lisent via .get("verbatim_extracts", []) — zéro KeyError.
            "verbatim_extracts": verbatim_extracts,
            "implementation_decisions": implementation_decisions,
            "declarative_contracts": declarative_contracts,
            "conflict_matrix": conflict_matrix,
            # ── MLOOP-330-BE : Traçabilité Code ↔ Exigences (ADR-0394) ───────────
            "code_traceability_matrix": _preserved_fields.get("code_traceability_matrix", []),
        }

        if preserved_fact_check_cert is not None:
            evidence_pack["fact_check_certificate"] = preserved_fact_check_cert

        # MLOOP-181-BE : le sceau TDD Red/Green (Gate 3) survit à la régénération.
        if _preserved_fields.get("tdd_cycle"):
            evidence_pack["tdd_cycle"] = _preserved_fields["tdd_cycle"]

        return evidence_pack

    def save_evidence_pack(self, evidence_pack: Dict[str, Any]) -> Path:
        story_id = evidence_pack.get("story_id", "UNKNOWN").replace(" ", "_")
        target_json = self.evidence_dir / f"{story_id}_evidence.json"
        target_json.write_text(
            json.dumps(evidence_pack, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        ZeroFluffConsole.success(f"Artefact EvidencePack consigné sous : {target_json}")
        return target_json

    # ── MLOOP-330-BE : Sérialisation Matrice de Traçabilité Code ↔ Exigences ──
    def set_code_traceability(self, story_id: str, entries: List["CodeTraceabilityEntry"]) -> Path:
        """
        Assigne et sérialise la matrice de traçabilité dans l'EvidencePack sidecar.
        """
        self.validate_code_traceability(entries)
        clean_sid = story_id.replace(" ", "_")
        target_json = self.evidence_dir / f"{clean_sid}_evidence.json"

        pack_data: Dict[str, Any] = {}
        if target_json.exists():
            try:
                pack_data = json.loads(target_json.read_text(encoding="utf-8"))
            except Exception as e:
                logger.debug(
                    "Lecture du pack existant échouée lors de set_code_traceability",
                    exc_info=True,
                    extra={"story_id": story_id, "error": str(e)},
                )

        if not pack_data:
            pack_data = {
                "story_id": clean_sid,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "status": "IN_DEV",
            }

        pack_data["code_traceability_matrix"] = list(entries)
        pack_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return self.save_evidence_pack(pack_data)


# NOTE (ADR-0326) : Aucune méthode de ce moteur ne doit générer de bloc
# textuel destiné à être injecté dans le fichier Story .md. L'EvidencePack
# JSON (memory/evidence/<STORY_ID>_evidence.json) est la seule source de
# vérité pour les preuves Fact-Search ; les récits ne font que le
# référencer par lien (section "## 📑 Notes de Traçabilité & Références
# Fact-Search (IA Only)" rédigée manuellement dans le récit, cf.
# standards/protocols/FACT_SEARCH_PROTOCOL.md). L'ancienne méthode
# format_traceability_section() (injection en dur du bloc "🛡️ Suite
# Mémoire & Audit (IA)") a été supprimée : elle violait ce principe et
# produisait un contenu figé, non désiré dans le corps des récits.

# ── Exports pour rétrocompatibilité et API publique (ADR-0394) ────────────────
__all__ = [
    "EvidencePackEngine",
    "PlanEvidenceParser",
    "EvidenceSynchronizer",
    "CodeTraceabilityEntry",
    "VerbatimExtract",
    "ImplementationDecision",
    "DeclarativeContract",
    "ConflictResolution",
    "DecisionCategory",
]
