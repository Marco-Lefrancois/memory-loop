# -*- coding: utf-8 -*-
"""
Token & Cost Ledger for mLoop (ADR-0329).
Garantit la traçabilité granulaire de chaque interaction LLM, par projet et par clé virtuelle LiteLLM.
Permet d'identifier instantanément les interactions les plus lourdes et de prévenir tout dépassement de budget.
"""

from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.utils.logger import get_logger

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
        """Identifie la clé active dans l'environnement ou ~/.secrets."""
        # 1. Charger .env en priorité absolue (SSOT)
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

        key_metro = os.getenv("LITELLM_API_KEY_METRO", "")
        key_boire = os.getenv("LITELLM_API_KEY_BOIRE", "")
        key_perso = os.getenv("LITELLM_API_KEY_PERSO", "")

        active_key = os.getenv("LITELLM_API_KEY", "")
        # Déréférencement automatique si LITELLM_API_KEY pointe vers une variable ou un alias
        alias_map = {
            "LITELLM_API_KEY_BOIRE": key_boire,
            "${LITELLM_API_KEY_BOIRE}": key_boire,
            "BOIRE": key_boire,
            "boire": key_boire,
            "LITELLM_API_KEY_METRO": key_metro,
            "${LITELLM_API_KEY_METRO}": key_metro,
            "METRO": key_metro,
            "metro": key_metro,
            "LITELLM_API_KEY_PERSO": key_perso,
            "${LITELLM_API_KEY_PERSO}": key_perso,
            "PERSO": key_perso,
            "perso": key_perso,
        }
        if active_key in alias_map and alias_map[active_key]:
            active_key = alias_map[active_key]
        elif active_key and not active_key.startswith("sk-"):
            clean_ref = active_key.strip("${}").strip()
            if clean_ref in os.environ and os.environ[clean_ref].startswith("sk-"):
                active_key = os.environ[clean_ref]

        if not active_key:
            secret_active = Path.home() / ".secrets" / "nmedia-key"
            if secret_active.exists():
                try:
                    active_key = secret_active.read_text(encoding="utf-8").strip()
                except Exception:
                    pass

        label = "Inconnue"
        if active_key:
            if key_boire and active_key == key_boire:
                label = "Boire et Frère"
            elif key_metro and active_key == key_metro:
                label = "Metro"
            elif key_perso and active_key == key_perso:
                label = "Perso (Générale)"
            elif "sk-o2o1" in active_key:
                label = "Boire et Frère"
            elif "sk-m3N2" in active_key:
                label = "Metro"
            elif "sk-jeUj" in active_key:
                label = "Perso (Générale)"

        masked = active_key[:7] + "..." + active_key[-4:] if len(active_key) > 12 else active_key
        return {
            "key_label": label,
            "key_masked": masked,
            "key_raw": active_key,
        }

    @classmethod
    def calculate_cost(cls, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calcule le coût estimé en USD."""
        clean_model = model.replace("nmedia_cloud/", "").replace("openai/", "").replace("anthropic/", "").replace("gemini/", "")
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
        Supporte la distinction bi-source ('llm_nmedia_cloud' vs 'antigravity-chat').
        """
        root = root_dir or Path(".")
        key_info = cls.resolve_active_key_info()
        resolved_key_label = key_label or key_info["key_label"]

        total_tokens = prompt_tokens + completion_tokens
        cost_usd = cls.calculate_cost(model, prompt_tokens, completion_tokens)

        # Normalisation stricte de la source LLM : 'llm_nmedia_cloud' vs 'antigravity-chat'
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
        except Exception as e:
            logger.warning(f"Impossible d'écrire dans le token ledger global ({global_ledger}): {e}")

        # 2. Écriture par projet
        if project_name and project_name != "Global":
            proj_dir = root / "Projects" / project_name / "memory"
            if proj_dir.exists():
                proj_ledger = proj_dir / "token_ledger.jsonl"
                try:
                    with open(proj_ledger, "a", encoding="utf-8") as f:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                except Exception as e:
                    logger.warning(f"Impossible d'écrire dans le token ledger projet ({proj_ledger}): {e}")

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
                    if project_name and project_name.lower() not in entry.get("project", "").lower():
                        continue
                    if date_filter:
                        ts = entry.get("timestamp", "")
                        if not ts.startswith(date_filter):
                            continue
                    entries.append(entry)
                except Exception as e:
                    logger.debug(f"Ligne JSON invalide ignorée dans token ledger: {e}")
        except Exception as e:
            logger.warning(f"Erreur de lecture du token ledger ({ledger_path}): {e}")

        return entries

    @classmethod
    def generate_report(
        cls,
        project_name: Optional[str] = None,
        date_filter: Optional[str] = None,
        top_n: int = 10,
        root_dir: Optional[Path] = None,
    ) -> str:
        """Génère un rapport ASCII complet d'audit des tokens et des coûts."""
        entries = cls.load_entries(project_name=project_name, date_filter=date_filter, root_dir=root_dir)

        today_str = date_filter or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        title_target = f"PROJET '{project_name}'" if project_name else "TOUS PROJETS"

        lines = [
            "=" * 70,
            f" 📊 AUDIT DES INTERACTIONS & TOKENS LITELLM - {title_target}",
            f" Période : {today_str} | Total interactions enregistrées : {len(entries)}",
            "=" * 70,
        ]

        if not entries:
            lines.append(f"\n [i] Aucune interaction enregistrée pour la période ({today_str}).")
            lines.append("=" * 70)
            return "\n".join(lines)

        # Agrégations
        total_tokens = sum(e.get("total_tokens_est", 0) for e in entries)
        total_cost = sum(e.get("cost_usd_est", 0.0) for e in entries)

        project_stats: Dict[str, Dict[str, Any]] = {}
        key_stats: Dict[str, Dict[str, Any]] = {}
        model_stats: Dict[str, Dict[str, Any]] = {}

        for e in entries:
            p = e.get("project", "Inconnu")
            k = e.get("key_label", "Inconnue")
            m = e.get("model", "Inconnu").replace("nmedia_cloud/", "")
            tok = e.get("total_tokens_est", 0)
            c = e.get("cost_usd_est", 0.0)

            # Projet
            if p not in project_stats:
                project_stats[p] = {"count": 0, "tokens": 0, "cost": 0.0}
            project_stats[p]["count"] += 1
            project_stats[p]["tokens"] += tok
            project_stats[p]["cost"] += c

            # Clé
            if k not in key_stats:
                key_stats[k] = {"count": 0, "tokens": 0, "cost": 0.0}
            key_stats[k]["count"] += 1
            key_stats[k]["tokens"] += tok
            key_stats[k]["cost"] += c

            # Modèle
            if m not in model_stats:
                model_stats[m] = {"count": 0, "tokens": 0, "cost": 0.0}
            model_stats[m]["count"] += 1
            model_stats[m]["tokens"] += tok
            model_stats[m]["cost"] += c

        # 1. Résumé Global
        lines.append(f"\n 💰 TOTAL GÉNÉRAL : {total_tokens:,} tokens (~{total_tokens/1_000_000:.3f} M) | Coût estimé : {total_cost:.4f} $")

        # 2. Ventilation par Projet
        lines.append("\n 📁 VENTILATION PAR PROJET :")
        lines.append(" " + "-" * 68)
        lines.append(f"   {'Projet':<28} | {'Interactions':<12} | {'Tokens (M)':<10} | {'Coût ($)':<8}")
        lines.append(" " + "-" * 68)
        for p, s in sorted(project_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
            tok_m = s["tokens"] / 1_000_000.0
            lines.append(f"   {p:<28} | {s['count']:<12} | {tok_m:9.3f}M | {s['cost']:7.4f} $")

        # 3. Ventilation par Clé LiteLLM
        lines.append("\n 🔑 VENTILATION PAR CLÉ LITELLM :")
        lines.append(" " + "-" * 68)
        lines.append(f"   {'Clé':<28} | {'Interactions':<12} | {'Tokens (M)':<10} | {'Coût ($)':<8}")
        lines.append(" " + "-" * 68)
        for k, s in sorted(key_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
            tok_m = s["tokens"] / 1_000_000.0
            lines.append(f"   {k:<28} | {s['count']:<12} | {tok_m:9.3f}M | {s['cost']:7.4f} $")

        # 4. Top N Interactions les plus lourdes
        lines.append(f"\n 🚨 TOP {top_n} INTERACTIONS LES PLUS CONSOMMATRICES :")
        lines.append(" " + "-" * 68)
        sorted_entries = sorted(entries, key=lambda x: x.get("total_tokens_est", 0), reverse=True)[:top_n]
        for idx, e in enumerate(sorted_entries, 1):
            ts = e.get("timestamp", "")[11:19]
            act = e.get("action", "action")
            tgt = e.get("target", "N/A")
            tok = e.get("total_tokens_est", 0)
            cost = e.get("cost_usd_est", 0.0)
            mod = e.get("model", "").replace("nmedia_cloud/", "")
            key = e.get("key_label", "Inconnue")
            lines.append(f"   {idx:2d}. [{ts}] {act:<14} | Cible: {tgt:<18} | {tok:,} tok ({cost:.4f} $) | Clé: {key}")
            if e.get("context_contributors"):
                top_files = ", ".join(e["context_contributors"][:3])
                lines.append(f"       ↳ Fichiers injectés : {top_files}")

        lines.append("=" * 70)
        return "\n".join(lines)
