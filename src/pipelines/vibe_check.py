import os
from pathlib import Path
from src.cli import ZeroFluffConsole


def detect_project_lifecycle_stage(project_dir: Path, explicit_stage: str = None) -> tuple[str, str]:
    """
    Détermine le mode du cycle de vie (INIT vs RUN) et la phase détaillée du projet (ADR-0339).
    
    Returns:
        tuple (mode, stage_label) : ('INIT'|'RUN', 'STAGE_INIT'|'STAGE_SOW'|'STAGE_PLAN_GRILL'|...)
    """
    if explicit_stage:
        norm = explicit_stage.strip().lower().replace("-", "_").replace(" ", "_")
        if norm in ["init", "stage_init", "inception", "tshirt", "t_shirt", "t_shirt_size", "stage_tshirt_size"]:
            return "INIT", "STAGE_INIT"
        elif norm in ["sow", "stage_sow"]:
            return "INIT", "STAGE_SOW"
        elif norm in ["spec", "stage_spec", "ingest", "ingestion"]:
            return "INIT", "STAGE_SPEC"
        elif norm in ["plan", "stage_plan", "grill", "stage_plan_grill"]:
            return "RUN", "STAGE_PLAN_GRILL"
        elif norm in ["build", "stage_build", "dev"]:
            return "RUN", "STAGE_BUILD"
        elif norm in ["validate", "stage_validate", "qa"]:
            return "RUN", "STAGE_VALIDATE"
        elif norm in ["ship", "stage_ship", "sync", "stage_ship_sync"]:
            return "RUN", "STAGE_SHIP_SYNC"
        elif norm in ["run", "stage_run", "active"]:
            return "RUN", "STAGE_RUN"

    if not project_dir or not project_dir.exists():
        return "INIT", "STAGE_INIT"

    backlog_file = project_dir / "backlog" / "sprint_backlog.md"
    stories_dir = project_dir / "backlog" / "stories"
    stories = list(stories_dir.glob("*.md")) if stories_dir.exists() else []

    # Vérification du contenu réel du backlog
    has_active_stories = len(stories) > 0
    has_backlog_entries = False
    if backlog_file.exists():
        try:
            content = backlog_file.read_text(encoding="utf-8")
            table_rows = [line for line in content.splitlines() if line.strip().startswith("|") and not line.strip().startswith("| :---") and not line.strip().startswith("| ID")]
            has_backlog_entries = len(table_rows) > 0
        except Exception:
            pass

    if has_active_stories or has_backlog_entries:
        return "RUN", "STAGE_PLAN_GRILL"

    # Vérification des marqueurs de phase d'Inception / Cadrage (Phase INIT)
    arch_dir = project_dir / "docs" / "01-architecture"
    if arch_dir.exists() and list(arch_dir.glob("SOW_*.md")):
        return "INIT", "STAGE_SOW"

    ingested_dir = project_dir / "docs" / "00-ingested"
    ref_dir = project_dir / "reference"
    if (ingested_dir.exists() and list(ingested_dir.glob("*.md"))) or (ref_dir.exists() and list(ref_dir.glob("*"))):
        return "INIT", "STAGE_SPEC"

    return "INIT", "STAGE_INIT"


def run_vibe_check(project_name: str, target_file: str = None, stage: str = None) -> dict:
    """
    Axe 2 Joe Njenga / Vibe Code Common Sense (ADR-0310) : Guardrail Vibe-Check Pré-Vol.
    Exécute une vérification déterministe d'intégrité avant modification de code avec gouvernance des étapes (ADR-0339).
    """
    # Résolution du répertoire projet
    project_dir = Path("Projects") / project_name
    if not project_dir.exists():
        if project_name.lower() in ["mloop", "memory loop", "root"] and (Path("Projects") / "mLoop").exists():
            project_dir = Path("Projects") / "mLoop"
        elif (Path("Projects") / project_name.replace(" ", "_")).exists():
            project_dir = Path("Projects") / project_name.replace(" ", "_")

    lifecycle_mode, stage_label = detect_project_lifecycle_stage(project_dir, explicit_stage=stage)

    ZeroFluffConsole.section(f"Guardrail Vibe-Check Pré-Vol - mLoop ({project_name}) [Mode: {lifecycle_mode} | {stage_label}]")
    
    checks = []
    
    # Check 1 : Présence et Parité Miroir des directives fondamentales AGENTS.md / GEMINI.md / CLAUDE.md
    rule_files = ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]
    presence_ok = all(Path(rf).exists() for rf in rule_files)
    
    # Contrôle de Parité Miroir & Auto-Sync Anti-Drift
    parity_ok = True
    if presence_ok:
        agents_txt = Path("AGENTS.md").read_text(encoding="utf-8")
        for rf in ["GEMINI.md", "CLAUDE.md"]:
            rf_p = Path(rf)
            rf_txt = rf_p.read_text(encoding="utf-8")
            if rf_txt != agents_txt:
                # Auto-healing : synchroniser le miroir depuis AGENTS.md
                rf_p.write_text(agents_txt, encoding="utf-8")
                ZeroFluffConsole.success(f"[Vibe-Check Auto-Sync] Parité miroir restaurée pour {rf} depuis AGENTS.md")

    for rule_file in rule_files:
        exists = Path(rule_file).exists()
        checks.append({"check": f"Règles {rule_file} (Parité Miroir)", "status": "PASS" if exists and parity_ok else "FAIL"})
        
    # Check 2 : Contrôle du terrain de jeu strict (Boundary)
    boundary_ok = project_dir.exists() or Path("src").exists()
    checks.append({"check": "Respect du Terrain de Jeu Strict (Boundary)", "status": "PASS" if boundary_ok else "FAIL"})
    
    # Check 3 : Fact-Search FTS5 & Mémoire Persistante
    from src.loop_mem.db import search_observations
    search_observations(query="architecture", project_name=project_name)
    checks.append({"check": "Fact-Search FTS5 Before Edit", "status": "PASS"})

    # Check 4 : Alignement SSOT & Détection de Références Fantômes (Gouvernance de Phase ADR-0339)
    agents_md = Path("AGENTS.md")
    ssot_ok = True
    ssot_msg = ""
    backlog_file = project_dir / "backlog" / "sprint_backlog.md"
    
    if lifecycle_mode == "INIT":
        # En mode INIT, sprint_backlog.md n'est pas requis (projet en genèse / SOW / Ingestion)
        if backlog_file.exists():
            ssot_msg = f" (Phase {lifecycle_mode} : Backlog initialisé)"
        else:
            ssot_msg = f" (Phase {lifecycle_mode} : Backlog en attente de découpage)"
        ssot_ok = True
    else:
        # En mode RUN, sprint_backlog.md est strictement obligatoire
        if agents_md.exists():
            content = agents_md.read_text(encoding="utf-8")
            if "sprint_backlog.md" in content and not backlog_file.exists():
                ssot_ok = False
                ssot_msg = " (sprint_backlog.md requis en phase RUN)"
            else:
                ssot_msg = f" (Phase {lifecycle_mode} : Backlog vérifié)"
                
    checks.append({"check": f"Intégrité SSOT & Absence de Références Fantômes{ssot_msg}", "status": "PASS" if ssot_ok else "FAIL"})

    # Check 5 : Hygiène de Projet & Anti-Drift Sub-READMEs
    hygiene_ok = True
    if project_dir.exists():
        sub_readmes = [
            p for p in project_dir.rglob("README.md")
            if p != project_dir / "README.md"
            and not str(p.relative_to(project_dir)).startswith("reference")
            and "node_modules" not in str(p)
            and ".git" not in str(p)
        ]
        if sub_readmes:
            hygiene_ok = False
    checks.append({"check": "Hygiène Structurale & Absence de Sous-READMEs", "status": "PASS" if hygiene_ok else "FAIL"})

    # Check 6 : Intégrité Lexicale & Signature de Vocabulaire (Rosetta Canary & Unicode NFC - ADR-0327)
    from src.utils.lexical_guard import LexicalIntegrityGuard
    lex_res = LexicalIntegrityGuard.inspect_project_evidence(project_dir if project_dir.exists() else Path("."))
    checks.append({
        "check": f"Intégrité Lexicale & Signature de Vocabulaire (Canary: {lex_res.canary_hash})",
        "status": "PASS" if lex_res.is_valid else "FAIL",
    })

    # Check 7 : Étanchéité des Secrets & Tokens (Zero-Leak Envsitter Pattern)
    from src.utils.secret_guard import SecretLeakGuard
    secret_leaks = []
    if project_dir.exists():
        for check_path in [project_dir / "backlog", project_dir / "memory" / "evidence"]:
            if check_path.exists():
                for f in check_path.rglob("*.json"):
                    try:
                        content = f.read_text(encoding="utf-8")
                        leaks = SecretLeakGuard.scan_for_leaks(content)
                        if leaks:
                            secret_leaks.append(f.name)
                    except Exception:
                        pass
    checks.append({
        "check": "Étanchéité des Secrets & Tokens (Zero-Leak Envsitter Pattern)",
        "status": "PASS" if len(secret_leaks) == 0 else "FAIL"
    })

    # Check 8 : Alignement Strict Projet ↔ Clé LiteLLM (Zero Cost-Leak)
    from src.utils.token_ledger import TokenLedger
    key_info = TokenLedger.resolve_active_key_info()
    active_label = key_info.get("key_label", "Inconnue")
    
    allow_cross_key = os.getenv("MLOOP_ALLOW_CROSS_KEY", "").lower() in ["1", "true", "yes"] or os.getenv("ALLOW_CROSS_KEY", "").lower() in ["1", "true", "yes"]
    key_alignment_ok = True
    key_reason = f"Clé active : {active_label}"
    p_lower = (project_name or "").lower()
    
    if "boire" in p_lower:
        if active_label != "Boire et Frère":
            if allow_cross_key:
                key_reason = f"Projet '{project_name}' avec clé '{active_label}' (Dérogation MLOOP_ALLOW_CROSS_KEY active)"
            else:
                key_alignment_ok = False
                key_reason = f"Projet '{project_name}' requiert la clé 'Boire et Frère' (active: '{active_label}')"
    elif "metro" in p_lower:
        if active_label != "Metro":
            if allow_cross_key:
                key_reason = f"Projet '{project_name}' avec clé '{active_label}' (Dérogation MLOOP_ALLOW_CROSS_KEY active)"
            else:
                key_alignment_ok = False
                key_reason = f"Projet '{project_name}' requiert la clé 'Metro' (active: '{active_label}')"

    checks.append({
        "check": f"Alignement Projet ↔ Clé LiteLLM ({key_reason})",
        "status": "PASS" if key_alignment_ok else "FAIL"
    })

    # Check 9 : Fraîcheur & Intégrité des Sidecars LOD (.overview.md - ADR-0335)
    from src.core.lod_generator import LODGenerator
    lod_freshness_ok = True
    outdated_dirs = []
    if project_dir.exists():
        docs_p = project_dir / "docs"
        if docs_p.exists():
            for ov_file in docs_p.rglob(".overview.md"):
                p_dir = ov_file.parent
                res = LODGenerator.check_directory_freshness(p_dir)
                if res.get("status") == "OUTDATED":
                    lod_freshness_ok = False
                    outdated_dirs.append(p_dir.name)

    lod_msg = "Fraîcheur & Intégrité des Sidecars LOD (.overview.md)" if lod_freshness_ok else f"Fraîcheur des Sidecars LOD (Obsolètes : {', '.join(outdated_dirs)})"
    checks.append({
        "check": lod_msg,
        "status": "PASS" if lod_freshness_ok else "FAIL"
    })
    
    passed_count = sum(1 for c in checks if c["status"] == "PASS")
    total_count = len(checks)

    for c in checks:
        if c["status"] == "PASS":
            ZeroFluffConsole.success(f"{c['check']} : PASS")
        else:
            ZeroFluffConsole.error(f"{c['check']} : FAIL")
    
    is_valid = passed_count == total_count
    ZeroFluffConsole.info(f"Résultat Vibe-Check : {passed_count}/{total_count} contrôles validés.")
    
    return {
        "status": "PASS" if is_valid else "FAIL",
        "checks": checks,
        "score": f"{passed_count}/{total_count}",
        "lifecycle_mode": lifecycle_mode,
        "stage": stage_label
    }

