"""
Pipeline d'Exportation & Préparation Granulaire Multi-Sources pour Google NotebookLM.
Génère 12 documents thématiques de référence couvrant les 6 Piliers, les 6 Phases,
les 58 Commandes CLI, l'Équipe d'Agents, les 35 Skills, la Boîte à Outils, les Hooks,
et l'Encyclopédie des 77 ADRs souverains.
"""

import os
import re
import time
from pathlib import Path
from typing import Optional, List, Dict

from src.cli import ZeroFluffConsole

class NotebookLMExporter:
    def __init__(self, root_dir: Path, output_dir: Optional[Path] = None):
        self.root_dir = root_dir
        self.output_dir = output_dir or (root_dir / "storage" / "notebooklm_export")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_framework_bundle(self) -> List[Path]:
        """Génère les 12 dossiers thématiques SSOT prêts pour NotebookLM."""
        ZeroFluffConsole.info(f"Génération du corpus granulaire mLoop dans : {self.output_dir}")
        generated_files = []

        # =====================================================================
        # 1. Piliers & Architecture Souveraine
        # =====================================================================
        readme = self.root_dir / "README.md"
        doc_piliers = "# 🌀 Memory Loop — Piliers Fondateurs & Architecture Souveraine\n\n"
        doc_piliers += "> **Périmètre** : Architecture Kernel-Pipeline, Pure State-Graph et Loi des 3 Piliers\n\n---\n\n"
        if readme.exists():
            doc_piliers += readme.read_text(encoding="utf-8")
        f1 = self.output_dir / "01_Piliers_et_Architecture_Souveraine.md"
        f1.write_text(doc_piliers, encoding="utf-8")
        generated_files.append(f1)
        ZeroFluffConsole.success(f"Généré : {f1.name}")

        # =====================================================================
        # 2. Les 6 Phases du Cycle de Vie
        # =====================================================================
        doc_phases = "# 🧭 Les 6 Phases Souveraines du Cycle de Vie mLoop\n\n"
        doc_phases += "> **Standard Opérationnel** : Inception, Ingestion, Architecture, Stories, Validation, Livraison\n\n---\n\n"
        doc_phases += """## Phase 0 — Inception & SOW
- **Objectif** : Cadrage initial, t-shirt sizing et estimation d'effort.
- **Commandes Clés** : `python src/swarm.py sow`
- **Livrables** : Matrice SOW, granularité des récits et jalons prévisionnels.

## Phase 1 — Spec & Ingestion
- **Objectif** : Ingestion documentaire brute sans lecture humaine directe.
- **Commandes Clés** : `python src/swarm.py ingest`, `python src/swarm.py crawl`
- **Livrables** : Markdown normalisé sous `docs/00-ingested/`, maquettes sous `docs/05-assets/`.

## Phase 2 — Plan & Architecture
- **Objectif** : Découpage vertical selon le standard INVEST et arbitrage contradictoire.
- **Commandes Clés** : `python src/swarm.py drill`, `python src/swarm.py plan`, `python src/swarm.py archify`
- **Livrables** : Modèles de données (DBML), règles métier, ADRs formalisés et diagrammes vectoriels.

## Phase 3 — Build & Stories
- **Objectif** : Rédaction des récits verticaux et profilage des contrats déclaratifs.
- **Commandes Clés** : `python src/swarm.py focus`, `python src/swarm.py story-write`
- **Livrables** : Récits Gherkin 4 Piliers sous `backlog/stories/<JIRA_KEY>.md` et EvidencePacks autonomes sous `memory/evidence/`.

## Phase 4 — Validate & QA
- **Objectif** : Contrôles pré-vol déterministes et audits contradictoires Red Team.
- **Commandes Clés** : `python src/swarm.py vibe-check`, `python src/swarm.py wikifix`, `python src/swarm.py rubber-duck`
- **Livrables** : Rapport WikiFix sous `memory/wikifix_report.md`, validation Sentinel et audit des 4 piliers Gherkin.

## Phase 5 — Ship & Sync
- **Objectif** : Synchronisation tripartite et clôture du cycle.
- **Commandes Clés** : `python src/swarm.py jira_sync`, `python src/swarm.py sync`, `python src/swarm.py notebooklm --bundle`
- **Livrables** : Dépôt Git à jour, tickets Jira Cloud synchronisés, graphe Graphify / SQLite FTS5 rafraîchi, et carnet Google NotebookLM mis à niveau.
"""
        f2 = self.output_dir / "02_Phases_du_Cycle_de_Vie.md"
        f2.write_text(doc_phases, encoding="utf-8")
        generated_files.append(f2)
        ZeroFluffConsole.success(f"Généré : {f2.name}")

        # =====================================================================
        # 3. Matrice CLI & Guide Exhaustif des Commandes (58 Commandes)
        # =====================================================================
        cli_guide = self.root_dir / "standards" / "protocols" / "CLI_PIPELINE_GUIDE.md"
        doc_cli = "# 📖 Matrice Complète du Pipeline CLI mLoop (SSOT)\n\n"
        if cli_guide.exists():
            doc_cli += cli_guide.read_text(encoding="utf-8")
        f3 = self.output_dir / "03_Matrice_CLI_et_Commandes_Pipeline.md"
        f3.write_text(doc_cli, encoding="utf-8")
        generated_files.append(f3)
        ZeroFluffConsole.success(f"Généré : {f3.name}")

        # =====================================================================
        # 4. Équipe d'Agents, Rôles & Protocole de Délégation
        # =====================================================================
        agents_file = self.root_dir / "AGENTS.md"
        doc_agents = "# 🤖 Équipe d'Agents mLoop, Rôles, Délégation & Limites Inviolables\n\n"
        if agents_file.exists():
            doc_agents += agents_file.read_text(encoding="utf-8")
        f4 = self.output_dir / "04_Equipe_Agents_Roles_et_Delegation.md"
        f4.write_text(doc_agents, encoding="utf-8")
        generated_files.append(f4)
        ZeroFluffConsole.success(f"Généré : {f4.name}")

        # =====================================================================
        # 5. Répertoire Complet des 35 Skills Cognitifs
        # =====================================================================
        skills_dir = self.root_dir / ".agents" / "skills"
        doc_skills = "# 🧠 Répertoire Exhaustif des 35 Skills Cognitifs mLoop\n\n"
        doc_skills += "> **Principe Dual-Track (ADR-0346)** : Directives in-process chargées à la demande sans surcharge de contexte.\n\n---\n\n"

        if skills_dir.exists():
            for s_dir in sorted(skills_dir.iterdir()):
                if s_dir.is_dir():
                    s_file = s_dir / "SKILL.md"
                    if s_file.exists():
                        doc_skills += f"## Skill : `{s_dir.name}`\n\n"
                        doc_skills += s_file.read_text(encoding="utf-8", errors="ignore")
                        doc_skills += "\n\n---\n\n"

        f5 = self.output_dir / "05_Repertoire_des_Skills_et_Competences.md"
        f5.write_text(doc_skills, encoding="utf-8")
        generated_files.append(f5)
        ZeroFluffConsole.success(f"Généré : {f5.name}")

        # =====================================================================
        # 6. Boîte à Outils & Tooling Transverse
        # =====================================================================
        tools_readme = self.root_dir / "tools" / "README.md"
        doc_tools = "# 🛠️ Boîte à Outils & Utilitaires Transverses mLoop\n\n"
        if tools_readme.exists():
            doc_tools += tools_readme.read_text(encoding="utf-8")
        
        # Ajouter le détail de chaque outil si disponible
        for tool_sub in ["archify", "budget", "drawdb", "jira", "office"]:
            sub_rm = self.root_dir / "tools" / tool_sub / "README.md"
            if sub_rm.exists():
                doc_tools += f"\n\n---\n\n## Outil Spécifique : `{tool_sub}`\n\n"
                doc_tools += sub_rm.read_text(encoding="utf-8", errors="ignore")

        f6 = self.output_dir / "06_Boite_a_Outils_et_Tooling_Transverse.md"
        f6.write_text(doc_tools, encoding="utf-8")
        generated_files.append(f6)
        ZeroFluffConsole.success(f"Généré : {f6.name}")

        # =====================================================================
        # 7. Hooks Git & Guardrails Pré-Vol
        # =====================================================================
        doc_hooks = "# 🛡️ Hooks Git, Vibe-Check & Guardrails de Sécurité Déterministes\n\n"
        doc_hooks += """## 1. Vibe-Check : Les 9 Contrôles Déterministes Pré-Vol
Exécuté obligatoirement via `python src/swarm.py vibe-check` au boot sequence :
1. **Cohérence de Phase & Stage** : Vérifie l'étape du cycle (SOW, Spec, Plan, Build, Validate, Ship).
2. **Intégrité SSOT & Piliers** : Présence des répertoires souverains (`docs/`, `backlog/`, `standards/`, `memory/`).
3. **Format-Guard & Frontmatter** : Conformité stricte du gabarit YAML `story_template.md`.
4. **Verrou Découpage Backlog** : Respect de l'alignement avec `backlog/sprint_backlog.md`.
5. **Anti-Ghost Bias Guard** : Interdiction du biais d'acceptation passive sur dossier vide.
6. **Passage-Level Grounding (Grill-with-Docs)** : Vérification de la présence de preuves sourcées.
7. **Jira-Linking-Only** : Vérification de l'absence de chemins disques physiques dans le corps des récits.
8. **Pureté Déclarative No-Code** : Préservation du niveau fonctionnel pur sans fuite de code.
9. **Contrat Visuel & Maquettes** : Cohérence avec les maquettes vectorielles et validation OCR.

## 2. Hooks Git Pre-Commit (Fail-Closed)
Installés via `python src/swarm.py install-hooks` :
- Bloque tout commit physique si le Vibe-Check échoue.
- Empêche la fuite de secrets (.env, clés Nmédia Cloud LiteLLM).
- Synchronise automatiquement le graphe sémantique en tâche de fond.
"""
        f7 = self.output_dir / "07_Hooks_Git_et_Guardrails_Pre_Vol.md"
        f7.write_text(doc_hooks, encoding="utf-8")
        generated_files.append(f7)
        ZeroFluffConsole.success(f"Généré : {f7.name}")

        # =====================================================================
        # 8 à 12. Les 77 ADRs regroupés par Domaines Thématiques
        # =====================================================================
        adr_dir = self.root_dir / "standards" / "adr-system"
        adr_files = sorted(adr_dir.glob("*.md")) if adr_dir.exists() else []

        adr_categories = {
            "08_ADR_Gouvernance_et_Stories_Agiles.md": {
                "title": "ADRs : Gouvernance, Découpage Agile & Spécifications Gherkin",
                "keywords": ["story", "gherkin", "grill", "jira", "sow", "invest", "lifecycle", "rework", "0300", "0301", "0302", "0304", "0305", "0306", "0307", "0320", "0329", "0331", "0339", "0344"]
            },
            "09_ADR_Architecture_Memoire_et_Graphes.md": {
                "title": "ADRs : Architecture d'État, Mémoire Persistante & Graphes",
                "keywords": ["memory", "graph", "resume", "eval", "fact", "fts", "hypergraph", "chunking", "0310", "0315", "0318", "0323", "0324", "0326", "0343", "0347", "0351", "0355"]
            },
            "10_ADR_Ingestion_Crawling_et_Contrat_Visuel.md": {
                "title": "ADRs : Ingestion Documentaire, Smart Crawler & Contrat Visuel",
                "keywords": ["crawl", "ingest", "svg", "ocr", "visual", "doc", "pdf", "slop", "0312", "0317", "0327", "0332", "0335", "0340", "0345", "0352"]
            },
            "11_ADR_Multi_Agents_Workers_et_Execution.md": {
                "title": "ADRs : Orchestration Multi-Agents, Workers Herdr & Gouvernance LLM",
                "keywords": ["worker", "agent", "herdr", "litellm", "pricing", "consensus", "zombie", "teardown", "red-team", "0308", "0309", "0319", "0338", "0346", "0348", "0350", "0354"]
            },
            "12_ADR_Synchronisations_et_Oracles_NotebookLM.md": {
                "title": "ADRs : Synchronisations Tripartites & Oracles de Savoir Externes",
                "keywords": ["sync", "notebooklm", "oracle", "tripartite", "karpathy", "0349", "0356", "0360"]
            }
        }

        # Répartir les ADRs
        for cat_filename, cat_info in adr_categories.items():
            cat_content = f"# 🏛️ {cat_info['title']}\n\n"
            cat_content += f"> **Horodatage d'Export** : {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            cat_content += f"> **Carnet Officiel** : https://notebook.google.com/notebook/ddf80a44-cf1c-4eb8-86fd-7cebe6156f87\n\n---\n\n"

            matched_adrs = []
            for adr in adr_files:
                if adr.name.lower() == "readme.md":
                    continue
                name_lower = adr.name.lower()
                if any(kw in name_lower for kw in cat_info["keywords"]):
                    matched_adrs.append(adr)

            cat_content += f"Total Décisions Indexées dans ce Document : {len(matched_adrs)}\n\n---\n\n"
            for adr in matched_adrs:
                cat_content += f"## 📄 {adr.stem}\n\n"
                cat_content += adr.read_text(encoding="utf-8", errors="ignore")
                cat_content += "\n\n---\n\n"

            cat_path = self.output_dir / cat_filename
            cat_path.write_text(cat_content, encoding="utf-8")
            generated_files.append(cat_path)
            ZeroFluffConsole.success(f"Généré : {cat_path.name} ({len(matched_adrs)} ADRs)")

        # Master Bundle Unique également disponible en bonus
        master_bundle = self.output_dir / "mloop_complete_ssot_bundle.md"
        master_content = "# 🌀 Memory Loop — Corpus Documentaire Maître (SSOT Complete Bundle)\n\n"
        for gf in generated_files:
            master_content += f"\n\n{'=' * 70}\n\n"
            master_content += gf.read_text(encoding="utf-8", errors="ignore")
        master_bundle.write_text(master_content, encoding="utf-8")
        generated_files.append(master_bundle)
        ZeroFluffConsole.success(f"🏆 Master Bundle Unique conservé en option : {master_bundle.name}")

        return generated_files

    def export_project_bundle(self, project_name: str) -> Optional[Path]:
        """Exporte le SSOT complet d'un projet spécifique."""
        proj_dir = self.root_dir / "Projects" / project_name
        if not proj_dir.exists():
            ZeroFluffConsole.warning(f"Projet introuvable : {proj_dir}")
            return None

        out_name = f"Project_{project_name}_SSOT.md"
        content = f"# Dossier d'Architecture & Spécifications Projet : {project_name}\n\n"
        content += f"> **Horodatage d'Export** : {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"

        backlog = proj_dir / "backlog" / "sprint_backlog.md"
        if backlog.exists():
            content += f"## Backlog & Sprint Courant\n\n{backlog.read_text(encoding='utf-8')}\n\n---\n\n"

        docs_dir = proj_dir / "docs"
        if docs_dir.exists():
            for doc in sorted(docs_dir.rglob("*.md")):
                content += f"### {doc.stem}\n\n{doc.read_text(encoding='utf-8', errors='ignore')}\n\n---\n\n"

        p_file = self.output_dir / out_name
        p_file.write_text(content, encoding="utf-8")
        ZeroFluffConsole.success(f"Généré pour le projet {project_name} : {p_file.name}")
        return p_file
