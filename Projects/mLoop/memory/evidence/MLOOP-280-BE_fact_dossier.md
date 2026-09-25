# 📁 Dossier de Preuves Documentaires — `MLOOP-280-BE`

- **Récit** : `MLOOP-280-BE` — Résolution Dynamique du Gabarit `project_adr_template.md` (EPIC-28-ADR-CLEAN-ARCHITECTURE)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill Macro EPIC-28 (Q1-A Cascade à 3 niveaux & Q2-A Substituteur Déterministe {{TAG}}) → `ADR-012_epic-28_assainissement_generateur_adr_clean_architecture.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `file:///C:/Memory%20Loop/Projects/mLoop/backlog/epics/epic_adr_clean_architecture.md`
- Blueprint Canonique : `standards/blueprints/project_adr_template.md`
- Code source existant : `src/pipelines/grill_engine.py` (Lignes 19-40, constante statique en dur)
- ADR associés : ADR-0320 (Grill-Me), ADR-0376 (Zéro Blindspot), ADR-012 (Décision d'architecture EPIC-28)
- Maquettes : Aucune (récit backend pur, composant de templating in-process)

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Template en dur Python vs Blueprint Markdown | **Blueprint > Python** : Le fichier `project_adr_template.md` devient la SSOT canonique (Q1-A). |
| Placeholders simples `{tag}` vs Moustaches `{{TAG}}` | **Moustaches doubles prioritaires** : Syntaxe standard mLoop {{TAG}} avec fallback permissif {tag} (Q2-A). |
| Jinja2 vs Substituteur Déterministe pur | **Python pur sans dépendance** : Regex direct pour éliminer les dépendances externes superflues. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `src/pipelines/grill_engine.py` (Lignes 19-24) :**
```python
ADR_TEMPLATE = """# 🏛️ ADR-{adr_id:03d} : {title}

- **Statut** : DECIDED
- **Date** : {date}
- **Décideurs** : Utilisateur & mLoop Agent
```
➔ **Fait établi (F-01)** : Le moteur utilise une constante Python figée, déconnectée du blueprint officiel.

**Extrait 2 — `standards/blueprints/project_adr_template.md` (Lignes 1-5) :**
```markdown
# 🏛️ ADR-{{ADR_ID}} : {{TITLE}}

- **Statut** : DECIDED
- **Date** : {{DATE}}
- **Décideurs** : Utilisateur & mLoop Agent
```
➔ **Fait établi (F-02)** : Le standard universel mLoop emploie les moustaches doubles `{{TAG}}`.
