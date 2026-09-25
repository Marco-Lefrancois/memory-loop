---
created: 2026-09-24T17:59:18.284Z
source: plannotator
tags: [plannotator, memory-loop, alignement, sant, food]
---

[[Plannotator Plans]]

# Plan d'Alignement SANTÉ ← FOOD (Décisions Légal validées) — Join par Package

## 🎯 Objectif
Aligner la catégorisation OneTrust du scan **SANTÉ** sur les décisions **validées Légal FOOD**, selon la règle : **si un package présent dans SANTÉ existe aussi dans FOOD → reprendre `Catégorie Recommandée` + `Decision legal` de FOOD**. Join package-par-package (les packages ne sont pas identiques entre bannières).

## 🔴 Découverte critique (preuve AST niveau 2)
Contrairement à ce qu'affirmait la note Légal FOOD (`Q-006`/`Q-012` : « Firebase Analytics supprimé physiquement dans SANTÉ »), le code source SANTÉ prouve le CONTRAIRE :
- `Pharma.Application.csproj` / `Pharma.Brunet.csproj` / `Pharma.PJC.csproj` → `Plugin.Firebase.Analytics v4.0.0` **PRÉSENT**
- `FirebaseTrackingService.Android/iOS.cs` → `CrossFirebaseAnalytics.LogEvent()`, `screen_view` → **GA4 ACTIF**
- `MauiProgram.cs` → `RegisterFirebaseServices()` inconditionnel au lancement (avant consentement)
➡️ L'équipe dev a raison : **SANTÉ contient bien du GA4**. Le profil SANTÉ ressemble donc à FOOD, l'alignement par package est justifié.

## 📥 Sources (100% fichiers .md — règle confirmée)
- **Référence FOOD (décisions Légal)** : `docs/OneTrust/00-ingested/03-scans-et-inventaires/ME00025 - Metro_Food-...AVEC_Categories+et+Delta_iOS.md` — colonnes `Package Name`, `Vu avec legal`, `Decision legal`, `Catégorie Recommandée`
- **Cible SANTÉ** : `reference/OneTrust/OneTrust_Apps_Scans/working_md/CONSOLIDE_SANTE.md` (consolidé source, à convertir/ingérer proprement en .md de travail) + les 4 scans ingérés `BRUNET_SANTE` / `JEANCOUTU_SANTE` (Android+iOS)

## 📋 Étapes

### Phase 0 — Cadrage & confirmation (AVANT toute écriture)
1. Établir le **.md de travail SANTÉ** unique consolidé (aligné sur la structure FOOD : mêmes 10 onglets + colonnes `Vu avec legal`/`Decision legal`). Si absent en `docs/`, l'ingérer depuis le consolidé source.
2. Extraire la **table de référence FOOD** (package → catégorie + décision légale) comme dictionnaire de mapping.

### Phase 1 — Join & classification (délégué à un worker Herdr — Volume/Durée > seuils)
3. Pour chaque package SANTÉ : chercher correspondance exacte dans FOOD (par `Package Name` normalisé).
   - **Match trouvé** → appliquer `Catégorie Recommandée` + `Decision legal` FOOD, colonne traçabilité « Aligné sur FOOD (réf. Q-0XX) ».
   - **Pas de match** → laisser la catégorie SANTÉ existante, marquer `À arbitrer (spécifique SANTÉ)` + créer question ouverte `Q-XXX` si sensible.
4. Cas Firebase/GA4 spécifiques (FCM `Q-013`, Analytics `Q-012`, Consent Mode) : appliquer les décisions FOOD ET signaler l'écart de conformité (GA4 actif avant consentement dans SANTÉ).

### Phase 2 — Livrables
5. Produire le **.md SANTÉ aligné** (toutes manipulations en .md).
6. Générer un **rapport de réconciliation** : `AUDIT_ALIGNEMENT_SANTE_SUR_FOOD_<date>.md` (packages alignés / non-matchés / écarts de conformité découverts dont GA4).
7. Mettre à jour le registre de questions ouvertes SANTÉ + note Légal sur l'écart GA4 (correction de Q-006/Q-012).
8. **Sync** post-modification (FTS5 + Graphify) avec réindexation forcée.
9. **Conversion finale .md → .xlsx** UNIQUEMENT à la toute fin, pour le livrable client (comme convenu).

## ⚠️ Points de vigilance / Anti-complaisance
- **Ne PAS copier en bloc** : le join est strictement package-par-package. Un package FOOD absent de SANTÉ n'est pas ajouté.
- **Écart de conformité GA4** : à remonter formellement au Légal (la note FOOD était factuellement erronée sur SANTÉ). Ne pas masquer.
- **SANTÉ = données de santé** : profil de sensibilité potentiellement PLUS strict que FOOD (Loi 25 renforcée). Une décision FOOD « permissive » sur un package pourrait ne pas convenir à SANTÉ → à signaler, pas appliquer aveuglément.
- **Bannières** : SANTÉ = Brunet + Jean Coutu (Android+iOS). Vérifier la cohérence inter-bannières.

## ❓ Questions à confirmer avant exécution
1. **Cible du .md de travail SANTÉ** : je consolide les 4 scans bannière en 1 seul .md aligné (comme FOOD), OU je pars du `CONSOLIDE_SANTE.md` source existant ?
2. **Packages non-matchés** (présents SANTÉ, absents FOOD) : je les laisse en l'état actuel SANTÉ, OU je les marque tous « à arbitrer Légal » ?
3. **Écart GA4** : je le documente en question ouverte + note Légal (recommandé), ou hors périmètre pour l'instant ?
4. Délégation à un **worker Herdr** pour le join massif : OK ?