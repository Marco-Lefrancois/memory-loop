---
name: plan
description: Analyse d'affaires amont, découpage en tranches verticales INVEST, arbitrage d'architecture Type 1 et synchronisation du backlog. Use when breaking down epics, planning new stories, analyzing business scope, or creating architecture decision records.
---

# 🎯 Skill : Analyse d'Affaires & Planification Verticale (`/plan`)

## Aperçu & Rôle Souverain
Ce skill régit la **Phase 2 : PLAN & ANALYSE** du cycle de vie unifié à 5 phases de Memory Loop ([ADR-0375](../../standards/adr-system/0375-project-lifecycle-5-phases-and-analysis-types.md), [ADR-0376](../../standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md), [ADR-0103](../../standards/adr-system/README.md), [ADR-0305](../../standards/adr-system/README.md), [ADR-0319](../../standards/adr-system/README.md)).

Il orchestre la dualité de la Phase 2 :
1. **Macro-Planification & Avant-Projet (Optionnel)** : Estimation budgétaire macro (`to-tshirt` ➔ `TSHIRT_SIZE_<PROJET>.md`) et cadrage contractuel formel (`to-sow` ➔ `SOW_<PROJET>.md`), cadrés par un Grill-Me Macro transverse (`grill-project`). En Fast-Track, cette étape est court-circuitée si des spécifications pré-existantes sont fournies.
2. **Micro-Analyse Fine 1:1 (Obligatoire pour le Dev)** : Découpage en Story Drafts (`story_draft_template.md`), qualification chirurgicale 1:1 (`grill-me --story <ID>`), et maturation vers le statut exécutable `READY_FOR_DEV` (`story_template.md`).

## Déclencheurs & Exclusions
- **Quand l'utiliser** : Cadrage d'avant-projet (T-Shirt Size, SOW), macro-découpage d'Epic/Projet en Story Drafts, analyse fine de récits unitaires, rédaction de User Stories, ou arbitrage d'architecture Type 1.
- **Quand NE PAS l'utiliser** : Pour découper les sous-tâches physiques d'implémentation de code (< 5 fichiers) ➔ déléguer à [`planning-and-task-breakdown`](../planning-and-task-breakdown/SKILL.md).

---

## 🚀 Protocole d'Ouverture de Session Plan (Obligatoire)

En début de toute session `/plan`, avant tout découpage, l'agent DOIT émettre ce bref état des lieux :

```markdown
## 📋 Cadrage Initial — Session Plan
### 1. Ce que je sais déjà (Faits établis & Preuves pivots)
- 📌 **Périmètre confirmé** : [Périmètre Epic/Projet confirmé depuis docs/ ou backlog/]
  > 🔍 *Preuve pivot :* `[docs/01-architecture/...:Lignes X-Y]`
- 📌 **Contraintes & Standards** : [Contraintes d'architecture identifiées (ADR-XXXX, templates)]
  > 🔍 *Preuve pivot :* `[standards/adr-system/...:Lignes X-Y]`
- 📁 *Dossier de preuves d'analyse :* `memory/evidence/<EPIC_OU_STORY>_fact_dossier.md`

### 2. L'unique arbitrage à trancher avant de découper
> ❓ **<Titre du point bloquant>**
> <Contexte factuel + impact sur le découpage>
> - **Option A** (Recommandée) : <Approche + justification appuyée par les preuves>
> - **Option B** : <Alternative + compromis>
> ➡️ Votre réponse débloque immédiatement le découpage.

### 3. Plan d'action dès validation
- [ ] Découper en N Story Drafts (gabarit story_draft_template.md)
- [ ] Ouvrir grill-me --story <ID> pour le récit le plus prioritaire
- [ ] Synchroniser sprint_backlog.md et EvidencePack
```

**Règles d'or du Cadrage :**
- **Principe Preuve Pivot & Sidecar** : Extraire 1 à 3 faits ou contraintes majeures avec liens cliquables (`[fichier.md:LX-Y]`). Ne pas polluer le chat avec le dossier exhaustif.
- Si aucun arbitrage fonctionnel n'est requis (tous les faits et règles sont documentés), supprimer le bloc 2 et passer directement à l'exécution du bloc 3. Ne jamais inventer une question pour paraître interactif.

---

## Les 6 Règles Inviolables de Planification

### 1. Règle Stricte des Exactement Deux Templates de Récits (Two-Tier Maturation)
L'écosystème mLoop n'admet que DEUX et exactement deux gabarits de récits :
- **Palier 1 : Ébauche d'Analyse (`standards/blueprints/story_draft_template.md`)** :
  - Statut initial : `status: DRAFT`
  - Métadonnées : `grill_me: PENDING`, `invest_score: 0/6` (ou partiel)
  - Issu du macro-découpage (`to-tickets`, `to-spec`) ou d'un T-Shirt/SOW. Contient l'intention métier, les zones de flou (`OQ-XXX`), l'estimation macro (XS/S/M/L/XL), et les dépendances supposées.
- **Palier 2 : Spécification Exécutable (`standards/blueprints/story_template.md`)** :
  - Statut exécutable : `status: READY_FOR_DEV`
  - Métadonnées : `grill_me: DONE`, DoR validé à 6/6 (INVEST, 4 Piliers Gherkin, CTA matrix, Profil B).
  - Issu de l'entretien chirurgical micro [`grill-me --story <ID>`](../grill/SKILL.md). Seul ce gabarit est autorisé en Phase 3 BUILD.
*Tout autre template intermédiaire ou spécialisé (ex. tracer bullet story template) est strictement proscrit et banni.*

### 2. Triptyque de Séparation Documentaire Stricte
Ne jamais fusionner ou corrompre les rôles des livrables :
- `docs/01-architecture/TSHIRT_SIZE_<PROJET>.md` : Macro-chiffrage, fourchettes de coûts/effort, hypothèses budgétaires, exclusions.
- `docs/01-architecture/SOW_<PROJET>.md` : Contrat juridique et commercial, livrables contractuels, jalons, RACI, SLA, clauses d'acceptation.
- `backlog/sprint_backlog.md` : Tableau de bord agile opérationnel vivant. N'y injecter aucune clause contractuelle ni détail budgétaire macro.

### 3. Découpage Vertical INVEST & Scope Capping
- **Tranches Verticales Minces** : Chaque story traverse toutes les couches nécessaires (UI, logique, contrat API) pour délivrer une valeur vérifiable de bout en bout.
- **Scope Capping (Seuil de Brouillard)** : Si le périmètre touche plus d'une Epic ou > 3 domaines, refuser le traitement monolithique. Découper immédiatement en sous-stories et analyser **une seule story à la fois** pour rester dans la zone de concentration cognitive.
- **Validation Formelle** : Valider chaque récit contre la checklist [`.agents/references/invest-story-checklist.md`](../references/invest-story-checklist.md).

### 4. Veto Anti-Annulation & Mandat de Requalification (No-Shortcut Rule)
- L'agent A L'INTERDICTION STRICTE de marquer un récit `CANCELLED` de sa propre initiative suite à une simplification de l'utilisateur (*"pas besoin"*, *"trop complexe"*).
- Tout besoin simplifié doit être **requalifié** (ex: télémétrie d'erreur, fallback dégradé, log d'audit) avec les **4 Piliers Gherkin**. L'annulation exige un ordre écrit explicite.

### 5. Symétrie Contractuelle Frontend / Backend (Profil B)
- Tout composant visuel FE déclenchant une mutation réseau DOIT avoir son contrat déclaré dans le profil B (méthode HTTP, URI canonique, payload, idempotence).
- **Zéro Fausse Route** : Ne jamais inventer d'URL fictive (`/api/dummy`). Si la route est inconnue, consigner une `OQ-XXX` dans `docs/04-transverse/00-questions-ouvertes.md`.

### 6. Filtrage des Décisions d'Architecture (ADR Type 1) & EvidencePack
- Réserver la rédaction d'un ADR formel aux décisions de **Type 1** (porte à sens unique, difficilement réversible), surprenantes sans contexte, et issues d'un arbitrage documenté selon [`.agents/references/adr-decision-checklist.md`](../references/adr-decision-checklist.md).
- Toute création ou modification de story génère de façon synchrone le sidecar `memory/evidence/<STORY_ID>_evidence.json` et journalise l'audit dans `memory/fact_search_log.jsonl`.

---

## Déroulé Opérationnel (Phase 2 PLAN & ANALYSE)

```
MACRO (Optionnel / Avant-Projet) :
   [to-tshirt] ──→ TSHIRT_SIZE_<PROJET>.md
   [to-sow]    ──→ SOW_<PROJET>.md
   [grill-project] ──→ Cadrage global (Loi 25, SSO, frontières)
               │
               ▼ (ou Fast-Track direct si specs/SOW déjà fournis)
MICRO (Obligatoire pour chaque récit) :
   1. [to-tickets] ──→ Découpage en Story Drafts (status: DRAFT, gabarit story_draft_template.md)
   2. [grill-me --story <ID>] ──→ Entretien chirurgical 1:1, résolution des OQ-XXX
   3. [Promotion] ──→ Spécification exécutable (status: READY_FOR_DEV, gabarit story_template.md)
   4. [Vérification] ──→ DoR 6/6, INVEST, EvidencePack synchrone
```

---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"C'est une grosse fonctionnalité, découper en petites stories ajoute de la bureaucratie."* | Les stories monolithiques masquent les régressions et bloquent l'évaluation continue. Slicing INVEST vertical obligatoire. |
| *"Je vais directement rédiger une story READY_FOR_DEV sans passer par le draft ni le grill 1:1."* | Interdit. Tout récit naît en `DRAFT` (Palier 1) et requiert l'entretien contradictoire micro avant promotion en `READY_FOR_DEV`. |
| *"Je fusionne le T-Shirt size et le SOW dans le sprint backlog pour gagner du temps."* | Violation de l'ADR-0375. Séparation stricte du triptyque documentaire (`TSHIRT_SIZE`, `SOW`, `sprint_backlog`). |
| *"Le PO a dit qu'on verra l'erreur plus tard, je ne mets que le nominal dans le Gherkin."* | Violation du Pilier 2 et 3. Un récit sans scénario d'erreur ni résilience est incomplet et rejeté par Sentinel. |
| *"L'endpoint n'est pas prêt, j'invente une route `/api/temp` pour finir la story."* | L'invention d'API contamine le code aval. Consigner obligatoirement une `OQ-XXX` et déclarer `[API à définir]`. |

---

## Signaux d'Alerte (Red Flags)
- Story naissant directement en `READY_FOR_DEV` sans passer par `DRAFT`.
- Utilisation de templates non officiels autres que les 2 autorisés.
- Story dépassant 5 fichiers cibles ou 3 jours de dev sans découpage.
- Absence d'un des 4 Piliers Gherkin dans le corps d'une story `READY_FOR_DEV`.
- Modification du backlog sans synchronisation de `sprint_backlog.md` et de l'EvidencePack.

## Vérification de Sortie
- [ ] Story draft rédigée selon `story_draft_template.md` (Palier 1) OU story exécutable selon `story_template.md` (Palier 2).
- [ ] Checklist `invest-story-checklist.md` validée.
- [ ] Sidecar `memory/evidence/<STORY_ID>_evidence.json` généré et valide.
