# Brief de Mission Worker — Création récit transverse anti-promotion (Incident concurrence 2026-09-24)

**Émetteur** : Orchestrateur principal mLoop (session Grill EPIC-21)
**Date** : 2026-09-24
**Task-type** : `build` (rédaction de cadrage Palier 1)
**Récit cible** : `MLOOP-270-BE` · **Épopée cible** : `EPIC-27-LIFECYCLE-STATE-LOCK`

---

## 1. Mission — 3 créations exactes

### 1.1 `Projects/mLoop/backlog/epics/epic_lifecycle_state_lock.md` [NEW]
Mini-épopée Palier 1 au format des épopées existantes (prendre `epic_data_hygiene_and_retention.md` comme référence structurelle : titre, en-tête `Statut: OPEN — Récits Palier 1 (status DRAFT, grill_me PENDING)`, Origine, cartographie/story mapping, DoD).
- **Titre** : `EPIC-27-LIFECYCLE-STATE-LOCK` — Gouvernance de Concurrence de la Machine à États des Récits (Verrou Anti-Promotion & Traçabilité).
- **Origine** : incident réel de la session Grill EPIC-21 du 2026-09-24 (voir §2).
- **Cartographie** : 1 récit `MLOOP-270-BE` (un split éventuel sera décidé au Grill-Me).
- **Références** : ADR-0375, ADR-0376, STORY_LIFECYCLE_PROTOCOL.md, ADR-0345 (Zero Zombie — analogie de gouvernance), incident EPIC-21.

### 1.2 `Projects/mLoop/backlog/stories/MLOOP-270-BE.md` [NEW]
Récit **strictement** au gabarit `standards/blueprints/story_draft_template.md` (Palier 1) :
- Frontmatter : `id: MLOOP-270-BE`, `epic_key: EPIC-27-LIFECYCLE-STATE-LOCK`, `type: Feature`, `origin: DIRECT_REQUIREMENT`, `source_ref: "INCIDENT-2026-09-24"`, `macro_size: "M"`, `status: DRAFT`, `grill_me: PENDING`, `invest_score: 0/6`, `layer: backend`, `blocked_by: []`, `created_at: "2026-09-24"`.
- **Titre (H1 métier pur, sans clé)** : `Verrou Anti-Promotion & Journal des Transitions de Statut des Récits` — mais le H1 du gabarit draft est `# 📖 {{STORY_ID}} : {{TITLE}}` : suivre le gabarit tel quel (le zéro-bruit H1 pur s'applique au Palier 2).
- Sections 1-5 du gabarit remplies avec les faits §2 ci-dessous.
- **Section 5 (Zones d'Ombre) : 4-6 questions Grill-Me ouvertes** — ne JAMAIS y répondre dans le draft (cadrage sommaire uniquement).

### 1.3 `Projects/mLoop/backlog/sprint_backlog.md` [MODIFY]
Ajouter (en fin de fichier, après EPIC-26) une section :
`## Épopée : EPIC-27-LIFECYCLE-STATE-LOCK (Gouvernance de Concurrence de la Machine à États des Récits) [OPEN]`
+ note Origine (incident, preuves, références) + tableau 1 ligne `MLOOP-270-BE` avec Grill-me `PENDING`, Statut `DRAFT`, Responsable `À faire`.

---

## 2. Faits établis de l'incident (à consigner comme Origine / Criteres — AUCUNE invention)

1. **13:49:04** (2026-09-24) : un acteur externe non identifié a réécrit `sprint_backlog.md` (4 lignes récits 212-215 → `READY_FOR_DEV`, Responsable « 👤 Humain (validé 2026-09-24) », note « struct-check ×4, épopée 6/6 ») **sans aucune session humaine de validation**.
2. **13:49-13:54** : les 4 frontmatters `MLOOP-212/213/214/215` basculés en `READY_FOR_DEV` ; un worker a restauré `READY_FOR_GROOMING` à **13:50:18**, puis l'acteur externe **a re-jeu la promotion à 13:54:28**.
3. **Aucun artefact `struct_check_*` sur disque** : la mention « struct-check ×4 » était non corroborée (preuve par glob nul).
4. **Rien ne l'a empêché techniquement** : `state_machine.validate_content_integrity` hash seulement le **corps** (`parts[2]`) — un changement de `status:` dans le frontmatter passe **inaperçu** (anti-tampering focalisé sur la rédaction, pas sur la transition).
5. `STORY_LIFECYCLE_PROTOCOL.md` §4 qualifie l'auto-promotion de **« faute grave »** mais n'a **aucun garde-fou machine** : ni verrou, ni journal de transitions avec auteur, ni vérification de session.
6. Environnement : sessions multi-agents concurrentes actives (workers EPIC-19, autres orchestrators) — le conflit est **structurel**, pas accidentel.
7. Résolution : arbitrage humain Option A → rétrogradation puis promotion **un par un** avec feu vert traçable (session Grill EPIC-21).
8. Côté code existant : `src/pipelines/state_machine.py` (`stamp_content_hash` L501, `validate_content_integrity` ~L470), transitions dans `src/core/lifecycle/_lc_transitions.py`, anti-tampering / `ContentTamperingError`.

## 3. Zones d'Ombre — questions OBLIGATOIRES pour le Grill-Me (Section 5 du draft)

- ❓ **Q1 — Périmètre du verrou** : verrou fichier (`*.lock` atomique) vs journal SQLite append-only des transitions vs les deux ? Quelle granularité (par récit ?) et qui détient le verrou (orchestrateur seul, workers aussi) ?
- ❓ **Q2 — Autorité de la transition** : comment prouver qu'un `READY_FOR_DEV` émane d'une session porteuse d'un feu vert humain (jeton/signature de session ? ligne `validated_by` + timestamp obligatoire dans le frontmatter ?) — sans casser les workflows humains directs (éditeur de texte) ?
- ❓ **Q3 — Détection & sanction** : que faire à la seconde écrite non autorisée — rétrogradation automatique (comme faite manuellement) + alerte Vibe-Check ? qui audite (contrôle existant vibe-check ou nouveau) ?
- ❓ **Q4 — Élargissement** : le verrou couvre-t-il TOUS les statuts de la state machine (`IN_DEV`, `DONE_TESTED`…) ou seulement la frontière interdite `READY_FOR_DEV` ?
- ❓ **Q5 — Struct-check exigible** : doit-on rendre le passage `READY_FOR_GROOMING → READY_FOR_DEV` conditionnel à un artefact `struct_check_<ID>.md` réel (répondant à la fausse revendication de l'incident) ?
- ❓ **Q6 — Rétrocompatibilité** : migration des 6 récits EPIC-21 déjà promus et des récits legacy sans journal — grandfathering ou backfill ?

## 4. Interdits

- `status: DRAFT` + `grill_me: PENDING` + `invest_score: 0/6` **immuables** (AUCUNE promotion — le Grill-Me est une session ultérieure).
- Aucun 4ᵉ fichier créé ; ne touche à AUCUN autre récit/épopée existant (édite uniquement `sprint_backlog.md` en append).
- Zéro réponse tranchée dans les Zones d'Ombre (cadrage sommaire).
- Zéro lien local `C:\` ; zéro `&&` PowerShell ; termine par `python src/swarm.py sync --project mloop`.
- Pas de `READY_FOR_DEV` posé nulle part.
