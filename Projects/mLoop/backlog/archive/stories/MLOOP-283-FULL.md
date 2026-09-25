---
id: MLOOP-283-FULL
jira_key: ''
epic_key: EPIC-28-ADR-CLEAN-ARCHITECTURE
type: Feature
title: Harnais de Tests de Non-Régression & Certification Vibe-Check
tags:
- grill
- tests
- non-regression
- vibe-check
- qa-certification
status: SHIPPED
validated_by: "Marco (PO - Feu Vert 2026-09-24)"
validated_at: "2026-09-24"
layer: fullstack
invest_score: 6/6
macro_size: S
created_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-283-FULL : Harnais de Tests de Non-Régression & Certification Vibe-Check

---

## Description
**En tant que** Responsable Qualité et Architecte mLoop,  
**je veux** certifier la résorption de la dette technique ADR et de la dette modulaire par un harnais complet de tests unitaires, d'intégration et d'assertions AST,  
**afin de** garantir zéro régression sur l'ensemble des modules appelants du framework et sceller la clôture d'EPIC-28.

---

## Contexte & Périmètre

### Contexte Métier
La refonte structurelle d'un module central comme `GrillEngine` requiert un verrou de certification opposable (ADR-0383). Pour éviter tout effet de bord sur les sessions de cadrage actives ou les commandes de synchronisation, ce récit orchestre la validation de bout en bout des fonctionnalités d'EPIC-28 avant le scellement définitif.

### In-Scope
- Tests unitaires complets dans `tests/test_grill_engine.py` couvrant :
  1. Résolution dynamique du blueprint `project_adr_template.md` et cascade de surcharge.
  2. Fallback d'urgence en mémoire en cas de blueprint manquant.
  3. Remplacement rigoureux de 100% des balises `{{TAG}}`.
  4. Calcul d'identifiant d'ADR par regex anti-collision avec gestion des trous.
  5. Validation de la rétrocompatibilité des imports via le shim `src/pipelines/grill_engine.py`.
- Validation par le linter statique AST `code-check` confirmant qu'aucun fichier ne dépasse 300 lignes.
- Validation intégrale par le harnais souverain `vibe-check` avec 0 FAIL.

### Out-of-Scope
- Tests de montée en charge réseau ou de stress multi-threads.

---

## Critères d'acceptation (Gherkin 4 Piliers)

### 1. Pilier Nominal (Happy Path)
```gherkin
Scénario: Exécution verte de la suite de tests unitaires étendue
  Étant donné la suite de tests unitaires "tests/test_grill_engine.py"
  Quand la commande "uv run pytest tests/test_grill_engine.py" est exécutée
  Alors 100% des tests unitaires sont au statut PASS
  Et aucune régression n'est constatée sur les tests existants
```

### 2. Pilier Exception & Cas Limites
```gherkin
Scénario: Validation des cas extrêmes de génération d'ADRs
  Étant donné un dossier avec des fichiers non standards et des numéros discontinus
  Quand les tests de calcul d'identifiants et de gabarits corrompus s'exécutent
  Alors les assertions vérifient que les erreurs sont interceptées et gérées conformément à l'ADR-012
```

### 3. Pilier Résilience & Intégrité du Codebase
```gherkin
Scénario: Contrôle souverain Vibe-Check sans échec
  Étant donné l'ensemble des modifications apportées sous src/pipelines/grill/
  Quand le contrôle "uv run python src/swarm.py vibe-check --project mLoop" est exécuté
  Alors le rapport final affiche "0 FAIL"
  Et le hook pre-commit autorise l'enregistrement des commits sans bypass MLOOP_SKIP_HOOKS
```

### 4. Pilier UX & Documentation Synchrone
```gherkin
Scénario: Synchronisation de la gouvernance de sprint
  Étant donné la clôture des développements d'EPIC-28
  Quand "uv run python src/swarm.py sync --project mLoop" s'exécute
  Alors les hypergraphes, le wikifix_report et le sprint_backlog.md sont parfaitement alignés
```

---

### Contrats d'Échange API (Harnais de Tests & Commandes CLI)

#### Matrice des Contrats API
- **OQ-283 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — harnais de tests et certification QA locale (`pytest`, `vibe-check`, `code-check`), sans interface HTTP ni route REST distante `[API de soumission à définir]` (ADR-0319).

**Contrats CLI & Assertions Internes :**
- `uv run pytest tests/test_grill_engine.py`
- `uv run python src/swarm.py code-check --project mLoop`
- `uv run python src/swarm.py vibe-check --project mLoop`

---

## Références
- 🏛️ **ADR Associés** : [ADR-0383](../../../../standards/adr-system/0383-deterministic-phase-4-qa-certification-harness.md) · [ADR-0376](../../../../standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) · [ADR-012](../../../docs/01-architecture/ADR-012_epic-28_assainissement_generateur_adr_clean_architecture.md)
- 📂 **Harnais de Test** : `tests/test_grill_engine.py`
- 📦 **Épopée Parente** : [`EPIC-28-ADR-CLEAN-ARCHITECTURE`](../epics/epic_adr_clean_architecture.md)