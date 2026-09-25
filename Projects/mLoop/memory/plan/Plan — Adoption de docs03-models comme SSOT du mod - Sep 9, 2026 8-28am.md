---
created: 2026-09-09T12:28:35.466Z
source: plannotator
tags: [plannotator, memory-loop, adoption, docs, 03-models]
---

[[Plannotator Plans]]

# Plan — Adoption de `docs/03-models/` comme SSOT du modèle + Audit de cohérence BE

## Contexte validé (faits vérifiés)
- `docs/03-models/Structure-de-données.md` (maître, maj 2026-09-09 08:05) est fractionné par pipeline vers 5 modèles modules ; le dérivé `02-incubation/modele-incubation.md` (maj 08:20) est synchrone.
- Le modèle courant contient `boire_inc_batch` (`status IncubationBatchStatus`, `date_mise_incubation`, `date_eclosion_prevue`) + `IncubationAssignment.batch_id`.
- Les directives actuelles désignent encore `reference/Structure-de-données.md` comme SSOT et **bannissent** `boire_inc_batch`.

## ACTION 1 — Inscrire la nouvelle directive de source de vérité
**Fichier : `directives/tech.md`** (§ Source Unique de Vérité du Schéma, L15)
- Remplacer la désignation `reference/Structure-de-données.md` par : SSOT = `docs/03-models/Structure-de-données.md` (fichier maître consolidé), fractionné par pipeline en modèles par module sous `docs/03-models/<NN-module>/`.
- Préciser : le pipeline garantit la fraîcheur (maître → modules) ; `reference/` devient source d'ingestion amont, non autoritaire pour le modèle applicatif.

**Fichier : `directives/business.md`** (§ Primauté de la Structure de Données, L34-39)
- L36 : réorienter la souveraineté vers `docs/03-models/Structure-de-données.md`.
- L37 : compléter la nomenclature `IncubationAssignment` avec `batch_id` et introduire `boire_inc_batch` (statut + dates) comme entité de regroupement de coup.

## ACTION 2 — Purger les 2 bannissements périmés de `boire_inc_batch`
**Fichier : `directives/business.md` L38** — réécrire : `boire_inc_batch` n'est plus banni ; il fait partie du modèle courant `docs/03-models/`. Conserver la mise en garde sur les vraies extrapolations (`preview_token`, `boire_ref_incubator` À CONFIRMER — vérifier s'il est aussi dans le modèle courant avant de le délister).
**Fichier : `memory/evidence/INC-003-BE_fact_dossier.md` L30** — retirer/réécrire la proscription de `boire_inc_batch`, ajouter une note de réalignement de source (`reference/` → `docs/03-models/`).

## ACTION 3 — Mettre à jour le dossier de preuves INC-004-BE
**Fichier : `memory/evidence/INC-004-BE_fact_dossier.md`**
- Lever le statut `STALE_PENDING_REVISION` → `CURRENT`.
- Matrice de conflits (§1.1) : acter `docs/03-models/` comme source autoritaire.
- §3 Schéma : ajouter `boire_inc_batch` (status, date_mise_incubation, date_eclosion_prevue) + `IncubationAssignment.batch_id`.
- §5 Frontière : **résoudre QD-002** via `boire_inc_batch.status` (PLANIFIE→EN_COURS) et **QD-001** via `boire_inc_batch.date_mise_incubation` (heure réelle) vs `date_eclosion_prevue` (sortie recalculée). Q-012 (seuils 30/45 min) reste ouverte.
- Rafraîchir `sources_hashes` (hash réel de `modele-incubation.md`).

## LIVRABLE COMPLÉMENTAIRE — Rapport d'audit de cohérence BE (déjà restitué dans le chat)
- 14/20 récits BE sans dossier de preuves (12 REC + 2 VNT) — signalé, hors périmètre des 3 actions.
- 6 dossiers INC sur 3 sources divergentes — seul INC-004-BE aligné.
- Dette de réalignement identifiée sur 5 récits INC (dont INC-002 & INC-003 en READY_FOR_DEV).

## Ce que je NE fais PAS dans ce plan (à arbitrer séparément)
- Je ne réécris PAS les récits INC-001/002/003/005/006 ni leurs dossiers au-delà de la purge du bannissement (INC-003). Le réalignement de fond de ces 5 récits sur `boire_inc_batch` est une décision d'architecture distincte (touche 2 récits READY_FOR_DEV) à valider séparément.
- Je ne crée PAS les 14 dossiers de preuves manquants (REC/VNT) — hors périmètre.
- Je ne touche PAS au fichier maître `Structure-de-données.md` ni au pipeline de fractionnement.

## Vérification post-édition
- `python src/swarm.py vibe-check --project BoireFrere_Segment2` pour confirmer l'absence de régression SSOT.

## Question ouverte pour toi
1. Confirmes-tu que `boire_ref_incubator` (cité dans le même bannissement L38) est aussi dans le modèle courant et doit être délisté, ou reste-t-il une extrapolation à bannir ?
2. Veux-tu que j'ouvre un chantier séparé pour réaligner les 5 récits INC restants sur `boire_inc_batch`, ou on laisse INC-004-BE seul aligné pour l'instant ?