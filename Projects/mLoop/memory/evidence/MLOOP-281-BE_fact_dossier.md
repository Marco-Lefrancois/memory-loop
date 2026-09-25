# 📁 Dossier de Preuves Documentaires — `MLOOP-281-BE`

- **Récit** : `MLOOP-281-BE` — Calculateur d'ID ADR Robuste par Regex Anti-Collision (EPIC-28-ADR-CLEAN-ARCHITECTURE)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill Macro EPIC-28 (Q3-A Regex anti-collision et formatage dynamique) → `ADR-012_epic-28_assainissement_generateur_adr_clean_architecture.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `file:///C:/Memory%20Loop/Projects/mLoop/backlog/epics/epic_adr_clean_architecture.md`
- Code source existant : `src/pipelines/grill_engine.py` (Ligne 180 : `next_id = len(existing_adrs) + 1`)
- Répertoire cible : `Projects/<projet>/docs/01-architecture/`
- ADR associés : ADR-0320, ADR-0376, ADR-012
- Maquettes : Aucune (récit backend pur)

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| `len(existing) + 1` vs `max(ids) + 1` | **Maximum mathématique** : `max(ids) + 1` immunise contre les collisions en cas de trous (Q3-A). |
| Numérotation 3 chiffres vs 4 chiffres | **Tolérance dynamique** : Regex flexible `^ADR-(\d+)` et formatage selon environnement. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `src/pipelines/grill_engine.py` (Lignes 179-181) :**
```python
existing_adrs = list(self.docs_dir.glob("ADR-*.md"))
next_id = len(existing_adrs) + 1
```
➔ **Fait établi (F-01)** : Vulnérabilité avérée aux collisions dès qu'un fichier est renommé ou supprimé.
