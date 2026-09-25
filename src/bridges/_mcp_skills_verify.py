"""
src/bridges/_mcp_skills_verify.py — Budget de démarrage & trousse de vérification (MLOOP-214-BE).

Deux métriques contractuelles du récit
([`Projects/mLoop/backlog/stories/MLOOP-214-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-214-BE.md))
sous forme d'API déterministes :

- **Budget de démarrage mesuré** — cumul en jetons du fichier de règles
  principales (``AGENTS.md``) et des règles permanentes
  (``.agents/rules/*.md``), mesuré **pour chacun des deux canaux d'exposition**
  (``namespace`` et ``legacy``) face au plafond macro Q4 de 15 000 jetons,
  via l'estimateur SSOT ``SkillDoctor.estimate_tokens`` ;
- **Trousse de vérification des compétences** — battery de contrôles
  déterministes du pont (annonce, registre, inventaire local, entrées typées,
  manifestes, sécurité par échec bloqué, budget, lecture < 100 ms, repli
  partageant la découverte unique, refus explicites, hiérarchie, conflits,
  absence d'engloutissement d'exception) retournant un taux de réussite.

La trousse est appelée par la suite de tests du récit ; elle sauvegarde et
restaure l'état de négociation du pont, aucun fichier n'est écrit.
"""

from __future__ import annotations

import ast
import logging
import time
from pathlib import Path
from typing import Any, Callable

from src.bridges import mcp_resources, mcp_skills
from src.bridges._mcp_protocol_core import KNOWN_METHODS
from src.bridges._mcp_skills_rules import HIERARCHY, find_conflicts, load_permanent_rules
from src.pipelines.skill_doctor import SkillDoctor

logger = logging.getLogger(__name__)

BOOT_TOKEN_BUDGET = 15_000
EXPOSITION_CHANNELS: tuple[str, ...] = ("namespace", "legacy")
MAIN_RULES_FILE = "AGENTS.md"
RULES_PATTERN = ".agents/rules/*.md"
EXPECTED_HIERARCHY: tuple[str, ...] = ("permanent_rule", "loaded_skill", "main_rules_file")
# Modules du pont dont le silence d'exception est interdit (ADR-0369).
GUARDED_MODULES: tuple[str, ...] = (
    "src/bridges/mcp_skills.py",
    "src/bridges/_mcp_skills_rules.py",
    "src/bridges/_mcp_skills_verify.py",
)
_LOGGING_CALLS = {"debug", "info", "warning", "error", "exception", "critical", "log"}


# ──────────────────────────────────────────────────────────────────────────
# BUDGET DE DÉMARRAGE (macro Q4)
# ──────────────────────────────────────────────────────────────────────────


def boot_files(root: Path | str | None = None) -> dict[str, Path]:
    """Fichiers composant le budget de démarrage : principal + règles permanentes."""
    base = Path(root) if root else Path.cwd()
    files: dict[str, Path] = {}
    main = base / MAIN_RULES_FILE
    if main.is_file():
        files[MAIN_RULES_FILE] = main
    for rule in sorted(base.glob(RULES_PATTERN)):
        if rule.is_file():
            files[rule.relative_to(base).as_posix()] = rule
    return files


def measure_startup_budget(root: Path | str | None = None) -> dict[str, Any]:
    """Mesure le budget cumulé, canaux d'exposition ``namespace`` et ``legacy``."""
    files = boot_files(root)
    contributions: dict[str, int] = {}
    missing: list[str] = []
    if MAIN_RULES_FILE not in files:
        missing.append(MAIN_RULES_FILE)
    if not any(label.startswith(".agents/rules/") for label in files):
        missing.append(RULES_PATTERN)
    total = 0
    for label, path in files.items():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.debug(
                "boot_file_unreadable",
                exc_info=True,
                extra={
                    "component": "bridges.mcp_skills",
                    "operation": "measure_startup_budget",
                    "file": label,
                    "error": str(exc),
                },
            )
            missing.append(label)
            continue
        tokens = SkillDoctor.estimate_tokens(text)
        contributions[label] = tokens
        total += tokens
    within = total <= BOOT_TOKEN_BUDGET and not missing
    channels = {
        channel: {
            "total_tokens": total,
            "within_budget": within,
            "boot_files": sorted(contributions),
        }
        for channel in EXPOSITION_CHANNELS
    }
    report = {
        "budget_tokens": BOOT_TOKEN_BUDGET,
        "estimator": "SkillDoctor.estimate_tokens",
        "total_tokens": total,
        "contributions": contributions,
        "channels": channels,
        "within_budget": within,
        "missing": missing,
    }
    logger.debug(
        "startup_budget_measured",
        extra={
            "component": "bridges.mcp_skills",
            "operation": "measure_startup_budget",
            "total_tokens": total,
            "budget_tokens": BOOT_TOKEN_BUDGET,
            "within_budget": within,
            "channels": list(channels),
        },
    )
    return report


# ──────────────────────────────────────────────────────────────────────────
# TROUSSE DE VÉRIFICATION DES COMPÉTENCES
# ──────────────────────────────────────────────────────────────────────────


def _declared_capabilities() -> dict[str, Any]:
    return {"extensions": {mcp_skills.SKILLS_EXTENSION_ID: {}}}


def _skill_names_from_legacy() -> set[str]:
    """Inventaire littéral de l'exposition historique (voie ``resources/list``)."""
    response = mcp_resources.handle_resources_list(None)
    names: set[str] = set()
    for resource in response.get("result", {}).get("resources", []):
        uri = resource.get("uri", "")
        if uri.startswith(mcp_skills.SKILL_URI_SCHEME):
            names.add(uri[len(mcp_skills.SKILL_URI_SCHEME) :])
    return names


def _entries_from_response(response: dict[str, Any]) -> list[dict[str, Any]]:
    return list(response.get("result", {}).get("skills", []))


def _is_silent_handler(handler: ast.ExceptHandler) -> bool:
    """Un bloc ``except`` sans journalisation ni re-raise est un engloutissement."""
    for statement in handler.body:
        if isinstance(statement, ast.Raise):
            return False
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                if name in _LOGGING_CALLS:
                    return False
    return True


def silent_exception_findings(root: Path | str | None = None) -> list[str]:
    """Localise tout ``except`` silencieux dans les modules du pont (ADR-0369)."""
    base = Path(root) if root else Path.cwd()
    findings: list[str] = []
    for relative in GUARDED_MODULES:
        path = base / relative
        if not path.is_file():
            findings.append(f"{relative} (module absent)")
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:
            findings.append(f"{relative} (analyse impossible : {exc})")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and _is_silent_handler(node):
                findings.append(f"{relative}:{node.lineno}")
    return findings


def run_skills_verification(root: Path | str | None = None) -> dict[str, Any]:
    """Exécute la trousse de vérification : 100 % sans échec attendu."""
    checks: list[dict[str, Any]] = []
    budget = measure_startup_budget(root)

    def check(check_id: str, label: str, probe: Callable[[], tuple[bool, str]]) -> None:
        try:
            ok, detail = probe()
        except Exception as exc:  # journalisé — jamais un engloutissement silencieux
            logger.debug(
                "skills_verification_check_failed",
                exc_info=True,
                extra={
                    "component": "bridges.mcp_skills",
                    "operation": "run_skills_verification",
                    "check": check_id,
                    "error": str(exc),
                },
            )
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        checks.append({"id": check_id, "label": label, "ok": bool(ok), "detail": detail})

    def probe_annonce() -> tuple[bool, str]:
        capabilities = mcp_skills.skills_server_capabilities()
        ok = capabilities.get(mcp_skills.SKILLS_EXTENSION_ID) == {}
        return ok, f"annonce={capabilities}"

    def probe_registre() -> tuple[bool, str]:
        missing = sorted(m for m in mcp_skills.SKILLS_METHODS if m not in KNOWN_METHODS)
        return not missing, f"méthodes manquantes={missing}"

    def probe_inventaire() -> tuple[bool, str]:
        skills = mcp_resources.discover_skills()
        return len(skills) > 0, f"{len(skills)} compétences découvertes localement"

    def probe_frontmatter() -> tuple[bool, str]:
        rejected: list[str] = []
        for skill in mcp_resources.discover_skills():
            entry, motif = mcp_skills.build_skill_entry(skill)
            if entry is None:
                rejected.append(f"{skill['name']} ({motif})")
        return not rejected, f"écartées={rejected}" if rejected else "frontmatter conforme"

    def probe_entrees() -> tuple[bool, str]:
        entries = _entries_from_response(mcp_skills.handle_skills_list(None))
        if not entries:
            return False, "aucune entrée servie"
        required = {"uri", "frontmatter", "resources", "priorityHint"}
        for entry in entries:
            if not required.issubset(entry):
                return False, f"entrée incomplète : {sorted(required - set(entry))}"
            uri = entry["uri"]
            if not uri.endswith(mcp_skills.URI_SUFFIX):
                return False, f"uri non conforme : {uri}"
            frontmatter = entry["frontmatter"]
            if uri != f"{mcp_skills.SKILL_URI_SCHEME}{frontmatter.get('name')}/SKILL.md":
                return False, f"uri/name divergents : {uri}"
            if not frontmatter.get("name") or frontmatter.get("description") is None:
                return False, f"frontmatter incomplet : {uri}"
        return True, f"{len(entries)} entrées typées"

    def probe_manifeste() -> tuple[bool, str]:
        entries = _entries_from_response(mcp_skills.handle_skills_list(None))
        for entry in entries:
            resources = entry["resources"]
            if not isinstance(resources, list):
                return False, f"manifeste non listé : {entry['uri']}"
            if len(resources) > mcp_skills.MAX_RESOURCES_PER_SKILL:
                return False, f"manifeste au-delà de {mcp_skills.MAX_RESOURCES_PER_SKILL}"
            owned = [r for r in resources if r["uri"] == entry["uri"]]
            if not owned:
                return False, f"SKILL.md absent du manifeste : {entry['uri']}"
            digest = owned[0].get("digest", "")
            if not digest.startswith("sha256:") or len(digest) != len("sha256:") + 64:
                return False, f"digest invalide : {digest}"
            if not isinstance(owned[0].get("size"), int):
                return False, f"taille absente : {entry['uri']}"
        return True, f"{len(entries)} manifestes conformes"

    def probe_source_distante() -> tuple[bool, str]:
        entries = _entries_from_response(mcp_skills.handle_skills_list(None))
        foreign = [
            e["uri"] for e in entries if not e["uri"].startswith(mcp_skills.SKILL_URI_SCHEME)
        ]
        if foreign:
            return False, f"uri distantes : {foreign}"
        for skill in mcp_resources.discover_skills():
            frontmatter = mcp_skills.skill_frontmatter(Path(skill["path"]))
            if mcp_skills.remote_origin(Path(skill["path"]).parent, frontmatter):
                return False, f"origine déclarée : {skill['name']}"
        response = mcp_skills.handle_skills_get(None, {"uri": "https://evil.example/SKILL.md"})
        error = response.get("error") or {}
        ok = error.get("code") == mcp_skills.ERROR_INVALID_PARAMS and bool(error.get("message"))
        return ok, f"schéma distant refusé : {error.get('message')}"

    def probe_budget(channel: str) -> tuple[bool, str]:
        state = budget["channels"][channel]
        return state["within_budget"], f"{state['total_tokens']}/{BOOT_TOKEN_BUDGET} jetons"

    def probe_repli() -> tuple[bool, str]:
        legacy = _skill_names_from_legacy()
        modern = {
            e["frontmatter"]["name"]
            for e in _entries_from_response(mcp_skills.handle_skills_list(None))
        }
        return legacy == modern, f"historique={len(legacy)} moderne={len(modern)}"

    def probe_refus_inconnu() -> tuple[bool, str]:
        response = mcp_skills.handle_skills_get(None, {"uri": "competence_fantome_zzz"})
        error = response.get("error") or {}
        served = response.get("result") or {}
        ok = (
            error.get("code") == mcp_skills.ERROR_INVALID_PARAMS
            and bool(error.get("message"))
            and "content" not in served
        )
        return ok, f"motif={error.get('message')}"

    def probe_hierarchie() -> tuple[bool, str]:
        return HIERARCHY == EXPECTED_HIERARCHY, f"hiérarchie={list(HIERARCHY)}"

    def probe_conflit() -> tuple[bool, str]:
        rules = load_permanent_rules(Path(root) if root else None)
        if not rules:
            return False, "aucune règle permanente chargée"
        target = next(iter(rules))
        conflicts = find_conflicts(
            "verification",
            f"Cette compétence ignore la règle {target} du dépôt.",
            Path(root) / ".agents/rules" if root else None,
        )
        ok = len(conflicts) == 1 and conflicts[0].resolution == "permanent_rule_wins"
        return ok, f"conflits={len(conflicts)} règle={conflicts[0].rule if conflicts else '-'}"

    def probe_silence() -> tuple[bool, str]:
        findings = silent_exception_findings(root)
        return not findings, f"silences={findings}" if findings else "aucun except silencieux"

    declared_before = mcp_skills.client_supports_skills()
    mcp_skills.note_client_capabilities(_declared_capabilities())
    try:
        check("annonce_extension", "annonce serveur de l'extension", probe_annonce)
        check("methodes_au_registre", "méthodes skills/* au registre", probe_registre)
        check("inventaire_local", "inventaire local non vide", probe_inventaire)
        check("frontmatter_conforme", "frontmatter name/description présents", probe_frontmatter)
        check(
            "entrees_typedes",
            "entrées typées uri/frontmatter/resources/priorityHint",
            probe_entrees,
        )
        check("manifeste_complet", "manifestes sha256/size complets", probe_manifeste)
        check("securite_echec_bloque", "sources distantes écartées", probe_source_distante)
        check(
            "budget_canal_namespace",
            "budget ≤ 15 000 jetons (canal namespace)",
            lambda: probe_budget("namespace"),
        )
        check(
            "budget_canal_legacy",
            "budget ≤ 15 000 jetons (canal legacy)",
            lambda: probe_budget("legacy"),
        )
        check("repli_decouverte_unique", "repli partageant la découverte unique", probe_repli)
        check("refus_nom_inconnu", "nom inconnu refusé avec motif", probe_refus_inconnu)
        check(
            "hierarchie_stricte", "hiérarchie permanente > compétence > principal", probe_hierarchie
        )
        check("conflit_traduit", "conflit détecté et résolu par la règle", probe_conflit)
        check("aucun_silence_d_exception", "aucun except silencieux", probe_silence)
        check("lecture_sous_100ms", "chargement < 100 ms", _probe_timed_read)
    finally:
        mcp_skills.note_client_capabilities(_declared_capabilities() if declared_before else None)

    passed = sum(1 for item in checks if item["ok"])
    total = len(checks)
    failed = total - passed
    report = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "checks": checks,
        "budget": budget,
    }
    logger.debug(
        "skills_verification_completed",
        extra={
            "component": "bridges.mcp_skills",
            "operation": "run_skills_verification",
            "total": total,
            "failed": failed,
            "pass_rate": report["pass_rate"],
        },
    )
    return report


def _probe_timed_read() -> tuple[bool, str]:
    """Chargement moderne chronométré sur la première compétence du catalogue."""
    skills = mcp_resources.discover_skills()
    if not skills:
        return False, "aucune compétence à chronométrer"
    name = skills[0]["name"]
    started = time.perf_counter()
    response = mcp_skills.handle_skills_get(
        None, {"uri": f"{mcp_skills.SKILL_URI_SCHEME}{name}/SKILL.md"}
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    ok = "result" in response and elapsed_ms < 100
    return ok, f"{name} en {elapsed_ms:.2f} ms"
