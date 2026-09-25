---
id: MLOOP-333-BE
jira_key: ""
epic_key: EPIC-33-REQUIREMENT-TO-CODE-TRACEABILITY-AND-CODE-EVIDENCE
type: Feature
title: "Sonde Vibe-Check Check 29 (Intégrité Traçabilité Code ↔ Exigences) & Commande CLI"
origin: DIRECT_REQUIREMENT
source_ref: "ADR-0394 / EPIC-33"
macro_size: S
status: DRAFT
grill_me: PENDING
invest_score: 0/6
layer: backend
blocked_by: [MLOOP-331-BE, MLOOP-332-BE]
created_at: "2026-09-25T09:10:00Z"
validated_by: Marco
validated_at: "2026-09-25T17:18:38.646725+00:00"

---

# 📖 MLOOP-333-BE : Sonde Vibe-Check Check 29 (Intégrité Traçabilité Code ↔ Exigences) & Commande CLI

## 1. Intention Métier (User Story)
**En tant qu'** Ingénieur QA ou Guardrail de Sécurité Vibe-Check,  
**je veux** un contrôle déterministe (Check 29) dans le guardrail pré-vol et une commande CLI dédiée `python src/swarm.py code-trace`,  
**afin d'** interdire tout commit ou promotion en Phase 4/5 si du code physique substantiel a été introduit sans justification dans la matrice de traçabilité.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `standards/adr-system/0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md` (Réf : `ADR-0394`)
- **Hypothèse de Chiffrage Retenue** : Intégration modulaire dans le pipeline Vibe-Check existant (`src/pipelines/vibe_check/`).
- **Enveloppe Macro Estimée** : S (fourchette de 1 à 2 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Ajout du contrôle Check 29 dans le catalogue des 28 contrôles existants de `vibe-check`.
- Nouvelle commande CLI `python src/swarm.py code-trace --story <ID> [--strict]`.
- Émission de diagnostics clairs : `PASS` si 100% des symboles sont justifiés, `WARNING` en DEV local, `BLOCKING` en pré-livraison Phase 5.

### Out-of-Scope (Macro)
- Blocage des commandes en mode FAST ou exploratory.

---

## 4. Critères de Succès Préliminaires
- [ ] `vibe-check` exécute le Check 29 et remonte les symboles de code orphelins.
- [ ] La commande `mloop code-trace` affiche la matrice lisible dans le terminal via `ZeroFluffConsole`.

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ Le Check 29 doit-il être bloquant dès la Phase 3 (BUILD) ou uniquement à partir de la Phase 4 (VALIDATE) ?
- ❓ Comment exempter explicitement certains fichiers de configuration ou migrations de schéma ?
