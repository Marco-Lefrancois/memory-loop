---
id: MLOOP-123-BE
jira_key: ''
epic_key: EPIC-12-PHASE4-HARDENING
type: Feature
title: 'Garde-Fous Automatiques Phase 4 : Vibe-Check & Zombie Reap'
tags:
- safety
- vibe-check
- herdr
- phase4
status: SHIPPED
layer: backend
invest_score: 6/6
created_at: '2026-09-21'
ttl_cycles: 4
---

# Garde-Fous Automatiques Phase 4 : Vibe-Check & Zombie Reap

---

## Description
**En tant que** Gardien de la qualité et du cycle de vie,
**je veux** que le vibe-check avertisse en cas d'absence de rapport QA en Phase 4, et que le nettoyage des workers Herdr orphelins soit systématique à chaque changement de gate,
**afin de** disposer de garde-fous passifs qui alertent sans bloquer le travail, tout en éliminant les workers zombies à chaque étape du cycle.

---

## Contexte & Périmètre

### Contexte Métier
Le vibe-check est le garde-fou pré-vol de session mLoop (17 contrôles déterministes). Cependant, il ne vérifie rien de spécifique à la Phase 4 (VALIDATE) — il est possible de démarrer une session en Phase 4 sans rapport QA sans aucun avertissement. De plus, les workers Herdr orphelins (zombies) ne sont purgés qu'au moment du harvest, créant des fuites de ressources entre les phases.

### In-Scope
- Ajout d'un WARNING dans `vibe_check.py` : si `stage == STAGE_4_VALIDATE` et `qa_certification_report.json` absent
- Ajout d'un appel `audit_and_reap_zombies()` dans `approve_gate()` pour toutes les gates (1-5)
- Tests des nouveaux garde-fous

### Out-of-Scope
- Pre-commit hook Phase 4 (protection déjà dans lifecycle.py)
- Refonte du vibe-check existant
- Nouveau système de hooks

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Vibe-Check Phase 4
- Un WARNING est émis si `stage == STAGE_4_VALIDATE` et `qa_certification_report.json` absent
- Le message contient "Lancez 'validate-sprint' pour certifier le sprint"
- La session continue normalement (pas de blocage)

#### 2. Zombie Reap Systématique
- `approve_gate()` invoque `audit_and_reap_zombies()` pour TOUTES les gates (1-5)
- Le nettoyage est exécuté AVANT la création du `GateApprovalRecord`
- Les workers purgés sont journalisés en debug

#### 3. Tests
- Test : vibe-check émet WARNING en Phase 4 sans rapport QA
- Test : vibe-check passe en Phase 4 avec rapport QA
- Test : zombie reap exécuté lors de gate-approve --gate 2

---

## Règles Métier
- **RM-123-01** : Le WARNING Phase 4 est émis UNIQUEMENT si `stage == STAGE_4_VALIDATE` et `qa_certification_report.json` n'existe pas
- **RM-123-02** : Le nettoyage workers est systématique à chaque `approve_gate()` — pas conditionné au numéro de gate
- **RM-123-03** : Le WARNING n'empêche JAMAIS la continuation de la session (mode passif)

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit ajoute des garde-fous automatiques au vibe-check et au lifecycle. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-123-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `vibe_check.run_vibe_check(stage=STAGE_4_VALIDATE)` | `src.pipelines.vibe_check:run_vibe_check` | Émet WARNING si rapport QA absent en Phase 4 |
| `lifecycle.approve_gate()` | `src.core.lifecycle:approve_gate` | Invoque `audit_and_reap_zombies()` pour toutes les gates |
| `herdr_adapter.audit_and_reap_zombies()` | `src.core.herdr_adapter:audit_and_reap_zombies` | Purge workers Herdr orphelins |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-123-01** : Ce récit ajoute des garde-fous internes (vibe-check WARNING + zombie reap systématique). Aucune API HTTP n'est exposée. Les interfaces sont des appels de fonction Python internes. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Vibe-check Phase 4 avec rapport QA absent
  Étant donné un projet en STAGE_4_VALIDATE sans rapport QA
  Quand le vibe-check est exécuté au boot de session
  Alors un WARNING est émis
  Et le message contient "Lancez 'validate-sprint' pour certifier le sprint"
  Et la session continue normalement
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Vibe-check Phase 4 avec rapport QA présent
  Étant donné un projet en STAGE_4_VALIDATE avec rapport QA valide
  Quand le vibe-check est exécuté
  Alors aucun WARNING n'est émis pour la Phase 4
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Nettoyage workers lors de l'approbation Gate 2
  Étant donné un projet avec 1 worker Herdr zombie
  Quand l'humain exécute gate-approve --gate 2
  Alors le worker zombie est purgé automatiquement
  Et le GateApprovalRecord est créé normalement
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Développeur démarre une session en Phase 4
  Étant donné un développeur en Phase 4 sans rapport QA
  Quand il démarre une session mLoop
  Alors il voit un WARNING clair dans le vibe-check
  Et il sait exactement quoi faire : lancer validate-sprint
```
