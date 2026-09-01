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
    check_id: str           # ex: "C2"
    severity: str           # "BLOCKING" | "WARNING"
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
            strict      : Si True, l'absence de gold_standard_ref est BLOCKING (C4).

        Returns:
            StructCheckReport avec la liste complète des violations détectées.
        """
        try:
            content = target_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            violation = StructViolation("C6", "BLOCKING", f"Impossible de lire le fichier : {e}")
            return StructCheckReport(target_file, None, False, [violation])

        fm_data = self._parse_frontmatter(content)
        gold_std_path = self._resolve_gold_standard(fm_data, strict)
        gold_content = gold_std_path.read_text(encoding="utf-8") if gold_std_path else None

        violations: list[StructViolation] = []
        violations += self._check_c1_heading_hierarchy(content)
        violations += self._check_c2_list_format(content)
        violations += self._check_c3_title_redundancy(content)
        violations += self._check_c4_gold_standard_diff(content, gold_content, strict)
        violations += self._check_c5_h2_separators(content)
        violations += self._check_c6_frontmatter_completeness(fm_data)
        violations += self._check_c7_h1_format(content)
        violations += self._check_c8_anti_goodhart_scenarios(content)

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
        1. gold_standard_ref dans le frontmatter → glob dans backlog/stories/
        2. Fallback : standards/blueprints/story_template.md
        3. Si strict et introuvable → None (C4 gérera la violation BLOCKING)
        """
        ref = fm_data.get("gold_standard_ref", "")
        if ref and str(ref).strip():
            ref_name = Path(str(ref).strip()).name
            # Chercher dans le backlog du projet
            candidates = list(self.project_path.glob(f"backlog/stories/**/{ref_name}"))
            if candidates:
                return candidates[0]
            # Chercher dans les gold_standards du framework
            gs_dir = Path("standards") / "gold_standards"
            if (gs_dir / ref_name).exists():
                return gs_dir / ref_name
            # Non trouvé en mode strict → C4 signalera la violation
            if strict:
                return None

        # Fallback universel : le gabarit standard
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
                violations.append(StructViolation(
                    check_id="C1",
                    severity="BLOCKING",
                    message=(
                        f"Saut de niveau de titre détecté : H{prev_level} → H{level} "
                        f"(titre : '{title.strip()}') sans niveau intermédiaire H{prev_level + 1}. "
                        "La hiérarchie doit être continue."
                    ),
                ))
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
        next_section_match = re.search(r"(?m)^(?:##\s+|###\s+(?!Interface\s+et\s+UX))", content[search_from:])
        ux_end = (search_from + next_section_match.start()) if next_section_match else len(content)
        ux_content = content[ux_start:ux_end]

        # Détecter les listes avec '*' ou '+' dans la section UX
        invalid_matches = _INVALID_LIST_PATTERN.finditer(ux_content)
        for match in invalid_matches:
            # Calculer le numéro de ligne approximatif dans le fichier original
            line_in_ux = ux_content[:match.start()].count("\n") + 1
            line_in_file = content[:ux_start].count("\n") + line_in_ux
            char = match.group().strip()[0]  # '*' ou '+'
            violations.append(StructViolation(
                check_id="C2",
                severity="BLOCKING",
                message=(
                    f"Liste avec '{char}' détectée dans la section '### Interface et UX' "
                    f"(ligne ≈{line_in_file}). Utiliser uniquement '-' (tiret) "
                    "pour les listes dans les sections UX (standard REC-015-FE)."
                ),
                line_hint=line_in_file,
            ))
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
            title_words = set(re.findall(r"\b\w{3,}\b", title_text[:paren_match.start()].lower()))
            paren_words = set(re.findall(r"\b\w{3,}\b", paren_content.lower()))
            # Chercher des recoupements sémantiques (mots communs ou sous-chaînes)
            has_overlap = any(
                pw in tw or tw in pw
                for pw in paren_words
                for tw in title_words
            )
            if has_overlap or len(paren_words) > 0:
                line_num = content[:match.start()].count("\n") + 1
                violations.append(StructViolation(
                    check_id="C3",
                    severity="WARNING",
                    message=(
                        f"Redondance potentielle détectée dans le titre H4 (ligne {line_num}) : "
                        f"'{title_text}'. "
                        "Les parenthèses dans les titres H4 peuvent créer une redondance bilingue. "
                        "Exemple corrigé : '#### 1. En-tête' au lieu de '#### 1. En-tête (Header)'."
                    ),
                    line_hint=line_num,
                ))
        return violations

    # ── Check C4 : Diff stylistique vs Gold Standard ──────────────────────────

    def _check_c4_gold_standard_diff(
        self, content: str, gold_content: Optional[str], strict: bool
    ) -> list[StructViolation]:
        """
        C4 : Compare les titres H3/H4 du récit avec ceux du Gold Standard.
        En mode strict, l'absence de Gold Standard est BLOCKING.
        """
        violations = []

        if gold_content is None:
            if strict:
                violations.append(StructViolation(
                    check_id="C4",
                    severity="BLOCKING",
                    message=(
                        "Mode --strict activé : aucun Gold Standard résolu "
                        "(gold_standard_ref absent ou fichier introuvable). "
                        "Renseigner le champ 'gold_standard_ref' dans le frontmatter YAML."
                    ),
                ))
            return violations

        # Extraire les titres H3/H4 des deux documents
        def _extract_section_titles(text: str) -> set[str]:
            return {
                title.strip().lower()
                for hashes, title in _HEADING_PATTERN.findall(text)
                if len(hashes) in (3, 4)
            }

        story_titles = _extract_section_titles(content)
        gold_titles = _extract_section_titles(gold_content)

        # Détecter les titres du récit qui ne sont pas dans le Gold Standard
        # (heuristique : divergence stylistique potentielle, pas une erreur formelle)
        divergent = story_titles - gold_titles
        if divergent and gold_titles:
            severity = "BLOCKING" if strict else "WARNING"
            violations.append(StructViolation(
                check_id="C4",
                severity=severity,
                message=(
                    f"{len(divergent)} titre(s) H3/H4 absent(s) du Gold Standard : "
                    f"{', '.join(sorted(divergent)[:5])}{'...' if len(divergent) > 5 else ''}. "
                    "Vérifier l'alignement stylistique avec le récit de référence."
                ),
            ))
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
            prefix_window = content[max(0, pos - 30):pos]
            if "---" not in prefix_window:
                line_num = content[:pos].count("\n") + 1
                header_text = match.group(1).strip()
                violations.append(StructViolation(
                    check_id="C5",
                    severity="WARNING",
                    message=(
                        f"Séparateur '---' manquant avant la section H2 "
                        f"'{header_text}' (ligne {line_num}). "
                        "ADR-0303 exige un séparateur entre chaque section H2. "
                        "Exécuter 'python src/swarm.py sync' pour l'auto-correction."
                    ),
                    line_hint=line_num,
                ))
        return violations

    # ── Check C6 : Frontmatter YAML ──────────────────────────────────────────

    def _check_c6_frontmatter_completeness(self, fm_data: dict) -> list[StructViolation]:
        """
        C6 : Vérifie que le frontmatter YAML contient tous les champs obligatoires.
        """
        violations = []

        if not fm_data:
            violations.append(StructViolation(
                check_id="C6",
                severity="BLOCKING",
                message=(
                    "Frontmatter YAML absent ou invalide. "
                    "Chaque récit mLoop doit commencer par un bloc '---' YAML "
                    "avec les champs : " + ", ".join(sorted(_REQUIRED_FM_FIELDS)) + "."
                ),
            ))
            return violations

        missing_fields = _REQUIRED_FM_FIELDS - set(fm_data.keys())
        if missing_fields:
            violations.append(StructViolation(
                check_id="C6",
                severity="BLOCKING",
                message=(
                    f"Champ(s) YAML obligatoire(s) manquant(s) : "
                    f"{', '.join(sorted(missing_fields))}. "
                    "Référence : standards/blueprints/story_template.md."
                ),
            ))
        return violations

    # ── Check C7 : Format du titre H1 ────────────────────────────────────────

    def _check_c7_h1_format(self, content: str) -> list[StructViolation]:
        """
        C7 : Vérifie que le titre H1 est présent et commence par un titre métier valide.
        """
        violations = []
        if not _H1_VALID_PATTERN.search(content):
            violations.append(StructViolation(
                check_id="C7",
                severity="WARNING",
                message=(
                    "Titre H1 non conforme au standard mLoop. "
                    "Format attendu : '# Titre Métier Pur' ou '# [JIRA-KEY] Titre Métier Pur'."
                ),
                line_hint=1,
            ))
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

        scenarios_content = content[scenarios_match.start():]
        
        # Détection des piliers Gherkin
        has_nominal = bool(re.search(r"(?i)(nominal|cas\s+passant|happy\s+path|pilier\s+1)", scenarios_content))
        has_exceptions = bool(re.search(r"(?i)(exception|erreur|cas\s+d'erreur|échec|invalide|pilier\s+2)", scenarios_content))
        has_resilience = bool(re.search(r"(?i)(résilience|resilience|timeout|réseau|offline|hors\s+ligne|dégradé|pilier\s+3)", scenarios_content))
        has_ux = bool(re.search(r"(?i)(ux|accessibilité|accessibilite|aria|contraste|vide|empty\s+state|pilier\s+4)", scenarios_content))

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
            violations.append(StructViolation(
                check_id="C8",
                severity="WARNING" if len(missing_pillars) <= 2 else "BLOCKING",
                message=(
                    f"Couverture Gherkin incomplète (Anti-Goodhart Guardrail) : "
                    f"Pilier(s) manquant(s) dans '## Scénarios de test' : {', '.join(missing_pillars)}. "
                    "Chaque récit mLoop doit couvrir les 4 piliers Gherkin (story_template.md)."
                ),
                line_hint=scenarios_content[:100].count("\n") + 1
            ))

        return violations
