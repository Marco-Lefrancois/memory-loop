---
name: plan
description: Analyse d'affaires amont, découpage en tranches verticales INVEST, arbitrage d'architecture Type 1 et synchronisation du backlog. Use when breaking down epics, planning new stories, analyzing business scope, or creating architecture decision records.
---

# 🎯 Skill : Analyse d'Affaires & Planification Verticale (`/plan`)

## Aperçu & Rôle Souverain
Ce skill régit la **Phase d'Analyse Amont (Phase 2)** de Memory Loop ([ADR-0103](../../standards/adr-system/README.md), [ADR-0305](../../standards/adr-system/README.md), [ADR-0319](../../standards/adr-system/README.md)). Il transforme une intention métier brute en un backlog de **Stories verticales INVEST** et formalise les décisions irréversibles (ADRs) avant tout travail physique de code.

## Déclencheurs & Exclusions
- **Quand l'utiliser** : Cadrage d'une Epic, découpage d'un nouveau besoin, rédaction de User Stories, ou arbitrage d'architecture Type 1.
- **Quand NE PAS l'utiliser** : Pour découper les sous-tâches physiques d'implémentation de code (< 5 fichiers) ➔ déléguer à [`planning-and-task-breakdown`](../planning-and-task-breakdown/SKILL.md).

---

## Les 5 Règles Inviolables de Planification

### 1. Découpage Vertical INVEST & Scope Capping
- **Tranches Verticales Minces** : Chaque story traverse toutes les couches nécessaires (UI, logique, contrat API) pour délivrer une valeur vérifiable de bout en bout.
- **Scope Capping (Seuil de Brouillard)** : Si le périmètre touche plus d'une Epic ou > 3 domaines, refuser le traitement monolithique. Découper immédiatement en sous-stories et analyser **une seule story à la fois** pour rester dans la zone de concentration cognitive.
- **Validation Formelle** : Valider chaque récit contre la checklist [`.agents/references/invest-story-checklist.md`](../references/invest-story-checklist.md).

### 2. Veto Anti-Annulation & Mandat de Requalification (No-Shortcut Rule)
- L'agent A L'INTERDICTION STRICTE de marquer un récit `CANCELLED` de sa propre initiative suite à une simplification de l'utilisateur (*"pas besoin"*, *"trop complexe"*).
- Tout besoin simplifié doit être **requalifié** (ex: télémétrie d'erreur, fallback dégradé, log d'audit) avec les **4 Piliers Gherkin**. L'annulation exige un ordre écrit explicite.

### 3. Symétrie Contractuelle Frontend / Backend (Profil B)
- Tout composant visuel FE déclenchant une mutation réseau DOIT avoir son contrat déclaré dans le profil B (méthode HTTP, URI canonique, payload, idempotence).
- **Zéro Fausse Route** : Ne jamais inventer d'URL fictive (`/api/dummy`). Si la route est inconnue, consigner une `OQ-XXX` dans `docs/04-transverse/00-questions-ouvertes.md`.

### 4. Filtrage des Décisions d'Architecture (ADR Type 1)
- Réserver la rédaction d'un ADR formel aux décisions de **Type 1** (porte à sens unique, difficilement réversible), surprenantes sans contexte, et issues d'un arbitrage documenté selon [`.agents/references/adr-decision-checklist.md`](../references/adr-decision-checklist.md).
- Indexer systématiquement tout nouvel ADR dans [`standards/adr-system/README.md`](../../standards/adr-system/README.md).

### 5. Génération Synchrone d'EvidencePack (Sidecar)
- Toute création ou modification de story génère de façon synchrone et sans demander la permission le sidecar `memory/evidence/<STORY_ID>_evidence.json` et journalise l'audit dans `memory/fact_search_log.jsonl`.

---

## Déroulé Opérationnel

```
1. Cadrage du Périmètre  ──→  2. Grilling Préalable  ──→  3. Rédaction du Récit  ──→  4. Audit Qualité & Preuves
   (Wayfinder / Scope)           (Fact-Search & Grill)        (Gabarit Gold Standard)       (Sentinel & EvidencePack)
```

1. **Évaluer la Criticité** :
   - *Niveau 1 (Trivial)* : 0 impact architectural.
   - *Niveau 2 (Moyen)* : 1 à 2 fichiers touchés.
   - *Niveau 3 (Critique)* : Plan formel bloquant obligatoire approuvé par l'humain avant action.
2. **Exécuter le Grilling** : Utiliser [`grill`](../grill/SKILL.md) pour vider la frontière et consigner le dossier de preuves.
3. **Rédiger la Story** : Appliquer les 4 Piliers Gherkin, la matrice CTA et les contrats API dans `backlog/stories/<ID>.md`.
4. **Handoff vers l'Aval** : Si découpage physique nécessaire, formater les tâches via [`planning-and-task-breakdown`](../planning-and-task-breakdown/SKILL.md) (compatible structure OpenSpec `proposal.md`, `specs/`, `tasks.md`).

---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"C'est une grosse fonctionnalité, découper en petites stories ajoute de la bureaucratie."* | Les stories monolithiques masquent les régressions et bloquent l'évaluation continue. Slicing INVEST vertical obligatoire. |
| *"Je vais rédiger le plan au fur et à mesure pendant que je code."* | C'est de la narration a posteriori, pas de la planification. Le plan doit être validé par l'humain AVANT toute écriture de code. |
| *"Le PO a dit qu'on verra l'erreur plus tard, je ne mets que le nominal dans le Gherkin."* | Violation du Pilier 2 et 3. Un récit sans scénario d'erreur ni résilience est incomplet et rejeté par Sentinel. |
| *"L'endpoint n'est pas prêt, j'invente une route `/api/temp` pour finir la story."* | L'invention d'API contamine le code aval. Consigner obligatoirement une `OQ-XXX` et déclarer `[API à définir]`. |

---

## Signaux d'Alerte (Red Flags)
- Story dépassant 5 fichiers cibles ou 3 jours de dev sans découpage.
- Absence d'un des 4 Piliers Gherkin dans le corps de la story.
- Modification du backlog sans synchronisation synchrone de `sprint_backlog.md` et de l'EvidencePack.

## Vérification de Sortie
- [ ] Story rédigée selon le gabarit canonique avec les 4 Piliers Gherkin.
- [ ] Checklist `invest-story-checklist.md` validée à 100%.
- [ ] Sidecar `memory/evidence/<STORY_ID>_evidence.json` généré et valide.
