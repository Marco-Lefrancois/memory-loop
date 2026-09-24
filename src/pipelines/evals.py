# -*- coding: utf-8 -*-
"""
evals.py — Moteur d'Évaluations Sémantiques Continuous mLoop (Evals Engine).
Aligne sur le standard Google Agents CLI Eval (Harness Engineering & Outcome-Based Evals).
Matrice hybride : Assertions Déterministes Système 1 + LLM-as-a-Judge Système 2 (100 pts).
Conforme ADR-0202 (<= 300 lignes) et ADR-0369 (Python Senior).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole
from src.pipelines.rubber_duck import RubberDuckEngine


SENTINEL_EVAL_JUDGE_SYSTEM_PROMPT = """Tu es l'Évaluateur Juridique et Fonctionnel en Chef (LLM-as-a-Judge) d'un pipeline de Spec-Driven Development.
Ton rôle est d'analyser rigoureusement une User Story Markdown générée par un agent, confrontée à son dossier de faits normatifs.

DIRECTIVES D'ENGAGEMENT :
1. "Lint is a floor, not the goal" : Ne perds pas de points sur de la simple ponctuation, juge la substance métier, l'ancrage et la robustesse contractuelle.
2. Anti-Sycophancy : Sois impitoyable sur les angles morts, l'invention de routes inexistantes et les scénarios de test paresseux.
3. Notation sur 100 points selon la Rubrique d'Évaluation formelle.

--- RUBRIQUE D'ÉVALUATION ---
A. ANCRAGE FACTUEL & ABSENCE D'HALLUCINATION (Poids : 30 pts)
   • 30 pts : Toutes les routes API et règles citées correspondent exactement aux "ground_truth_facts".
   • 15 pts : Une route ou un payload est approximatif mais sans contradiction majeure.
   • 0 pt (ÉCHEC CRITIQUE) : Présence d'une fausse route inventée (/api/dummy, /api/test) sans ancrage documentaire.
B. RIGUEUR DES 4 PILIERS GHERKIN (Poids : 30 pts)
   • 30 pts : Les 4 piliers sont articulés avec précision (Nominal, Exceptions, Résilience, UX/Observabilité).
   • 15 pts : Scénarios présents mais superficiels ou omettant la gestion d'erreur réseau/timeout.
   • 0 pt : Un des piliers est manquant ou contient des commentaires d'omission (TODO, placeholder).
C. PURETÉ DÉCLARATIVE & ABSENCE DE CODE PHYSIQUE (Poids : 20 pts)
   • 20 pts : Langage naturel métier pur, zéro snippet de code d'implémentation (C#, TS, SQL) ni classes internes.
   • 10 pts : Quelques fuites mineures de typage technique dans la description fonctionnelle.
   • 0 pt : Injection de blocs de code d'implémentation ou de pseudo-code syntaxique dans le corps du récit.
D. DÉLIMITATION DU PÉRIMÈTRE & GESTION DES CAS LIMITES (Poids : 20 pts)
   • 20 pts : Le hors-périmètre (Out-of-Scope) est formellement délimité (approche IS / IS-NOT), cas limites traités.
   • 10 pts : Limites implicites déductibles du contexte mais sans clause d'exclusion claire.
   • 0 pt : Périmètre ouvert sujet au Scope Creep, cas aux limites ignorés.
"""


class EvalsEngine:
    """Moteur d'évaluations hybrides mLoop aligné sur Google Agents CLI Eval."""

    PASS_THRESHOLD_SCORE: float = 85.0

    def __init__(self, project_name: str = "mLoop") -> None:
        self.project_name = project_name
        self.project_path = (
            Path("Projects") / project_name
            if (Path("Projects") / project_name).exists()
            else Path(".")
        )
        self.rubber_duck = RubberDuckEngine(project_path=self.project_path)

    @staticmethod
    def _run_deterministic_checks(file_path: Path, content: str) -> Tuple[Dict[str, bool], List[str]]:
        """Contrôles Système 1 : Assertions mécaniques strictes (plancher qualité)."""
        checks: Dict[str, bool] = {}
        flaws: List[str] = []

        # 1. Concision modulaire ADR-0202 (<= 300 lignes)
        line_count = len(content.splitlines())
        checks["max_file_lines"] = line_count <= 300
        if not checks["max_file_lines"]:
            flaws.append(f"[DÉTERMINISTE] Dépassement de concision : {line_count} lignes (max 300).")

        # 2. Clés frontmatter requises
        frontmatter_keys = ["id", "status"]
        has_fm = content.startswith("---") and "---" in content[3:]
        checks["frontmatter_valid"] = has_fm and all(f"{k}:" in content.split("---")[1] for k in frontmatter_keys)
        if not checks["frontmatter_valid"]:
            flaws.append("[DÉTERMINISTE] Frontmatter YAML incomplet ou absent.")

        # 3. Zéro chemins locaux absolus en dur
        checks["zero_local_hardcoded_paths"] = not bool(re.search(r"file:///[a-zA-Z]:", content, re.IGNORECASE))
        if not checks["zero_local_hardcoded_paths"]:
            flaws.append("[DÉTERMINISTE] Présence d'hyperliens absolus locaux 'file:///C:' au lieu de chemins relatifs.")

        # 4. Zéro snippet de code physique d'implémentation
        code_snippets = re.findall(r"```(?:csharp|cs|sql|typescript|ts|javascript|js|python|py)\b", content, re.IGNORECASE)
        checks["zero_code_snippets"] = len(code_snippets) == 0
        if not checks["zero_code_snippets"]:
            flaws.append(f"[DÉTERMINISTE] Présence de blocs de code physique interdits : {code_snippets}")

        return checks, flaws

    @staticmethod
    def _compute_rubric_scores(
        content: str,
        rubber_duck_res: Dict[str, Any],
        det_checks: Dict[str, bool],
        custom_forbidden_routes: Optional[List[str]] = None,
    ) -> Tuple[float, Dict[str, float], List[str], List[str]]:
        """Calcule les scores pondérés sur la rubrique 100 points Google Agents CLI Eval."""
        blocking: List[str] = list(rubber_duck_res.get("blocking_issues", []))
        recommendations: List[str] = list(rubber_duck_res.get("suggestions", []))

        # A. Ancrage factuel & Absence d'hallucination (30 pts)
        grounding_score = 30.0
        forbidden_routes = custom_forbidden_routes or ["/api/dummy", "/api/test", "/api/checkout/pay", "/api/fake"]
        found_phantoms = [r for r in forbidden_routes if r.lower() in content.lower()]
        if found_phantoms:
            grounding_score = 0.0
            blocking.append(f"[HALLUCINATION ROUTE] Route non-normative détectée : {found_phantoms}")
        elif "## Contrats d'échange API" in content and "GET /" not in content and "POST /" not in content and "PUT /" not in content and "[API à définir]" not in content:
            grounding_score = 15.0
            recommendations.append("Préciser les endpoints API ou consigner formellement '[API à définir]' avec OQ.")

        # Prise en compte des rejets bloquants Sentinel (ADR-0319 ou manque de cadrage)
        for bi in rubber_duck_res.get("blocking_issues", []):
            if "ADR-0319" in bi or "Matrice des Contrats API" in bi:
                grounding_score = max(0.0, grounding_score - 15.0)
            elif "Absence de contextualisation" in bi or "critères d'acceptation" in bi:
                grounding_score = max(0.0, grounding_score - 15.0)

        # B. Rigueur des 4 piliers Gherkin (30 pts)
        has_nom = bool(re.search(r"(?:nominal|succès)", content, re.IGNORECASE))
        has_exc = bool(re.search(r"(?:exception|erreur|rejet)", content, re.IGNORECASE))
        has_res = bool(re.search(r"(?:résilience|resilience|timeout|dégradé|idempotence)", content, re.IGNORECASE))
        has_ux = bool(re.search(r"(?:ux|accessibilité|clavier|focus|aria|toast|chargement)", content, re.IGNORECASE))
        pillars = [has_nom, has_exc, has_res, has_ux]
        present_count = sum(1 for p in pillars if p)
        gherkin_score = round(present_count * 7.5, 1)
        if present_count < 4:
            missing_names = []
            if not has_nom: missing_names.append("Nominal")
            if not has_exc: missing_names.append("Exceptions")
            if not has_res: missing_names.append("Résilience")
            if not has_ux: missing_names.append("UX/Observabilité")
            recommendations.append(f"Compléter les piliers Gherkin manquants : {', '.join(missing_names)}.")

        # C. Pureté déclarative & absence de code physique (20 pts)
        if not det_checks.get("zero_code_snippets", True):
            declarative_score = 0.0
            blocking.append("[FUITE DE CODE] Remplacer les blocs de code physique par des règles d'affaires déclaratives.")
        else:
            declarative_score = 20.0

        # D. Délimitation du périmètre & gestion des cas limites (20 pts)
        scope_score = 20.0
        has_oos = bool(re.search(r"(?:out-of-scope|hors-périmètre|hors périmètre)", content, re.IGNORECASE))
        if not has_oos:
            scope_score -= 10.0
            recommendations.append("Ajouter une section Out-of-Scope explicite pour éliminer le Scope Creep.")
        
        # Détection de cas limites ignorés
        missing_limits = []
        if not re.search(r"(?:timeout|délai|coupure|offline)", content, re.IGNORECASE):
            missing_limits.append("timeout/offline")
        if not re.search(r"(?:vide|null|invalide|incomplet)", content, re.IGNORECASE):
            missing_limits.append("données invalides/vides")
        if missing_limits:
            scope_score = max(0.0, scope_score - len(missing_limits) * 5.0)
            recommendations.append(f"Prendre en compte les cas limites non traités : {', '.join(missing_limits)}.")

        total_score = round(grounding_score + gherkin_score + declarative_score + scope_score, 1)
        breakdown = {
            "grounding_and_hallucination": grounding_score,
            "gherkin_four_pillars": gherkin_score,
            "declarative_purity": declarative_score,
            "scope_and_edge_cases": scope_score,
        }
        return total_score, breakdown, blocking, recommendations

    def run_evals(self, state: LoopState = None) -> Dict[str, Any]:
        """Exécute la suite d'évaluations hybrides sur l'ensemble des récits du backlog."""
        ZeroFluffConsole.step_s1("Evals Engine", f"Démarrage du Harnais d'Évaluation Google Agents CLI Eval pour '{self.project_name}'...")
        stories_dir = self.project_path / ProjectLayout.BACKLOG / "stories"
        if not stories_dir.exists():
            stories_dir = Path("backlog/stories")

        if not stories_dir.exists() or not list(stories_dir.rglob("*.md")):
            ZeroFluffConsole.warning("Aucun récit trouvé dans le backlog pour l'évaluation.")
            return {"score": 100.0, "semantic_quality_score": 100.0, "total_stories": 0, "passed": 0, "failed": 0, "details": []}

        story_files = sorted([f for f in stories_dir.rglob("*.md") if f.is_file()])
        results: List[Dict[str, Any]] = []
        passed_count = 0
        total_score_sum = 0.0

        for story_file in story_files:
            test_case_id = f"EVAL-{story_file.stem}"
            content = story_file.read_text(encoding="utf-8")
            
            # 1. Exécution des assertions déterministes (Système 1)
            det_checks, det_flaws = self._run_deterministic_checks(story_file, content)
            
            # 2. Exécution du LLM-as-a-Judge / Sentinel (Système 2)
            try:
                rubber_res = self.rubber_duck.evaluate_file(story_file)
            except Exception as exc:
                rubber_res = {"blocking_issues": [f"Erreur d'analyse RubberDuck : {str(exc)}"], "non_blocking_issues": [], "suggestions": []}

            # 3. Calcul de la rubrique sur 100 points
            total_score, breakdown, blocking, recs = self._compute_rubric_scores(content, rubber_res, det_checks)
            blocking.extend(det_flaws)

            is_passed = total_score >= self.PASS_THRESHOLD_SCORE and len(blocking) == 0
            if is_passed:
                passed_count += 1
            total_score_sum += total_score

            results.append({
                "test_case_id": test_case_id,
                "file": story_file.name,
                "verdict": "PASSED" if is_passed else "FAILED",
                "passed": is_passed,
                "total_score": total_score,
                "scores_breakdown": breakdown,
                "deterministic_checks": det_checks,
                "blocking_issues": blocking,
                "non_blocking_issues": rubber_res.get("non_blocking_issues", []),
                "recommendations": recs,
            })

        total = len(story_files)
        avg_score = round(total_score_sum / total, 1) if total > 0 else 100.0

        report = {
            "project": self.project_name,
            "score": avg_score,
            "semantic_quality_score": avg_score,
            "eval_framework": "Google Agents CLI Eval (Harness Engineering)",
            "pass_threshold_score": self.PASS_THRESHOLD_SCORE,
            "total_stories": total,
            "passed": passed_count,
            "failed": total - passed_count,
            "details": results,
        }

        # Écriture des rapports d'audit sous memory/
        memory_dir = self.project_path / ProjectLayout.MEMORY
        memory_dir.mkdir(parents=True, exist_ok=True)
        (memory_dir / "evals_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        md_content = f"# 🧪 Rapport d'Évaluations Google Agents CLI Eval (mLoop)\n\n"
        md_content += f"- **Projet :** {self.project_name}\n"
        md_content += f"- **Score Moyen de Qualité :** **{avg_score} / 100** (Seuil requis : {self.PASS_THRESHOLD_SCORE})\n"
        md_content += f"- **Taux de Succès :** {passed_count}/{total} récits conformes ({round((passed_count/total)*100, 1) if total else 100}%)\n\n"
        md_content += "## 📊 Matrice d'Évaluation par Récit\n\n"
        md_content += "| Récit | Verdict | Score Total | Grounding (/30) | Gherkin (/30) | Déclaratif (/20) | Scope (/20) |\n"
        md_content += "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        for r in results:
            icon = "✅ PASS" if r["passed"] else "❌ FAIL"
            b = r["scores_breakdown"]
            md_content += f"| `{r['file']}` | {icon} | **{r['total_score']}** | {b['grounding_and_hallucination']} | {b['gherkin_four_pillars']} | {b['declarative_purity']} | {b['scope_and_edge_cases']} |\n"

        md_content += "\n## 🛑 Défauts Bloquants & Recommandations\n\n"
        for r in results:
            if r["blocking_issues"] or r["recommendations"]:
                md_content += f"### `{r['file']}` ({r['verdict']} — {r['total_score']}/100)\n"
                for bi in r["blocking_issues"]:
                    md_content += f"- 🛑 **Bloquant** : {bi}\n"
                for rec in r["recommendations"]:
                    md_content += f"- 💡 **Conseil** : {rec}\n"
                md_content += "\n"

        (memory_dir / "evals_report.md").write_text(md_content, encoding="utf-8")

        if avg_score >= self.PASS_THRESHOLD_SCORE:
            ZeroFluffConsole.success(f"Harnais Eval terminé : Score moyen {avg_score}/100 ({passed_count}/{total} conformes).")
        else:
            ZeroFluffConsole.warning(f"Harnais Eval terminé : Score moyen {avg_score}/100 ({passed_count}/{total} conformes).")

        return report
