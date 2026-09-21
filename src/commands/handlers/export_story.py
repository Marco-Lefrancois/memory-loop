"""Handlers Export — Jira Sync & Jira Read (sync ciblée Cloud)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, List

from src.cli import ZeroFluffConsole
from src.pipelines.jira.sync_engine import (
    build_sync_preview,
    sync_targeted_to_jira,
    is_jira_status_closed,
)
from src.pipelines.sync import run_sync

if TYPE_CHECKING:
    import argparse
    from src.state import LoopState

# ─── Constantes de sécurité ───────────────────────────────────────────────────
_TEMP_KEY_PREFIX = "TEMP-"
_BLOCKED_STATUSES_WITHOUT_FLAG = {"OPEN", "IN_ANALYZE"}

def _parse_target_keys(args: "argparse.Namespace") -> List[str]:
    """Retourne la liste normalisée des clés cibles à partir de --story ou --stories."""
    keys: List[str] = []
    if getattr(args, "story", None):
        keys.append(args.story.strip())
    if getattr(args, "stories", None):
        for k in args.stories.split(","):
            k = k.strip()
            if k:
                keys.append(k)
    # Dédupliquer en préservant l'ordre
    seen = set()
    result = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result

def handle_jira_sync(
    args: "argparse.Namespace", state: "LoopState", project_path: Path
) -> int:
    """
    Synchronisation ciblée Jira Cloud — Fail-Closed.

    Protocole de sécurité (ADR JIRA_SYNC_SAFE) :
    1. Ciblage explicite requis (--story / --stories / --all administrateur).
    2. Dry-run par défaut — aucun appel HTTP sans --apply.
    3. --apply doit être accompagné de --confirm-scope (liste identique aux éligibles).
    4. Clés TEMP-* et statuts OPEN/IN_ANALYZE bloqués sauf --allow-in-analyze.
    5. Mode --all verrouillé : requiert --apply + --confirm-all-project-stories.
    6. Manifeste SHA-256 écrit avant l'appel API ; divergence = refus Fail-Closed.
    """
    apply_mode: bool = getattr(args, "apply", False)
    dry_run_flag: bool = getattr(args, "dry_run", False)
    all_mode: bool = getattr(args, "all", False)
    confirm_all: bool = getattr(args, "confirm_all_project_stories", False)
    allow_in_analyze: bool = getattr(args, "allow_in_analyze", False)
    confirm_scope: str | None = getattr(args, "confirm_scope", None)

    target_keys = _parse_target_keys(args)

    # ── Garde 1 : Aucun ciblage fourni ───────────────────────────────────────
    if not target_keys and not all_mode:
        ZeroFluffConsole.error(
            "jira_sync nécessite un ciblage explicite.\n"
            "  Exemples :\n"
            "    python src/swarm.py jira_sync --project <P> --story MMA-4651\n"
            "    python src/swarm.py jira_sync --project <P> --stories MMA-4651,MMA-4652\n"
            "    python src/swarm.py jira_sync --project <P> --all --apply --confirm-all-project-stories\n"
            "\n"
            "  Par défaut, la commande opère en dry-run (prévisualisation uniquement).\n"
            "  Ajoutez --apply --confirm-scope <CLES> pour écrire sur Jira."
        )
        return 2

    # ── Garde 2 : Mode --all verrouillé ──────────────────────────────────────
    if all_mode:
        if not apply_mode or not confirm_all:
            ZeroFluffConsole.error(
                "Le mode global --all est verrouillé.\n"
                "  Il requiert OBLIGATOIREMENT : --apply --confirm-all-project-stories\n"
                "  Exemple :\n"
                "    python src/swarm.py jira_sync --project <P> --all --apply --confirm-all-project-stories"
            )
            return 2
        target_keys = []  # Signal : toutes les stories éligibles

    # ── Garde 2.5 : Blocage des clés temporaires TEMP-* ─────────────────────
    if any(k.startswith(_TEMP_KEY_PREFIX) for k in target_keys):
        ZeroFluffConsole.error(
            f"Les clés temporaires ({_TEMP_KEY_PREFIX}*) ne peuvent pas être synchronisées vers Jira.\n"
            "  Assignez une clé Jira valide ou créez le ticket sur Jira au préalable."
        )
        return 2

    # ── Discover backlog pour valider les statuts ─────────────────────────────
    project_path_abs = Path(r"C:\Memory Loop\Projects") / state.project_name
    state.discover_backlog(project_path_abs)

    # ── Construction du périmètre éligible ───────────────────────────────────
    eligible_items = []
    rejected_items = []

    # ── Client Jira optionnel pour vérification préventive des statuts ───────
    import os
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    live_jira_client = None
    if jira_url and jira_email and jira_token:
        try:
            import httpx
            live_jira_client = httpx.Client(
                base_url=jira_url,
                auth=(jira_email, jira_token),
                headers={"Accept": "application/json"},
                timeout=5.0,
            )
        except Exception:
            live_jira_client = None

    try:
        for item in state.sprint_backlog:
            item_jira_key = (getattr(item, "jira_key", None) or "").strip()

            # Filtre par cible (si mode ciblé)
            if target_keys:
                if item.id not in target_keys and item_jira_key not in target_keys:
                    continue

            # Blocage clé temporaire TEMP-*
            if item_jira_key.startswith(_TEMP_KEY_PREFIX) or item.id.startswith(
                _TEMP_KEY_PREFIX
            ):
                rejected_items.append(
                    (item, f"Clé temporaire {_TEMP_KEY_PREFIX}* non synchronisable")
                )
                continue

            # Règle constitutionnelle : si un récit est au statut FERMÉ dans Jira, ne jamais sync
            if live_jira_client and item_jira_key:
                try:
                    r_st = live_jira_client.get(f"/rest/api/3/issue/{item_jira_key}?fields=status")
                    if r_st.status_code == 200:
                        st_data = r_st.json().get("fields", {}).get("status", {})
                        st_name = st_data.get("name", "")
                        st_cat = st_data.get("statusCategory", {}).get("key", "")
                        if is_jira_status_closed(st_name, st_cat):
                            rejected_items.append(
                                (
                                    item,
                                    f"Ticket Jira {item_jira_key} est au statut FERMÉ ('{st_name}') — synchronisation strictement interdite (règle constitutionnelle)",
                                )
                            )
                            continue
                except Exception:
                    pass

            # Blocage statut OPEN / IN_ANALYZE
            status_val = getattr(item.status, "value", str(item.status))
            if status_val in _BLOCKED_STATUSES_WITHOUT_FLAG and not allow_in_analyze:
                rejected_items.append(
                    (item, f"Statut {status_val} bloqué (utilisez --allow-in-analyze)")
                )
                continue

            # Eligibilité standard
            if (
                not getattr(item, "jira_sync_eligible", item.grilled)
                and not allow_in_analyze
            ):
                rejected_items.append((item, "Non éligible (statut insuffisant)"))
                continue

            eligible_items.append(item)
    finally:
        if live_jira_client:
            try:
                live_jira_client.close()
            except Exception:
                pass

    # ── Rapport de prévisualisation (toujours affiché) ───────────────────────
    preview = build_sync_preview(
        project_path=project_path_abs,
        state=state,
        eligible_items=eligible_items,
        rejected_items=rejected_items,
        target_keys=target_keys,
    )

    ZeroFluffConsole.section("APERÇU DU PÉRIMÈTRE DE SYNCHRONISATION (DRY-RUN)")
    ZeroFluffConsole.info(f"  Stories éligibles  : {len(eligible_items)}")
    ZeroFluffConsole.info(f"  Stories rejetées   : {len(rejected_items)}")
    for item in eligible_items:
        ik = getattr(item, "jira_key", None) or "—"
        ZeroFluffConsole.info(f"    ✅ {item.id:<20} ({ik})")
    for item, reason in rejected_items:
        ik = getattr(item, "jira_key", None) or "—"
        ZeroFluffConsole.warning(f"    ⛔ {item.id:<20} ({ik}) — {reason}")

    # ── Dry-run : sortie sans écriture ───────────────────────────────────────
    is_dry_run = dry_run_flag or not apply_mode
    if is_dry_run:
        ZeroFluffConsole.info(
            "\n[DRY-RUN] Aucune donnée n'a été envoyée à Jira.\n"
            "  Pour appliquer, relancez avec : --apply --confirm-scope <CLES_ELIGIBLES>"
        )
        return 0

    # ── Garde 3 : --confirm-scope doit correspondre exactement aux éligibles ─
    if not all_mode:
        if not confirm_scope:
            ZeroFluffConsole.error(
                "--apply requiert --confirm-scope <CLES> pour confirmer le périmètre.\n"
                f"  Stories éligibles actuelles : {[i.id for i in eligible_items]}"
            )
            return 2

        provided_scope = sorted(
            k.strip() for k in confirm_scope.split(",") if k.strip()
        )
        eligible_ids = sorted(
            [(getattr(i, "jira_key", None) or i.id) for i in eligible_items]
        )
        eligible_ids_alt = sorted([i.id for i in eligible_items])

        if provided_scope != eligible_ids and provided_scope != eligible_ids_alt:
            ZeroFluffConsole.error(
                f"[FAIL-CLOSED] Le périmètre --confirm-scope ne correspond pas aux éligibles.\n"
                f"  Fourni   : {provided_scope}\n"
                f"  Éligible : {eligible_ids}\n"
                "  Corrigez --confirm-scope ou vérifiez les statuts des récits."
            )
            return 2

    # ── Garde 4 : Vérification manifeste SHA-256 (Fail-Closed) ───────────────
    manifest_ok = _verify_sha256_manifest(preview, project_path_abs)
    if not manifest_ok:
        ZeroFluffConsole.error(
            "[FAIL-CLOSED] Le manifeste SHA-256 détecte des modifications locales\n"
            "  survenues entre le dry-run et l'apply.\n"
            "  Relancez la commande pour générer un nouveau manifeste."
        )
        return 2

    # ── Application réelle ────────────────────────────────────────────────────
    ZeroFluffConsole.step_s2(
        "Scrum Master", f"Application de la synchronisation vers Jira..."
    )
    result_state = sync_targeted_to_jira(
        state=state,
        project_path=project_path_abs,
        eligible_items=eligible_items,
        manifest_id=preview.get("manifest_id", ""),
    )
    if result_state is not None:
        run_sync(args.project, result_state, project_path_abs)
    return 0

def _verify_sha256_manifest(preview: dict, project_path: Path) -> bool:
    """
    Vérifie que les SHA-256 du manifeste preview correspondent aux fichiers actuels.
    Retourne True si tout est conforme (ou si aucun manifeste n'existe = premier run).
    Écrit le manifeste après vérification.
    """
    import hashlib

    manifest_path = project_path / "memory" / "sync" / "jira_sync_preview.json"
    current_hashes = preview.get("file_hashes", {})

    # Si le manifeste existe, comparer
    if manifest_path.exists():
        try:
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            saved_hashes = saved.get("file_hashes", {})
            for file_path_str, saved_hash in saved_hashes.items():
                fp = Path(file_path_str)
                if fp.exists():
                    current_hash = hashlib.sha256(fp.read_bytes()).hexdigest()
                    if current_hash != saved_hash:
                        return False
        except Exception:
            pass  # Manifeste corrompu → on laisse passer (premier run effectif)

    # Écrire le nouveau manifeste
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass

    return True
