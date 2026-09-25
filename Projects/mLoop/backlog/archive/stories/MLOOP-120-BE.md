---
id: MLOOP-120-BE
jira_key: ''
epic_key: EPIC-12-PHASE4-HARDENING
type: Feature
title: 'Fondations Normatives & Spécification Phase 4 : ADR-0383, Checklist & Parité'
tags:
- standards
- adr
- phase4
status: SHIPPED
layer: backend
invest_score: 6/6
created_at: '2026-09-21'
ttl_cycles: 4
---

# Fondations Normatives & Spécification Phase 4 : ADR-0383, Checklist & Parité

---

## Description
**En tant qu'**Architecte du framework mLoop,
**je veux** disposer d'une ADR-0383 prescriptive formalisant le harnais déterministe de Phase 4 (5 niveaux + Niveau 6 Sentinel LLM) et d'une checklist Phase 4 spécifique,
**afin de** garantir que la certification QA est un processus normatif, traçable, reproductible et enrichi d'un jugement LLM contradictoire.

---

## Contexte & Périmètre

### Contexte Métier
Le framework mLoop dispose d'un harnais de certification Phase 4 à 5 niveaux (Pytest, AST, CEL, NLI, Leakage) et de 5 verrous bloquants Gate 4. Cependant, l'ADR-0383 référencée par les récits MLOOP-090-BE à MLOOP-092-BE n'existe pas physiquement — c'est un fantôme normatif. De plus, le skill Sentinel (audit contradictoire Red Team) n'est pas connecté au pipeline Phase 4, créant un angle mort de jugement LLM.

### In-Scope
- Rédaction de l'ADR-0383 prescriptive formalisant les 5 niveaux existants + le Niveau 6 Sentinel LLM
- Création de `phase4-qa-review-checklist.md` (checklist Phase 4 spécifique)
- Correction des tests fantômes dans `PHASE_FILES_AND_TEST_PLAN.md`
- Vérification parité CLI guide pour les commandes Phase 4

### Out-of-Scope
- Implémentation du pont SentinelQaBridge (couvert par MLOOP-122-BE)
- Création de tests unitaires
- Modification du pipeline de certification existant

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. ADR-0383 Prescriptive
- L'ADR-0383 est rédigée sous `standards/adr-system/0383-deterministic-phase-4-qa-certification-harness.md`
- Elle spécifie les 5 niveaux de certification (Pytest, AST, CEL, NLI, Leakage)
- Elle spécifie les 5 verrous bloquants Gate 4
- Elle spécifie le Niveau 6 — Jugement LLM Sentinel (interfaces et contrat)
- Elle spécifie le format du handoff Phase 4 (résumé lisible + lien)
- Elle spécifie le modèle `GateApprovalRecord` avec champ `qa_certification_hash`
- Elle est indexée dans `standards/adr-system/README.md`

#### 2. Checklist Phase 4
- Le fichier `phase4-qa-review-checklist.md` existe dans `.agents/references/`
- Il contient 5 axes d'audit ciblés Phase 4
- Il liste les fichiers critiques du pipeline
- Il identifie les red flags spécifiques à la certification

#### 3. Correction Tests Fantômes
- `PHASE_FILES_AND_TEST_PLAN.md` est corrigé (zéro test fantôme)
- Tous les noms de tests listés correspondent à de vrais fichiers

#### 4. Parité CLI Guide
- `CLI_PIPELINE_GUIDE.md` reflète fidèlement `_registry.py` pour les commandes Phase 4
- La commande `guide --sync` est exécutée et retourne "parité OK"

---

## Règles Métier
- **RM-120-01** : Toute ADR de la famille 03xx doit être indexée dans `standards/adr-system/README.md` sous le bon thème
- **RM-120-02** : La checklist Phase 4 doit référencer uniquement des fichiers physiquement existants dans `src/`
- **RM-120-03** : La parité CLI guide est vérifiable par `python src/swarm.py guide --check`

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit produit des artefacts normatifs (ADR, checklist, guide CLI) sans implémenter d'API HTTP. Les contrats ci-dessous décrivent les interfaces internes du pipeline Phase 4.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `qa_certifier.run_certification` | `src.pipelines.qa_certifier:run_certification` | Exécute les 6 niveaux de certification (Pytest L1, AST L2, CEL L3, NLI L4, Leakage L5, Sentinel L6) |
| `vibe_check.run_vibe_check` | `src.pipelines.vibe_check:run_vibe_check` | Exécute 20 contrôles pré-vol |
| `SentinelQaBridge.audit` | `src.bridges.sentinel_qa_bridge:SentinelQaBridge.audit` | Invoque le skill Sentinel (Red Team) pour audit contradictoire Gherkin 4 piliers |
| `GateApprovalRecord` | `src.core.lifecycle:GateApprovalRecord` | Enregistre l'approbation d'une gate avec hash de certification SHA-256 |

**Artefacts produits** :
- `standards/adr-system/0383-deterministic-phase-4-qa-certification-harness.md` (ADR prescriptive)
- `.agents/references/phase4-qa-review-checklist.md` (Checklist Phase 4)
- `standards/protocols/CLI_PIPELINE_GUIDE.md` (Parité CLI via `guide --sync`)

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-120-01** : Ce récit produit des artefacts normatifs (ADR, checklist, guide CLI) sans implémenter d'API HTTP. Les interfaces sont des appels de fonction Python internes, pas des routes HTTP. La matrice ci-dessus documente les interfaces internes pour la traçabilité. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Rédaction et indexation de l'ADR-0383
  Étant donné un framework mLoop sans ADR formalisant Phase 4
  Quand l'architecte rédige l'ADR-0383 prescriptive avec les 6 niveaux
  Alors l'ADR est indexée dans README.md
  Et l'ADR contient la spécification du Niveau 6 Sentinel LLM
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Rejet d'une ADR-0383 descriptive uniquement
  Étant donné une ADR-0383 qui ne décrit que le statu quo
  Quand l'audit de conformité vérifie la présence du Niveau 6
  Alors l'audit échoue avec le motif "Niveau 6 Sentinel non spécifié"
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Checklist Phase 4 introuvable
  Étant donné le skill Sentinel invoqué en Phase 4
  Quand le fichier phase4-qa-review-checklist.md est absent
  Alors Sentinel émet un avertissement WARNING
  Et Sentinel continue avec la checklist intégrée au SKILL.md
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Vérification parité CLI guide
  Étant donné une modification de _registry.py avec une commande Phase 4
  Quand guide --sync est exécuté
  Alors le CLI_PIPELINE_GUIDE.md reflète fidèlement le registre
  Et le rapport de synchronisation indique "parité OK"
```
