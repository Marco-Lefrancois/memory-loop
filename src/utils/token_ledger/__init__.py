# -*- coding: utf-8 -*-
"""
Façade TokenLedger — Package token_ledger (ADR-0329 / MLOOP-101-BE).

Ré-exporte la classe TokenLedger pour transparence totale des 7 sites d'import :
  `from src.utils.token_ledger import TokenLedger`
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger
from src.utils.token_ledger.key_info import resolve_active_key_info
from src.utils.token_ledger.reporting import generate_report as _generate_report

logger = get_logger("token_ledger")


class TokenLedger:
    """Moteur de journalisation et d'audit des tokens et des coûts d'interaction."""

    DEFAULT_PRICING_PER_1M = {
        # Modèle : (Prix Input / 1M, Prix Output / 1M)
        "gemini-3.8-flash": (0.75, 3.75),
        "gemini-3.7-flash": (0.75, 3.75),
        "gpt-transcribe": (0.00, 0.00),
        "gemini-3.1-pro-preview": (1.25, 5.00),
        "gemini-3.1-pro-preview-thinking": (1.25, 5.00),
        "gemini-3.1-pro": (1.25, 5.00),
        "gemini-3-flash-preview": (0.075, 0.30),
        "gemini-3-flash-preview-thinking": (0.075, 0.30),
        "gemini-3.5-flash": (0.075, 0.30),
        "gemini-3.1-flash-lite": (0.0375, 0.15),
        "gemini-3.1-flash-lite-thinking": (0.0375, 0.15),
        "gemini-3.5-flash-lite": (0.0375, 0.15),
        "gpt-5.6-terra": (15.00, 60.00),
        "gpt-5.6-terra-thinking": (15.00, 60.00),
        "gpt-5.6-sol": (10.00, 40.00),
        "gpt-5.6-luna": (5.00, 20.00),
        "gpt-5.6-luna-thinking": (5.00, 20.00),
        "gpt-5.5": (2.50, 10.00),
        "gpt-5.5-thinking": (2.50, 10.00),
        "gpt-5.4": (1.00, 4.00),
        "gpt-5.4-mini": (0.15, 0.60),
        "gpt-5-mini": (0.15, 0.60),
        "claude-opus-4.8": (15.00, 75.00),
        "claude-opus-4-8": (15.00, 75.00),
        "claude-opus-4.6": (15.00, 75.00),
        "claude-opus-4-6": (15.00, 75.00),
        "claude-sonnet-5": (3.00, 15.00),
        "claude-sonnet-5-thinking": (3.00, 15.00),
        "claude-sonnet-4.6": (3.00, 15.00),
        "claude-sonnet-4-6": (3.00, 15.00),
        "claude-haiku-4.5": (0.80, 4.00),
        "claude-haiku-4-5": (0.80, 4.00),
    }

    FALLBACK_PRICING = (1.00, 3.00)

    @classmethod
    def resolve_active_key_info(cls) -> Dict[str, str]:
        """Identifie la clé active dans l'environnement ou ~/.secrets. Délègue à key_info."""
        return resolve_active_key_info()

    @classmethod
    def calculate_cost(cls, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calcule le coût estimé en USD."""
        clean_model = (
            model.replace("nmedia_cloud/", "")
            .replace("openai/", "")
            .replace("anthropic/", "")
            .replace("gemini/", "")
        )
        pricing = cls.DEFAULT_PRICING_PER_1M.get(clean_model, cls.FALLBACK_PRICING)
        in_cost = (prompt_tokens / 1_000_000.0) * pricing[0]
        out_cost = (completion_tokens / 1_000_000.0) * pricing[1]
        return in_cost + out_cost

    @classmethod
    def record_interaction(
        cls,
        project_name: str,
        action: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        key_label: Optional[str] = None,
        target: Optional[str] = None,
        context_contributors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        root_dir: Optional[Path] = None,
        source: str = "llm_nmedia_cloud",
    ) -> Dict[str, Any]:
        """
        Enregistre une interaction avec calcul automatique des tokens, coûts et clés.
        Écrit dans memory/token_ledger.jsonl et Projects/<projet>/memory/token_ledger.jsonl.
        """
        root = root_dir or Path(".")
        key_info = cls.resolve_active_key_info()
        resolved_key_label = key_label or key_info["key_label"]

        total_tokens = prompt_tokens + completion_tokens
        cost_usd = cls.calculate_cost(model, prompt_tokens, completion_tokens)

        # Normalisation stricte de la source LLM
        src_val = (source or "llm_nmedia_cloud").strip()
        if src_val.lower() in ("nmedia_cloud", "nmedia", "llm_nmedia_cloud"):
            norm_source = "llm_nmedia_cloud"
        elif src_val.lower() in ("google", "antigravity", "antigravity-chat"):
            norm_source = "antigravity-chat"
        else:
            norm_source = src_val

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": norm_source,
            "project": project_name or "Global",
            "key_label": resolved_key_label,
            "key_masked": key_info["key_masked"],
            "action": action,
            "target": target or "N/A",
            "model": model,
            "prompt_tokens_est": prompt_tokens,
            "completion_tokens_est": completion_tokens,
            "total_tokens_est": total_tokens,
            "cost_usd_est": round(cost_usd, 6),
            "context_contributors": context_contributors or [],
            "metadata": metadata or {},
        }

        # 1. Écriture globale
        global_ledger = root / "memory" / "token_ledger.jsonl"
        global_ledger.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(global_ledger, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning(
                "Impossible d'écrire dans le token ledger global",
                extra={"global_ledger": str(global_ledger), "error": str(e)},
            )

        # 2. Écriture par projet
        if project_name and project_name != "Global":
            proj_dir = root / "Projects" / project_name / "memory"
            if proj_dir.exists():
                proj_ledger = proj_dir / "token_ledger.jsonl"
                try:
                    with open(proj_ledger, "a", encoding="utf-8") as f:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                except OSError as e:
                    logger.warning(
                        "Impossible d'écrire dans le token ledger projet",
                        extra={"proj_ledger": str(proj_ledger), "error": str(e)},
                    )

        return entry

    @classmethod
    def load_entries(
        cls,
        project_name: Optional[str] = None,
        date_filter: Optional[str] = None,
        root_dir: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """Charge et filtre les entrées du journal."""
        root = root_dir or Path(".")
        ledger_path = root / "memory" / "token_ledger.jsonl"
        if not ledger_path.exists():
            return []

        entries = []
        try:
            for line in ledger_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if (
                        project_name
                        and project_name.lower() not in entry.get("project", "").lower()
                    ):
                        continue
                    if date_filter:
                        ts = entry.get("timestamp", "")
                        if not ts.startswith(date_filter):
                            continue
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    logger.debug(
                        "Ligne JSON invalide ignorée dans token ledger",
                        extra={"error": str(e)},
                    )
        except OSError as e:
            logger.warning(
                "Erreur de lecture du token ledger",
                extra={"ledger_path": str(ledger_path), "error": str(e)},
            )

        return entries

    @classmethod
    def generate_report(
        cls,
        project_name: Optional[str] = None,
        date_filter: Optional[str] = None,
        top_n: int = 10,
        root_dir: Optional[Path] = None,
    ) -> str:
        """Génère un rapport ASCII complet d'audit des tokens et des coûts. Délègue à reporting."""
        entries = cls.load_entries(
            project_name=project_name, date_filter=date_filter, root_dir=root_dir
        )
        return _generate_report(
            entries=entries,
            project_name=project_name,
            date_filter=date_filter,
            top_n=top_n,
        )


__all__ = ["TokenLedger"]
