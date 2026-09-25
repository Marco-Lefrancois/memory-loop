---
id: MLOOP-170-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: refactoring
title: Récit Pilote — Refactoring Modulaire de vibe_check.py (880L → <300L/module)
origin: DIRECT_REQUIREMENT
source_ref: EPIC-17/epic_modular_refactoring_ast_debt.md §1
macro_size: M
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-22'
content_hash: 4ee57cfab92a505a
ttl_cycles: 4
---

# 📖 Récit Pilote — Refactoring Modulaire de vibe_check.py

## 1. Intention Métier (User Story)
**En tant que** Ingénieur du framework mLoop,
**je veux** découper `src/pipelines/vibe_check.py` (880 lignes) en sous-modules cohérents (un module par famille de contrôles, ou un registre de checks),
**afin de** ramener chaque unité sous le plafond de 300 lignes (ADR-0202 / RULE-AST-01) sans altérer le comportement du guardrail ni casser ses callers.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md` (§1 — Récit Pilote)
- **Faits vérifiés (2026-09-22)** : `vibe_check.py` = **880 lignes** ; structure = 2 définitions top-level (`detect_project_lifecycle_stage` L10, `run_vibe_check` L129 — le reste est le corps monolithique de `run_vibe_check` avec 28 mentions de familles de checks) ; **19 fichiers** référencent `vibe_check` sous `src/` + `tests/`
- **Rôle du pilote** : établir le pattern d'extraction réutilisable qui servira aux 38 fichiers restants (MLOOP-172-BE)
- **Enveloppe Macro Estimée** : M (2-4 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Découpage de `vibe_check.py` en sous-modules thématiques sous `src/pipelines/vibe_check/` (package)
- **Signature publique inchangée** : `run_vibe_check(project_name, target_file=None, stage=None) -> dict` et structure de retour exactes
- Rétrocompatibilité des imports (ré-export depuis `src/pipelines/vibe_check.py` ou shim)
- Suite de tests verte à chaque étape d'extraction (approche red-green ADR-0381)

### Out-of-Scope (Macro)
- Toute évolution fonctionnelle des contrôles (comportement figé)
- Les 38 autres fichiers en dette (récits de lots suivants)
- RULE-AST-02/03

---

## 4. Critères de Succès Préliminaires
- [x] Chaque module produit < 300 lignes (zéro violation RULE-AST-01 sur le package)
- [x] Nombre et verdicts des contrôles identiques à avant refactoring (sortie `vibe-check` byte-compatible ou explicitement comparée)
- [x] 19 fichiers callers sans modification

---

## 6. Arbitrages Grill-Me Micro 1:1 (Séance du 2026-09-22)
> ✅ Séance tenue (1 question par tour, arbitrages verbatim PO ; frontière close).

| OQ | Décision Arbitrée |
|:---|:---|
| OQ-170-01 | **Orchestrateur fin + un module par famille de contrôles, imports explicites** — pas d'auto-découverte magique (pattern registry proscrit pour ce package) |
| OQ-170-02 | **Découplage complet d'EPIC-16** — démarrage immédiat autorisé ; contrat de signature publique `run_vibe_check` gelé ; l'agent dashboard n'est que consommateur de l'import |
| OQ-170-03 | **DISSOLUE par OQ-171-02** — le garde-fou anti-aggravation est bloquant dès maintenant ; le pilote s'exécute donc sous contrôle actif (pas après) |
| OQ-170-04 | **Hybridation pragmatique (délégué au Cerveau, approuvé PO « go »)** — tests existants immobiles (filet de régression, ADR-0381) ; compatibilité structurelle via package + ré-exports `__init__.py` ; tests miroir neufs uniquement pour chaque famille extraite (`tests/vibe_check/<famille>_test.py`) |

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Découpage (OQ-170-01)
- [x] Package `src/pipelines/vibe_check/` : un module par famille de contrôles + orchestrateur fin à imports explicites (zéro auto-découverte)
- [x] Chaque module < 300 lignes — zéro violation RULE-AST-01

#### 2. Contrat Public Gelé (OQ-170-02)
- [x] Signature `run_vibe_check(project_name, target_file=None, stage=None) -> dict` et structure de retour strictement inchangées
- [x] `__init__.py` ré-exporte l'API publique : les 19 fichiers callers restent inchangés

#### 3. Comportement Figé
- [x] Nombre et verdicts des contrôles identiques (sortie `vibe-check` comparée avant/après)

#### 4. Tests (OQ-170-04)
- [x] Les ~10 fichiers de tests existants restent immobiles ; tests miroir neufs pour chaque famille extraite
- [x] Suite verte à chaque étape d'extraction (red-green ADR-0381), sous garde-fou anti-aggravation actif (OQ-171-02)

### Scénarios de test (Gherkin 4 Piliers)

#### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Découpage conforme au contrat
  Étant donné "vibe_check.py" monolithique de 880 lignes
  Quand le découpage en package est appliqué
  Alors chaque module de famille pèse moins de 300 lignes
  Et la sortie de "vibe-check" est identique en nombre de contrôles et en verdicts
```

#### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Altération du contrat public rejetée
  Étant donné le contrat gelé "run_vibe_check(project_name, target_file=None, stage=None)"
  Quand une extraction modifie la signature ou la structure de retour
  Alors le test de contrat échoue et l'extraction est refusée
```

#### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Échec d'un check pendant le refactoring
  Étant donné un contrôle en échec métier lors de l'exécution
  Quand "run_vibe_check" est appelé depuis le package refondé
  Alors la structure d'erreur retournée est identique à celle d'avant refactoring
  Et aucun caller n'est impacté par la forme du message
```

#### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Transparence utilisateur totale
  Étant donné un utilisateur du CLI "vibe-check"
  Quand le refactoring est livré
  Alors la sortie console reste inchangée (mêmes messages, mêmes codes)
```

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : refactoring modulaire interne de `src/pipelines/vibe_check.py` — **aucune route HTTP n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-170` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

| Contrat | Engagement |
|:---|:---|
| `run_vibe_check(project_name, target_file=None, stage=None) -> dict` | Signature + structure de retour gelées (consommateurs : `server.py` dashboard, 19 callers) |
| `src/pipelines/vibe_check/` (package) | Orchestrateur fin + modules familles, imports explicites |
| `tests/vibe_check/<famille>_test.py` | Tests miroir neufs par famille extraite (existant immobile) |
