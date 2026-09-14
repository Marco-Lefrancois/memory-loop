# -*- coding: utf-8 -*-
"""
StructCheckEngine — Gatekeeper Structurel Read-Only (ADR-0338)

Vérifie la cohérence typographique et stylistique d'un récit mLoop
par comparaison avec le Gold Standard du projet.

7 checks :
  C1 — Hiérarchie des titres (pas de saut H2→H4 sans H3)
  C2 — Format des listes dans sections UX ('-' uniquement)
  C3 — Redondances bilingues dans titres H4
  C4 — Diff stylistique H3/H4 vs Gold Standard
  C5 — Séparateurs '---' entre sections H2 (Read-Only, sans auto-heal)
  C6 — Frontmatter YAML : champs obligatoires présents
  C7 — Titre H1 : format '# [JIRA-KEY] Titre métier'

Principes :
  - Read-Only : aucune modification de fichier.
  - Zéro Auto-Healing (contrairement à WikiFixAgent).
  - Réutilise les patterns regex établis dans le codebase mLoop.
"""

from __future__ import annotations

import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class StructViolation:
    """Représente un écart structurel détecté."""

    check_id: str  # ex: "C2"
    severity: str  # "BLOCKING" | "WARNING"
    message: str
    line_hint: Optional[int] = None  # numéro de ligne approximatif (1-indexed)

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.check_id}: {self.message}"


@dataclass
class StructCheckReport:
    """Résultat complet d'un audit structurel sur un fichier."""

    file: Path
    gold_standard: Optional[Path]
    passed: bool
    violations: list[StructViolation] = field(default_factory=list)

    @property
    def blocking_violations(self) -> list[StructViolation]:
        return [v for v in self.violations if v.severity == "BLOCKING"]

    @property
    def warnings(self) -> list[StructViolation]:
        return [v for v in self.violations if v.severity == "WARNING"]


# ─── Constantes ───────────────────────────────────────────────────────────────

# Champs YAML obligatoires dans le frontmatter d'une story mLoop
_REQUIRED_FM_FIELDS = {"id", "layer", "status", "type", "title"}

# Pattern de détection du frontmatter YAML (compatible avec les 4 variantes du codebase)
_FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Pattern de détection des titres Markdown (H1 à H6)
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

# Pattern de détection du titre H1 conforme : # Titre métier pur ou # [JIRA-KEY] Titre
_H1_VALID_PATTERN = re.compile(r"^#\s+([A-Za-zÀ-ÿ0-9\[\"'])", re.MULTILINE)

# Pattern de détection des listes avec '*' ou '+' (format interdit dans les sections UX)
_INVALID_LIST_PATTERN = re.compile(r"^[ \t]*[*+]\s+", re.MULTILINE)

# Pattern de détection des séparateurs '---' entre sections H2
_H2_PATTERN = re.compile(r"(?m)^(##\s+.+)$")

# Pattern de détection de redondance bilingue dans un titre H4
# Détecte : "#### N. Titre (Traduction)" où les mots entre parenthèses
# se recoupent sémantiquement avec le titre principal.
# Heuristique simplifiée : présence de parenthèses dans un titre H4
_H4_REDUNDANCY_PATTERN = re.compile(r"^####\s+.+\(.+\)\s*$", re.MULTILINE)

# Délimiteurs de la section "Interface et UX" (début et fin)
_UX_SECTION_START = re.compile(r"###\s+Interface\s+et\s+UX", re.IGNORECASE)
_NEXT_H2_OR_H3 = re.compile(r"^(?:##|###)\s+", re.MULTILINE)


# ─── Moteur Principal ─────────────────────────────────────────────────────────


class StructCheckEngine:
    """
    Gatekeeper structurel Read-Only pour les récits mLoop.

    Usage :
        engine = StructCheckEngine(project_path)
        report = engine.check_file(Path("backlog/stories/.../REC-011-FE.md"))
    """

    def __init__(self, project_path: Path) -> None:
        self.project_path = project_path

    # ── Point d'entrée public ──────────────────────────────────────────────────

    def check_file(self, target_file: Path, strict: bool = False) -> StructCheckReport:
        """
        Exécute les 7 checks sur un fichier de récit.

        Args:
            target_file : Chemin absolu ou relatif du fichier .md à auditer.
            strict      : Si True, les divergences H3/H4 sont BLOCKING (C4).

        Returns:
            StructCheckReport avec la liste complète des violations détectées.
        """
        try:
            content = target_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            violation = StructViolation(
                "C6", "BLOCKING", f"Impossible de lire le fichier : {e}"
            )
            return StructCheckReport(target_file, None, False, [violation])

        fm_data = self._parse_frontmatter(content)
        gold_std_path = self._resolve_gold_standard(fm_data, strict)
        gold_content = (
            gold_std_path.read_text(encoding="utf-8") if gold_std_path else None
        )

        violations: list[StructViolation] = []
        violations += self._check_c1_heading_hierarchy(content)
        violations += self._check_c2_list_format(content)
        violations += self._check_c3_title_redundancy(content)
        violations += self._check_c4_gold_standard_diff(content, gold_content, strict)
        violations += self._check_c5_h2_separators(content)
        violations += self._check_c6_frontmatter_completeness(fm_data)
        violations += self._check_c7_h1_format(content)
        violations += self._check_c8_anti_goodhart_scenarios(content)
        violations += self._check_c9_fact_dossier_presence(
            target_file, fm_data, content, strict
        )
        violations += self._check_c10_anti_ephemeral_rules(content)
        violations += self._check_c11_rule_engine_integration(content)

        passed = all(v.severity != "BLOCKING" for v in violations)
        return StructCheckReport(target_file, gold_std_path, passed, violations)

    # ── Helpers internes ──────────────────────────────────────────────────────

    def _parse_frontmatter(self, content: str) -> dict:
        """Extrait et parse le frontmatter YAML. Retourne {} si absent ou invalide."""
        match = _FM_PATTERN.match(content)
        if not match:
            # Fallback : tentative avec split (pattern alternatif du codebase)
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    return yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    return {}
            return {}
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}

    def _resolve_gold_standard(self, fm_data: dict, strict: bool) -> Optional[Path]:
        """
        Résout le chemin du Gold Standard selon la logique de fallback :
        1. Chemin direct si ref pointe vers un fichier existant (absolu ou relatif)
        2. gold_standard_ref dans le frontmatter → glob dans backlog/stories/ (story pilote locale)
        3. Chercher dans standards/blueprints/
        4. Fallback universel : standards/blueprints/story_template.md
        5. Si strict et introuvable → None (C4 gérera la violation BLOCKING)
        """
        ref = fm_data.get("gold_standard_ref", "")
        if ref and str(ref).strip():
            ref_str = str(ref).strip()
            # 1. Vérification chemin direct (relatif au repo ou absolu)
            direct_p = Path(ref_str)
            if direct_p.exists() and direct_p.is_file():
                return direct_p
            abs_p = Path("C:/Memory Loop") / ref_str
            if abs_p.exists() and abs_p.is_file():
                return abs_p

            ref_name = direct_p.name
            # 2. Chercher dans le backlog du projet (story pilote locale)
            candidates = list(self.project_path.glob(f"backlog/stories/**/{ref_name}"))
            if candidates:
                return candidates[0]
            # 3. Chercher dans les blueprints du framework
            bp_dir = Path("standards") / "blueprints"
            if (bp_dir / ref_name).exists():
                return bp_dir / ref_name
            # Non trouvé en mode strict → C4 signalera la violation
            if strict:
                return None

        # Fallback universel : le gabarit standard auto-portant
        template = Path("standards") / "blueprints" / "story_template.md"
        if template.exists():
            return template
        # Chemin absolu depuis le répertoire de travail habituel de mLoop
        template_abs = Path("C:/Memory Loop/standards/blueprints/story_template.md")
        if template_abs.exists():
            return template_abs
        return None

    # ── Check C1 : Hiérarchie des titres ─────────────────────────────────────

    def _check_c1_heading_hierarchy(self, content: str) -> list[StructViolation]:
        """
        C1 : Détecte les sauts de niveau de titre.
        Un H4 ne peut apparaître qu'après un H3, un H3 qu'après un H2, etc.
        """
        violations = []
        headings = _HEADING_PATTERN.findall(content)
        if not headings:
            return violations

        prev_level = 1  # H1 est toujours le niveau de départ
        for i, (hashes, title) in enumerate(headings):
            level = len(hashes)
            # On ignore le H1 initial et les retours à des niveaux supérieurs
            if level > prev_level + 1:
                violations.append(
                    StructViolation(
                        check_id="C1",
                        severity="BLOCKING",
                        message=(
                            f"Saut de niveau de titre détecté : H{prev_level} → H{level} "
                            f"(titre : '{title.strip()}') sans niveau intermédiaire H{prev_level + 1}. "
                            "La hiérarchie doit être continue."
                        ),
                    )
                )
            prev_level = level
        return violations

    # ── Check C2 : Format des listes dans sections UX ─────────────────────────

    def _check_c2_list_format(self, content: str) -> list[StructViolation]:
        """
        C2 : Dans le bloc '### Interface et UX', les listes doivent utiliser '-' uniquement.
        Les listes avec '*' ou '+' sont BLOCKING.
        """
        violations = []
        # Localiser le début de la section "Interface et UX"
        ux_match = _UX_SECTION_START.search(content)
        if not ux_match:
            return violations  # Pas de section UX → check non applicable

        ux_start = ux_match.start()

        # Trouver la fin de la section UX :
        # soit le prochain H2 (##), soit le prochain H3 (###) qui n'est pas "Interface et UX"
        # On cherche dans le reste du contenu après la ligne de début de section UX
        search_from = ux_start + len(ux_match.group())
        next_section_match = re.search(
            r"(?m)^(?:##\s+|###\s+(?!Interface\s+et\s+UX))", content[search_from:]
        )
        ux_end = (
            (search_from + next_section_match.start())
            if next_section_match
            else len(content)
        )
        ux_content = content[ux_start:ux_end]

        # Détecter les listes avec '*' ou '+' dans la section UX
        invalid_matches = _INVALID_LIST_PATTERN.finditer(ux_content)
        for match in invalid_matches:
            # Calculer le numéro de ligne approximatif dans le fichier original
            line_in_ux = ux_content[: match.start()].count("\n") + 1
            line_in_file = content[:ux_start].count("\n") + line_in_ux
            char = match.group().strip()[0]  # '*' ou '+'
            violations.append(
                StructViolation(
                    check_id="C2",
                    severity="BLOCKING",
                    message=(
                        f"Liste avec '{char}' détectée dans la section '### Interface et UX' "
                        f"(ligne ≈{line_in_file}). Utiliser uniquement '-' (tiret) "
                        "pour les listes dans les sections UX (standard REC-015-FE)."
                    ),
                    line_hint=line_in_file,
                )
            )
            break  # Une seule violation par fichier suffit pour orienter la correction

        return violations

    # ── Check C3 : Redondances bilingues dans titres H4 ──────────────────────

    def _check_c3_title_redundancy(self, content: str) -> list[StructViolation]:
        """
        C3 : Détecte les redondances bilingues dans les titres H4.
        Heuristique : titre H4 contenant des parenthèses avec mots de 3+ caractères.
        Ex: '#### 1. En-tête (Header)' → WARNING
        """
        violations = []
        h4_redundancy_matches = _H4_REDUNDANCY_PATTERN.finditer(content)
        for match in h4_redundancy_matches:
            title_text = match.group().strip()
            # Extraire le contenu entre parenthèses
            paren_match = re.search(r"\(([^)]+)\)", title_text)
            if not paren_match:
                continue
            paren_content = paren_match.group(1)
            # Extraire les mots significatifs (3+ caractères) du titre et des parenthèses
            title_words = set(
                re.findall(r"\b\w{3,}\b", title_text[: paren_match.start()].lower())
            )
            paren_words = set(re.findall(r"\b\w{3,}\b", paren_content.lower()))
            # Chercher des recoupements sémantiques (mots communs ou sous-chaînes)
            has_overlap = any(
                pw in tw or tw in pw for pw in paren_words for tw in title_words
            )
            if has_overlap or len(paren_words) > 0:
                line_num = content[: match.start()].count("\n") + 1
                violations.append(
                    StructViolation(
                        check_id="C3",
                        severity="WARNING",
                        message=(
                            f"Redondance potentielle détectée dans le titre H4 (ligne {line_num}) : "
                            f"'{title_text}'. "
                            "Les parenthèses dans les titres H4 peuvent créer une redondance bilingue. "
                            "Exemple corrigé : '#### 1. En-tête' au lieu de '#### 1. En-tête (Header)'."
                        ),
                        line_hint=line_num,
                    )
                )
        return violations

    # ── Check C4 : Diff stylistique vs Blueprint de Référence ─────────────────

    def _check_c4_gold_standard_diff(
        self, content: str, gold_content: Optional[str], strict: bool
    ) -> list[StructViolation]:
        """
        C4 : Compare les titres H3/H4 du récit avec ceux du gabarit blueprint (story_template.md).
        En mode strict, l'absence de gabarit résolu est BLOCKING.
        """
        violations = []

        if gold_content is None:
            if strict:
                violations.append(
                    StructViolation(
                        check_id="C4",
                        severity="BLOCKING",
                        message=(
                            "Mode --strict activé : aucun gabarit blueprint résolu. "
                            "Vérifier la présence de standards/blueprints/story_template.md."
                        ),
                    )
                )
            return violations

        # Titres canoniques reconnus par le standard mLoop (ADR-0366)
        canonical_titles = {
            "spécifications de l'interface",
            "spécifications de l'interface & ux",
            "spécifications de l'interface et ux",
            "liste call to actions",
            "parcours interactif",
            "parcours interactif & api",
            "parcours interactif (frontend / déclencheurs ui)",
            "parcours interactif (frontend / déclencheurs)",
            "contrats d'échange api (backend / services)",
            "contrats d'échange api",
            "opérations métier & logique backend",
            "spécifications métier",
            "spécifications métier backend",
            "matrice des réponses http & filtres métier",
            "navigation",
            "états d'interaction",
            "preuves amont & traçabilité factuelle",
            "spécifications & modèles de données ssot",
            "handoff technique aval & référentiel dev",
            "paquet openspec",
            "paquet openspec (handoff développeur)",
            "spécifications openspec",
            "handoff technique openspec",
            "navigation / contrats d'échange api",
            "in-scope",
            "out-of-scope",
            "contexte métier",
            "maquettes ssot",
            "maquettes",
        }

        def _normalize_title(t: str) -> str:
            # Nettoyer balises Markdown et notes explicatives entre parenthèses
            cleaned = re.sub(r"[*_]", "", t)
            cleaned = re.sub(r"\s*\([^)]*\)", "", cleaned)
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
            return cleaned.strip().lower()

        # Extraire les titres H3/H4 normalisés des deux documents
        def _extract_section_titles(text: str) -> set[str]:
            titles = set()
            for hashes, title in _HEADING_PATTERN.findall(text):
                h_level = len(hashes)
                norm = _normalize_title(title)
                if not norm:
                    continue
                if h_level == 3:
                    titles.add(norm)
                elif h_level == 4:
                    # Ne retenir en H4 que les titres structurels/fixes (non dynamiques/numérotés)
                    if not re.match(r"^\d+[\.\)]", title.strip()) and not re.match(r"^\[.*\]$", norm):
                        titles.add(norm)
            return titles

        story_titles = _extract_section_titles(content)
        gold_titles = _extract_section_titles(gold_content)

        # Détecter les titres du récit qui ne sont ni dans le Gold Standard ni dans les titres canoniques
        raw_divergent = story_titles - gold_titles
        divergent = {t for t in raw_divergent if t not in canonical_titles}
        if divergent and gold_titles:
            severity = "BLOCKING" if strict else "WARNING"
            violations.append(
                StructViolation(
                    check_id="C4",
                    severity=severity,
                    message=(
                        f"{len(divergent)} titre(s) H3/H4 absent(s) du gabarit blueprint : "
                        f"{', '.join(sorted(divergent)[:5])}{'...' if len(divergent) > 5 else ''}. "
                        "Vérifier l'alignement stylistique avec standards/blueprints/story_template.md."
                    ),
                )
            )
        return violations

    # ── Check C5 : Séparateurs '---' entre H2 (Read-Only) ────────────────────

    def _check_c5_h2_separators(self, content: str) -> list[StructViolation]:
        """
        C5 : Vérifie la présence de séparateurs '---' avant chaque section H2
        (sauf le premier). Read-Only : aucune modification du fichier.
        """
        violations = []
        h2_matches = list(_H2_PATTERN.finditer(content))
        if len(h2_matches) <= 1:
            return violations

        for match in h2_matches[1:]:  # Ignorer le premier H2
            pos = match.start()
            # Fenêtre de 30 caractères précédant le H2
            prefix_window = content[max(0, pos - 30) : pos]
            if "---" not in prefix_window:
                line_num = content[:pos].count("\n") + 1
                header_text = match.group(1).strip()
                violations.append(
                    StructViolation(
                        check_id="C5",
                        severity="WARNING",
                        message=(
                            f"Séparateur '---' manquant avant la section H2 "
                            f"'{header_text}' (ligne {line_num}). "
                            "ADR-0303 exige un séparateur entre chaque section H2. "
                            "Exécuter 'python src/swarm.py sync' pour l'auto-correction."
                        ),
                        line_hint=line_num,
                    )
                )
        return violations

    # ── Check C6 : Frontmatter YAML ──────────────────────────────────────────

    def _check_c6_frontmatter_completeness(
        self, fm_data: dict
    ) -> list[StructViolation]:
        """
        C6 : Vérifie que le frontmatter YAML contient tous les champs obligatoires.
        """
        violations = []

        if not fm_data:
            violations.append(
                StructViolation(
                    check_id="C6",
                    severity="BLOCKING",
                    message=(
                        "Frontmatter YAML absent ou invalide. "
                        "Chaque récit mLoop doit commencer par un bloc '---' YAML "
                        "avec les champs : "
                        + ", ".join(sorted(_REQUIRED_FM_FIELDS))
                        + "."
                    ),
                )
            )
            return violations

        missing_fields = _REQUIRED_FM_FIELDS - set(fm_data.keys())
        if missing_fields:
            violations.append(
                StructViolation(
                    check_id="C6",
                    severity="BLOCKING",
                    message=(
                        f"Champ(s) YAML obligatoire(s) manquant(s) : "
                        f"{', '.join(sorted(missing_fields))}. "
                        "Référence : standards/blueprints/story_template.md."
                    ),
                )
            )
        return violations

    # ── Check C7 : Format du titre H1 ────────────────────────────────────────

    def _check_c7_h1_format(self, content: str) -> list[StructViolation]:
        """
        C7 : Vérifie que le titre H1 est présent et commence par un titre métier valide.
        """
        violations = []
        if not _H1_VALID_PATTERN.search(content):
            violations.append(
                StructViolation(
                    check_id="C7",
                    severity="WARNING",
                    message=(
                        "Titre H1 non conforme au standard mLoop. "
                        "Format attendu : '# Titre Métier Pur' ou '# [JIRA-KEY] Titre Métier Pur'."
                    ),
                    line_hint=1,
                )
            )
        return violations

    # ── Check C8 : Anti-Goodhart & Complétude Gherkin (4 Piliers) ────────────

    def _check_c8_anti_goodhart_scenarios(self, content: str) -> list[StructViolation]:
        """
        C8 : DualConstraintPenaltyMatrix (Blindspot #5 / Goodhart Hijacking).
        Vérifie que les scénarios de test couvrent les 4 piliers Gherkin
        (Nominal, Exceptions, Résilience, UX/Accessibilité) et qu'aucune suppression
        artificielle d'exceptions n'a été effectuée pour raccourcir le récit.
        """
        violations = []
        scenarios_match = re.search(r"(?i)##\s+Scénarios\s+de\s+test", content)
        if not scenarios_match:
            return violations

        scenarios_content = content[scenarios_match.start() :]

        # Détection des piliers Gherkin
        has_nominal = bool(
            re.search(
                r"(?i)(nominal|cas\s+passant|happy\s+path|pilier\s+1)",
                scenarios_content,
            )
        )
        has_exceptions = bool(
            re.search(
                r"(?i)(exception|erreur|cas\s+d'erreur|échec|invalide|pilier\s+2)",
                scenarios_content,
            )
        )
        has_resilience = bool(
            re.search(
                r"(?i)(résilience|resilience|timeout|réseau|offline|hors\s+ligne|dégradé|pilier\s+3)",
                scenarios_content,
            )
        )
        has_ux = bool(
            re.search(
                r"(?i)(ux|accessibilité|accessibilite|aria|contraste|vide|empty\s+state|pilier\s+4)",
                scenarios_content,
            )
        )

        missing_pillars = []
        if not has_nominal:
            missing_pillars.append("1. Nominal (Happy path)")
        if not has_exceptions:
            missing_pillars.append("2. Exceptions (Cas d'erreur)")
        if not has_resilience:
            missing_pillars.append("3. Résilience (Réseau / Timeout / Mode dégradé)")
        if not has_ux:
            missing_pillars.append("4. UX / Accessibilité / État vide")

        if missing_pillars:
            violations.append(
                StructViolation(
                    check_id="C8",
                    severity="WARNING" if len(missing_pillars) <= 2 else "BLOCKING",
                    message=(
                        f"Couverture Gherkin incomplète (Anti-Goodhart Guardrail) : "
                        f"Pilier(s) manquant(s) dans '## Scénarios de test' : {', '.join(missing_pillars)}. "
                        "Chaque récit mLoop doit couvrir les 4 piliers Gherkin (story_template.md)."
                    ),
                    line_hint=scenarios_content[:100].count("\n") + 1,
                )
            )

        return violations

    # ── Check C9 : Présence et Intégrité du Dossier de Preuves Documentaires ───

    def _check_c9_fact_dossier_presence(
        self, target_file: Path, fm_data: dict, content: str, strict: bool
    ) -> list[StructViolation]:
        """
        C9 : Vérifie la présence et l'intégrité du Dossier de Preuves Documentaires.
        - Si un lien vers un _fact_dossier.md est présent dans ## Références,
          vérifie que le fichier cible existe physiquement (BLOCKING si lien brisé).
        - Si la story est en statut READY_FOR_DEV ou READY_FOR_GROOMING avec
          fact_dossier_required: true (ou en mode strict), vérifie qu'un dossier existe
          sous memory/evidence/<STORY_ID>_fact_dossier.md.
        """
        violations = []
        story_id = fm_data.get("id") or target_file.stem
        status = fm_data.get("status", "")

        # 1. Vérification des liens de dossier dans le texte
        dossier_links = re.findall(
            r"\[([^\]]*fact_dossier[^\]]*)\]\(([^)]+)\)", content
        )
        for link_text, link_target in dossier_links:
            if link_target.startswith("http://") or link_target.startswith("https://"):
                continue
            target_path = (target_file.parent / link_target).resolve()
            if not target_path.exists():
                violations.append(
                    StructViolation(
                        check_id="C9",
                        severity="BLOCKING",
                        message=(
                            f"Lien vers le Dossier de Preuves Documentaires brisé : '{link_target}'. "
                            f"Le fichier cible n'existe pas sur le disque ({target_path})."
                        ),
                        line_hint=1,
                    )
                )

        # 2. Vérification d'obligation pour nouveaux récits ou mode strict
        requires_dossier = fm_data.get("fact_dossier_required", False) or (
            strict and status in ("READY_FOR_DEV", "READY_FOR_GROOMING")
        )
        if requires_dossier:
            evidence_dir = self.project_path / "memory" / "evidence"
            dossier_candidates = (
                list(evidence_dir.glob(f"**/{story_id}_fact_dossier.md"))
                if evidence_dir.exists()
                else []
            )
            has_valid_link = any(
                (target_file.parent / lt).resolve().exists() for _, lt in dossier_links
            )
            if not dossier_candidates and not has_valid_link:
                violations.append(
                    StructViolation(
                        check_id="C9",
                        severity="BLOCKING" if strict else "WARNING",
                        message=(
                            f"Dossier de Preuves Documentaires manquant pour {story_id}. "
                            f"Conformément à DOSSIER_DE_PREUVES_PROTOCOL.md, un fichier "
                            f"memory/evidence/{story_id}_fact_dossier.md doit être produit avant dev."
                        ),
                        line_hint=1,
                    )
                )

        return violations

    # ── Check C10 : Validation des identifiants normés dans les Règles d'affaires ───

    def _check_c10_anti_ephemeral_rules(self, content: str) -> list[StructViolation]:
        """
        C10 : Vérifie la conformité des règles d'affaires selon ADR-0301 (Amendement 2026-09).
        Chaque règle doit porter :
        - Soit un identifiant formel standardisé suivi du nom : '- **RM-XXX [Nom de la Règle]** :'
        - Soit un titre métier pur en gras : '- **[Nom de la Règle]** :'
        Les préfixes éphémères ad-hoc (RM-TEMP, RM-TODO, WIP) ou les identifiants sans titre
        métier sont interdits (BLOCKING).
        """
        violations = []
        rules_match = re.search(r"(?i)##\s+Règles\s+d['’]affaires", content)
        if not rules_match:
            return violations

        rules_content = content[rules_match.start() :]
        next_h2 = re.search(r"(?m)^##\s+", rules_content[4:])
        if next_h2:
            rules_content = rules_content[: next_h2.start() + 4]

        # 1. Détection des tags temporaires / placeholders interdits
        forbidden_matches = re.findall(
            r"(?m)^\s*[-*]\s*\*\*\s*(?:RM-(?:TEMP|TODO|FIXME|WIP)|TODO|FIXME|WIP)\b",
            rules_content,
            re.IGNORECASE,
        )
        if forbidden_matches:
            bad_prefixes = ", ".join(set(m.strip() for m in forbidden_matches))
            violations.append(
                StructViolation(
                    check_id="C10",
                    severity="BLOCKING",
                    message=(
                        f"Identifiants éphémères interdits dans les règles d'affaires : {bad_prefixes}. "
                        "Conformément à ADR-0301 (Amendement 2026-09), utiliser le standard "
                        "'- **RM-XXX [Titre Métier Pur]** :' ou '- **[Titre Métier Pur]** :'."
                    ),
                    line_hint=1,
                )
            )

        # 2. Détection d'identifiants sans titre métier associé (ex: '- **RM-101** :')
        bare_id_matches = re.findall(
            r"(?m)^\s*[-*]\s*\*\*\s*RM-[A-Z0-9-]+\s*\*\*\s*:",
            rules_content,
        )
        if bare_id_matches:
            bad_bare = ", ".join(set(m.strip() for m in bare_id_matches))
            violations.append(
                StructViolation(
                    check_id="C10",
                    severity="BLOCKING",
                    message=(
                        f"Règle d'affaires sans titre fonctionnel : {bad_bare}. "
                        "Conformément à ADR-0301 (Amendement 2026-09), un identifiant RM-XXX "
                        "doit être immédiatement suivi du nom de la règle entre crochets : "
                        "'- **RM-XXX [Nom de la Règle]** :'."
                    ),
                    line_hint=1,
                )
            )

        return violations

    # ── Check C11 : Intégration Dynamique RuleEngine (ADR-0328 §2.2) ─────────

    def _check_c11_rule_engine_integration(self, content: str) -> list[StructViolation]:
        """
        C11 : Charge les règles déclaratives `validation_rules` du frontmatter
        YAML des ADRs (`docs/01-architecture/` du projet cible) et les exécute
        sur le contenu du récit courant, exactement comme le fait déjà WikiFix
        (`wikifix.py` §4.7). ADR-0328 §2.2 promet explicitement que ces règles
        soient « injectées dynamiquement dans struct-check, vibe-check,
        validate » — ce check comble le branchement manquant côté struct-check.

        Absence de docs/01-architecture/ ou de règles chargées -> aucune
        violation, jamais d'exception (dégradation gracieuse).
        """
        violations: list[StructViolation] = []
        try:
            from src.core.rule_engine import RuleEngine

            adr_dir = self.project_path / "docs" / "01-architecture"
            if not adr_dir.exists():
                return violations

            rule_engine = RuleEngine()
            rule_engine.load_from_adr_dir(adr_dir)
            rule_violations = rule_engine.validate_all(
                content, target="backlog_stories"
            )
            for rv in rule_violations:
                violations.append(
                    StructViolation(
                        check_id="C11",
                        severity=rv.severity,
                        message=f"[{rv.adr_id}] {rv.message}",
                        line_hint=1,
                    )
                )
        except Exception:
            # Dégradation gracieuse : un ADR malformé ne doit jamais faire
            # échouer l'audit structurel complet.
            pass
        return violations
