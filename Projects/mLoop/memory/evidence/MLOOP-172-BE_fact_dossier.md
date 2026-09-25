---
dossier_id: MLOOP-172-BE_fact_dossier
story_id: MLOOP-172-BE
dossier_status: CURRENT
created_at: "2026-09-22"
sources_hashes:
  epic_modular_refactoring_ast_debt.md: "pending"
  MLOOP-170-BE: "pending"
---

# Dossier de Preuves Documentaires — MLOOP-172-BE

## 🧭 1. Sources Physiques & Matrice de Vérité

| Source | Type | Rôle | Statut |
| :--- | :---: | :--- | :--- |
| `backlog/epic_modular_refactoring_ast_debt.md` (§3) | Épic | Cadrage pattern réutilisable | ✅ CURRENT |
| `backlog/stories/MLOOP-170-BE.md` | Story amont | Expérience réelle du pilote (bloquant) | ✅ READY_FOR_GROOMING |
| Grill-Me Micro 1:1 du 2026-09-22 | Séance | 3 arbitrages PO verbatim (OQ-172-01→03) | ✅ Acté |

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

> Extrait 1 — Cadrage EPIC-17 (§3) :
> « le pattern sera extrait de l'expérience réelle du refactoring `vibe_check.py` (MLOOP-170-BE), pas théorique ; l'épopée cible 39 fichiers (audit frais) dont le top : `_registry.py` 2028L, `server.py` 1632L, `svg_to_md.py` 991L »
> ➔ Fait établi : pattern empirique (pas spéculatif), périmètre 39 fichiers, 3 cibles critiques >900L.

> Extrait 2 — Arbitrages Grill-Me 1:1 (22/09/2026, PO) :
> « OQ-172-01 : Couverture exhaustive dès la v1 — section dédiée par cas spécial (registres déclaratifs, singletons d'état, effets de bord à l'import), chacune avec contre-exemples »
> « OQ-172-03 : Nouveau contrôle Vibe-Check dédié — conformité au protocole armée en Phase 3 BUILD »
> ➔ Fait établi : protocole v1 exhaustif (3 cas spéciaux) + gate Vibe-Check Phase 3 exigé.

> Extrait 3 — Clause exemption ADR-0319 (ajoutée 22/09 pour débloquer le Sentinel) :
> « artefact de protocole documentaire (`standards/protocols/`) — **aucune route HTTP n'est consommée ni exposée**… `[API de soumission à définir]` — jamais inventée »
> ➔ Fait établi : livrable 100% documentaire, exemption OQ-172 déclarée et validée par Rubber Duck.

## 🗄️ 3. Périmètre Structurel

- **Livrable principal** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` (+ éventuel gabarit `standards/blueprints/`).
- **Validation** : application sur un second module indépendant (< 300L, zéro import cassé).
- **Armement** : check fumée imports + contrôle Vibe-Check Phase 3 (plan + fumée).
- **Non impacté** : exécution des lots de refactoring (récits dédiés), ADR (traités en Grill).

## 🎯 4. Contrats Déclaratifs Cibles

- **Aucune route HTTP** — exemption `OQ-172` + mention `[API de soumission à définir]` (Zéro Fausse Route).
- **Contrats documentaires** : protocole Markdown, check fumée exécutable, contrôle Vibe-Check.

## 🏁 5. Évaluation de la Frontière Active (Admission of Limits)

- **Ce que le dossier PROUVE** : source du pattern (pilote 170), 3 arbitrages PO, 3 cas spéciaux exigés, périmètre 39 fichiers, exemption API.
- **Ce qu'il ne PRUVE PAS** : le contenu exact du protocole (rédigé en Phase 3), la réussite de l'application sur le second module (testée en Phase 3), la couverture réelle des 3 cas spéciaux.
- **Frontière** : ce dossier couvre le **cadrage** (Phase 2) — la rédaction du protocole et la validation d'application appartiennent à MLOOP-172-BE (Phase 3).
