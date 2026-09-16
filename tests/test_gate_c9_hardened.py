import pytest
from pathlib import Path
from src.pipelines.struct_checker import StructCheckEngine
from src.pipelines.state_machine import StateMachineEngine, StateTransitionError


def test_gate_c9_missing_dossier_raises_blocking_in_strict(tmp_path):
    project_dir = tmp_path / "TestProjectC9"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-01.md"
    story_file.write_text(
        """---
id: US-01
status: READY_FOR_DEV
---
# US-01
## Critères d'acceptation
- Critère 1
## Scénarios de test
### Pilier 1 : Nominal
- Scénario 1
""",
        encoding="utf-8",
    )

    checker = StructCheckEngine(project_dir)
    res = checker.check_file(story_file, strict=True)
    c9_violations = [v for v in res.violations if v.check_id == "C9"]
    assert len(c9_violations) > 0
    assert any(v.severity == "BLOCKING" for v in c9_violations)

    sm = StateMachineEngine(project_dir)
    with pytest.raises(StateTransitionError, match="Dossier de Preuves Documentaires"):
        sm.validate_fact_dossier_gate(story_file, strict=True)


def test_gate_c9_draft_dossier_rejected(tmp_path):
    project_dir = tmp_path / "TestProjectDraft"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    evidence_dir = project_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True)

    dossier = evidence_dir / "US-02_fact_dossier.md"
    dossier.write_text(
        """---
story_id: US-02
dossier_status: DRAFT
---
# Dossier de Preuves
## 2. Faits
| **F-01** | Table | Def | Role |
```mermaid
erDiagram
    A ||--o{ B : rel
```
`GET /api/test`
""",
        encoding="utf-8",
    )

    story_file = stories_dir / "US-02.md"
    story_file.write_text(
        """---
id: US-02
status: READY_FOR_DEV
---
# US-02
## Critères d'acceptation
- Critère 1
## Scénarios de test
### Pilier 1 : Nominal
- Scénario 1
""",
        encoding="utf-8",
    )

    checker = StructCheckEngine(project_dir)
    res = checker.check_file(story_file, strict=True)
    c9_violations = [v for v in res.violations if v.check_id == "C9" and "DRAFT" in v.message]
    assert len(c9_violations) > 0

    sm = StateMachineEngine(project_dir)
    with pytest.raises(StateTransitionError, match="DRAFT"):
        sm.validate_fact_dossier_gate(story_file, strict=True)


def test_gate_c9_complete_dossier_passes(tmp_path):
    project_dir = tmp_path / "TestProjectComplete"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    evidence_dir = project_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True)

    dossier = evidence_dir / "US-03_fact_dossier.md"
    dossier.write_text(
        """---
story_id: US-03
dossier_status: CURRENT
sources_hashes:
  model.md: 123456
---
# Dossier de Preuves — US-03

## 🔬 2. Faits Extraits & Verbatims
| # | Table / Source | Définition DBML Exacte | Rôle dans le Payload API |
| :---: | :--- | :--- | :--- |
| **F-01** | `table_x` | `Table table_x { id uuid }` | Role dans payload |

## 🗄️ 3. Schéma Relationnel SSOT
```mermaid
erDiagram
    table_x ||--o{ table_y : links
```

## 🎯 4. Contrats Déclaratifs Cibles
`GET /api/v1/test/route`
Payload 200 OK :
```json
{"status": "ok"}
```
""",
        encoding="utf-8",
    )

    story_file = stories_dir / "US-03.md"
    story_file.write_text(
        """---
id: US-03
status: READY_FOR_DEV
---
# US-03 : Test Story
## Critères d'entrée
- Entrée 1
## Critères d'acceptation
- Critère 1
## Scénarios de test
### Pilier 1 : Nominal
- Scénario 1
### Pilier 2 : Exception
- Scénario 2
### Pilier 3 : Résilience
- Scénario 3
### Pilier 4 : UX
- Scénario 4
""",
        encoding="utf-8",
    )

    checker = StructCheckEngine(project_dir)
    res = checker.check_file(story_file, strict=True)
    c9_violations = [v for v in res.violations if v.check_id == "C9"]
    assert len(c9_violations) == 0

    sm = StateMachineEngine(project_dir)
    assert sm.validate_fact_dossier_gate(story_file, strict=True) is True
