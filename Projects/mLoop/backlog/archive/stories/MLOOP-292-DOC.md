---
id: MLOOP-292-DOC
jira_key: ""
epic_key: EPIC-29-GRILL-V2-FRONTIER-SKILLS
type: Documentation
title: "Alignement des Blueprints Gates (G6/G7) & Protocole de Cadrage Phase 2"
tags:
  - grill
  - blueprints
  - gates
  - governance
  - quality
status: SHIPPED
validated_by: "Marco (PO - Feu Vert 2026-09-24)"
validated_at: "2026-09-24"
grill_me: DONE
layer: backend
invest_score: 6/6
macro_size: S
created_at: "2026-09-24"
ttl_cycles: 4
---

# 📖 MLOOP-292-DOC : Alignement des Blueprints Gates (G6/G7) & Protocole de Cadrage Phase 2

---

## Description
**En tant que** Responsable de la Gouvernance Qualité mLoop et Auditeur Méthodologique,  
**je veux** actualiser `standards/blueprints/gates_grill_me.template.md` avec les portes G6 (Handoff Ungrillables) et G7 (Context Health) avec sémantique tri-état, et refondre `docs/01-architecture/framework/grill_with_docs_protocol.md`,  
**afin de** garantir que les agents, les validateurs automatiques et les humains contrôlent formellement l'absence d'enlisement IHM, le respect du budget de tokens et la continuité du contexte lors de la transition en Phase 3.

---

## Contexte & Périmètre

### Contexte Métier
L'ADR-013 (issu de l'ADR-0389) entérine l'intégration de deux nouvelles portes de qualité au rituel Grill-Me :
1. **Porte G6 (Handoff Ungrillables)** :
   - `PASS` : toute décision d'interface/ergonomie est matérialisée par un artefact visuel (prototype ou mockup SVG) sans question ouverte résiduelle.
   - `SKIPPED` : si le récit est purement backend (`layer: backend`).
   - `FAIL` : s'il subsiste une zone d'ombre IHM sans support visuel.
2. **Porte G7 (Context Health)** :
   - `PASS` : session < 80k tokens.
   - `WARNING` : entre 80k et 120k tokens (exige la présence d'un fichier de point de contrôle `checkpoint_in_flight.json`).
   - `FAIL` : > 120k tokens ("Dumb Zone") sans stratégie formalisée de clôture immédiate.
3. **Protocole de Phase 2** : révision intégrale pour éliminer le mythe de la purge de contexte post-grill et sceller le flux hybride Macro (Rounds) / Micro (1:1).

### In-Scope
- Mise à jour de `standards/blueprints/gates_grill_me.template.md` : insertion formelle des portes G6 et G7 avec rubriques `COMMAND_CHECK` et `EVIDENCE_FILE`.
- Mise à jour de `docs/01-architecture/framework/grill_with_docs_protocol.md` :
  - Section "Dualité Macro/Micro & Frontier Rounds".
  - Section "Protocole Handoff Ungrillables (Zéro-Build)".
  - Section "Gestion de la Fenêtre de Contexte & Anti-Amnésie".
- Schémas Mermaid illustrant le flux décisionnel v2.

### Out-of-Scope
- Écriture d'un hook Git de blocage côté client (couvert par le Vibe-Check standard).

---

## Critères d'acceptation (Gherkin 4 Piliers)

### 1. Pilier Nominal (Happy Path - Présence & Sémantique des Gates G6/G7)
```gherkin
Scénario: Validation nominale des portes G6 et G7 dans le blueprint
  Étant donné le gabarit "standards/blueprints/gates_grill_me.template.md"
  Quand un auditeur ou le script d'évaluation inspecte les portes définies
  Alors les portes G1 à G7 sont exhaustivement listées
  Et la porte G6 définit les statuts PASS, SKIPPED et FAIL selon la présence d'artefacts IHM
  Et la porte G7 définit les statuts PASS, WARNING et FAIL selon le budget de tokens (<80k, 80k-120k, >120k)
```

### 2. Pilier Exception & Récit Purement Backend (Bypass G6)
```gherkin
Scénario: Évaluation de la porte G6 sur un récit backend
  Étant donné une story qualifiée de "layer: backend"
  Quand le contrôle de la porte G6 est exécuté
  Alors le statut de la porte est "SKIPPED"
  Et le rapport de conformité indique "Exemption G6 accordée : absence de composant IHM"
```

### 3. Pilier Dégradé & Gestion du Checkpoint G7
```gherkin
Scénario: Évaluation de la porte G7 en zone d'alerte avec checkpoint
  Étant donné une session de cadrage se situant entre 80k et 120k tokens
  Et un fichier "checkpoint_in_flight.json" présent dans le répertoire de session
  Quand la porte G7 est auditée
  Alors le statut est "WARNING" non-bloquant
  Et la transition vers la phase 3 est autorisée avec consigne de vigilance
```

### 4. Pilier Parité Documentaire & Zéro Blindspot
```gherkin
Scénario: Cohérence absolue entre protocole de cadrage et skill grill
  Étant donné le protocole "grill_with_docs_protocol.md" et le skill ".agents/skills/grill/SKILL.md"
  Quand on compare les règles de rounds et de no-reset de contexte
  Alors aucune contradiction normative n'est constatée entre les deux documents
```

---

### Contrats d'Échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-292 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — récits documentaire et blueprints Markdown (`gates_grill_me.template.md`, `grill_with_docs_protocol.md`), sans code exécutable réseau `[API de soumission à définir]` (ADR-0319).

**Spécification des Portes G6/G7 :**
- `Gate G6: Handoff Ungrillables (IHM/UX)` : `PASS | SKIPPED | FAIL`
- `Gate G7: Context Health & No-Reset` : `PASS | WARNING | FAIL`

---

## Structure Normative des Portes G6 et G7

```markdown
### Porte G6 : Handoff Ungrillables (IHM / UX)
- **Objectif** : Zéro débat textuel abstrait sur l'ergonomie.
- **Règle** : Si une décision concerne la disposition, la densité ou le comportement d'un écran, un prototype HTML5 ou SVG doit exister sous `scratch/prototypes/` ou `docs/05-assets/mockups/`.
- **Statuts** :
  - `PASS` : Artefact visuel présent et validé.
  - `SKIPPED` : Récit purement backend (`layer: backend`).
  - `FAIL` : Zone d'ombre IHM sans support visuel.

### Porte G7 : Context Health & Continuité Cognitive
- **Objectif** : Prévention de la Dumb Zone (> 120k tokens) et interdiction absolue de purge de mémoire post-grill.
- **Règle** :
  - `PASS` : $< 80\text{k}$ tokens consommés.
  - `WARNING` : $80\text{k} - 120\text{k}$ tokens (exige un `checkpoint_in_flight.json`).
  - `FAIL` : $> 120\text{k}$ tokens sans checkpoint, ou détection d'un reset intempestif de session.
```

---

## Références
- 🏛️ **ADR Associés** : [ADR-013](../../../docs/01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md) · [ADR-0389](../../../../standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md) · [ADR-0376](../../../../standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md)
- 📂 **Blueprint Ciblé** : `standards/blueprints/gates_grill_me.template.md`
- 📦 **Épopée Parente** : [`EPIC-29-GRILL-V2-FRONTIER-SKILLS`](../epics/epic_grill_v2_frontier_rounds_ungrillable_context.md)