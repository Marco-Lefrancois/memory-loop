# 📁 Dossier de Preuves Documentaires — `MLOOP-283-FULL`

- **Récit** : `MLOOP-283-FULL` — Harnais de Tests de Non-Régression & Certification Vibe-Check
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill Macro EPIC-28 (Certification globale 4 Piliers & AST) → `ADR-012_epic-28_assainissement_generateur_adr_clean_architecture.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `file:///C:/Memory%20Loop/Projects/mLoop/backlog/epics/epic_adr_clean_architecture.md`
- Fichier de tests existant : `tests/test_grill_engine.py` (11 tests passants)
- Normes qualité : ADR-0383 (Harnais QA Phase 4), ADR-0376 (Rigueur Zéro Blindspot), ADR-012
- Maquettes : Aucune (récit fullstack/outillage CLI)

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Tests partiels vs Certification Vibe-Check E2E | **Triangulation 4 Piliers** : validation unitaire pytest + code-check AST + vibe-check souverain. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `tests/test_grill_engine.py` :**
```text
tests\test_grill_engine.py ........... [100%]
11 passed in 0.47s
```
➔ **Fait établi (F-01)** : Socle unitaire existant validé, servant de référence de non-régression.
