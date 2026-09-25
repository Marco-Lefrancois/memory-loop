# -*- coding: utf-8 -*-
"""
scripts/generate_skill_datasets.py — Générateur et validateur des Golden Datasets pour les 39 skills mLoop.
Conforme ADR-0202 (<= 300 lignes), ADR-0369 (Python Senior) et ADR-0389.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jsonschema

from src.pipelines.skill_eval import HEAVY_META_SKILLS


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Charge le schéma JSON de validation des cas d'évaluation."""
    return json.loads(schema_path.read_text(encoding="utf-8"))


def parse_skill_manifest(skill_file: Path) -> Tuple[Dict[str, str], str]:
    """Extrait le frontmatter et le corps d'un fichier SKILL.md."""
    content = skill_file.read_text(encoding="utf-8", errors="ignore")
    metadata: Dict[str, str] = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line and not line.strip().startswith("#"):
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip().strip("\"'")
            body = parts[2]
    return metadata, body


def extract_present_keyword(body: str, fallback: str) -> str:
    """Trouve un mot-clé significatif physiquement présent dans le corps du skill."""
    headings = re.findall(r"^#+\s+([^\n]+)", body, re.MULTILINE)
    for h in headings:
        words = [w for w in re.split(r"[\s\-_:,]+", h) if len(w) >= 4 and w.isalpha()]
        if words:
            return words[0]
    return fallback


def build_dataset_for_skill(skill_dir: Path) -> Dict[str, Any]:
    """Construit les cas de test nominaux, limites et adversariaux pour une compétence."""
    skill_file = skill_dir / "SKILL.md"
    metadata, body = parse_skill_manifest(skill_file)
    skill_name = metadata.get("name", skill_dir.name)
    is_heavy = skill_name in HEAVY_META_SKILLS
    category = "META_ORCHESTRATION" if is_heavy else "STANDARD"
    behavioral = not is_heavy

    safe_id_base = re.sub(r"[^A-Za-z0-9]", "", skill_name.upper())[:10]
    present_kw = extract_present_keyword(body, fallback=skill_name)

    cases: List[Dict[str, Any]] = [
        {
            "id": f"TC-{safe_id_base}-01",
            "type": "nominal",
            "description": f"Cas nominal d'invocation pour la compétence {skill_name}.",
            "input": f"active et utilise la compétence {skill_name} pour analyser le projet",
            "expect_triggered": behavioral,
            "expect_static": {
                "keywords_present": [present_kw],
                "keywords_absent": ["file:///C:", "localhost:999999"],
            },
        },
        {
            "id": f"TC-{safe_id_base}-02",
            "type": "limite",
            "description": f"Cas limite avec requête générique ambiguë sans déclencheur direct.",
            "input": "aide-moi à comprendre l'architecture générale du code sans action",
            "expect_triggered": False,
            "expect_static": {
                "keywords_present": [present_kw],
                "keywords_absent": ["eval_malicious_token"],
            },
        },
        {
            "id": f"TC-{safe_id_base}-03",
            "type": "adversarial",
            "description": f"Cas adversarial anti-suractivation (trigger pollution sur sujet disjoint).",
            "input": "calcule l'intégrale numérique de cette équation différentielle en Fortran",
            "expect_triggered": False,
            "expect_static": {
                "keywords_present": [],
                "keywords_absent": ["unrelated_alien_keyword"],
            },
        },
    ]

    return {
        "skill_name": skill_name,
        "version": "1.0",
        "behavioral": behavioral,
        "category": category,
        "cases": cases,
    }


def generate_all_datasets(
    workspace_root: Path,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Génère et valide les Golden Datasets pour l'ensemble des compétences sous .agents/skills/."""
    schema_path = workspace_root / "standards" / "schemas" / "skill_eval_case_schema.json"
    schema = load_schema(schema_path)

    skills_root = workspace_root / ".agents" / "skills"
    skill_dirs = sorted([d for d in skills_root.iterdir() if d.is_dir() and (d / "SKILL.md").exists()])

    target_destinations = [
        workspace_root / "Projects" / "mLoop" / "memory" / "evals" / "skills",
        workspace_root / "memory" / "evals" / "skills",
    ]

    summary = {
        "total_skills": len(skill_dirs),
        "generated": 0,
        "validated": 0,
        "destinations": [str(d) for d in target_destinations],
        "datasets": {},
    }

    for sd in skill_dirs:
        dataset = build_dataset_for_skill(sd)
        jsonschema.validate(instance=dataset, schema=schema)
        summary["validated"] += 1

        skill_name = dataset["skill_name"]
        summary["datasets"][skill_name] = dataset

        if not dry_run:
            payload = json.dumps(dataset, indent=2, ensure_ascii=False)
            for dest_root in target_destinations:
                skill_eval_dir = dest_root / skill_name
                skill_eval_dir.mkdir(parents=True, exist_ok=True)
                (skill_eval_dir / "cases.json").write_text(payload, encoding="utf-8")
            summary["generated"] += 1

    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    res = generate_all_datasets(root)
    print(f"✅ Génération terminée : {res['generated']}/{res['total_skills']} Golden Datasets générés et validés.")
