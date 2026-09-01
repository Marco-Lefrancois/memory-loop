import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from src.cli import ZeroFluffConsole
from src.state import LoopState, ProjectLayout


class MemoryHygieneAgent:
    """
    Agent Memory Hygiene (Audit de Fraîcheur & Confiance de Mémoire Vive mLoop).
    Inspiré des patterns COG Second Brain (gstack/gbrain).
    Re-vérifie la présence physique des faits et preuves dans memory/evidence/*.json,
    calcule la confiance (HIGH / MEDIUM / LOW) et estampille 'last_verified'.
    """

    def __init__(self):
        self.name = "MemoryHygiene"

    def audit_evidence_pack(self, pack_file: Path, project_path: Path) -> Dict[str, Any]:
        """Audite un fichier EvidencePack JSON et met à jour les scores de confiance."""
        content = json.loads(pack_file.read_text(encoding="utf-8"))
        now_iso = datetime.now(timezone.utc).isoformat()

        sources = content.get("sources_consulted", [])
        existing_sources = 0
        missing_sources = []
        code_extensions = {"cs", "csproj", "plist", "xml"}
        code_source_count = 0

        for src in sources:
            # Recherche de la source dans project_path
            matches = list(project_path.glob(f"**/{src}"))
            if matches:
                existing_sources += 1
                ext = src.rsplit(".", 1)[-1].lower() if "." in src else ""
                if ext in code_extensions:
                    code_source_count += 1
            else:
                missing_sources.append(src)

        total_sources = len(sources)
        # ADR-0320 §G : verification_method distingue une preuve de code source physique
        # (plus forte, "code_source_verified") d'une simple présence documentaire
        # ("file_existence_only") — ce contrôle reste toutefois limité à l'existence
        # du fichier sur disque, jamais à la véracité sémantique de l'affirmation citée.
        if total_sources == 0:
            confidence = "MEDIUM"
            confidence_score = 0.75
            verification_method = "file_existence_only"
        else:
            ratio = existing_sources / total_sources
            verification_method = "code_source_verified" if code_source_count > 0 else "file_existence_only"
            if ratio == 1.0 and code_source_count == total_sources:
                confidence = "HIGH"
                confidence_score = 1.0
            elif ratio == 1.0:
                confidence = "MEDIUM"
                confidence_score = 0.75 + 0.25 * (code_source_count / total_sources)
            elif ratio >= 0.5:
                confidence = "MEDIUM"
                confidence_score = ratio
            else:
                confidence = "LOW"
                confidence_score = ratio

        source_type = "code" if code_source_count > 0 else "documentation"

        # Mise à jour des champs COG Trust & Memory Hygiene
        content["last_verified"] = now_iso
        content["confidence"] = confidence
        content["confidence_score"] = round(confidence_score, 2)
        content["missing_sources"] = missing_sources
        content["verification_method"] = verification_method
        content["source_type"] = source_type

        # Validation V-Model : Vérifier l'existence du fichier récit associé
        file_path_rel = content.get("file_path")
        if file_path_rel:
            story_file = project_path / file_path_rel
            content["story_file_exists"] = story_file.exists()
        else:
            content["story_file_exists"] = False

        pack_file.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
        return content

    def execute(self, state: LoopState, verbose: bool = False) -> LoopState:
        ZeroFluffConsole.step_s1(self.name, "Démarrage du balayage de confiance de la mémoire vive (Memory Hygiene)...")
        project_path = Path("Projects") / state.project_name

        if not project_path.exists():
            ZeroFluffConsole.error(f"Dossier du projet '{state.project_name}' introuvable.")
            return state

        evidence_dir = project_path / ProjectLayout.MEMORY / "evidence"
        if not evidence_dir.exists():
            ZeroFluffConsole.info("Aucun dossier memory/evidence à balayer.")
            return state

        evidence_files = list(evidence_dir.glob("*_evidence.json"))
        if not evidence_files:
            ZeroFluffConsole.info("Aucun fichier EvidencePack trouvé.")
            return state

        high_cnt = 0
        med_cnt = 0
        low_cnt = 0
        audited_packs = []

        for ef in evidence_files:
            try:
                res = self.audit_evidence_pack(ef, project_path)
                audited_packs.append(res)
                if res["confidence"] == "HIGH":
                    high_cnt += 1
                elif res["confidence"] == "MEDIUM":
                    med_cnt += 1
                else:
                    low_cnt += 1
            except Exception as e:
                ZeroFluffConsole.error(f"Erreur lors du balayage de {ef.name} : {e}")

        # Rédaction du bilan de santé dans memory/SESSION_MEMORY_HEALTH.md
        session_health_file = project_path / ProjectLayout.MEMORY / "SESSION_MEMORY_HEALTH.md"
        active_memo_file = project_path / ProjectLayout.MEMORY / "active_memo_profile.json"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        active_memo_name = "Trajectory Retrieval Strategy (Default ALMA)"
        if active_memo_file.exists():
            try:
                data = json.loads(active_memo_file.read_text(encoding="utf-8"))
                active_memo_name = f"{data.get('name')} (ID: {data.get('profile_id')}, Score: {data.get('score', 0.9):.2f})"
            except Exception:
                pass

        report_lines = [
            f"# 🧪 Bilan de Santé de Mémoire - Memory Hygiene ({state.project_name})",
            f"* **Dernier balayage** : {now_str}",
            f"* **Stratégie Mémoire Active (ALMA)** : `{active_memo_name}`",
            f"* **Total EvidencePacks contrôlés** : {len(evidence_files)}",
            f"* **Niveau de Confiance** : 🟢 HIGH: {high_cnt} | 🟡 MEDIUM: {med_cnt} | 🔴 LOW: {low_cnt}",
            "",
            "## 📊 Détail des Artefacts de Preuve",
            "| Story ID | Statut Fichier | Confiance | Sources Manquantes | Dernier Audit |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]

        for p in audited_packs:
            f_status = "✅ Présent" if p.get("story_file_exists") else "❌ Manquant"
            conf = p.get("confidence", "MEDIUM")
            conf_badge = f"🟢 {conf}" if conf == "HIGH" else (f"🟡 {conf}" if conf == "MEDIUM" else f"🔴 {conf}")
            missing = ", ".join(p.get("missing_sources", [])) or "Aucune"
            sid = p.get("story_id", "UNKNOWN")
            last_ver = p.get("last_verified", "")[:19] or "N/A"
            report_lines.append(f"| `{sid}` | {f_status} | {conf_badge} (`{p.get('confidence_score', 0.0)}`) | {missing} | {last_ver} |")

        report_lines.append("")
        session_health_file.write_text("\n".join(report_lines), encoding="utf-8")
        ZeroFluffConsole.success(f"Balayage Memory Hygiene terminé. Bilan consigné dans {session_health_file.relative_to(project_path)}.")
        return state
