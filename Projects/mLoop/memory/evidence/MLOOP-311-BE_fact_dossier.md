# 📋 Fact Dossier — `MLOOP-311-BE` : Assainissement Anti-Hardcoding de state_machine.py (Verticaux, TTL & Arborescence)

---

- **Récit Cible** : `MLOOP-311-BE`
- **Épopée** : `EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION`
- **Composant** : `Pipelines/FSM` (`src/pipelines/state_machine.py`)
- **Établi le** : 2026-09-25 — Session Macro-Grill VALIDÉE (PO Marco)
- **Autorité** : PO mLoop (Marco) / Architecte Framework

---

## ⚖️ 1. Matrice des Décisions Validées en Session Macro-Grill

| # | Question Grillée | Option Retenue | Justification & Impact Technique |
| :- | :--- | :---: | :--- |
| **Q1** | Résolution dynamique des catégories Sentinel | **Option 1.A (Miroir dynamique + rglob)** | Remplacement du filtre en dur `["FOOD", "COMMERCE", "SANTE"]` par une détection dynamique `category = story_file.parent.name if story_file.parent != self.stories_path else ""` avec recherche prioritaire dans `reviews/{category}/`, puis à la racine de `reviews/`, puis en `rglob`. Éradication intégrale des fuites clients. |
| **Q2** | Unification de la constante `DEFAULT_TTL_CYCLES` | **Option 2.A (SSOT Configurable)** | Suppression de la définition conflictuelle L22 (`= 3`). Centralisation d'une définition unique L174 lisant `int(os.getenv("MLOOP_DEFAULT_TTL_CYCLES", "5"))`. |

---

## 🔍 2. Extraits Sourcés & Passage-Level Grounding (Vérité Terrain)

### Extrait 1 — `src/pipelines/state_machine.py` (Lignes 260–265) : Hardcoding des verticaux clients
```python
        story_stem = story_file.stem
        category = (
            story_file.parent.name
            if story_file.parent.name in ["FOOD", "COMMERCE", "SANTE"]
            else ""
        )
```
* **Fait Établi** : Fuite métier flagrante d'un ancien client spécifique dans le moteur cœur du framework. La détection doit être 100% relative à l'arborescence effective sous `self.stories_path`.

### Extrait 2 — `src/pipelines/state_machine.py` (Lignes 22 & 174) : Duplication conflictuelle
```python
# Ligne 22 :
DEFAULT_TTL_CYCLES = 3

# Ligne 174 :
DEFAULT_TTL_CYCLES = 5
```
* **Fait Établi** : Double déclaration de constante au sein du même module créant une ambiguïté sur la valeur réelle utilisée lors des calculs de dépréciation.

### Extrait 3 — `src/pipelines/state_machine.py` (Lignes 230, 348–353, 496) : Chaînes littérales de statuts
```python
# L230:
if isinstance(data, dict) and data.get("status") == "IN_ANALYZE":

# L348-353:
gated_statuses = ("READY_FOR_DEV", "READY_FOR_GROOMING", "IN_DEV", "IN_QA")

# L496:
if not stored_hash or status not in ("READY_FOR_GROOMING", "READY_FOR_DEV"):
```
* **Fait Établi** : Utilisation de chaînes littérales non typées. Substitution obligatoire par les énumérateurs de `StoryStatus` et `ProjectLayout`.

---

## 🏛️ 3. Structure de Données & Typage Cible

- Résolution miroir :
  ```python
  def _resolve_review_file(self, story_file: Path) -> Optional[Path]:
      story_stem = story_file.stem
      rel_parent = story_file.parent.relative_to(self.stories_path) if story_file.parent != self.stories_path else Path()
      candidate = self.reviews_path / rel_parent / f"rubber_duck_{story_stem}.md"
      if candidate.exists():
          return candidate
      root_candidate = self.reviews_path / f"rubber_duck_{story_stem}.md"
      if root_candidate.exists():
          return root_candidate
      matches = list(self.reviews_path.rglob(f"rubber_duck_{story_stem}.md"))
      return matches[0] if matches else None
  ```
- Typage strict via `StoryStatus.READY_FOR_QA`, `StoryStatus.QA_CERTIFIED`, `StoryStatus.READY_TO_SHIP`.

---

## 🚪 4. Frontière Active & Admission of Limits

- **In-Scope MLOOP-311-BE** :
  - Nettoyage chirurgical de `src/pipelines/state_machine.py`.
  - Éradication de `"FOOD"`, `"COMMERCE"`, `"SANTE"`.
  - Unification de `DEFAULT_TTL_CYCLES`.
  - Typage des vérifications Sentinel, C9 et Anti-Tampering via `StoryStatus`.
- **Out-of-Scope** :
  - Matrice des transitions FSM (`MLOOP-312-BE`).
  - Regex des tables Markdown (`MLOOP-313-BE`).
