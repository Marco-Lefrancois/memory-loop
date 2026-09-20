# -*- coding: utf-8 -*-
"""
Rapport budgétaire des tokens LLM (ADR-0329 / MLOOP-101-BE).
Sous-module du package token_ledger.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def generate_report(
    entries: List[Dict[str, Any]],
    project_name: Optional[str] = None,
    date_filter: Optional[str] = None,
    top_n: int = 10,
) -> str:
    """Génère un rapport ASCII complet d'audit des tokens et des coûts."""
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

    for e in entries:
        p = e.get("project", "Inconnu")
        k = e.get("key_label", "Inconnue")
        tok = e.get("total_tokens_est", 0)
        c = e.get("cost_usd_est", 0.0)

        if p not in project_stats:
            project_stats[p] = {"count": 0, "tokens": 0, "cost": 0.0}
        project_stats[p]["count"] += 1
        project_stats[p]["tokens"] += tok
        project_stats[p]["cost"] += c

        if k not in key_stats:
            key_stats[k] = {"count": 0, "tokens": 0, "cost": 0.0}
        key_stats[k]["count"] += 1
        key_stats[k]["tokens"] += tok
        key_stats[k]["cost"] += c

    # 1. Résumé Global
    lines.append(
        f"\n 💰 TOTAL GÉNÉRAL : {total_tokens:,} tokens (~{total_tokens / 1_000_000:.3f} M)"
        f" | Coût estimé : {total_cost:.4f} $"
    )

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
    sorted_entries = sorted(entries, key=lambda x: x.get("total_tokens_est", 0), reverse=True)[
        :top_n
    ]
    for idx, e in enumerate(sorted_entries, 1):
        ts = e.get("timestamp", "")[11:19]
        act = e.get("action", "action")
        tgt = e.get("target", "N/A")
        tok = e.get("total_tokens_est", 0)
        cost = e.get("cost_usd_est", 0.0)
        key = e.get("key_label", "Inconnue")
        lines.append(
            f"   {idx:2d}. [{ts}] {act:<14} | Cible: {tgt:<18} | {tok:,} tok ({cost:.4f} $) | Clé: {key}"
        )
        if e.get("context_contributors"):
            top_files = ", ".join(e["context_contributors"][:3])
            lines.append(f"       ↳ Fichiers injectés : {top_files}")

    lines.append("=" * 70)
    return "\n".join(lines)
