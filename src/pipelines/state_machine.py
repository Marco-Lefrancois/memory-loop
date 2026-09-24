"""
mLoop Framework State Machine Engine
Contrôleur déterministe de la Machine à États des récits (Stories) basé sur les Métadonnées Frontmatter.

Garde-fous implémentés :
  - Strict FSM Enforcement : dictionnaire ALLOWED_TRANSITIONS bloquant les sauts illicites.
  - Cryptographic Anti-Tampering : hash SHA-256 du contenu injecté au passage en READY_*.
  - Token-Burn TTL : compteur de cycles décrémenté à chaque échec, forçant ON_HOLD à 0.
"""

import hashlib
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from src.state import StoryStatus
from src.utils.logger import get_logger

logger = get_logger("pipelines.state_machine")

DEFAULT_TTL_CYCLES = 3


def _clean_yaml_str(raw_yaml: str) -> dict:
    """Parse YAML de manière tolérante aux tirets nus non quotés."""
    sanitized = re.sub(r"(?m)^(\s*[\w_]+\s*:\s*)-(\s*)$", r'\1"-"\2', raw_yaml)
    try:
        res = yaml.safe_load(sanitized)
        return res if isinstance(res, dict) else {}
    except Exception as e:
        logger.debug(
            "Parse YAML tolérant échoué, retour d'un dict vide",
            exc_info=True,
            extra={
                "component": "pipelines.state_machine",
                "operation": "clean_yaml_str",
                "error": str(e),
            },
        )
        return {}


# ─── Transitions autorisées (SSOT) ────────────────────────────────────────────
# Chaque clé mappe vers la liste des statuts cibles légaux.
ALLOWED_TRANSITIONS = {
    StoryStatus.DRAFT: [
        StoryStatus.OPEN,
        StoryStatus.IN_ANALYZE,
        StoryStatus.READY_FOR_GROOMING,
        StoryStatus.READY_FOR_DEV,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
    StoryStatus.BACKLOG: [
        StoryStatus.DRAFT,
        StoryStatus.OPEN,
        StoryStatus.IN_ANALYZE,
        StoryStatus.IN_REVIEW,
        StoryStatus.ON_HOLD,
    ],
    StoryStatus.OPEN: [
        StoryStatus.DRAFT,
        StoryStatus.IN_ANALYZE,
        StoryStatus.IN_REVIEW,
        StoryStatus.BACKLOG,
        StoryStatus.ON_HOLD,
    ],
    StoryStatus.IN_ANALYZE: [
        StoryStatus.IN_PLAN,
        StoryStatus.IN_REVIEW,
        StoryStatus.READY_FOR_GROOMING,
        StoryStatus.OPEN,
        StoryStatus.BACKLOG,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
    StoryStatus.IN_PLAN: [
        StoryStatus.IN_VALIDATE,
        StoryStatus.IN_BUILD,
        StoryStatus.IN_REVIEW,
        StoryStatus.IN_ANALYZE,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
    StoryStatus.IN_BUILD: [
        StoryStatus.IN_VALIDATE,
        StoryStatus.IN_PLAN,
        StoryStatus.IN_REVIEW,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
    StoryStatus.IN_VALIDATE: [
        StoryStatus.READY_FOR_GROOMING,
        StoryStatus.IN_REVIEW,
        StoryStatus.SHIPPED,
        StoryStatus.IN_ANALYZE,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
    StoryStatus.IN_REVIEW: [
        StoryStatus.READY_FOR_DEV,
        StoryStatus.READY_FOR_GROOMING,
        StoryStatus.IN_ANALYZE,
        StoryStatus.ON_HOLD,
        StoryStatus.OPEN,
        StoryStatus.ERROR,
    ],
    StoryStatus.READY_FOR_GROOMING: [
        StoryStatus.READY_FOR_DEV,
        StoryStatus.IN_REVIEW,
        StoryStatus.IN_ANALYZE,
        StoryStatus.ON_HOLD,
    ],
    StoryStatus.READY_FOR_DEV: [
        StoryStatus.IN_DEV,
        StoryStatus.IN_REVIEW,
        StoryStatus.IN_ANALYZE,
        StoryStatus.ON_HOLD,
    ],
    StoryStatus.IN_DEV: [
        StoryStatus.IN_QA,
        StoryStatus.ACCEPTED,
        StoryStatus.DONE,
        StoryStatus.DONE_TESTED,
        StoryStatus.READY_FOR_DEV,
        StoryStatus.IN_REVIEW,
        StoryStatus.IN_ANALYZE,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
    StoryStatus.IN_QA: [
        StoryStatus.ACCEPTED,
        StoryStatus.DONE,
        StoryStatus.IN_DEV,
        StoryStatus.IN_REVIEW,
        StoryStatus.IN_ANALYZE,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
    StoryStatus.DONE: [
        StoryStatus.ACCEPTED,
        StoryStatus.IN_DEV,
        StoryStatus.IN_ANALYZE,
        StoryStatus.IN_REVIEW,
    ],
    StoryStatus.DONE_TESTED: [
        StoryStatus.SHIPPED,
        StoryStatus.IN_REVIEW,
        StoryStatus.IN_DEV,
        StoryStatus.ON_HOLD,
        StoryStatus.ERROR,
    ],
    StoryStatus.ACCEPTED: [
        StoryStatus.IN_DEV,
        StoryStatus.IN_ANALYZE,
        StoryStatus.IN_REVIEW,
    ],
    StoryStatus.SHIPPED: [StoryStatus.IN_ANALYZE, StoryStatus.IN_REVIEW],
    StoryStatus.ON_HOLD: [
        StoryStatus.BACKLOG,
        StoryStatus.OPEN,
        StoryStatus.IN_ANALYZE,
        StoryStatus.IN_REVIEW,
    ],
    StoryStatus.ERROR: [
        StoryStatus.IN_ANALYZE,
        StoryStatus.IN_REVIEW,
        StoryStatus.OPEN,
        StoryStatus.BACKLOG,
    ],
}

DEFAULT_TTL_CYCLES = 5


class StateTransitionError(ValueError):
    """Exception levée lorsqu'une transition d'état illicite est détectée par le pipeline."""

    pass


class ContentTamperingError(ValueError):
    """Exception levée lorsqu'une modification non autorisée du contenu est détectée après validation."""

    pass


class StateMachineEngine:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.backlog_path = self.project_path / "backlog"
        self.stories_path = self.backlog_path / "stories"
        self.reviews_path = self.backlog_path / "reviews"

    # ─── 1. Strict FSM Enforcement ─────────────────────────────────────────

    def validate_transition(self, current: StoryStatus, target: StoryStatus) -> bool:
        """
        Vérifie qu'une transition d'état est autorisée par le dictionnaire ALLOWED_TRANSITIONS.
        Lève StateTransitionError si la transition est illicite.
        """
        allowed = ALLOWED_TRANSITIONS.get(current, [])
        if target not in allowed:
            allowed_str = ", ".join(s.value for s in allowed) if allowed else "AUCUN"
            raise StateTransitionError(
                f"[FSM BLOQUANT] Transition illicite : {current.value} → {target.value}\n"
                f"Transitions autorisées depuis {current.value} : [{allowed_str}]\n"
                f"➡ Corrigez le statut ou passez par les étapes intermédiaires obligatoires."
            )
        return True

    def validate_single_in_analyze(self) -> list[str]:
        """
        Interroge les métadonnées d'en-tête de toutes les stories et vérifie
        qu'il n'y a pas plus d'UNE story au statut 'IN_ANALYZE' simultanément par projet.
        """
        in_analyze_stories = []
        if not self.stories_path.exists():
            return in_analyze_stories

        for file in self.stories_path.glob("**/*.md"):
            try:
                text = file.read_text(encoding="utf-8")
                if not text.startswith("---"):
                    continue
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    data = _clean_yaml_str(parts[1])
                    if isinstance(data, dict) and data.get("status") == "IN_ANALYZE":
                        rel_path = file.relative_to(self.stories_path).as_posix()
                        in_analyze_stories.append(rel_path)
            except Exception as e:
                logger.debug(
                    "Lecture/parse d'un récit échouée, fichier ignoré",
                    exc_info=True,
                    extra={
                        "component": "pipelines.state_machine",
                        "operation": "validate_single_in_analyze",
                        "file": str(file),
                        "error": str(e),
                    },
                )
                continue

        if len(in_analyze_stories) > 1:
            raise StateTransitionError(
                f"[VIOLATION STATE MACHINE] Plus d'une story est au statut 'IN_ANALYZE' simultanément :\n"
                f"Stories détectées : {in_analyze_stories}\n"
                f"Le framework mLoop impose STRICTEMENT un seul récit au statut 'IN_ANALYZE' à la fois !"
            )

        return in_analyze_stories

    def validate_sentinel_approval(self, story_file: Path) -> bool:
        """
        Vérifie qu'un rapport de revue contradictoire Sentinel (Rubber Duck) existe
        sous backlog/reviews/ (ou ses sous-dossiers) et porte le statut APPROUVÉ.
        """
        story_stem = story_file.stem
        category = (
            story_file.parent.name
            if story_file.parent.name in ["FOOD", "COMMERCE", "SANTE"]
            else ""
        )

        candidates = []
        if category:
            candidates.append(self.reviews_path / category / f"rubber_duck_{story_stem}.md")
        candidates.append(self.reviews_path / f"rubber_duck_{story_stem}.md")

        review_file = None
        for cand in candidates:
            if cand.exists():
                review_file = cand
                break

        if not review_file:
            # Recherche récursive de repli
            matches = list(self.reviews_path.rglob(f"rubber_duck_{story_stem}.md"))
            if matches:
                review_file = matches[0]

        if not review_file or not review_file.exists():
            raise StateTransitionError(
                f"[VERROU SENTINEL BLOQUANT] Le récit '{story_file.name}' n'a pas été audité par l'agent Sentinel (Rubber Duck) !\n"
                f"Rapport manquant : backlog/reviews/{category + '/' if category else ''}rubber_duck_{story_stem}.md\n"
                f"➡ Action obligatoire : Exécutez 'python src/swarm.py rubber-duck --project {self.project_path.name} --file {story_file.as_posix()}'"
            )

        review_text = review_file.read_text(encoding="utf-8")
        if (
            "REJETÉ" in review_text
            or "REJETE" in review_text
            or (
                "Problèmes de Blocage" in review_text
                and "Aucun problème bloquant" not in review_text
            )
        ):
            raise StateTransitionError(
                f"[VERROU SENTINEL BLOQUANT] Le récit '{story_file.name}' présente des rejets de revue Rubber Duck non résolus !\n"
                f"Rapport : {review_file.relative_to(self.project_path).as_posix()}\n"
                f"➡ Action obligatoire : Corrigez le récit puis relancez 'python src/swarm.py rubber-duck --project {self.project_path.name} --file {story_file.as_posix()}'"
            )

        return True

    # ─── 1b. Gate C9 : Dossier de Preuves Documentaires (Phase 2) ──────────

    def validate_fact_dossier_gate(self, story_file: Path, strict: bool = False) -> bool:
        """
        Gate déterministe sur le Dossier de Preuves Documentaires (ADR-0320 §H,
        ADR-0326, DOSSIER_DE_PREUVES_PROTOCOL.md) pour les récits en statut
        READY_FOR_DEV / READY_FOR_GROOMING (et au-delà du cycle de vie).

        Réutilise la même logique de détection que `struct_checker.py` Check C9
        (existence de memory/evidence/<STORY_ID>_fact_dossier.md ou lien valide
        dans '## Références'), mais rattachée à la Machine à États plutôt qu'au
        seul rapport `struct-check` consultatif.

        Sévérité (décision actée — période de transition) :
        - `strict=False` (défaut) : dossier manquant -> WARNING affiché via
          ZeroFluffConsole, retourne True (non bloquant). Évite de bloquer les
          stories déjà en READY_FOR_DEV sans dossier historique.
        - `strict=True` (CI/audit explicite) : dossier manquant -> lève
          StateTransitionError (BLOCKING).

        Hors périmètre (retourne True sans vérification, aucun WARNING) :
        - Statuts non gérés (OPEN, ON_HOLD, IN_ANALYZE, etc.).
        - Statuts DONE / ACCEPTED : un récit déjà terminé n'a pas besoin de
          rétro-équiper un Dossier de Preuves (décision PO — la période de
          transition ne concerne que les récits encore actifs). Seuls
          READY_FOR_DEV / READY_FOR_GROOMING / IN_DEV / IN_QA sont gatés.
        """
        text = story_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return True

        parts = text.split("---", 2)
        if len(parts) < 3:
            return True

        data = _clean_yaml_str(parts[1])
        if not isinstance(data, dict):
            return True

        status = data.get("status", "")
        gated_statuses = (
            "READY_FOR_DEV",
            "READY_FOR_GROOMING",
            "IN_DEV",
            "IN_QA",
        )
        if status not in gated_statuses:
            return True

        story_id = data.get("id") or story_file.stem
        content = parts[2]

        # 1. Lien direct dans '## Références' pointant vers un _fact_dossier.md existant
        dossier_links = re.findall(r"\[([^\]]*fact_dossier[^\]]*)\]\(([^)]+)\)", content)
        has_valid_link = any(
            (story_file.parent / link_target).resolve().exists()
            for _, link_target in dossier_links
            if not link_target.startswith(("http://", "https://"))
        )

        # 2. Fichier canonique sous memory/evidence/<STORY_ID>_fact_dossier.md
        evidence_dir = self.project_path / "memory" / "evidence"
        dossier_candidates = (
            list(evidence_dir.glob(f"**/{story_id}_fact_dossier.md"))
            if evidence_dir.exists()
            else []
        )

        target_dossier = None
        if dossier_candidates:
            target_dossier = dossier_candidates[0]
        else:
            for _, link_target in dossier_links:
                cand = (story_file.parent / link_target).resolve()
                if cand.exists() and cand.is_file():
                    target_dossier = cand
                    break

        if target_dossier and target_dossier.exists():
            try:
                dossier_txt = target_dossier.read_text(encoding="utf-8", errors="replace")
                st_m = re.search(r"^dossier_status:\s*(.+)$", dossier_txt, re.MULTILINE)
                dossier_status = st_m.group(1).strip() if st_m else "CURRENT"
                has_facts = bool(
                    re.search(
                        r"(?m)(?:\|\s*\*{0,2}F-\d+|Extrait\s*\d+|➔\s*\*{0,2}Fait établi|\bF-\d{2}\b)",
                        dossier_txt,
                    )
                )

                if dossier_status == "DRAFT":
                    msg = (
                        f"[GATE C9 — DOSSIER DE PREUVES] Le dossier '{target_dossier.name}' du récit '{story_file.name}' "
                        f"est encore au statut 'DRAFT'. Il doit être validé ('CURRENT' ou 'VALIDATED')."
                    )
                    if strict:
                        raise StateTransitionError(msg)
                    from src.cli import ZeroFluffConsole

                    ZeroFluffConsole.warning(msg)

                if not has_facts or len(dossier_txt.strip()) < 100:
                    msg = (
                        f"[GATE C9 — DOSSIER DE PREUVES] Le dossier '{target_dossier.name}' du récit '{story_file.name}' "
                        f"est incomplet ou ne contient aucun fait vérifié (Section 2)."
                    )
                    if strict:
                        raise StateTransitionError(msg)
                    from src.cli import ZeroFluffConsole

                    ZeroFluffConsole.warning(msg)
            except StateTransitionError:
                raise
            except Exception as e:
                logger.debug(
                    "Évaluation du dossier de preuves échouée, le gate retourne True (non bloquant)",
                    exc_info=True,
                    extra={
                        "component": "pipelines.state_machine",
                        "operation": "validate_fact_dossier_gate",
                        "story_file": str(story_file),
                        "strict": strict,
                        "error": str(e),
                    },
                )
            return True

        message = (
            f"[GATE C9 — DOSSIER DE PREUVES] Le récit '{story_file.name}' (statut {status}) "
            f"n'a pas de Dossier de Preuves Documentaires détecté.\n"
            f"Attendu : memory/evidence/{story_id}_fact_dossier.md "
            f"(cf. DOSSIER_DE_PREUVES_PROTOCOL.md §2 — Gate Pré-Rédaction)."
        )

        if strict:
            raise StateTransitionError(
                message + "\n➡ Générez le dossier avant de poursuivre (mode strict)."
            )

        try:
            from src.cli import ZeroFluffConsole

            ZeroFluffConsole.warning(message)
        except Exception as e:
            logger.debug(
                "Affichage console du warning Gate C9 échoué",
                exc_info=True,
                extra={
                    "component": "pipelines.state_machine",
                    "operation": "gate_c9_console_warning",
                    "story_file": str(story_file),
                    "error": str(e),
                },
            )
        return True

    # ─── 2. Cryptographic Anti-Tampering ───────────────────────────────────

    @staticmethod
    def compute_content_hash(markdown_body: str) -> str:
        """
        Calcule un hash SHA-256 du corps Markdown (hors frontmatter).
        Utilisé pour détecter les modifications silencieuses post-validation.
        """
        normalized = markdown_body.strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def validate_content_integrity(self, story_file: Path) -> bool:
        """
        Vérifie que le contenu d'un récit validé (READY_FOR_GROOMING / READY_FOR_DEV)
        n'a pas été modifié après l'injection du hash.
        Lève ContentTamperingError si le hash ne correspond plus.
        """
        text = story_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return True

        parts = text.split("---", 2)
        if len(parts) < 3:
            return True

        data = _clean_yaml_str(parts[1])
        if not isinstance(data, dict):
            return True

        stored_hash = data.get("content_hash")
        status = data.get("status", "")

        if not stored_hash or status not in ("READY_FOR_GROOMING", "READY_FOR_DEV"):
            return True

        current_hash = self.compute_content_hash(parts[2])
        if current_hash != stored_hash:
            raise ContentTamperingError(
                f"[ANTI-TAMPERING] Le contenu du récit '{story_file.name}' a été modifié après validation !\n"
                f"Hash stocké : {stored_hash} | Hash actuel : {current_hash}\n"
                f"➡ Le récit est automatiquement rétrogradé en IN_ANALYZE pour forcer un nouvel audit Sentinel."
            )

        return True

    def stamp_content_hash(self, story_file: Path) -> Optional[str]:
        """
        Injecte le hash SHA-256 du contenu dans le frontmatter d'un récit
        lors du passage en READY_FOR_GROOMING ou READY_FOR_DEV.
        Retourne le hash injecté, ou None si non applicable.
        """
        text = story_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None

        parts = text.split("---", 2)
        if len(parts) < 3:
            return None

        data = _clean_yaml_str(parts[1])
        if not isinstance(data, dict):
            return None

        content_hash = self.compute_content_hash(parts[2])
        data["content_hash"] = content_hash

        new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True).strip()
        new_text = f"---\n{new_yaml}\n---{parts[2]}"
        story_file.write_text(new_text, encoding="utf-8")

        return content_hash

    # ─── 3. Token-Burn TTL ─────────────────────────────────────────────────

    def decrement_ttl(self, story_file: Path) -> int:
        """
        Décrémente le compteur TTL (Time To Live) d'un récit.
        Initialise à DEFAULT_TTL_CYCLES si absent.
        Retourne le TTL restant après décrémentation.
        """
        text = story_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return DEFAULT_TTL_CYCLES

        parts = text.split("---", 2)
        if len(parts) < 3:
            return DEFAULT_TTL_CYCLES

        data = _clean_yaml_str(parts[1])
        if not isinstance(data, dict):
            return DEFAULT_TTL_CYCLES

        current_ttl = data.get("ttl_cycles", DEFAULT_TTL_CYCLES)
        new_ttl = max(0, current_ttl - 1)
        data["ttl_cycles"] = new_ttl

        new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True).strip()
        new_text = f"---\n{new_yaml}\n---{parts[2]}"
        story_file.write_text(new_text, encoding="utf-8")

        return new_ttl

    def check_ttl(self, story_file: Path) -> bool:
        """
        Vérifie si le TTL d'un récit a atteint 0.
        Si oui, force le statut en ON_HOLD et lève StateTransitionError.
        Retourne True si le TTL est encore valide.
        """
        text = story_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return True

        parts = text.split("---", 2)
        if len(parts) < 3:
            return True

        data = _clean_yaml_str(parts[1])
        if not isinstance(data, dict):
            return True

        ttl = data.get("ttl_cycles", DEFAULT_TTL_CYCLES)

        if ttl <= 0:
            data["status"] = StoryStatus.ON_HOLD.value
            data["ttl_exhausted_at"] = datetime.now(timezone.utc).isoformat()

            new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True).strip()
            new_text = f"---\n{new_yaml}\n---{parts[2]}"
            story_file.write_text(new_text, encoding="utf-8")

            raise StateTransitionError(
                f"[TTL ÉPUISÉ] Le récit '{story_file.name}' a épuisé ses {DEFAULT_TTL_CYCLES} cycles de tentatives.\n"
                f"Le statut a été forcé en ON_HOLD pour intervention humaine.\n"
                f"➡ Analysez les échecs répétés avant de relancer le pipeline."
            )

        return True
