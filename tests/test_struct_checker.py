# -*- coding: utf-8 -*-
"""
Tests unitaires — StructCheckEngine (7 checks C1–C7)
Phase RED du cycle TDD mLoop.

Couvre :
  C1. Hiérarchie des titres : pas de saut H2→H4 sans H3
  C2. Format des listes dans sections UX : '-' uniquement (interdit '*' et '+')
  C3. Redondances bilingues dans titres H4 (ex: "En-tête (Header)")
  C4. Diff stylistique H3/H4 vs Gold Standard
  C5. Séparateurs '---' entre sections H2 (Read-Only, pas d'auto-heal)
  C6. Frontmatter YAML : champs obligatoires présents
  C7. Titre H1 : format '# [JIRA-KEY] Titre métier'
"""

import tempfile
import unittest
from pathlib import Path

from src.pipelines.struct_checker import StructCheckEngine, StructCheckReport


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_file(content: str, tmp_dir: Path, name: str = "REC-TEST-FE.md") -> Path:
    """Écrit un fichier temporaire et retourne son chemin."""
    p = tmp_dir / name
    p.write_text(content, encoding="utf-8")
    return p


VALID_FRONTMATTER = """\
---
id: REC-TEST-FE
jira_key: PROJ-001
epic_key: EPIC-001
type: Feature
title: Story de test
layer: frontend
status: DRAFT
---
"""

VALID_H1 = "# [PROJ-001] Story de test (REC-TEST-FE)\n\n"

VALID_UX_SECTION = """\
## Critères d'acceptation

### Interface et UX

#### 1. En-tête
- **[Navigation]** : Flèche de retour.
- **[Titre]** : Titre de l'écran.

#### 2. Corps
- **[Liste]** : Items affichés.

---

"""

VALID_SCENARIOS = """\
## Scénarios de test

### Scénario 1 : Nominal
Scénario: Chargement nominal
  Étant donné que l'utilisateur est connecté
  Quand il accède à l'écran
  Alors l'interface s'affiche

### Scénario 2 : Exception
Scénario: Erreur réseau
  Étant donné que le réseau est indisponible
  Quand il accède à l'écran
  Alors un message d'erreur s'affiche

### Scénario 3 : Résilience
Scénario: Timeout backend
  Étant donné que le backend répond lentement
  Quand il accède à l'écran
  Alors l'interface affiche un état de chargement

### Scénario 4 : UX
Scénario: Retour utilisateur
  Étant donné que l'écran est affiché
  Quand l'utilisateur appuie sur retour
  Alors il retourne au tableau de bord

---

## Règles d'affaires

- Règle 1 : L'accès est conditionnel au rôle utilisateur.
"""


def _valid_story() -> str:
    return VALID_FRONTMATTER + VALID_H1 + VALID_UX_SECTION + VALID_SCENARIOS


# ─── Test Suite ───────────────────────────────────────────────────────────────

class TestStructCheckerC1HeadingHierarchy(unittest.TestCase):
    """C1 : Pas de saut de niveau de titre (ex: H2 → H4 sans H3)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.engine = StructCheckEngine(self.tmp_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_c1_valid_hierarchy(self):
        """H2 → H3 → H4 : aucune violation C1."""
        content = _valid_story()
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c1_violations = [v for v in report.violations if v.check_id == "C1"]
        self.assertEqual(len(c1_violations), 0, f"C1 violations inattendues : {c1_violations}")

    def test_c1_h2_to_h4_skip_blocking(self):
        """H2 → H4 sans H3 : violation C1 BLOCKING."""
        content = VALID_FRONTMATTER + VALID_H1 + """\
## Critères d'acceptation

#### 1. Section sans H3 parent
- Item 1.

---

""" + VALID_SCENARIOS
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c1_violations = [v for v in report.violations if v.check_id == "C1"]
        self.assertGreater(len(c1_violations), 0, "C1 doit détecter le saut H2→H4")
        self.assertTrue(any(v.severity == "BLOCKING" for v in c1_violations))


class TestStructCheckerC2ListFormat(unittest.TestCase):
    """C2 : Format des listes dans sections UX — tirets '-' uniquement."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.engine = StructCheckEngine(self.tmp_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_c2_valid_dashes(self):
        """Listes avec '-' dans section UX : aucune violation C2."""
        content = _valid_story()
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c2_violations = [v for v in report.violations if v.check_id == "C2"]
        self.assertEqual(len(c2_violations), 0)

    def test_c2_asterisk_in_ux_blocking(self):
        """Liste avec '*' dans section UX : violation C2 BLOCKING."""
        content = VALID_FRONTMATTER + VALID_H1 + """\
## Critères d'acceptation

### Interface et UX

#### 1. En-tête
* **[Navigation]** : Flèche de retour.
* **[Titre]** : Titre de l'écran.

---

""" + VALID_SCENARIOS
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c2_violations = [v for v in report.violations if v.check_id == "C2"]
        self.assertGreater(len(c2_violations), 0, "C2 doit détecter les '*' dans la section UX")
        self.assertTrue(any(v.severity == "BLOCKING" for v in c2_violations))

    def test_c2_plus_in_ux_blocking(self):
        """Liste avec '+' dans section UX : violation C2 BLOCKING."""
        content = VALID_FRONTMATTER + VALID_H1 + """\
## Critères d'acceptation

### Interface et UX

#### 1. En-tête
+ **[Navigation]** : Flèche de retour.
+ **[Titre]** : Titre de l'écran.

---

""" + VALID_SCENARIOS
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c2_violations = [v for v in report.violations if v.check_id == "C2"]
        self.assertGreater(len(c2_violations), 0, "C2 doit détecter les '+' dans la section UX")

    def test_c2_asterisk_outside_ux_no_violation(self):
        """Liste avec '*' hors section UX (ex: Règles d'affaires) : aucune violation C2."""
        content = VALID_FRONTMATTER + VALID_H1 + VALID_UX_SECTION + """\
## Scénarios de test

### Scénario 1 : Nominal
Scénario: Chargement nominal
  Étant donné que l'utilisateur est connecté
  Quand il accède à l'écran
  Alors l'interface s'affiche

### Scénario 2 : Exception
Scénario: Erreur réseau
  Étant donné que le réseau est indisponible
  Quand il accède à l'écran
  Alors un message d'erreur s'affiche

### Scénario 3 : Résilience
Scénario: Timeout backend
  Étant donné que le backend répond lentement
  Quand il accède à l'écran
  Alors l'interface affiche un état de chargement

### Scénario 4 : UX
Scénario: Retour utilisateur
  Étant donné que l'écran est affiché
  Quand l'utilisateur appuie sur retour
  Alors il retourne au tableau de bord

---

## Règles d'affaires

* Règle avec astérisque hors UX — acceptable.
"""
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c2_violations = [v for v in report.violations if v.check_id == "C2"]
        self.assertEqual(len(c2_violations), 0, f"C2 ne doit pas signaler les listes hors section UX : {c2_violations}")


class TestStructCheckerC3TitleRedundancy(unittest.TestCase):
    """C3 : Redondances bilingues dans titres H4."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.engine = StructCheckEngine(self.tmp_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_c3_no_redundancy(self):
        """Titres H4 sans redondance : aucune violation C3."""
        content = _valid_story()
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c3_violations = [v for v in report.violations if v.check_id == "C3"]
        self.assertEqual(len(c3_violations), 0)

    def test_c3_bilingual_redundancy_warning(self):
        """Titre H4 avec redondance bilingue (ex: 'En-tête (Header)') : violation C3 WARNING."""
        content = VALID_FRONTMATTER + VALID_H1 + """\
## Critères d'acceptation

### Interface et UX

#### 1. En-tête (Header)
- **[Navigation]** : Flèche de retour.

#### 2. Corps Principal (Body)
- **[Liste]** : Items affichés.

---

""" + VALID_SCENARIOS
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c3_violations = [v for v in report.violations if v.check_id == "C3"]
        self.assertGreater(len(c3_violations), 0, "C3 doit détecter la redondance bilingue H4")
        self.assertTrue(any(v.severity == "WARNING" for v in c3_violations))


class TestStructCheckerC5Separators(unittest.TestCase):
    """C5 : Séparateurs '---' entre sections H2 (Read-Only)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.engine = StructCheckEngine(self.tmp_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_c5_separators_present(self):
        """Séparateurs '---' présents : aucune violation C5."""
        content = _valid_story()
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c5_violations = [v for v in report.violations if v.check_id == "C5"]
        self.assertEqual(len(c5_violations), 0)

    def test_c5_missing_separator_warning(self):
        """Séparateur '---' manquant avant un H2 : violation C5 WARNING (sans auto-heal)."""
        content = VALID_FRONTMATTER + VALID_H1 + """\
## Critères d'acceptation

### Interface et UX

#### 1. En-tête
- **[Navigation]** : Flèche de retour.

## Scénarios de test

### Scénario 1 : Nominal
Scénario: Chargement nominal
  Étant donné que l'utilisateur est connecté
  Quand il accède à l'écran
  Alors l'interface s'affiche

### Scénario 2 : Exception
Scénario: Erreur réseau
  Étant donné que le réseau est indisponible
  Quand il accède à l'écran
  Alors un message d'erreur s'affiche

### Scénario 3 : Résilience
Scénario: Timeout
  Étant donné que le backend est lent
  Quand il accède à l'écran
  Alors un état de chargement s'affiche

### Scénario 4 : UX
Scénario: Retour
  Étant donné que l'écran est affiché
  Quand l'utilisateur appuie sur retour
  Alors il retourne au tableau de bord

## Règles d'affaires

- Règle 1.
"""
        f = _make_file(content, self.tmp_path)
        original_mtime = f.stat().st_mtime
        report = self.engine.check_file(f)
        # Vérifier que le fichier N'A PAS été modifié (Read-Only)
        self.assertEqual(f.stat().st_mtime, original_mtime, "C5 ne doit PAS modifier le fichier (Read-Only)")
        c5_violations = [v for v in report.violations if v.check_id == "C5"]
        self.assertGreater(len(c5_violations), 0, "C5 doit détecter le séparateur manquant")
        self.assertTrue(any(v.severity == "WARNING" for v in c5_violations))


class TestStructCheckerC6Frontmatter(unittest.TestCase):
    """C6 : Frontmatter YAML — champs obligatoires."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.engine = StructCheckEngine(self.tmp_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_c6_valid_frontmatter(self):
        """Frontmatter complet : aucune violation C6."""
        content = _valid_story()
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c6_violations = [v for v in report.violations if v.check_id == "C6"]
        self.assertEqual(len(c6_violations), 0)

    def test_c6_missing_layer_blocking(self):
        """Frontmatter sans 'layer' : violation C6 BLOCKING."""
        content = """\
---
id: REC-TEST-FE
jira_key: PROJ-001
epic_key: EPIC-001
type: Feature
title: Story de test
status: DRAFT
---
""" + VALID_H1 + VALID_UX_SECTION + VALID_SCENARIOS
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c6_violations = [v for v in report.violations if v.check_id == "C6"]
        self.assertGreater(len(c6_violations), 0, "C6 doit détecter l'absence de 'layer'")
        self.assertTrue(any(v.severity == "BLOCKING" for v in c6_violations))

    def test_c6_missing_id_blocking(self):
        """Frontmatter sans 'id' : violation C6 BLOCKING."""
        content = """\
---
jira_key: PROJ-001
epic_key: EPIC-001
type: Feature
title: Story de test
layer: frontend
status: DRAFT
---
""" + VALID_H1 + VALID_UX_SECTION + VALID_SCENARIOS
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c6_violations = [v for v in report.violations if v.check_id == "C6"]
        self.assertGreater(len(c6_violations), 0, "C6 doit détecter l'absence de 'id'")

    def test_c6_no_frontmatter_blocking(self):
        """Fichier sans frontmatter YAML : violation C6 BLOCKING."""
        content = "# [PROJ-001] Story sans frontmatter\n\nContenu quelconque.\n"
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c6_violations = [v for v in report.violations if v.check_id == "C6"]
        self.assertGreater(len(c6_violations), 0, "C6 doit détecter l'absence de frontmatter")
        self.assertTrue(any(v.severity == "BLOCKING" for v in c6_violations))


class TestStructCheckerC7H1Format(unittest.TestCase):
    """C7 : Titre H1 au format '# [JIRA-KEY] Titre métier'."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.engine = StructCheckEngine(self.tmp_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_c7_valid_h1(self):
        """Titre H1 conforme : aucune violation C7."""
        content = _valid_story()
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c7_violations = [v for v in report.violations if v.check_id == "C7"]
        self.assertEqual(len(c7_violations), 0)

    def test_c7_valid_pure_h1(self):
        """Titre H1 métier pur : aucune violation C7."""
        content = VALID_FRONTMATTER + "# Story de test métier pur\n\n" + VALID_UX_SECTION + VALID_SCENARIOS
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c7_violations = [v for v in report.violations if v.check_id == "C7"]
        self.assertEqual(len(c7_violations), 0)

    def test_c7_missing_h1_warning(self):
        """Absence de titre H1 : violation C7 WARNING."""
        content = VALID_FRONTMATTER + "## Description\n\n" + VALID_UX_SECTION + VALID_SCENARIOS
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        c7_violations = [v for v in report.violations if v.check_id == "C7"]
        self.assertGreater(len(c7_violations), 0, "C7 doit détecter l'absence de titre H1")
        self.assertTrue(any(v.severity == "WARNING" for v in c7_violations))


class TestStructCheckerReport(unittest.TestCase):
    """Tests sur la structure du rapport et le champ 'passed'."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.engine = StructCheckEngine(self.tmp_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_report_passed_on_valid_story(self):
        """Story valide : report.passed == True."""
        content = _valid_story()
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        self.assertIsInstance(report, StructCheckReport)
        blocking = [v for v in report.violations if v.severity == "BLOCKING"]
        self.assertEqual(len(blocking), 0, f"Violations BLOCKING inattendues : {blocking}")
        self.assertTrue(report.passed)

    def test_report_failed_on_invalid_story(self):
        """Story avec violations BLOCKING : report.passed == False."""
        # Story sans frontmatter = violation C6 BLOCKING garantie
        content = "# Story sans frontmatter\n\nContenu.\n"
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        self.assertFalse(report.passed)

    def test_report_file_path_correct(self):
        """Le rapport contient le bon chemin de fichier."""
        content = _valid_story()
        f = _make_file(content, self.tmp_path)
        report = self.engine.check_file(f)
        self.assertEqual(report.file, f)


if __name__ == "__main__":
    unittest.main()
