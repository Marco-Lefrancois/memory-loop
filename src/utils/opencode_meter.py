"""
src/utils/opencode_meter.py — Collecteur et Synchroniseur de Tokens OpenCode Desktop (ADR-0104/0369).

Extrait la consommation de jetons et sessions interactives depuis la base locale OpenCode
(~/.local/share/opencode/opencode.db) et injecte les transactions dans le Token Ledger mLoop
avec identification du projet (ex: Boire & Frères) et du module métier (ex: 01-reception).
Conforme ADR-0202 (<300 lignes, <15 Ko).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.dashboard.project_utils import REPO_ROOT
from src.utils.logger import get_logger
from src.utils.token_ledger import TokenLedger

logger = get_logger("opencode_meter")

DEFAULT_OPENCODE_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"


class OpenCodeMeter:
    """Synchroniseur de consommation de jetons OpenCode Desktop."""

    @classmethod
    def get_existing_fingerprints(cls, ledger_path: Path) -> Set[str]:
        """Collecte les empreintes uniques pour garantir une synchronisation idempotente."""
        fps = set()
        if not ledger_path.exists():
            return fps
        try:
            with open(ledger_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        meta = e.get("metadata", {})
                        if "opencode_session_id" in meta:
                            fps.add(f"opencode_{meta['opencode_session_id']}")
                        else:
                            fps.add(f"{e.get('timestamp')}_{e.get('action')}_{e.get('target')}")
                    except Exception:
                        pass
        except Exception as err:
            logger.debug(f"Erreur lecture fingerprints OpenCode: {err}")
        return fps

    @classmethod
    def deduce_project_and_module(cls, title: str, directory: str = "") -> Tuple[str, str]:
        """
        Déduit le projet canonique et le module métier à partir du titre et contexte de session.
        Gère Boire & Frères (réception, incubation, ventes), Metro (Food, Commerce, Santé) et Shopify.
        """
        t = (title or "").lower()
        d = (directory or "").lower()
        comb = f"{t} {d}"

        # 1. Boire & Frères
        if any(k in comb for k in ["boire", "couv", "inc-", "rec-", "vnt-", "incubation", "réception", "reception", "poussin", "couvoir"]):
            proj = "BoireFrere_Segment2"
            if any(k in comb for k in ["rec", "réception", "reception", "quai"]):
                mod = "01-reception"
            elif any(k in comb for k in ["inc", "incubation", "mirage"]):
                mod = "02-incubation"
            elif any(k in comb for k in ["vnt", "vente", "ventes", "expedition"]):
                mod = "03-ventes"
            else:
                mod = "01-reception"
            return proj, mod

        # 2. Metro (Alimentation, Commerce, Santé / Pharma)
        if any(k in comb for k in ["metro", "onetrust", "papercut", "mma-", "circulaire", "rabais"]):
            if any(k in comb for k in ["sante", "santé", "pharma", "rxpro", "jean coutu", "brunet", "dossier"]):
                proj = "Metro_SANTE"
                mod = "AccesDossier" if "dossier" in comb else "OneTrust_SANTE"
            elif any(k in comb for k in ["commerce", "ecom"]):
                proj = "Metro_COMMERCE"
                mod = "OneTrust_COMMERCE"
            elif any(k in comb for k in ["papercut", "upsell"]):
                proj = "Metro_FOOD"
                mod = "PAPERCUTS"
            elif any(k in comb for k in ["offer", "rabais", "circulaire"]):
                proj = "Metro_FOOD"
                mod = "Metro_Food_Offers"
            elif "avion" in comb:
                proj = "Metro_FOOD"
                mod = "RBC_Avion"
            else:
                proj = "Metro_FOOD"
                mod = "OneTrust_FOOD"
            return proj, mod

        # 3. Shopify AI
        if "shop" in comb:
            return "Shopify_AI_Item_Creator", "default"

        # 4. Défaut : mLoop Core
        return "Memory Loop", "default"

    @classmethod
    def parse_model_identifier(cls, raw_model: Any) -> str:
        """Extrait l'identifiant propre du modèle depuis la colonne model d'OpenCode."""
        if not raw_model:
            return "claude-opus-4.8"
        if isinstance(raw_model, str):
            try:
                data = json.loads(raw_model)
                if isinstance(data, dict):
                    return data.get("id") or data.get("name") or raw_model
            except Exception:
                pass
            return raw_model
        if isinstance(raw_model, dict):
            return raw_model.get("id") or raw_model.get("name") or "claude-opus-4.8"
        return str(raw_model)

    @classmethod
    def sync(cls, opencode_db_path: Optional[Path] = None) -> Dict[str, int]:
        """
        Synchronise les sessions OpenCode Desktop vers les token_ledger.jsonl (projet et global).
        Idempotent : ne réinjecte jamais une session déjà indexée.
        """
        db_path = opencode_db_path or DEFAULT_OPENCODE_DB
        if not db_path.exists():
            return {"synced": 0, "skipped": 0}

        global_ledger = REPO_ROOT / "memory" / "token_ledger.jsonl"
        existing_fps = cls.get_existing_fingerprints(global_ledger)

        synced_count = 0
        skipped_count = 0

        try:
            # Connexion URI read-only pour ne jamais bloquer l'IDE OpenCode
            uri = f"file:{db_path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=5.0)
            cur = conn.cursor()

            cur.execute("""
                SELECT id, slug, title, directory, cost, tokens_input, tokens_output, model, time_created, time_updated
                FROM session
                WHERE (tokens_input > 0 OR tokens_output > 0)
                ORDER BY time_created ASC
            """)
            sessions = cur.fetchall()
            conn.close()
        except Exception as e:
            logger.warning(f"Erreur d'accès à la base OpenCode {db_path}: {e}")
            return {"synced": 0, "skipped": 0, "error": str(e)}

        entries_to_append: List[Dict[str, Any]] = []

        for row in sessions:
            s_id, slug, title, directory, cost_db, t_in, t_out, model_raw, t_created, t_updated = row
            fp = f"opencode_{s_id}"
            if fp in existing_fps:
                skipped_count += 1
                continue

            proj, mod = cls.deduce_project_and_module(title or slug or "", directory or "")
            model_name = cls.parse_model_identifier(model_raw)
            p_tokens = int(t_in or 0)
            c_tokens = int(t_out or 0)
            tot_tokens = p_tokens + c_tokens

            # Calcul du coût estimé
            cost_usd = float(cost_db or 0.0)
            if cost_usd <= 0.0 and tot_tokens > 0:
                cost_usd = TokenLedger.calculate_cost(model_name, p_tokens, c_tokens)

            # Date ISO UTC
            ts_sec = (t_created or t_updated or 0) / 1000.0
            dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
            iso_ts = dt.isoformat()

            entry = {
                "timestamp": iso_ts,
                "project": proj,
                "module": mod,
                "source": "opencode-desktop",
                "action": "opencode_session",
                "target": title or slug or "OpenCode Desktop Session",
                "model": model_name,
                "prompt_tokens_est": p_tokens,
                "completion_tokens_est": c_tokens,
                "total_tokens_est": tot_tokens,
                "cost_usd_est": round(cost_usd, 4),
                "context_contributors": [f"backlog/stories/{mod}/"] if mod != "default" else [],
                "metadata": {
                    "opencode_session_id": s_id,
                    "session_slug": slug,
                    "directory": directory,
                },
            }
            entries_to_append.append(entry)
            existing_fps.add(fp)
            synced_count += 1

        if entries_to_append:
            # 1. Écriture dans le ledger global
            global_ledger.parent.mkdir(parents=True, exist_ok=True)
            with open(global_ledger, "a", encoding="utf-8") as f:
                for ent in entries_to_append:
                    f.write(json.dumps(ent, ensure_ascii=False) + "\n")

            # 2. Écriture ventilée dans les ledgers dédiés de projets
            for ent in entries_to_append:
                proj_name = ent.get("project")
                if proj_name and proj_name not in ("ALL", "Memory Loop"):
                    p_dir = REPO_ROOT / "Projects" / proj_name / "memory"
                    if p_dir.exists():
                        proj_ledger = p_dir / "token_ledger.jsonl"
                        with open(proj_ledger, "a", encoding="utf-8") as pf:
                            pf.write(json.dumps(ent, ensure_ascii=False) + "\n")

            logger.info(f"[OPENCODE METER] {synced_count} sessions OpenCode Desktop synchronisées dans le Token Ledger.")

        return {"synced": synced_count, "skipped": skipped_count}
