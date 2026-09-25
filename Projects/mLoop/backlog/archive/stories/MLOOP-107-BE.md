---
id: MLOOP-107-BE
jira_key: ""
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Bug
title: "Correction du Verrou d'Attention Focus (Persistance Frontmatter et Verdict)"
origin: "DIRECT_REQUIREMENT"
source_ref: "MLOOP-101-BE Grill-Me 1:1 Arbitrage #5 (2026-09-20)"
macro_size: "XS"
status: SHIPPED
grill_me: PENDING
invest_score: 0/6
layer: backend
blocked_by: []
created_at: "2026-09-20"
---

# 📖 MLOOP-107-BE : Correction du Verrou d'Attention Focus (Persistance Frontmatter et Verdict)

## 1. Intention Métier (User Story)
**En tant que** Agent Orchestrateur mLoop,  
**je veux** que `focus --story <ID>` persiste la transition IN_ANALYZE même sans suffixe `.md` et n'affiche le succès que si la transition est réellement effectuée,  
**afin de** garantir la fiabilité du verrou d'attention (une story non verrouillée fait dériver toute la session).

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Grill-Me 1:1 MLOOP-101-BE — Arbitrage #5 (bug confirmé par lecture directe, `memory/evidence/MLOOP-101-BE_fact_dossier.md`)
- **Hypothèse de Chiffrage Retenue** : correctif localisé ~5-15 lignes + tests
- **Enveloppe Macro Estimée** : XS (fourchette de 0.5 jour)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- `src/pipelines/focus.py` : réassignation de `story_rel_path` dans le fallback `.md` (L32-33) ; fiabilisation de la comparaison de persistance (L90) ; conditionnement du verdict de succès (L114-115, plus de `return True` inconditionnel).
- Purge de la violation ADR-0369 du fichier lui-même (`except Exception: pass` L52-53).

### Out-of-Scope (Macro)
- `src/utils/` (MLOOP-101-BE) et `src/commands/` (MLOOP-106-BE).
- Toute autre pipeline que `focus.py`.

---

## 4. Critères de Succès Préliminaires
- [ ] `focus --story MLOOP-107-BE` (sans `.md`) persiste le statut IN_ANALYZE dans le frontmatter.
- [ ] Toute story introuvable produit une erreur explicite (exit ≠ 0), jamais un faux succès.

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ OQ-1 : Normaliser l'entrée dès la résolution (ajout systématique de `.md`) ou fiabiliser la comparaison relative ? (impact : log du message final).
- ❓ OQ-2 : Emplacement du test unitaire de non-régression du focus (aucune suite pipelines n'existe).
- ❓ OQ-3 : Le verdict conditionné doit-il aussi couvrir le cas « déjà IN_ANALYZE » (idempotence vs re-emission) ?
