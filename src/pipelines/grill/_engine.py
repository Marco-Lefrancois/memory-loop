"""
Grill Engine - mLoop (ADR-0320 / ADR-012)
Moteur d'interrogatoire interactif (Grill-with-Docs).
Séparation stricte Faits vs Décisions, Porte de confirmation, Auto-ADR et Marquage de Récits Grilled.
Support du Fact-Search préalable et journalisation (ADR-0326).
"""

import datetime
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import yaml

from src.cli import ZeroFluffConsole
from src.pipelines.grill._adr_writer import (
    get_next_adr_id,
    render_adr_content,
    resolve_adr_template,
    write_adr_file,
)
from src.pipelines.grill._frontier import (
    UNGRILLABLE_KEYWORDS,
    check_context_health,
    detect_ungrillable_signals,
    format_frontier_round,
)
from src.state import ProjectLayout

logger = logging.getLogger(__name__)


class GrillEngine:
    UNGRILLABLE_KEYWORDS = UNGRILLABLE_KEYWORDS

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.docs_dir = project_path / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
        self.backlog_dir = project_path / ProjectLayout.BACKLOG
        self.stories_dir = self.backlog_dir / "stories"
        self.oq_file = (
            project_path
            / ProjectLayout.DOCS
            / ProjectLayout.DOCS_TRANSVERSE
            / ProjectLayout.OPEN_QUESTIONS_FILE
        )

    def _grade_certainty(self, results: List[Dict[str, Any]]) -> str:
        """Gradue la certitude Fact-Search selon le nombre et le rang des résultats (ADR-0320 §G)."""
        if not results:
            return "NONE"
        if len(results) == 1:
            return "MEDIUM"
        return "HIGH"

    def _search_code_source(
        self, query: str, source_project_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """Fallback Code Source (ADR-0320 §G, niveau 5 de la Search Hierarchy)."""
        target = source_project_path or self.project_path
        ref_dir = target / "reference"
        if not ref_dir.exists():
            return []

        results: List[Dict[str, Any]] = []
        code_extensions = (".cs", ".csproj", ".plist", ".xml")
        query_tokens = [t.lower() for t in re.split(r"\W+", query) if len(t) > 2]
        if not query_tokens:
            return []

        for f in ref_dir.rglob("*"):
            if f.suffix.lower() not in code_extensions or not f.is_file():
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.debug(
                    "Lecture code source échouée, fichier ignoré",
                    exc_info=True,
                    extra={
                        "component": "pipelines.grill",
                        "operation": "code_source_read",
                        "file": str(f),
                        "error": str(e),
                    },
                )
                continue
            lower_text = text.lower()
            if any(tok in lower_text for tok in query_tokens):
                results.append(
                    {
                        "id": str(f.relative_to(target)).replace("\\", "/"),
                        "label": f.name,
                        "source_type": "code",
                    }
                )
            if len(results) >= 5:
                break
        return results

    def perform_fact_search(
        self, query: str, source_project_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """Effectue une recherche Fact-Search préalable (FTS5 / Graphe, puis fallback Code Source)."""
        from src.loop_mem.db import search_in_memory

        ZeroFluffConsole.info(f"[FACT-SEARCH] 🔍 Requête FTS5 : '{query}'")
        results = search_in_memory(self.project_path, query, limit=5)
        source_type = "documentation"

        if not results:
            code_results = self._search_code_source(query, source_project_path)
            if code_results:
                results = code_results
                source_type = "code"

        certainty = self._grade_certainty(results)

        log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "project": self.project_path.name,
            "query": query,
            "results_count": len(results),
            "top_sources": [r.get("id") or r.get("label") for r in results[:3]],
            "source_type": source_type,
            "certainty": certainty,
        }

        log_file = self.project_path / "memory" / "fact_search_log.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug(f"Erreur écriture fact_search_log: {exc}", exc_info=True)

        if results:
            top = results[0]
            ZeroFluffConsole.success(
                f"[FACT-SEARCH] 💡 Source trouvée ({source_type}) : {top.get('label', top.get('id', 'Fait vérifié'))} (Certitude: {certainty})"
            )
        else:
            ZeroFluffConsole.info(
                "[FACT-SEARCH] ℹ️ Aucun fait pré-établi trouvé. Question de cadrage PO légitime."
            )

        return results

    def record_adr(
        self,
        title: str,
        context: str = "",
        decision: str = "",
        positives: str = "",
        negatives: str = "",
    ) -> Path:
        """
        Enregistre de manière synchrone une nouvelle décision d'architecture (ADR)
        en résolvant dynamiquement le gabarit et en calculant l'ID anti-collision (ADR-012).
        """
        template_str = resolve_adr_template(self.project_path)
        next_id, max_id = get_next_adr_id(self.docs_dir)

        content = render_adr_content(
            template_str=template_str,
            adr_id=next_id,
            title=title,
            context=context,
            decision=decision,
            positives=positives,
            negatives=negatives,
            max_id=max_id,
        )
        return write_adr_file(self.docs_dir, next_id, title, content, max_id=max_id)

    def mark_story_grilled(self, story_id: str) -> bool:
        """Passe le statut d'un récit à READY_FOR_GROOMING via la FSM et tampe le hash."""
        from src.pipelines.state_machine import StateMachineEngine
        from src.state import StoryStatus

        engine = StateMachineEngine(str(self.project_path))
        updated_any = False

        if self.stories_dir.exists():
            matches = set(self.stories_dir.rglob(f"*{story_id}*.md"))
            if not matches:
                for candidate in self.stories_dir.rglob("*.md"):
                    try:
                        head = candidate.read_text(encoding="utf-8")
                    except Exception as e:
                        logger.debug("Lecture candidate échouée", exc_info=True)
                        continue
                    if not head.startswith("---"):
                        continue
                    fm_parts = head.split("---", 2)
                    if len(fm_parts) < 3:
                        continue
                    try:
                        fm_data = yaml.safe_load(fm_parts[1])
                    except Exception:
                        continue
                    if isinstance(fm_data, dict) and story_id in (
                        str(fm_data.get("id", "")),
                        str(fm_data.get("jira_key", "")),
                    ):
                        matches.add(candidate)

            for story_file in matches:
                content = story_file.read_text(encoding="utf-8")
                if not content.startswith("---") or "status:" not in content:
                    continue

                parts = content.split("---", 2)
                if len(parts) >= 3:
                    data = yaml.safe_load(parts[1])
                    if isinstance(data, dict):
                        current_status = StoryStatus.from_raw(data.get("status", "OPEN"))
                        engine.validate_transition(current_status, StoryStatus.READY_FOR_GROOMING)

                        data["status"] = StoryStatus.READY_FOR_GROOMING.value
                        new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True).strip()
                        new_content = f"---\n{new_yaml}\n---{parts[2]}"
                        story_file.write_text(new_content, encoding="utf-8")
                        engine.stamp_content_hash(story_file)
                        updated_any = True

        sprint_file = self.backlog_dir / ProjectLayout.SPRINT_BACKLOG_FILE
        if sprint_file.exists():
            sprint_lines = sprint_file.read_text(encoding="utf-8").splitlines()
            new_lines = []
            found_in_sprint = False
            for line in sprint_lines:
                if f"**{story_id}**" in line or f"| {story_id} " in line:
                    found_in_sprint = True
                    parts = line.split("|")
                    if len(parts) >= 9:
                        statut_cell = parts[7]
                        new_statut = re.sub(r"`?[A-Z_]+`?", "`READY_FOR_GROOMING`", statut_cell)
                        parts[7] = new_statut
                        new_lines.append("|".join(parts))
                        updated_any = True
                        continue
                    else:
                        new_line = re.sub(
                            rf"(\|.*?{re.escape(story_id)}.*?\|\s*)(?:`?[A-Z_]+`?)(\s*\|)",
                            r"\g<1>READY_FOR_GROOMING\g<2>",
                            line,
                        )
                        new_lines.append(new_line)
                        updated_any = True
                        continue
                new_lines.append(line)

            if not found_in_sprint:
                logger.warning("Récit %s introuvable dans sprint_backlog.md", story_id)

            new_sprint_content = "\n".join(new_lines) + ("\n" if sprint_lines else "")
            if new_sprint_content != sprint_file.read_text(encoding="utf-8"):
                sprint_file.write_text(new_sprint_content, encoding="utf-8")

        return updated_any

    def detect_ungrillable_signals(self, question: str) -> Dict[str, Any]:
        """Détecte si une question relève du domaine ungrillable (IHM/UX - ADR-0389)."""
        return detect_ungrillable_signals(question)

    def format_frontier_round(
        self, questions: List[Dict[str, Any]], round_num: int = 1, theme: str = ""
    ) -> str:
        """Formate un round de frontière orthogonal (ADR-0389)."""
        return format_frontier_round(questions, round_num=round_num, theme=theme)

    def check_context_health(self, estimated_tokens: int) -> Dict[str, Any]:
        """Évalue la santé du contexte de session et de la Dumb Zone (ADR-0389)."""
        return check_context_health(estimated_tokens)
