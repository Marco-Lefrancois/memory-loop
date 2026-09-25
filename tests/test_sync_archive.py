"""
test_sync_archive.py — Tests unitaires pour l'archivage automatique du backlog (ADR-0391).
"""

from pathlib import Path
from src.pipelines.sync._sync_archive import parse_epic_sections, auto_archive_completed_epics


def test_parse_epic_sections():
    sample_content = """# Sprint Backlog

> 📦 **Archives des Sprints Antérieurs** : [archive/history.md](archive/history.md)

---

## Épopée : EPIC-99-TEST-CLOSED [DONE]

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **TEST-001-BE** | - | Backend | Titre 1 | `DONE` | `SHIPPED` | IA |
| [ ] | **TEST-002-BE** | - | Backend | Titre 2 | `DONE` | `DONE_TESTED` | IA |

---

## Épopée : EPIC-100-TEST-OPEN [OPEN]

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [ ] | **TEST-101-BE** | - | Backend | Titre 3 | `PENDING` | `DRAFT` | Humain |
| [ ] | **TEST-102-BE** | - | Backend | Titre 4 | `DONE` | `READY_FOR_DEV` | Humain |

---
"""
    epics = parse_epic_sections(sample_content)
    assert len(epics) == 2
    assert epics[0]["epic_key"] == "EPIC-99-TEST-CLOSED"
    assert epics[0]["is_complete"] is True
    assert len(epics[0]["stories"]) == 2

    assert epics[1]["epic_key"] == "EPIC-100-TEST-OPEN"
    assert epics[1]["is_complete"] is False
    assert len(epics[1]["stories"]) == 2


def test_auto_archive_completed_epics(tmp_path: Path):
    backlog_dir = tmp_path / "backlog"
    stories_dir = backlog_dir / "stories"
    epics_dir = backlog_dir / "epics"
    archive_dir = backlog_dir / "archive"

    stories_dir.mkdir(parents=True)
    epics_dir.mkdir(parents=True)

    # Création des stories physiques
    (stories_dir / "TEST-001-BE.md").write_text("---\nid: TEST-001-BE\nstatus: SHIPPED\n---\n", encoding="utf-8")
    (stories_dir / "TEST-101-BE.md").write_text("---\nid: TEST-101-BE\nstatus: DRAFT\n---\n", encoding="utf-8")

    # Création du fichier d'épopée
    (epics_dir / "epic_test_closed.md").write_text("# 🏛️ Épopée : EPIC-99-TEST-CLOSED\n", encoding="utf-8")
    (epics_dir / "epic_test_open.md").write_text("# 🏛️ Épopée : EPIC-100-TEST-OPEN\n", encoding="utf-8")

    # Backlog
    backlog_content = """# Sprint Backlog

> 📦 **Archives des Sprints Antérieurs** : [archive/old.md](archive/old.md)

---

## Épopée : EPIC-99-TEST-CLOSED [DONE]

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **TEST-001-BE** | - | Backend | Titre 1 | `DONE` | `SHIPPED` | IA |

---

## Épopée : EPIC-100-TEST-OPEN [OPEN]

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [ ] | **TEST-101-BE** | - | Backend | Titre 2 | `PENDING` | `DRAFT` | Humain |

---
"""
    (backlog_dir / "sprint_backlog.md").write_text(backlog_content, encoding="utf-8")

    # Exécution de l'archivage
    res = auto_archive_completed_epics(tmp_path, archive_filename="history_test.md")
    assert res["status"] == "success"
    assert res["archived_epics"] == 1
    assert res["archived_epics_keys"] == ["EPIC-99-TEST-CLOSED"]
    assert res["archived_stories"] == 1
    assert res["archived_stories_ids"] == ["TEST-001-BE"]

    # Vérification déplacement stories
    assert not (stories_dir / "TEST-001-BE.md").exists()
    assert (archive_dir / "stories" / "TEST-001-BE.md").exists()
    assert (stories_dir / "TEST-101-BE.md").exists()

    # Vérification déplacement epics
    assert not (epics_dir / "epic_test_closed.md").exists()
    assert (archive_dir / "epics" / "epic_test_closed.md").exists()
    assert (epics_dir / "epic_test_open.md").exists()

    # Vérification contenu du sprint backlog
    updated_backlog = (backlog_dir / "sprint_backlog.md").read_text(encoding="utf-8")
    assert "EPIC-99-TEST-CLOSED" not in updated_backlog
    assert "EPIC-100-TEST-OPEN" in updated_backlog
    assert "history_test.md" in updated_backlog

    # Vérification du fichier d'archive
    archive_file = archive_dir / "history_test.md"
    assert archive_file.exists()
    archive_text = archive_file.read_text(encoding="utf-8")
    assert "EPIC-99-TEST-CLOSED" in archive_text
    assert "TEST-001-BE" in archive_text


def test_auto_archive_dry_run(tmp_path: Path):
    backlog_dir = tmp_path / "backlog"
    stories_dir = backlog_dir / "stories"
    stories_dir.mkdir(parents=True)
    (stories_dir / "TEST-001-BE.md").write_text("---\nid: TEST-001-BE\nstatus: SHIPPED\n---\n", encoding="utf-8")

    backlog_content = """# Sprint Backlog

## Épopée : EPIC-99-TEST-CLOSED [DONE]

| État | Récit | Clé Jira | Composant | Titre | Grill-me | Statut | Responsable |
| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- |
| [x] | **TEST-001-BE** | - | Backend | Titre 1 | `DONE` | `SHIPPED` | IA |

---
"""
    (backlog_dir / "sprint_backlog.md").write_text(backlog_content, encoding="utf-8")

    res = auto_archive_completed_epics(tmp_path, dry_run=True)
    assert res["status"] == "success"
    assert res["archived_epics"] == 1
    assert (stories_dir / "TEST-001-BE.md").exists()
    assert not (backlog_dir / "archive" / "stories" / "TEST-001-BE.md").exists()
