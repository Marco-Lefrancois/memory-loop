---
id: MLOOP-124-BE
jira_key: ''
epic_key: EPIC-12-PHASE4-HARDENING
type: Feature
title: 'Observabilité & Clôture Phase 4 : Logs Structurés & Rapport'
tags:
- observability
- logging
- phase4
status: SHIPPED
layer: backend
invest_score: 6/6
created_at: '2026-09-21'
ttl_cycles: 4
---

# Observabilité & Clôture Phase 4 : Logs Structurés & Rapport

---

## Description
**En tant qu'**Opérateur du framework mLoop,
**je veux** disposer de logs structurés traçant chaque niveau de certification Phase 4, et d'un rapport de clôture documentant le bilan du renforcement,
**afin de** pouvoir auditer le déroulement de la certification et disposer d'un artefact de clôture opposable.

---

## Contexte & Périmètre

### Contexte Métier
Le moteur de certification QA (`qa_certifier.py`) exécute 5 niveaux de vérification mais ne produit aucun log structuré traçant le résultat de chaque niveau. Les opérateurs n'ont aucun moyen d'auditer le déroulement de la certification sans ouvrir le rapport JSON complet. De plus, l'EPIC-12 de renforcement Phase 4 n'a pas d'artefact de clôture documentant le bilan.

### In-Scope
- Enrichissement de `qa_certifier.py` avec des logs structurés pour chaque niveau (ADR-0369)
- Création du rapport de clôture `memory/phase4_harden_report.md`
- Synchronisation du guide CLI via `guide --sync`

### Out-of-Scope
- Ajout de la dépendance OpenTelemetry (hors stack mLoop)
- Nouveau widget dashboard (widget existant suffisant — dette technique notée)
- Rapport dynamique de certification (déjà couvert par `qa_certification_report.json`)

### 🔮 Dette Technique Notée
- Enrichir le widget dashboard Phase 4 existant pour afficher le verdict QA spécifique (réservé récit ultérieur)

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Logs Structurés Certification
- Chaque niveau de certification émet un log structuré via `logger.info("qa.certification.level.N", extra={...})`
- Le champ `extra` contient : niveau, statut (passed/failed), durée, détails
- Les logs sont conformes au standard ADR-0369 (pas de `except Exception: pass`)

#### 2. Rapport de Clôture
- Le fichier `memory/phase4_harden_report.md` existe
- Il contient : liste des fichiers créés/modifiés, nombre de tests ajoutés, statut global
- Il est mis à jour (pas créé en double) si déjà existant

#### 3. Parité CLI Guide
- `guide --sync` est exécuté et retourne "parité OK"

---

## Règles Métier
- **RM-124-01** : Les logs structurés utilisent le pattern `logger.info("qa.certification.level.N", extra={...})` conformément à ADR-0369
- **RM-124-02** : Le rapport de clôture est un fichier Markdown statique mis à jour en fin d'EPIC-12
- **RM-124-03** : Le guide CLI doit être synchronisé via `guide --sync` après toute modification de `_registry.py`

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit enrichit `qa_certifier.py` avec des logs structurés et produit un rapport de clôture Markdown. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-124-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `qa_certifier.run_certification()` | `src.pipelines.qa_certifier:run_certification` | Exécute 5 niveaux + logs structurés `qa.certification.level.N` |
| `qa_certifier._log_level_result()` | `src.pipelines.qa_certifier:_log_level_result` | Émet log structuré `qa.certification.level.N` |
| `qa_certifier._write_harden_report()` | `src.pipelines.qa_certifier:_write_harden_report` | Écrit/met à jour `memory/phase4_harden_report.md` |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-124-01** : Ce récit enrichit un pipeline interne avec des logs structurés et produit un rapport Markdown statique. Aucune API HTTP n'est exposée. Les interfaces sont des appels de fonction Python internes. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Certification QA avec logs structurés
  Étant donné un projet en STAGE_4_VALIDATE
  Quand validate-sprint est exécuté
  Alors chaque niveau émet un log structuré (level.1 à level.5)
  Et le rapport de clôture est mis à jour avec le bilan
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Certification QA avec échec au niveau 2 (AST)
  Étant donné un projet avec violations AST
  Quand validate-sprint est exécuté
  Alors le log level.2 contient "passed: false" et le nombre de violations
  Et le rapport de clôture documente l'échec avec le motif
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Rapport de clôture déjà existant
  Étant donné un rapport de clôture existant
  Quand validate-sprint est relancé
  Alors le rapport est mis à jour (pas créé en double)
  Et la date de dernière mise à jour est actualisée
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Lecture du rapport de clôture
  Étant donné un opérateur qui clôture l'EPIC-12
  Quand il ouvre memory/phase4_harden_report.md
  Alors il voit la liste des fichiers créés et modifiés
  Et le nombre de tests ajoutés
  Et le statut global du renforcement
```
