# Brief Worker — P6-A (Création Ébauches DRAFT — 5 Monolithes EPIC-17)

> **Mission** : Rédiger **5 ébauches de récits** (Palier 1) pour le refactoring des monolithes critiques RULE-AST-01, en suivant strictement le gabarit officiel.
> **Working dir** : `C:\Memory Loop`
> **Statut cible des fichiers** : `DRAFT` · `grill_me: PENDING` (l'humain griliera ensuite).

---

## 1. Contexte

- **P5 terminée** : pilote `vibe_check` (170), cartographie (171), pattern (172) = `DONE_TESTED`.
- **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` (v1, 3 cas spéciaux).
- **Gabarit OBLIGATOIRE** : `standards/blueprints/story_draft_template.md` — **aucun autre template** (ADR-0375).
- **Matrice fraîche** : `Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md` (39 fichiers, BR desc).
- **Épopée** : `Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md` (Lot 1 / OQ-171-04 : zéro dérogation, `_registry` inclus).

---

## 2. Les 5 récits à créer (un fichier chacun)

Chemin : `Projects/mLoop/backlog/stories/<ID>.md`

| # | ID temporaire suggéré | Composant | Taille | BR | Lot | Cas spécial protocole |
|:-:|:---|:---|---:|---:|:---:|:---|
| 1 | `MLOOP-173-BE` | `src/state.py` | 770L | **78** | Lot 1 | §3.2 Singletons d'état |
| 2 | `MLOOP-174-BE` | `src/core/lifecycle.py` | 852L | 8 | Lot 1 | Cas général + gates |
| 3 | `MLOOP-175-BE` | `src/commands/_registry.py` | **2028L** | 3 | Lot 1 | §3.1 Registres déclaratifs |
| 4 | `MLOOP-176-BE` | `src/converters/svg_to_md.py` | 991L | ? | Lot 2/3 | Cas général (OCR/converters) |
| 5 | `MLOOP-177-BE` | `src/dashboard/server.py` | **1634L** | 0 | Lot 3 (OQ-171-03) | Cas général (FastAPI routers) |

> **Vérifier les BR/ tailles exacts** dans la matrice avant rédaction (ne pas inventer). Si un ID est déjà pris dans `backlog/stories/`, incrémenter (`MLOOP-178-BE`, etc.) — vérifier par `Test-Path`.

---

## 3. Structure exigée pour CHAQUE ébauche (Palier 1)

Suivre **à la lettre** `standards/blueprints/story_draft_template.md` :

1. **Frontmatter YAML** minimum :
   ```yaml
   id: MLOOP-17X-BE
   jira_key: ''
   epic_key: EPIC-17-MODULAR-REFACTORING
   type: standard          # ou refactor si le gabarit le prévoit
   title: <Titre métier pur, sans clé Jira>
   layer: backend
   status: DRAFT
   grill_me: PENDING
   invest_score: 0/6        # réévalué après grill
   macro_size: S            # ou M si >1 jour
   blocked_by: []           # ou dépendances réelles (ex: priorité BR)
   created_at: '2026-09-23'
   ```
2. **H1** : titre métier pur uniquement (zéro clé Jira entre parenthèses).
3. **Sections du gabarit draft** (intention, origine, périmètre, critères préliminaires) — version courte.
4. **Lien protocole** : chaque récit référence explicitement `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` et le cas spécial applicable (§2/§3.1/§3.2/§3.3).
5. **Zéro** 4 piliers Gherkin détaillés en DRAFT (ils viendront au palier 2 après grill).
6. **Zéro** invented API / faux JSON / chemin local `C:\...` dans le corps.

---

## 4. Contraintes strictes

| Contrainte | Détail |
|:---|:---|
| Gabarit unique | **Uniquement** `story_draft_template.md` (ADR-0375) |
| IDs | Temporaires déterministes `MLOOP-17X-BE` ; **jamais** inventer de clé Jira définitive |
| Sprint backlog | **Ajouter** 5 lignes `[ ]` en zone refactoring/EPIC-17 avec statut `DRAFT` (si zone inexistante, ajouter sous la section la plus proche) — **ne pas** toucher aux statuts des récits existants |
| Épopée | Ajouter 5 entrées `### N. MLOOP-17X-BE` au registre + lignes matrice `| 4+ … | DRAFT |` sans écraser les DONE |
| ADR-0369 | Si code auxiliaire : timeout / with / zéro `except pass` |
| Git | **Aucun commit** |
| Ne pas | Modifier les récits 170/171/172 · le protocole · le frontmatter des stories existantes autres que les 5 nouvelles |
| Ne pas | Exécuter `grill-me` ou promouvoir `READY_FOR_DEV` (orchestrateur/humain) |

---

## 5. Méthode de fin (DONE)

1. 5 fichiers créés sous `Projects/mLoop/backlog/stories/MLOOP-17X-BE.md` — chacun `status: DRAFT`, `grill_me: PENDING`.
2. `sprint_backlog.md` : 5 lignes DRAFT visibles.
3. Épopée : registre enrichi, statut global inchangé `OPEN`.
4. Rapport : `Projects/mLoop/memory/evidence/P6A_drafts_report.md`
   - Table : ID | fichier cible | tailles/BR vérifiés vs matrice | cas spécial protocole | chemins créés
   - Dernière ligne : `STATUS: DONE` ou `STATUS: BLOCKED — <raison>`.
5. Ne pas fermer le worker (orchestrateur harvest).
