---
id: MLOOP-182-BE
jira_key: ''
epic_key: EPIC-18-EVIDENCE-PARITY-PHASE3
type: Feature
title: Backfill Rétroactif des EvidencePacks Existants vers la Parité Phase 2
origin: DIRECT_REQUIREMENT
source_ref: epic_evidence_impl_decisions.md
macro_size: M
status: DONE
grill_me: DONE
invest_score: 0/6
layer: backend
blocked_by:
- MLOOP-180-BE
created_at: '2026-09-22'
content_hash: 1a867a1209b775a6
---

# 📖 MLOOP-182-BE : Backfill Rétroactif des EvidencePacks Existants vers la Parité Phase 2

## 1. Intention Métier (User Story)
**En tant qu'** Auditeur mLoop,  
**je veux** un backfill qui enrichit les 39 EvidencePacks existants (EPIC-10 à 17) avec les décisions, citations et contrats extraits des fact_dossiers et plans d'implémentation,  
**afin de** rattraper l'écart de richesse sur tout le backlog non-legacy.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `epic_evidence_impl_decisions.md` (Réf : Audit 39 packs EPIC-10 à 17)
- **Hypothèse de Chiffrage Retenue** : Extraction documentaire multi-sources + injection JSON + mise à jour hash
- **Enveloppe Macro Estimée** : M (fourchette de 1-2 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Script/CLI de backfill ciblant les EPIC-10 à 17 (39 stories)
- Extraction des décisions depuis `fact_dossier.md`, `implementation_plan_*.md`, sections `Règles d'affaires`
- Extraction des citations verbatim depuis les mêmes sources (ancrages ligne si disponibles)
- Extraction des contrats déclaratifs référencés dans les plans
- Remplissage `epistemic_audit.what_it_does_not_prove` depuis les Admission of Limits existantes
- Injection dans les champs du pack + mise à jour hash SHA-256 et timestamp

### Out-of-Scope (Macro)
- EPIC 1-9 (legacy — strictement exclus)
- Extraction depuis l'historique git du code source (trop complexe pour un backfill)
- Modification des récits .md source

---

## 4. Contexte métier

39 EvidencePacks (EPIC-10→17) ont été générés avant l'extension de parité — ils sont structurellement complets mais épistémiquement vides (0 citation, 0 décision). Le PO a tranché : **EPIC 10→18 = nouvelle structure, code parfait exigé** ; **EPIC 1-9 = legacy, strictement exclus**. Ce récit rattrape l'écart uniquement sur le périmètre prioritaire.


---

## Critères d'acceptation

- [ ] **CA-1** : Les 39 packs EPIC-10→17 ont `implementation_decisions`, `verbatim_extracts` (via fact_dossier) et `epistemic_audit` peuplés — ou vide documenté si source absente.
- [ ] **CA-2** : **Zéro invention** — extraction uniquement depuis `fact_dossier.md`, `implementation_plan_*.md`, sections `Règles d'affaires` des récits.
- [ ] **CA-3** : **Idempotent** — re-exécution = hash SHA-256 inchangé si champs déjà non vides.
- [ ] **CA-4** : **Legacy intouché** — aucun fichier `EPIC 1-9` (`MLOOP-0xx`, `MLOOP-1xx` < 100) modifié (Décision 6 : strictement exclus).
- [ ] **CA-5** : Granularité citations **hybride D** reconstruite : 1/fichier + 1/décision extraite.
- [ ] **CA-6** : `richness_penalty` calculé selon la Décision 5 (multiplicateur) après injection.

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : script de backfill local, aucune route HTTP. Toute route découverte dans les plans → `OQ-001` + `[API de soumission à définir]`.

---

## 5. Piliers Gherkin

### Pilier 1 : Nominal
```gherkin
Scénario: Backfill d'un pack EPIC-10→17
  Étant donné le pack MLOOP-160-BE sans implementation_decisions
  Quand le backfill est exécuté avec le fact_dossier associé
  Alors implementation_decisions est peuplé avec les décisions du dossier
  Et verbatim_extracts référence le fact_dossier (Décision 3)
  Et le hash SHA-256 et le timestamp sont mis à jour
```

### Pilier 2 : Exceptions
```gherkin
Scénario: Pack legacy EPIC 1-9 résiste au backfill
  Étant donné le pack MLOOP-010-BE (legacy, EPIC 1)
  Quand le backfill est exécuté sur l'intégralité du dossier evidence/
  Alors le fichier MLOOP-010-BE_evidence.json n'est pas ouvert en écriture
  Et un log INFO "legacy_skipped" liste les fichiers exclus

Scénario: Source absente pour un pack
  Étant donné un pack sans fact_dossier ni plan d'implémentation
  Quand le backfill tente l'extraction
  Alors les champs restent null
  Et une note "NO_SOURCE_AVAILABLE" est ajoutée à epistemic_audit
  Et le hash n'est pas modifié (idempotence)
```

### Pilier 3 : Résilience & Mode Dégradé
```gherkin
Scénario: Interruption mid-backfill
  Étant donné un backfill sur 39 packs interrompu au pack 20
  Quand le script est relancé
  Alors les 19 packs déjà traités sont détectés (idempotence) et ignorés
  Et les 19 restants sont traités
  Et aucun pack n'est laissé dans un état partiellement écrit

Scénario: Fact-dossier corrompu
  Étant donné un fact_dossier avec YAML invalide
  Quand le parsing échoue
  Alors le pack cible reste intact
  Et l'erreur est loggée avec exc_info (ADR-0369 Zero-Silent-Pass)
  Et le backfill continue sur les autres packs
```

### Pilier 4 : UX (Observabilité)
```gherkin
Scénario: Rapport de backfill traçable
  Étant donné un backfill terminé (39/39)
  Quand le rapport est généré
  Alors il liste : packs traités, packs legacy exclus, packs sans source
  Et affiche le delta de richesse moyen (citations avant/après)
  Et le timestamp UTC de la run est mentionné
---

## 6. Décisions du Grill 1:1 Intégrées

- **Déc. 1 (Granularité)** : reconstruction hybride 1/fichier + 1/décision.
- **Déc. 2 (Sources)** : fact_dossier + plan + règles d'affaires (pas de git history).
- **Déc. 3 (Emplacement)** : décisions → JSON, citations → fact_dossier existant.
- **Déc. 4 (Gate 5)** : backfill non requis pour legacy — warning only.
- **Déc. 5 (Confiance)** : `richness_penalty` recalculé après injection.
- **Déc. 6 (Legacy)** : **EPIC 1-9 strictement exclus** (PO : focus 10→18, code parfait exigé).

---

## 7. Zones d'Ombre Restantes (post-Grill)

- ❓ Script one-shot ou CLI réutilisable `swarm.py evidence-backfill` ?
- ❓ Seuil de confiance minimal pour injecter une décision extraite ?
- ❓ Re-validation des citations contre la source originale avant injection ?
