---
id: {{STORY_ID}}
jira_key: ""
epic_key: {{EPIC_KEY}}
type: {{TYPE}}
title: "{{TITLE}}"
origin: "{{ORIGIN}}"           # TSHIRT_SIZE | SOW | SPEC_SLICING | DIRECT_REQUIREMENT
source_ref: "{{SOURCE_REF}}"   # Réf. ligne T-Shirt (ex: TS-02) ou clause SOW (ex: SOW-§3.1)
macro_size: "{{MACRO_SIZE}}"   # XS | S | M | L | XL
status: DRAFT                  # Ébauche de cadrage initial
grill_me: PENDING              # PENDING -> DONE après séance 1:1
invest_score: 0/6              # Évalué après Grill-Me et validation DoR
layer: {{LAYER}}               # frontend | backend | fullstack
blocked_by: {{BLOCKERS}}
created_at: "{{CREATED_AT}}"
---

# 📖 {{STORY_ID}} : {{TITLE}}

## 1. Intention Métier (User Story)
**En tant que** {{PERSONA}},  
**je veux** {{WANT}},  
**afin de** {{SO_THAT}}.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `{{SOURCE_DOC}}` (Réf : `{{SOURCE_REF}}`)
- **Hypothèse de Chiffrage Retenue** : {{ESTIMATE_ASSUMPTION}}
- **Enveloppe Macro Estimée** : {{MACRO_SIZE}} (fourchette de {{DAYS_RANGE}} jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- {{MACRO_IN_SCOPE}}

### Out-of-Scope (Macro)
- {{MACRO_OUT_OF_SCOPE}}

---

## 4. Critères de Succès Préliminaires
- [ ] {{SUCCESS_CRITERIA_1}}
- [ ] {{SUCCESS_CRITERIA_2}}

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*  
> *Leur résolution avec le PO / Expert métier permet de transformer cette ébauche en récit haute fidélité (`story_template.md`) prêt pour le développement (`READY_FOR_DEV`).*

- ❓ {{OPEN_QUESTION_1}}
- ❓ {{OPEN_QUESTION_2}}
