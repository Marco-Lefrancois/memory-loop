---
id: MLOOP-122-BE
jira_key: ''
epic_key: EPIC-12-PHASE4-HARDENING
type: Feature
title: 'Traçabilité & Preuves Phase 4 : Lien QA → Lifecycle → Handoff'
tags:
- lifecycle
- evidence
- handoff
- phase4
status: SHIPPED
layer: backend
invest_score: 6/6
created_at: '2026-09-21'
ttl_cycles: 4
---

# Traçabilité & Preuves Phase 4 : Lien QA → Lifecycle → Handoff

---

## Description
**En tant qu'**Auditeur de conformité et Lead Architect,
**je veux** que le hash SHA-256 du rapport de certification QA soit persisté dans le GateApprovalRecord et référencé dans le handoff avec un résumé lisible,
**afin de** disposer d'une traçabilité infalsifiable reliant la Gate 4 au rapport de certification, tout en offrant une lecture humaine immédiate.

---

## Contexte & Périmètre

### Contexte Métier
Le rapport de certification QA (`qa_certification_report.json`) est l'artefact central de la Phase 4. Cependant, aucun lien physique ne relie ce rapport au lifecycle state (`GateApprovalRecord`) ni au package de handoff. Le hash du rapport n'est pas calculé, pas persisté, pas référencé — la chaîne de traçabilité est brisée.

### In-Scope
- Ajout du champ `qa_certification_hash: Optional[str] = None` au modèle `GateApprovalRecord`
- Calcul du hash SHA-256 du rapport QA lors de l'approbation Gate 4
- Enrichissement du template de handoff avec la section "Phase 4 Certification" (résumé lisible + lien)
- Tests de traçabilité : lien QA → GateApprovalRecord → Handoff

### Out-of-Scope
- Injection du hash dans chaque EvidencePack (décidé : niveau SPRINT, pas story)
- Refonte du système d'EvidencePacks
- Nouveau système de reporting

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Modèle GateApprovalRecord
- Le champ `qa_certification_hash: Optional[str] = None` est ajouté au modèle `GateApprovalRecord` (lifecycle.py)
- Le champ est `None` tant que la Gate 4 n'est pas approuvée
- Le champ est typé `Optional[str]` (nullable)

#### 2. Calcul et Persistance du Hash
- Lors de `approve_gate(gate_number=4)`, le hash SHA-256 du fichier `qa_certification_report.json` est calculé
- Le hash est stocké dans `GateApprovalRecord.qa_certification_hash`
- Le hash est calculé sur le JSON brut (pas le Markdown)

#### 3. Handoff Phase 4
- Le template de handoff contient la section "Phase 4 Certification"
- La section affiche : statut (CERTIFIÉ/REJETÉ), date, approbateur, hash SHA-256, lien vers le rapport
- En mode dégradé (rapport absent), la section affiche un avertissement

#### 4. Tests de Traçabilité
- Test : hash QA présent dans le lifecycle state après approbation Gate 4
- Test : handoff contient la section Phase 4 Certification
- Test : mode dégradé si rapport QA introuvable

---

## Règles Métier
- **RM-122-01** : Le hash SHA-256 est calculé sur le contenu du fichier `qa_certification_report.json` (JSON brut, pas le Markdown)
- **RM-122-02** : Le champ `qa_certification_hash` est `None` tant que la Gate 4 n'est pas approuvée
- **RM-122-03** : Le handoff Phase 4 contient TOUJOURS un résumé lisible, même si le hash est absent (mode dégradé)
- **RM-122-04** : La spécification du format handoff est formalisée dans l'ADR-0383

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit enrichit le modèle `GateApprovalRecord` et le template de handoff avec le hash SHA-256 du rapport QA. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-122-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `GateApprovalRecord.qa_certification_hash` | `src.core.lifecycle:GateApprovalRecord` | Champ SHA-256 du rapport QA (nullable) |
| `lifecycle.approve_gate(gate=4)` | `src.core.lifecycle:approve_gate` | Calcule hash SHA-256 du `qa_certification_report.json` |
| `handoff.generate_phase4_section()` | `src.pipelines.handoff:generate_phase4_section` | Génère section "Phase 4 Certification" dans le handoff |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-122-01** : Ce récit enrichit des modèles de données internes et un template de handoff Markdown. Aucune API HTTP n'est exposée. Les interfaces sont des appels de fonction Python internes. **[API de soumission à définir]**

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Approbation Gate 4 avec persistance du hash
  Étant donné un projet en STAGE_4_VALIDATE avec rapport QA certifié
  Quand l'humain exécute gate-approve --gate 4 --approver "Marco"
  Alors le GateApprovalRecord contient qa_certification_hash non vide
  Et le hash correspond au SHA-256 du fichier qa_certification_report.json
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Tentative d'approbation sans rapport QA
  Étant donné un projet en STAGE_4_VALIDATE sans rapport QA
  Quand l'humain exécute gate-approve --gate 4
  Alors l'erreur "aucun rapport de certification QA" est levée
  Et le GateApprovalRecord n'est pas créé
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Handoff avec rapport QA indisponible
  Étant donné un handoff Phase 4 généré
  Quand le fichier qa_certification_report.json est introuvable
  Alors le handoff affiche un avertissement
  Et le lien pointe vers le fichier manquant
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Lecture du handoff Phase 4
  Étant donné un handoff contenant la section Phase 4 Certification
  Quand un développeur ouvre le handoff
  Alors il voit immédiatement le statut (CERTIFIÉ/REJETÉ)
  Et la date, l'approbateur et le nombre de niveaux validés
  Et un lien cliquable vers le rapport complet
```
