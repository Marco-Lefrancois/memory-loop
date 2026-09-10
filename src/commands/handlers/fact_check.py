# -*- coding: utf-8 -*-
"""
CLI Handler for 'fact-check' command (mLoop Core - ADR-0326).

Exécute l'audit de vérité terrain NLI sur une User Story
et affiche un bilan de conformité avec les preuves documentaires.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Any

from src.engine.fact_check import FactCheckEngine, VerdictEnum
from src.cli import ZeroFluffConsole
from src.utils.lexicon_resolver import SemanticLexiconResolver


def handle_fact_check(args: argparse.Namespace, state: Optional[Any] = None, project_path: Optional[Path] = None) -> int:
    """Handler pour la commande 'fact-check'."""
    project_name = getattr(args, "project", None)
    story_query = getattr(args, "story", None)
    strict_mode = getattr(args, "strict", False)

    if not project_name:
        ZeroFluffConsole.error("Le paramètre --project <nom_projet> est obligatoire.")
        return 1

    canonical_project = SemanticLexiconResolver.resolve_project_alias(project_name) or project_name
    project_dir = Path("Projects") / canonical_project
    if not project_dir.exists():
        project_dir = Path.cwd()

    stories_dir = project_dir / "backlog" / "stories"

    if not story_query:
        # Si aucune story n'est spécifiée, chercher la première story du backlog
        all_stories = list(stories_dir.rglob("*.md")) if stories_dir.exists() else []
        if not all_stories:
            ZeroFluffConsole.error(f"Aucune User Story trouvée sous {stories_dir}.")
            return 1
        target_story = all_stories[0]
    else:
        # Résolution dynamique du récit
        target_story = SemanticLexiconResolver.resolve_story_query(story_query, stories_dir)
        if not target_story or not target_story.exists():
            # Chercher récursivement par nom
            matches = list(stories_dir.rglob(f"*{story_query}*"))
            if matches:
                target_story = matches[0]
            else:
                cand = Path(story_query)
                if cand.exists():
                    target_story = cand
                else:
                    ZeroFluffConsole.error(f"Impossible de trouver le récit pour la requête '{story_query}'.")
                    return 1

    ZeroFluffConsole.section(f"AUDIT FACT-CHECK NLI — {canonical_project.upper()} ({target_story.stem})")
    
    certificate = FactCheckEngine.check_story(
        story_path=target_story,
        project_name=canonical_project,
        persist_evidence=True,
    )

    # Affichage du rapport
    print(f"\n📊 Bilan Fact-Check pour {target_story.name} :")
    print(f"   • Total Affirmations Atomiques : {certificate.total_claims}")
    print(f"   • ✅ Confirmées (Entailment)   : {certificate.entailment_count}")
    print(f"   • ❌ Contradictions            : {certificate.contradiction_count}")
    print(f"   • ⚠️  Sans Preuve (Unsupported) : {certificate.unsupported_count}")
    print(f"   • 🎯 Fact-Check Trust Index    : {certificate.trust_index}%\n")

    if certificate.contradictions:
        print("🚨 CONTRADICTIONS DÉTECTÉES (BLOQUANT) :")
        for c in certificate.contradictions:
            print(f"   - [L{c.get('claim_id')}] {c.get('statement')}")
            print(f"     ➔ {c.get('rationale')}")
            if c.get("proof_source"):
                print(f"     ➔ Source SSOT : {c.get('proof_source')}")
        print("")

    if certificate.admission_of_limits:
        print("─" * 65)
        print("⚠️  LIMITES DE PREUVE (ADMISSION OF LIMITS) :")
        print(f"   {certificate.admission_of_limits}")
        print("─" * 65 + "\n")

    if certificate.is_compliant:
        ZeroFluffConsole.success(f"Certificat Fact-Check ÉMIS : {certificate.status} (Trust Index: {certificate.trust_index}%)")
        return 0
    else:
        if strict_mode or certificate.contradiction_count > 0:
            ZeroFluffConsole.error(f"Certificat Fact-Check REJETÉ : {certificate.status} (Contradictions ou score insuffisant)")
            return 1
        else:
            ZeroFluffConsole.warning(f"Certificat Fact-Check ATTENTION : {certificate.status} (Exigences non documentées)")
            return 0
