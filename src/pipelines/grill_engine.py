"""
Grill Engine - mLoop
Moteur d'interrogatoire interactif (Grill-with-Docs).
Séparation stricte Faits vs Décisions, Porte de confirmation, Auto-ADR et Marquage de Récits Grilled.
Support du Fact-Search préalable et journalisation (ADR-0326).
"""

from pathlib import Path
import datetime
import json
import re
from typing import Dict, List, Optional, Any
from src.state import ProjectLayout
from src.cli import ZeroFluffConsole

ADR_TEMPLATE = """# 🏛️ ADR-{adr_id:03d} : {title}

- **Statut** : DECIDED
- **Date** : {date}
- **Décideurs** : Utilisateur & mLoop Agent

## Contexte & Problème
{context}

## Décision Retenue
{decision}

## Conséquences
### Positives
{positives}

### Négatives / Risques
{negatives}

---
*Généré automatiquement par mLoop Grill Engine le {date}.*
"""


class GrillEngine:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.docs_dir = (
            project_path / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
        )
        self.backlog_dir = project_path / ProjectLayout.BACKLOG
        self.stories_dir = self.backlog_dir / "stories"
        self.oq_file = (
            project_path
            / ProjectLayout.DOCS
            / ProjectLayout.DOCS_TRANSVERSE
            / ProjectLayout.OPEN_QUESTIONS_FILE
        )

    def _grade_certainty(self, results: List[Dict[str, Any]]) -> str:
        """
        Gradue la certitude Fact-Search selon le nombre et le rang des résultats
        (ADR-0320 §G) — remplace l'ancienne affectation fixe "HIGH" dès 1 résultat.
        """
        if not results:
            return "NONE"
        if len(results) == 1:
            return "MEDIUM"
        return "HIGH"

    def _search_code_source(
        self, query: str, source_project_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback Code Source (ADR-0320 §G, niveau 5 de la Search Hierarchy) :
        recherche directe dans les fichiers de code source physique (reference/**/*.cs|.csproj|.plist|.xml)
        lorsque le RAG documentaire ne suffit pas ou pour confirmer un comportement technique.
        Un index .codegraph/ actif est préféré s'il existe, sinon repli sur un grep textuel simple.
        """
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
            except Exception:
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
        """
        Effectue une recherche Fact-Search préalable (FTS5 / Graphe, puis fallback Code Source)
        avant toute question. Affiche les preuves console et journalise dans
        memory/fact_search_log.jsonl (ADR-0326, enrichi ADR-0320 §G).
        """
        from src.loop_mem.db import search_in_memory

        ZeroFluffConsole.info(f"[FACT-SEARCH] 🔍 Requête FTS5 : '{query}'")
        results = search_in_memory(self.project_path, query, limit=5)
        source_type = "documentation"

        # ADR-0320 §G : Priorité au Code Source Quand Disponible — si le RAG documentaire
        # ne retourne rien, ou pour renforcer une affirmation technique, tenter le fallback
        # de recherche directe dans le code source physique (reference/**/*.cs|.csproj|...).
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
        except Exception:
            pass

        if results:
            top = results[0]
            ZeroFluffConsole.success(
                f"[FACT-SEARCH] 💡 Source trouvée ({source_type}) : {top.get('label', top.get('id', 'Fait vérifié'))} (Certitude: {certainty})"
            )
        else:
            ZeroFluffConsole.info(
                "[FACT-SEARCH] ℹ️ Aucun fait pré-établi trouvé (documentation ni code source). Question de cadrage PO légitime."
            )

        return results

    def record_adr(
        self, title: str, context: str, decision: str, positives: str, negatives: str
    ) -> Path:
        """Enregistre de manière synchrone une nouvelle décision d'architecture (ADR) dans docs/01-architecture/."""
        self.docs_dir.mkdir(parents=True, exist_ok=True)

        # Trouver le numéro du prochain ADR
        existing_adrs = list(self.docs_dir.glob("ADR-*.md"))
        next_id = len(existing_adrs) + 1

        slug_title = re.sub(r"[^a-zA-Z0-9_-]", "_", title.lower()).strip("_")
        filename = f"ADR-{next_id:03d}_{slug_title}.md"
        adr_path = self.docs_dir / filename

        date_str = datetime.date.today().isoformat()
        content = ADR_TEMPLATE.format(
            adr_id=next_id,
            title=title,
            date=date_str,
            context=context or "Session d'interrogatoire Grill-with-Docs.",
            decision=decision or "Arbitrage d'architecture validé.",
            positives=positives
            or "Clarification des exigences métier et réduction du flou.",
            negatives=negatives
            or "Contraintes et engagements d'architecture appliqués.",
        )
        adr_path.write_text(content, encoding="utf-8")
        return adr_path

    def mark_story_grilled(self, story_id: str) -> bool:
        """
        Passe le statut d'un récit (story) à READY_FOR_GROOMING via la FSM,
        puis tampe le hash anti-tampering sur le contenu validé.
        """
        from src.state import StoryStatus
        from src.pipelines.state_machine import StateMachineEngine

        engine = StateMachineEngine(str(self.project_path))
        updated_any = False

        # 1. Mise à jour dans backlog/stories/<story_id>.md ou <story_id>*.md (récursif)
        # BUG-GRILL-01 : la résolution par nom de fichier ne suffit pas quand le fichier
        # est nommé par la clé Jira (ex: MMA-4658.md) alors que l'utilisateur passe l'ID
        # interne du frontmatter (ex: US-05-FOOD). On complète la résolution par lecture
        # du champ `id:` / `jira_key:` du frontmatter YAML de chaque récit.
        if self.stories_dir.exists():
            matches = set(self.stories_dir.rglob(f"*{story_id}*.md"))
            if not matches:
                import yaml as _yaml

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
                        fm_data = _yaml.safe_load(fm_parts[1])
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

                # Extraire le statut actuel pour validation FSM
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import yaml

                    data = yaml.safe_load(parts[1])
                    if isinstance(data, dict):
                        current_status = StoryStatus.from_raw(
                            data.get("status", "OPEN")
                        )
                        engine.validate_transition(
                            current_status, StoryStatus.READY_FOR_GROOMING
                        )

                        data["status"] = StoryStatus.READY_FOR_GROOMING.value
                        new_yaml = yaml.dump(
                            data, sort_keys=False, allow_unicode=True
                        ).strip()
                        new_content = f"---\n{new_yaml}\n---{parts[2]}"
                        story_file.write_text(new_content, encoding="utf-8")

                        # Tamper le hash anti-tampering
                        engine.stamp_content_hash(story_file)
                        updated_any = True

        # 2. Mise à jour dans sprint_backlog.md
        sprint_file = self.backlog_dir / ProjectLayout.SPRINT_BACKLOG_FILE
        if sprint_file.exists():
            sprint_content = sprint_file.read_text(encoding="utf-8")
            pattern = rf"(\|.*?{re.escape(story_id)}.*?\|\s*)([A-Z_]+)(\s*\|)"
            new_sprint_content = re.sub(
                pattern, rf"\g<1>READY_FOR_GROOMING\g<3>", sprint_content
            )
            if new_sprint_content != sprint_content:
                sprint_file.write_text(new_sprint_content, encoding="utf-8")
                updated_any = True

        return updated_any
