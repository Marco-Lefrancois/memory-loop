"""
Grill Engine - mLoop (ADR-0320 / ADR-012). Moteur d'interrogatoire interactif (Grill-with-Docs).
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
from src.pipelines.grill._grill_guards import assert_grill_target_allowed
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
        if not results:
            return "NONE"
        if len(results) == 1:
            return "MEDIUM"
        return "HIGH"

    def _search_code_source(
        self, query: str, source_project_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
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
                    "Lecture code source échouée",
                    exc_info=True,
                    extra={
                        "component": "pipelines.grill",
                        "operation": "code_source_read",
                        "file": str(f),
                        "error": str(e),
                    },
                )
                continue
            if any(tok in text.lower() for tok in query_tokens):
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

    def mark_story_grilled(self, story_id: str, *, target_status: Optional[str] = None) -> bool:
        from src.pipelines.state_machine import StateMachineEngine
        from src.state import StoryStatus

        # Bridage strict (ADR-0393) : verrou anti-promotion directe vers READY_FOR_DEV.
        assert_grill_target_allowed(self.project_path, story_id, target_status)

        engine = StateMachineEngine(str(self.project_path))
        frontmatter_updated = False
        if self.stories_dir.exists():
            matches = set(self.stories_dir.rglob(f"*{story_id}*.md"))
            if not matches:
                for candidate in self.stories_dir.rglob("*.md"):
                    try:
                        head = candidate.read_text(encoding="utf-8")
                    except Exception:
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
                        story_file.write_text(f"---\n{new_yaml}\n---{parts[2]}", encoding="utf-8")
                        engine.stamp_content_hash(story_file)
                        frontmatter_updated = True
        backlog_outcome = self._mark_backlog_status(story_id)
        if backlog_outcome == "BLOCKED":
            return False
        return frontmatter_updated or backlog_outcome in ("UPDATED", "ALREADY")

    def _mark_backlog_status(self, story_id: str) -> str:
        from src.pipelines.sync._sync_backlog_parser import (
            STATUS_VOCAB_RE,
            _ID_RE,
            _SEPARATOR_RE,
            _find_statut_col_index,
        )

        sprint_file = self.backlog_dir / ProjectLayout.SPRINT_BACKLOG_FILE
        if not sprint_file.exists():
            return "ROW_ABSENT"
        lines = sprint_file.read_text(encoding="utf-8").splitlines(keepends=True)
        statut_idx: Optional[int] = None
        header_len = 0
        outcome = "ROW_ABSENT"
        target_seen = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("|"):
                statut_idx = None
                header_len = 0
                continue
            if _SEPARATOR_RE.match(stripped) and "---" in stripped:
                header = lines[i - 1] if i > 0 else ""
                if header.strip().startswith("|"):
                    cells = [str(c) for c in header.split("|")]
                    statut_idx = _find_statut_col_index(cells)
                    header_len = len(cells)
                else:
                    statut_idx = None
                continue
            if statut_idx is None:
                continue
            cells = line.split("|")
            if len(cells) != header_len:
                continue
            if not any(tok.upper() == story_id.upper() for tok in _ID_RE.findall(line)):
                continue
            target_seen = True
            raw_cell = cells[statut_idx]
            match = STATUS_VOCAB_RE.search(raw_cell)
            if not match:
                outcome = "BLOCKED"
                break
            if match.group(1).upper().replace("-", "_") == "READY_FOR_GROOMING":
                outcome = "ALREADY"
                break
            cells[statut_idx] = (
                raw_cell[: match.start(1)] + "READY_FOR_GROOMING" + raw_cell[match.end(1) :]
            )
            lines[i] = "|".join(cells)
            outcome = "UPDATED"
            break
        if outcome == "UPDATED":
            sprint_file.write_text("".join(lines), encoding="utf-8")
            return outcome
        if outcome == "BLOCKED":
            logger.warning(
                "Colonne Statut non mise à jour pour %s : incohérence story↔backlog",
                story_id,
                extra={
                    "component": "pipelines.grill",
                    "operation": "mark_backlog_status",
                    "story_id": story_id,
                    "reason": outcome,
                },
            )
        elif not target_seen:
            logger.warning(
                "Récit %s introuvable dans sprint_backlog.md",
                story_id,
                extra={
                    "component": "pipelines.grill",
                    "operation": "mark_backlog_status",
                    "story_id": story_id,
                    "reason": "ROW_ABSENT",
                },
            )
        return outcome

    def detect_ungrillable_signals(self, question: str) -> Dict[str, Any]:
        return detect_ungrillable_signals(question)

    def format_frontier_round(
        self, questions: List[Dict[str, Any]], round_num: int = 1, theme: str = ""
    ) -> str:
        return format_frontier_round(questions, round_num=round_num, theme=theme)

    def check_context_health(self, estimated_tokens: int) -> Dict[str, Any]:
        return check_context_health(estimated_tokens)
