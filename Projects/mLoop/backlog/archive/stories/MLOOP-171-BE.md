---
id: MLOOP-171-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: analysis
title: Cartographie & Priorisation des 39 Modules en Dépassement (Blast Radius)
origin: DIRECT_REQUIREMENT
source_ref: EPIC-17/epic_modular_refactoring_ast_debt.md §2
macro_size: S
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-22'
content_hash: d66154662c04393e
ttl_cycles: 4
---

# 📖 Cartographie & Priorisation des 39 Modules en Dépassement (Blast Radius)

## 1. Intention Métier (User Story)
**En tant que** Architecte mLoop,
**je veux** un inventaire priorisé des 39 fichiers dépassant le plafond modulaire RULE-AST-01, classés par blast radius (nombre de callers via CodeGraph) et criticité fonctionnelle,
**afin de** séquencer le refactoring du plus risqué au moins risqué sans big-bang.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md` (§ Registre) + audit frais `code-check --all` archivé sous `memory/evidence/codecheck_audit_epic17.txt`
- **Constat Chiffré (2026-09-22)** : 317 fichiers analysés, **66 mentions RULE-AST-01, 39 fichiers uniques** en dépassement (vs 38 à la création de l'épopée — la dette **s'aggrave** : `archify.py` (463L) a été créé hors plafond par l'agent EPIC-16, `server.py` est monté à 1632L)
- **Top 5 dettes** : `_registry.py` (2028L) · `dashboard/server.py` (1632L) · `svg_to_md.py` (991L) · `loop_mem/db.py` (956L) · `pipelines/crawler.py` (927L)
- **Enveloppe Macro Estimée** : S (1-2 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Extraction déterministe de l'inventaire depuis le rapport `code-check --all` (zéro extrapolation)
- Comptage du blast radius par fichier (callers via CodeGraph/AST)
- Matrice de priorisation : taille × blast radius × criticité fonctionnelle (pipelines cœur vs tooling)
- Ordre de traitement par lots proposé et consigné dans `backlog/epic_modular_refactoring_ast_debt.md`

### Out-of-Scope (Macro)
- Le refactoring lui-même (récits suivants)
- Toute modification de code `src/`
- Les règles RULE-AST-02/03 (déjà traitées par le passé)

---

## 4. Critères de Succès Préliminaires
- [ ] Inventaire factuel des 39 fichiers avec taille exacte et blast radius
- [ ] Ordre de traitement par criticité décroissante validé
- [ ] Question « garde-fou anti-aggravation » arbitrée en Grill (voir §5)

---

## 6. Arbitrages Grill-Me Micro 1:1 (Séance du 2026-09-22)
> ✅ Séance tenue (1 question par tour, arbitrages verbatim du PO). Frontière close : 5/5 OQ résolues, zéro question résiduelle.

| OQ | Décision Arbitrée |
|:---|:---|
| OQ-171-01 | **Blast radius d'abord** — traiter en priorité les fichiers avec le plus de callers (ex: `state.py`, `lifecycle.py`) pour éliminer le risque maximal tôt |
| OQ-171-02 | **Garde-fou bloquant immédiat** — tout commit agrandissant un fichier déjà en dépassement RULE-AST-01 est rejeté (vibe-check + hook). *Ajoute un livrable au périmètre : implémentation du contrôle anti-aggravation* |
| OQ-171-03 | **Rétro-couverture EPIC-17** — `archify.py` (463L) et l'agrégation `server.py` (1632L) intègrent la file de refactoring après le pilote |
| OQ-171-04 | **Zéro dérogation** — plafond 300L strict pour 100% des fichiers, `_registry.py` inclus (découpage en registres partiels par domaine) |
| OQ-171-05 | **Stratégie Beachhead** — pilote + top 5 critiques en récits unitaires, le reste en lots adaptatifs |

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Inventaire Factuel
- [ ] Extraction déterministe des 39 fichiers depuis `code-check --all` (taille exacte, zéro extrapolation)
- [ ] Blast radius mesuré par fichier (callers via CodeGraph/AST)

#### 2. Priorisation & Lots
- [ ] Matrice triée par blast radius décroissant (OQ-171-01)
- [ ] Séquence Beachhead : pilote + top 5 critiques en récits unitaires, reste en lots adaptatifs (OQ-171-05)
- [ ] `archify.py` et l'agrégation `server.py` inclus dans la file (OQ-171-03)

#### 3. Garde-fou Anti-Aggravation
- [ ] Contrôle bloquant : rejet de tout commit agrandissant un fichier déjà > 300L (vibe-check + hook pre-commit)
- [ ] Échappatoire `MLOOP_SKIP_HOOKS` tracée (log d'audit à chaque usage)

#### 4. Non-Régression
- [ ] Zéro dérogation au plafond 300L, `_registry.py` inclus (OQ-171-04)
- [ ] Inventaire et matrice archivés sous `memory/evidence/`

### Scénarios de test (Gherkin 4 Piliers)

#### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Production de l'inventaire priorisé
  Étant donné le rapport "code-check --all" à jour
  Quand l'inventaire est généré
  Alors les 39 fichiers en dépassement sont listés avec leur taille et leur blast radius
  Et l'ordre de traitement suit le blast radius décroissant
```

#### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Commit aggravant rejeté
  Étant donné un fichier "server.py" déjà en dépassement à 1632 lignes
  Quand un commit augmente sa taille
  Alors le hook pre-commit rejette le commit avec la violation RULE-AST-01 détaillée
  Et le contournement "MLOOP_SKIP_HOOKS" est consigné au journal d'audit s'il est utilisé
```

#### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : CodeGraph indisponible
  Étant donné le moteur CodeGraph non opérationnel
  Quand le blast radius doit être mesuré
  Alors un fallback AST déterministe (comptage d'imports) est utilisé
  Et la méthode de mesure utilisée est annotée dans la matrice
```

#### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Matrice lisible et actionnable
  Étant donné l'inventaire complet généré
  Quand la matrice de priorisation est produite
  Alors chaque ligne expose fichier, lignes, blast radius, lot attribué
  Et la séquence Beachhead est explicitement lisible en tête de rapport
```

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **OQ-171-06** : l'exposition REST de la matrice de priorisation (endpoint dashboard pour consommer l'inventaire EPIC-17) est une surface API **[API de soumission à définir]** — explicitement hors périmètre du présent récit (livrables : CLI + hook pre-commit). Question ouverte routée vers un futur récit d'intégration dashboard.

| Commande | Livrable |
|:---|:---|
| `python src/swarm.py code-check --all --project mLoop` | Source d'inventaire (exit 1 tant que la dette existe) |
| Hook pre-commit + vibe-check | Contrôle anti-aggravation bloquant (RULE-AST-01 sur delta) |
| `memory/evidence/epic17_top40_oversized.txt` | Matrice brute consolidée (à enrichir blast radius) |

