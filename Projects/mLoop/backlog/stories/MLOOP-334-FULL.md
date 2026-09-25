---
id: MLOOP-334-FULL
jira_key: ""
epic_key: EPIC-33-REQUIREMENT-TO-CODE-TRACEABILITY-AND-CODE-EVIDENCE
type: Feature
title: "Harnais de Validation Intégrale, Tests de Non-Régression & Parité Documentaire"
origin: DIRECT_REQUIREMENT
source_ref: "ADR-0394 / EPIC-33"
macro_size: M
status: DRAFT
grill_me: PENDING
invest_score: 0/6
layer: fullstack
blocked_by: [MLOOP-330-BE, MLOOP-331-BE, MLOOP-332-BE, MLOOP-333-BE]
created_at: "2026-09-25T09:10:00Z"
validated_by: Marco
validated_at: "2026-09-25T17:18:38.646725+00:00"

---

# 📖 MLOOP-334-FULL : Harnais de Validation Intégrale, Tests de Non-Régression & Parité Documentaire

## 1. Intention Métier (User Story)
**En tant qu'** Équipe Core mLoop & Responsable de l'Écosystème,  
**je veux** un harnais de tests automatisés complet (tests unitaires, cas limites et d'injection de code fantôme) et la synchronisation stricte de la documentation constitutionnelle (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `CLI_PIPELINE_GUIDE.md`),  
**afin de** sceller l'épopée EPIC-33 sans aucun angle mort, avec une parité SSOT absolue.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `standards/adr-system/0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md` (Réf : `ADR-0394`)
- **Hypothèse de Chiffrage Retenue** : Respect strict du protocole ADR-0376 (Audit 360° en 7 couches) et ADR-0370 (Zero-CLI-Drift).
- **Enveloppe Macro Estimée** : M (fourchette de 2 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Création de la suite de tests automatisés `tests/test_code_evidence_tracer.py` et `tests/test_vibe_check_traceability.py`.
- Synchronisation déterministe du guide CLI via `python src/swarm.py guide --sync` (parité SSOT 134+ commandes).
- Harmonisation miroir des règles dans `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` et `.clinerules`.

### Out-of-Scope (Macro)
- Nouveaux modules d'IA générative non déterministes.

---

## 4. Critères de Succès Préliminaires
- [ ] 100% des tests de la suite de traçabilité passent avec succès sous `pytest`.
- [ ] Le Vibe-Check rapporte 29 contrôles exécutés avec parité miroir et absence de dérive documentaire CLI (`Zero-CLI-Drift`).

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ Comment simuler un test adversarial de "Code Fantôme" (injection de fonction orpheline) dans la suite de tests unitaires sans polluer le repo ?
- ❓ Quels exemples de symboles canoniques inclure dans `CLI_PIPELINE_GUIDE.md` ?
