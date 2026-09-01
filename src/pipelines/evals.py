import json
from pathlib import Path
from typing import Dict, Any, List
from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole
from src.pipelines.rubber_duck import RubberDuckEngine

class EvalsEngine:
    """
    Moteur d'Évaluations Sémantiques Continuous mLoop (Evals Engine).
    S'appuie sur RubberDuckEngine pour exécuter des Assert Evals (Gherkin, Résilience, Anti-Fluff)
    sur l'ensemble des récits du backlog mLoop.
    """

    def __init__(self, project_name: str = "mLoop"):
        self.project_name = project_name
        self.project_path = Path("Projects") / project_name if (Path("Projects") / project_name).exists() else Path(".")
        self.rubber_duck = RubberDuckEngine(project_path=self.project_path)

    def run_evals(self, state: LoopState = None) -> Dict[str, Any]:
        ZeroFluffConsole.step_s1("Evals Engine", f"Démarrage de la suite d'évaluations sémantiques pour '{self.project_name}'...")
        
        stories_dir = self.project_path / ProjectLayout.BACKLOG / "stories"
        if not stories_dir.exists():
            stories_dir = Path("backlog/stories")

        if not stories_dir.exists() or not list(stories_dir.rglob("*.md")):
            ZeroFluffConsole.warning("Aucun récit trouvé dans le backlog pour l'évaluation.")
            return {"score": 100, "total_stories": 0, "passed": 0, "failed": 0, "details": []}

        story_files = [f for f in stories_dir.rglob("*.md") if f.is_file()]
        results = []
        passed_count = 0

        for story_file in story_files:
            try:
                eval_res = self.rubber_duck.evaluate_file(story_file)
                blocking = eval_res.get("blocking_issues", [])
                non_blocking = eval_res.get("non_blocking_issues", [])
                
                is_pass = len(blocking) == 0
                if is_pass:
                    passed_count += 1
                
                results.append({
                    "file": story_file.name,
                    "passed": is_pass,
                    "blocking_count": len(blocking),
                    "non_blocking_count": len(non_blocking),
                    "blocking_issues": blocking,
                    "non_blocking_issues": non_blocking
                })
            except Exception as e:
                results.append({
                    "file": story_file.name,
                    "passed": False,
                    "blocking_count": 1,
                    "non_blocking_count": 0,
                    "blocking_issues": [f"Erreur d'analyse : {str(e)}"],
                    "non_blocking_issues": []
                })

        total = len(story_files)
        score = round((passed_count / total) * 100, 1) if total > 0 else 100.0

        report = {
            "project": self.project_name,
            "semantic_quality_score": score,
            "total_stories": total,
            "passed": passed_count,
            "failed": total - passed_count,
            "details": results
        }

        # Écriture des rapports
        memory_dir = self.project_path / ProjectLayout.MEMORY
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        json_report_path = memory_dir / "evals_report.json"
        json_report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        md_content = f"# 🧪 Rapport d'Évaluations Sémantiques mLoop (Evals)\n\n"
        md_content += f"- **Projet :** {self.project_name}\n"
        md_content += f"- **Score de Qualité Sémantique (Evals Pass Rate) :** {score}%\n"
        md_content += f"- **Récits Conformes :** {passed_count}/{total}\n\n"
        md_content += "## Détails par Récit\n\n"

        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            md_content += f"### {status} - `{r['file']}`\n"
            if r["blocking_issues"]:
                md_content += "**Bloquants :**\n"
                for issue in r["blocking_issues"]:
                    md_content += f"- 🛑 {issue}\n"
            if r["non_blocking_issues"]:
                md_content += "**Avertissements :**\n"
                for issue in r["non_blocking_issues"]:
                    md_content += f"- ⚠️ {issue}\n"
            md_content += "\n"

        md_report_path = memory_dir / "evals_report.md"
        md_report_path.write_text(md_content, encoding="utf-8")

        if score >= 80:
            ZeroFluffConsole.success(f"Evals terminés : Score {score}% ({passed_count}/{total} conformes). Rapport sous {md_report_path.name}")
        else:
            ZeroFluffConsole.warning(f"Evals terminés : Score {score}% ({passed_count}/{total} conformes). Rapport sous {md_report_path.name}")

        return report
