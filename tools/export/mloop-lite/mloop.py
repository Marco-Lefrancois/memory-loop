#!/usr/bin/env python3
"""
mLoop Lite — Framework Méthodologique Distillé en 4 Phases
INCEPTION | SPEC / INGEST | PLAN | VALIDATE

Outils essentiels inclus :
- mloop init / inception  : Phase 0 (Amorçage de projet et profil métier)
- mloop ingest            : Phase 1 (Normalisation, MarkItDown, RapidOCR & FTS5)
- mloop crawl             : Ingestion web / scraping Markdown propre
- mloop plan              : Phase 2 (Fact-Search & Cadrage Grill-with-Docs)
- mloop validate          : Phase 3 (Gatekeeper structurel & EvidencePacks)
- mloop export            : 🌟 Export exécutif HTML / PDF corporatif imprimable
- mloop questions         : 🌟 Registre des questions ouvertes & blocages (OQ-XXX)
- mloop adr               : 🌟 Registre universel des décisions (ADR-XXXX)
- mloop lexique           : 🌟 Lexique métier ubiquitaire (anti-glissement lexical)
- mloop check             : 🌟 Guardrail pré-vol d'intégrité (Index, fichiers, alertes)
- mloop resume            : 🌟 Anti-Amnésie de session (État, décisions, prochaine action)
- mloop status            : Tableau de bord visuel des 4 phases
"""
import sys
import os
import re
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent

def resolve_project_dir(project_arg: str = None) -> Path:
    """Résout le répertoire de travail du projet (multi-projets ou autonome)."""
    if project_arg:
        p_dir = BASE_DIR / "projects" / project_arg
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir
    if Path("mloop.json").exists():
        return Path.cwd()
    projects_dir = BASE_DIR / "projects"
    if projects_dir.exists():
        all_projs = [p for p in projects_dir.iterdir() if p.is_dir() and (p / "mloop.json").exists()]
        if len(all_projs) == 1:
            return all_projs[0]
        elif len(all_projs) > 1:
            projs_names = [p.name for p in all_projs]
            print(f"⚠️ Plusieurs projets détectés sous projects/ : {', '.join(projs_names)}")
            print("👉 Précisez le projet avec : --project <nom>")
            sys.exit(1)
    return Path.cwd()

# -----------------------------------------------------------------------------
# PHASE 0 : INCEPTION
# -----------------------------------------------------------------------------
def cmd_inception(role: str, project_name: str = None, project_arg: str = None):
    profile_file = BASE_DIR / "profiles" / f"{role}.json"
    if not profile_file.exists():
        available = [f.stem for f in (BASE_DIR / "profiles").glob("*.json")]
        print(f"❌ Rôle inconnu '{role}'. Rôles disponibles : {', '.join(available)}")
        sys.exit(1)
        
    profile_data = json.loads(profile_file.read_text(encoding="utf-8"))
    target_name = project_arg or project_name or Path.cwd().name
    if project_arg or (BASE_DIR / "projects").exists():
        target_dir = BASE_DIR / "projects" / target_name
    else:
        target_dir = Path.cwd()
        
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*75}")
    print(f"🚀 [PHASE 0 : INCEPTION] — Initialisation mLoop Lite")
    print(f"   Rôle Métier : {profile_data['name']} ({role.upper()})")
    print(f"   Projet      : {target_name}")
    print(f"   Emplacement : {target_dir}")
    print(f"{'='*75}")
    
    (target_dir / "reference").mkdir(exist_ok=True)
    (target_dir / "docs" / "adr").mkdir(parents=True, exist_ok=True)
    (target_dir / "deliverables").mkdir(exist_ok=True)
    (target_dir / "memory" / "evidence").mkdir(parents=True, exist_ok=True)
    
    # 1. Copie des gabarits du rôle depuis standards/blueprints
    dest_tpl = target_dir / "deliverables" / "templates"
    dest_tpl.mkdir(parents=True, exist_ok=True)
    role_tpl_dir = BASE_DIR / "standards" / "blueprints" / role
    if not role_tpl_dir.exists():
        role_tpl_dir = BASE_DIR / "standards" / "blueprints" / role
    if role_tpl_dir.exists():
        for tpl_file in role_tpl_dir.glob("*.md"):
            shutil.copy2(tpl_file, dest_tpl / tpl_file.name)
            
    # 1b. Déploiement de .agents/ (rules + skills) et standards/ dans le projet
    (target_dir / ".agents" / "rules").mkdir(parents=True, exist_ok=True)
    (target_dir / ".agents" / "skills" / "grill").mkdir(parents=True, exist_ok=True)
    if (BASE_DIR / ".agents" / "rules").exists():
        for rf in (BASE_DIR / ".agents" / "rules").glob("*.md"):
            shutil.copy2(rf, target_dir / ".agents" / "rules" / rf.name)
    shutil.copy2(BASE_DIR / "SKILL.md", target_dir / ".agents" / "skills" / "grill" / "SKILL.md")
    # 1c. Déploiement de opencode.json et .env dans le projet
    if (BASE_DIR / "opencode.json").exists():
        shutil.copy2(BASE_DIR / "opencode.json", target_dir / "opencode.json")
    if (BASE_DIR / ".env").exists():
        shutil.copy2(BASE_DIR / ".env", target_dir / ".env")
    if (BASE_DIR / ".env.example").exists():
        shutil.copy2(BASE_DIR / ".env.example", target_dir / ".env.example")
    if (BASE_DIR / ".gitignore").exists():
        shutil.copy2(BASE_DIR / ".gitignore", target_dir / ".gitignore")


    # Lexique
    lexique_target = target_dir / "docs" / "LEXIQUE.md"
    if not lexique_target.exists():
        lex_tpl = BASE_DIR / "standards" / "blueprints" / "common" / "lexique.template.md"
        if lex_tpl.exists():
            lex_content = lex_tpl.read_text(encoding="utf-8").replace("<NOM_DU_PROJET>", target_name)
            lexique_target.write_text(lex_content, encoding="utf-8")
            print(f"📖 Lexique Métier initialisé : docs/LEXIQUE.md")
    # 2b. Pré-chargement des 5 ADRs Fondateurs
    baseline_adr_dir = BASE_DIR / "standards" / "blueprints" / "common" / "baseline_adrs"
    dest_adr_dir = target_dir / "docs" / "adr"
    dest_adr_dir.mkdir(parents=True, exist_ok=True)
    if baseline_adr_dir.exists():
        for adr_f in baseline_adr_dir.glob("ADR-*.md"):
            dest_f = dest_adr_dir / adr_f.name
            if not dest_f.exists():
                shutil.copy2(adr_f, dest_f)
        print(f"🏛️ 5 ADRs Fondateurs initialisés sous docs/adr/")

            
    # Questions Ouvertes
    qo_target = target_dir / "docs" / "QUESTIONS_OUVERTES.md"
    if not qo_target.exists():
        qo_tpl = BASE_DIR / "standards" / "blueprints" / "common" / "questions_ouvertes.template.md"
        if qo_tpl.exists():
            qo_content = qo_tpl.read_text(encoding="utf-8").replace("<NOM_DU_PROJET>", target_name)
            qo_target.write_text(qo_content, encoding="utf-8")
            print(f"❓ Registre des Questions Ouvertes : docs/QUESTIONS_OUVERTES.md")
            
    # Configuration
    project_config = {
        "project_name": target_name,
        "active_role": role,
        "role_name": profile_data["name"],
        "mission": profile_data["mission"],
        "phase": "0_INCEPTION",
        "deliverables_available": profile_data["deliverables"],
        "grill_focus": profile_data["grill_focus"],
        "created_at": datetime.now().isoformat(),
        "version": "1.0.0-lite"
    }
    (target_dir / "mloop.json").write_text(json.dumps(project_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    
    # Skill
    agents_grill = target_dir / ".agents" / "skills" / "grill"
    agents_grill.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BASE_DIR / "SKILL.md", agents_grill / "SKILL.md")
    
    print(f"\n✅ Projet initialisé avec succès !")
    print(f"📁 Espaces créés sous {target_dir.name}/ :")
    print(f"   ├── 📂 reference/    ➔ Déposez vos matières premières (Word, Excel, PDFs, scans, notes)")
    print(f"   ├── 📂 docs/         ➔ Base SSOT indexée (LEXIQUE.md, QUESTIONS_OUVERTES.md, adr/)")
    print(f"   ├── 📂 deliverables/ ➔ Vos livrables d'affaires et gabarits officiels")
    print(f"   └── 📂 memory/       ➔ Index FTS5, traçabilité et EvidencePacks")
    print(f"\n💡 Étape suivante : Déposez vos fichiers dans reference/, puis lancez :")
    print(f"   👉 python mloop.py ingest" + (f" --project {target_name}" if target_dir != Path.cwd() else ""))

# -----------------------------------------------------------------------------
# PHASE 1 : SPEC / INGEST
# -----------------------------------------------------------------------------
def cmd_ingest(project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    sys.path.insert(0, str(BASE_DIR / "core"))
    import ingest_engine
    import fts_engine
    
    print(f"\n{'='*75}")
    print(f"⚙️ [PHASE 1 : SPEC / INGEST] — Projet : {target_dir.name}")
    print(f"{'='*75}")
    
    src_p = target_dir / "reference"
    dest_p = target_dir / "docs"
    db_p = target_dir / "memory" / ".fact_search_index.db"
    
    stats = ingest_engine.run_ingestion_pipeline(src_p, dest_p)
    print(f"📥 Documents traités depuis 'reference' vers 'docs' :")
    print(f"   • Fichiers textes/Markdown copiés         : {stats['copied']}")
    print(f"   • Documents Office/PDF (MarkItDown)       : {stats['converted_markitdown']}")
    print(f"   • Images numérisées / Scans (RapidOCR)    : {stats['converted_ocr']}")
    
    db_p.parent.mkdir(parents=True, exist_ok=True)
    fts_stats = fts_engine.index_directory(str(dest_p), db_p)
    print(f"🗄️ Index SQLite FTS5 actualisé : {fts_stats['indexed_files']} fichier(s), {fts_stats['total_passages']} passages indexés.")
    
    cfg_p = target_dir / "mloop.json"
    if cfg_p.exists():
        try:
            cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
            cfg["phase"] = "1_SPEC_INGEST"
            cfg["last_ingest"] = datetime.now().isoformat()
            cfg_p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception:
            pass
    print(f"\n✅ Ingestion terminée avec succès !")

# -----------------------------------------------------------------------------
# CRAWLER
# -----------------------------------------------------------------------------
def cmd_crawl(url: str, project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    sys.path.insert(0, str(BASE_DIR / "core"))
    import crawler
    import fts_engine
    
    dest_p = target_dir / "docs"
    crawled_file = crawler.crawl_url(url, dest_p)
    db_p = target_dir / "memory" / ".fact_search_index.db"
    if db_p.exists():
        fts_engine.index_directory(str(dest_p), db_p)
        print("🗄️ Base FTS5 mise à jour avec la nouvelle page web.")

# -----------------------------------------------------------------------------
# PHASE 2 : PLAN
# -----------------------------------------------------------------------------
def cmd_plan(query: str = None, topic: str = None, project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    sys.path.insert(0, str(BASE_DIR / "core"))
    import fts_engine
    
    db_p = target_dir / "memory" / ".fact_search_index.db"
    if not db_p.exists():
        cmd_ingest(project_arg)
        
    search_term = query or topic or "règle"
    results = fts_engine.search_passages(search_term, limit=3, db_path=db_p)
    
    print(f"\n{'='*75}")
    print(f"🎯 [PHASE 2 : PLAN & ARBITRAGE] — Projet : {target_dir.name}")
    print(f"🔍 Preuves factuelles pour : \"{search_term}\" ({len(results)} extraits)\n")
    
    for i, r in enumerate(results, 1):
        print(f"[{i}] 📄 {r['file_path']} (L.{r['start_line']}–{r['end_line']}) — Section: {r['section']}")
        print(f"    Extrait verbatim : {r['snippet']}\n")

# -----------------------------------------------------------------------------
# PHASE 3 : VALIDATE
# -----------------------------------------------------------------------------
def cmd_validate(project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    print(f"\n{'='*75}")
    print(f"🛡️ [PHASE 3 : VALIDATE / QA] — Projet : {target_dir.name}")
    print(f"{'='*75}")
    
    deliv_p = target_dir / "deliverables"
    deliv_files = list(deliv_p.glob("*.md")) if deliv_p.exists() else []
    print(f"📋 1. Livrables d'Affaires ({len(deliv_files)} document(s)) :")
    all_valid = True
    for f in deliv_files:
        lines = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        status = "✅ Conforme" if lines >= 20 else "⚠️ Trop court"
        if lines < 20: all_valid = False
        print(f"   {status} ➔ {f.name} ({lines} lignes)")
        
    # Check questions ouvertes
    qo_p = target_dir / "docs" / "QUESTIONS_OUVERTES.md"
    pending_count = 0
    if qo_p.exists():
        content = qo_p.read_text(encoding="utf-8")
        pending_count = content.count("EN_ATTENTE")
    print(f"\n❓ 2. Questions Ouvertes : {pending_count} en attente du client")
    
    # Check ADRs
    adrs = list((target_dir / "docs" / "adr").glob("ADR-*.md"))
    print(f"🏛️ 3. Décisions Figées (ADR) : {len(adrs)} décision(s) enregistrée(s)")
    
    print("-" * 75)
    if all_valid and pending_count == 0:
        print("🏆 VERDICT QUALITÉ : 100% CONFORME (Prêt pour Livraison / Dev-Ready) ✅")
    else:
        print("🟡 VERDICT QUALITÉ : ACTION REQUISE (Compléter le livrable ou résoudre les blocages)")

# -----------------------------------------------------------------------------
# ESSENTIEL 1 : EXPORT EXÉCUTIF CLIENT (HTML / PDF)
# -----------------------------------------------------------------------------
def cmd_export(file_name: str = None, project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    sys.path.insert(0, str(BASE_DIR / "core"))
    import exporter
    
    deliv_dir = target_dir / "deliverables"
    if not file_name:
        candidates = list(deliv_dir.glob("*.md"))
        if not candidates:
            print("❌ Aucun fichier Markdown trouvé dans deliverables/ à exporter.")
            return
        target_file = candidates[0]
    else:
        target_file = deliv_dir / file_name
        if not target_file.exists():
            target_file = Path(file_name)
            
    if not target_file.exists():
        print(f"❌ Fichier introuvable : {target_file}")
        return
        
    out_html = target_dir / "deliverables" / f"{target_file.stem}_EXECUTIF.html"
    exporter.export_to_html(target_file, out_html, target_dir.name)
    print(f"\n{'='*75}")
    print(f"📤 LIVRABLE CLIENT EXÉCUTIF GÉNÉRÉ AVEC SUCCÈS !")
    print(f"{'='*75}")
    print(f"📄 Document HTML : {out_html}")
    print(f"🖨️ Pour obtenir le PDF corporatif : Ouvrez le fichier dans votre navigateur et faites Ctrl + P (Enregistrer en PDF) !")

# -----------------------------------------------------------------------------
# ESSENTIEL 2 : REGISTRE DES QUESTIONS OUVERTES (OQ-XXX)
# -----------------------------------------------------------------------------
def cmd_questions(action: str = None, text: str = None, client: str = None, adr_ref: str = None, project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    qo_file = target_dir / "docs" / "QUESTIONS_OUVERTES.md"
    
    if not qo_file.exists():
        cmd_inception("ba", target_dir.name, project_arg)
        
    content = qo_file.read_text(encoding="utf-8")
    
    # 1. Lister les questions
    if not action or action == "list":
        print(f"\n{'='*75}")
        print(f"❓ REGISTRE DES QUESTIONS OUVERTES — {target_dir.name.upper()}")
        print(f"{'='*75}\n")
        lines = [l for l in content.splitlines() if l.strip().startswith("| **OQ-")]
        if not lines:
            print("   ✅ Aucune question ouverte. Tous les points sont clarifiés !")
        else:
            for l in lines:
                print(f"   {l}")
        print(f"\n💡 Pour ajouter une question : python mloop.py questions add \"<Votre question>\"")
        return
        
    # 2. Ajouter une question
    if action == "add":
        if not text:
            print("❌ Veuillez préciser la question à ajouter.")
            return
        # Calcul de l'ID suivant
        existing_ids = re.findall(r'OQ-(\d{4})', content)
        next_id = max([int(i) for i in existing_ids] + [0]) + 1
        id_str = f"OQ-{next_id:04d}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        client_str = client or "Client PO"
        
        new_row = f"| **{id_str}** | {date_str} | {text} | {client_str} | 🔴 Haute | EN_ATTENTE | — |\n"
        
        # Insérer dans le tableau
        if "## 📋 Tableau de Suivi" in content:
            parts = content.split("---", 2)
            content = parts[0] + "---\n\n" + parts[1].strip() + "\n" + new_row + "\n---\n" + (parts[2] if len(parts) > 2 else "")
        else:
            content += "\n" + new_row
            
        qo_file.write_text(content, encoding="utf-8")
        print(f"\n✅ Question ouverte enregistrée : [{id_str}] {text}")
        print(f"💡 Document mis à jour : docs/QUESTIONS_OUVERTES.md")
        return
        
    # 3. Clore une question
    if action == "close":
        if not text: # ici text sert de target ID (ex: OQ-0001)
            print("❌ Précisez l'identifiant de la question à clore (ex: OQ-0001).")
            return
        target_id = text.upper()
        adr_tag = adr_ref or "Arbitré en atelier"
        if target_id not in content:
            print(f"❌ Identifiant {target_id} introuvable dans docs/QUESTIONS_OUVERTES.md.")
            return
        lines = []
        for l in content.splitlines():
            if f"**{target_id}**" in l:
                l = l.replace("EN_ATTENTE", "RÉSOLUE")
                l = re.sub(r'\| — \|$', f'| {adr_tag} |', l)
            lines.append(l)
        qo_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n✅ Question {target_id} marquée comme RÉSOLUE (Reliée à : {adr_tag}) !")

# -----------------------------------------------------------------------------
# ESSENTIEL 3 : GUARDRAIL PRÉ-VOL D'INTÉGRITÉ (mloop check)
# -----------------------------------------------------------------------------
def cmd_check(project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    print(f"\n{'='*75}")
    print(f"🛡️ GUARDRAIL PRÉ-VOL D'INTÉGRITÉ — {target_dir.name.upper()}")
    print(f"{'='*75}\n")
    
    alerts = []
    
    # 1. Vérification des fichiers non ingérés dans reference/
    ref_files = list((target_dir / "reference").glob("**/*.*")) if (target_dir / "reference").exists() else []
    docs_files = list((target_dir / "docs").glob("**/*.*")) if (target_dir / "docs").exists() else []
    
    unmatched = 0
    for rf in ref_files:
        expected = target_dir / "docs" / rf.relative_to(target_dir / "reference").with_suffix(".md")
        if not expected.exists():
            unmatched += 1
            
    if unmatched > 0:
        alerts.append(f"⚠️ {unmatched} fichier(s) dans reference/ n'ont pas encore été ingérés ! (Lancez: python mloop.py ingest)")
    else:
        print("   🟢 Documents : Tous les fichiers de reference/ sont bien ingérés dans docs/.")
        
    # 2. Vérification de l'index FTS5
    db_p = target_dir / "memory" / ".fact_search_index.db"
    if not db_p.exists():
        alerts.append("🔴 Index FTS5 absent ! L'IA n'a aucune base de recherche factuelle (Lancez: python mloop.py ingest).")
    else:
        print("   🟢 Recherche : L'index SQLite FTS5 est actif et prêt.")
        
    # 3. Vérification du Lexique Métier
    lex_p = target_dir / "docs" / "LEXIQUE.md"
    if not lex_p.exists() or len(lex_p.read_text(encoding="utf-8").strip()) < 50:
        alerts.append("🟡 Lexique Métier (docs/LEXIQUE.md) vide ou manquant. Risque de glissement de vocabulaire.")
    else:
        print("   🟢 Lexique : docs/LEXIQUE.md est présent et actif.")
        
    # 4. Vérification des Questions Bloquantes
    qo_p = target_dir / "docs" / "QUESTIONS_OUVERTES.md"
    if qo_p.exists():
        pending = qo_p.read_text(encoding="utf-8").count("EN_ATTENTE")
        if pending > 0:
            alerts.append(f"🔴 Attention : Il reste {pending} question(s) ouverte(s) en attente du client !")
        else:
            print("   🟢 Questions : Aucun point bloquant en suspens.")
            
    print("-" * 75)
    if not alerts:
        print("✨ INTÉGRITÉ PARFAITE : Le projet est 100% prêt pour la session de travail ! 🚀\n")
    else:
        print("🚨 ALERTES DÉTECTÉES :")
        for a in alerts:
            print(f"   {a}")
        print()

# -----------------------------------------------------------------------------
# ESSENTIEL 4 : ANTI-AMNÉSIE DE SESSION (mloop resume)
# -----------------------------------------------------------------------------
def cmd_resume(project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    cfg_p = target_dir / "mloop.json"
    if not cfg_p.exists():
        print(f"❌ Aucun projet détecté sous {target_dir}. Lancez: python mloop.py init")
        return
        
    cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
    
    print(f"\n{'='*75}")
    print(f"🧠 REPRISE DE CONTEXTE ANTI-AMNÉSIE — {cfg.get('project_name').upper()}")
    print(f"   Profil : {cfg.get('role_name')} ({cfg.get('active_role')})")
    print(f"   Phase Active : {cfg.get('phase', '0_INCEPTION')}")
    print(f"{'='*75}\n")
    
    # 1. Les derniers ADRs
    adrs = sorted(list((target_dir / "docs" / "adr").glob("ADR-*.md")), reverse=True)[:2]
    print("🏛️ Dernières Décisions Retenues (ADR) :")
    if not adrs:
        print("   • Aucun ADR pour le moment.")
    else:
        for a in adrs:
            first_line = a.read_text(encoding="utf-8").splitlines()[0]
            print(f"   • {a.name} ➔ {first_line.replace('#', '').strip()}")
            
    # 2. Questions ouvertes urgentes
    qo_p = target_dir / "docs" / "QUESTIONS_OUVERTES.md"
    print("\n❓ Questions Ouvertes Critiques en Attente :")
    if qo_p.exists():
        pending_lines = [l for l in qo_p.read_text(encoding="utf-8").splitlines() if "EN_ATTENTE" in l and "🔴 Haute" in l][:2]
        if not pending_lines:
            print("   • Aucune question haute priorité en attente.")
        else:
            for pl in pending_lines:
                print(f"   • {pl}")
    else:
        print("   • Aucune question ouverte.")
        
    # 3. Dernier livrable
    delivs = list((target_dir / "deliverables").glob("*.md"))
    print("\n📑 Livrables en Cours de Rédaction :")
    if not delivs:
        print("   • Aucun livrable commencé sous deliverables/.")
    else:
        for d in delivs:
            print(f"   • {d.name}")
            
    # 4. Prochaine action suggérée
    phase = cfg.get("phase", "0_INCEPTION")
    print(f"\n💡 Prochaine Action Recommandée :")
    if phase == "0_INCEPTION":
        print("   👉 Déposez vos notes dans reference/ et lancez : python mloop.py ingest")
    elif phase == "1_SPEC_INGEST":
        print("   👉 Lancez la recherche ou le grill : python mloop.py plan --query \"<sujet>\"")
    elif phase == "2_PLAN":
        print("   👉 Rédigez le livrable dans deliverables/, puis validez : python mloop.py validate")
    else:
        print("   👉 Exportez le livrable pour votre client : python mloop.py export")
    print(f"{'='*75}\n")

# -----------------------------------------------------------------------------
# COMMANDES EXISTANTES : ADR, LEXIQUE, STATUS
# -----------------------------------------------------------------------------
def cmd_adr(title: str = None, project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    adr_dir = target_dir / "docs" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    if not title:
        adr_files = sorted(list(adr_dir.glob("ADR-*.md")))
        print(f"\n{'='*75}")
        print(f"🏛️ REGISTRE DES DÉCISIONS (ADR) — {target_dir.name.upper()} ({len(adr_files)} décision(s))")
        print(f"{'='*75}\n")
        if not adr_files:
            print("   ℹ️ Aucun ADR enregistré.")
            return
        for f in adr_files:
            content = f.read_text(encoding="utf-8", errors="ignore")
            status = "ACCEPTÉ" if "ACCEPTÉ" in content else "PROPOSÉ"
            first_line = content.splitlines()[0] if content.splitlines() else f.name
            print(f"   • {f.name} [{status}] ➔ {first_line.replace('#', '').strip()}")
        return
        
    existing = list(adr_dir.glob("ADR-*.md"))
    next_num = len(existing) + 1
    num_str = f"{next_num:04d}"
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:50]
    filename = f"ADR-{num_str}-{slug}.md"
    target_file = adr_dir / filename
    tpl_file = BASE_DIR / "standards" / "blueprints" / "common" / "adr.template.md"
    if tpl_file.exists():
        content = tpl_file.read_text(encoding="utf-8")
        content = content.replace("<NUMERO>", num_str).replace("<TITRE DE LA DÉCISION>", title).replace("<NOM_DU_PROJET>", target_dir.name).replace("<YYYY-MM-DD>", datetime.now().strftime("%Y-%m-%d"))
    else:
        content = f"# 🏛️ ADR-{num_str} : {title}\n"
    target_file.write_text(content, encoding="utf-8")
    print(f"\n✅ Décision d'Architecture enregistrée : docs/adr/{filename}")

def cmd_lexique(term: str = None, project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    lex_file = target_dir / "docs" / "LEXIQUE.md"
    if not lex_file.exists():
        print(f"⚠️ docs/LEXIQUE.md manquant sous {target_dir}.")
        return
    content = lex_file.read_text(encoding="utf-8")
    if not term:
        print(f"\n{'='*75}\n📖 LEXIQUE MÉTIER — {target_dir.name.upper()}\n{'='*75}\n" + content)
        return
    for line in content.splitlines():
        if "|" in line and term.lower() in line.lower():
            print(f"👉 {line}")

def cmd_status(project_arg: str = None):
    target_dir = resolve_project_dir(project_arg)
    cfg_p = target_dir / "mloop.json"
    if not cfg_p.exists():
        print(f"❌ Aucun projet détecté sous {target_dir}.")
        return
    cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
    ref_c = len(list((target_dir / "reference").glob("**/*.*"))) if (target_dir / "reference").exists() else 0
    docs_c = len(list((target_dir / "docs").glob("**/*.*"))) if (target_dir / "docs").exists() else 0
    deliv_c = len(list((target_dir / "deliverables").glob("*.md"))) if (target_dir / "deliverables").exists() else 0
    print(f"\n{'='*75}\n🧭 STATUT DU PROJET — {cfg.get('project_name').upper()}\n   Phase : {cfg.get('phase', '0_INCEPTION')}\n{'='*75}")
    print(f"""
  [PHASE 0 : INCEPTION]  ➔  [PHASE 1 : INGEST]  ➔  [PHASE 2 : PLAN]  ➔  [PHASE 3 : VALIDATE]
      📁 {ref_c} fichier(s)          🗄️ {docs_c} document(s)       📑 {deliv_c} livrable(s)      🛡️ Vérifié
    """)

# -----------------------------------------------------------------------------
# MAIN DISPATCHER
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="mLoop Lite — Framework Méthodologique Distillé en 4 Phases")
    parser.add_argument("--project", "-p", help="Nom du projet cible")
    subparsers = parser.add_subparsers(dest="command")
    
    # Phase 0
    p_init = subparsers.add_parser("init", aliases=["inception"], help="Phase 0 : Inception")
    p_init.add_argument("--role", required=True, choices=["ba", "dev", "qa", "design", "pm", "sales"])
    p_init.add_argument("--name", help="Nom du projet")
    p_init.add_argument("--project", "-p")
    
    # Phase 1
    p_ing = subparsers.add_parser("ingest", help="Phase 1 : Spec / Ingest")
    p_ing.add_argument("--project", "-p")
    
    p_crawl = subparsers.add_parser("crawl", help="mLoop Crawler Web")
    p_crawl.add_argument("url")
    p_crawl.add_argument("--project", "-p")
    
    # Phase 2
    p_plan = subparsers.add_parser("plan", help="Phase 2 : Plan & Arbitrage")
    p_plan.add_argument("--query", "-q")
    p_plan.add_argument("--project", "-p")
    
    # Phase 3
    p_val = subparsers.add_parser("validate", help="Phase 3 : Validate")
    p_val.add_argument("--project", "-p")
    
    # NOUVEAUX OUTILS ESSENTIELS
    p_exp = subparsers.add_parser("export", help="🌟 Export exécutif client (HTML stylé / Imprimable PDF)")
    p_exp.add_argument("file", nargs="?", help="Fichier markdown sous deliverables/ à exporter")
    p_exp.add_argument("--project", "-p")
    
    p_qo = subparsers.add_parser("questions", help="🌟 Registre des questions ouvertes & blocages")
    p_qo.add_argument("action", nargs="?", choices=["list", "add", "close"], default="list")
    p_qo.add_argument("text", nargs="?", help="Texte de la question ou ID (ex: OQ-0001)")
    p_qo.add_argument("--client", help="Nom du responsable côté client")
    p_qo.add_argument("--adr", help="Référence de l'ADR résolvant la question")
    p_qo.add_argument("--project", "-p")
    
    p_chk = subparsers.add_parser("check", help="🌟 Guardrail pré-vol d'intégrité (Index, fichiers, alertes)")
    p_chk.add_argument("--project", "-p")
    
    p_res = subparsers.add_parser("resume", help="🌟 Anti-Amnésie de session (État, décisions, prochaine action)")
    p_res.add_argument("--project", "-p")
    
    # Utilitaires
    p_adr = subparsers.add_parser("adr", help="Décisions d'Architecture (ADR)")
    p_adr.add_argument("title", nargs="?")
    p_adr.add_argument("--project", "-p")
    
    p_lex = subparsers.add_parser("lexique", help="Lexique Métier Ubiquitaire")
    p_lex.add_argument("term", nargs="?")
    p_lex.add_argument("--project", "-p")
    
    p_stat = subparsers.add_parser("status", help="Tableau de bord de statut")
    p_stat.add_argument("--project", "-p")
    
    args = parser.parse_args()
    proj = getattr(args, "project", None)
    
    if args.command in ["init", "inception"]:
        cmd_inception(args.role, args.name, proj)
    elif args.command == "ingest":
        cmd_ingest(proj)
    elif args.command == "crawl":
        cmd_crawl(args.url, proj)
    elif args.command == "plan":
        cmd_plan(args.query, None, proj)
    elif args.command == "validate":
        cmd_validate(proj)
    elif args.command == "export":
        cmd_export(args.file, proj)
    elif args.command == "questions":
        cmd_questions(args.action, args.text, args.client, args.adr, proj)
    elif args.command == "check":
        cmd_check(proj)
    elif args.command == "resume":
        cmd_resume(proj)
    elif args.command == "adr":
        cmd_adr(args.title, proj)
    elif args.command == "lexique":
        cmd_lexique(args.term, proj)
    elif args.command == "status":
        cmd_status(proj)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
