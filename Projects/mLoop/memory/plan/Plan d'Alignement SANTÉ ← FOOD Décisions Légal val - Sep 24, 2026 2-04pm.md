---
created: 2026-09-24T18:04:47.708Z
source: plannotator
tags: [plannotator, memory-loop, alignement, sant, food]
---

[[Plannotator Plans]]

# Plan d'Alignement SANTÉ ← FOOD (Décisions Légal validées) — Join par Package

## 🎯 Objectif
Aligner la catégorisation OneTrust du scan **SANTÉ** sur les décisions **validées Légal FOOD**, selon la règle : **si un package présent dans SANTÉ existe aussi dans FOOD → reprendre `Catégorie Recommandée` + `Decision legal` de FOOD**. Le contenu reste propre à la codebase SANTÉ — seul le sous-ensemble de packages en correspondance exacte hérite de la décision FOOD. Aucune copie en bloc, aucun ajout de package FOOD absent de SANTÉ.

## 📌 Contexte confirmé
- SANTÉ (Brunet + Jean Coutu) contient bien `Plugin.Firebase.Analytics` (GA4) actif au niveau code (`FirebaseTrackingService`, `MauiProgram.RegisterFirebaseServices()`), confirmé par l'équipe dev. Ce point est déjà connu (pas une nouvelle découverte) — il justifie que le join FOOD→SANTÉ sur les packages Firebase/GA4/FCM soit pertinent et applicable.

## 📥 Sources (100% fichiers .md)
- **Référence FOOD (décisions Légal validées)** : `docs/OneTrust/00-ingested/03-scans-et-inventaires/ME00025 - Metro_Food-...AVEC_Categories+et+Delta_iOS.md` (onglet `All SDKs Consolidé`) — colonnes clés : `Package Name`, `Vu avec legal`, `Decision legal`, `Catégorie Recommandée`.
- **Cible SANTÉ — ⚠️ correction de fraîcheur détectée** : les 4 `.md` déjà ingérés dans `docs/OneTrust/00-ingested/03-scans-et-inventaires/` (`8002-BRUNET_SANTE-*_GOLD.md`, `8002-JEANCOUTU_SANTE-*_GOLD.md`) datent du **1er septembre 2026** et reflètent un `output/gold/*.xlsx` figé au **13 août 2026**. Or `reference/OneTrust/OneTrust_Apps_Scans/working_md/CONSOLIDE_SANTE.md` (264 Ko) est **daté du 11 septembre 2026**, accompagné de `DELTA_NATIF_SANTE.md` et `SDK_CODE_MAUI_SANTE.md`, et a servi de base au livrable client `shared/8002-Metro_Sante-Android_iOS-Scan_OneTrust.xlsx` généré le même jour. **Le `CONSOLIDE_SANTE.md` (+ delta) est donc la version la plus à jour et fait foi** — les 4 `.md` ingérés seront remplacés/régénérés à partir de cette source avant le join, pour éviter de baser l'alignement légal sur des données périmées de ~3 semaines.


## 📋 Étapes

### Phase 0 — Préparation (session principale)
1. Fusionner les 4 scans bannière SANTÉ en **un seul .md consolidé** aligné sur la structure FOOD (10 onglets : Overview Global, All SDKs Consolidé, C0001-C0004, Hors-Périmètre, SDKs Reclassés, SDK Code MAUI, Delta iOS-Android), en préservant la distinction par bannière (Brunet / Jean Coutu) et par plateforme (Android / iOS) dans les colonnes.
2. Extraire la table de référence FOOD (`Package Name` → `Catégorie Recommandée` + `Decision legal` + `Vu avec legal`) comme dictionnaire de mapping normalisé (nom de package insensible à la casse/variantes plateforme).

### Phase 1 — Join & classification (délégué à un worker Herdr isolé)
3. Pour chaque package du consolidé SANTÉ :
   - **Match exact trouvé dans FOOD** → appliquer `Catégorie Recommandée` + `Decision legal` FOOD, ajouter une note de traçabilité (« Aligné sur décision Légal FOOD — réf. [Q-XXX] ») dans la colonne justification.
   - **Pas de match** → conserver tel quel le traitement/catégorie SANTÉ existant (aucune modification, aucun marquage supplémentaire).
4. Attention particulière aux packages Firebase/GA4/FCM (couverts par `Q-012`, `Q-013` FOOD) : appliquer la décision FOOD si le package correspond exactement dans SANTÉ.

### Phase 2 — Livrables (retour session principale)
5. Récupérer le .md SANTÉ aligné produit par le worker (harvest).
6. Générer un rapport de réconciliation court : `AUDIT_ALIGNEMENT_SANTE_SUR_FOOD_<date>.md` (liste des packages alignés avec référence FOOD, compte des packages non-matchés laissés inchangés).
7. **Sync** post-modification (FTS5 + Graphify), avec réindexation forcée si nécessaire (même procédure que pour l'ingestion FOOD précédente).
8. Conversion finale **.md → .xlsx** uniquement en toute fin, pour le livrable client (comme convenu précédemment).

## ✅ Décisions confirmées
- Base .md SANTÉ : **consolidation des 4 scans bannière ingérés** (pas le `CONSOLIDE_SANTE.md` source brut).
- Délégation : **worker Herdr** pour la phase de join massif (Volume ≥3 fichiers + Durée >5min — Delegation Gate ADR-0346).
- Toutes les manipulations se font en **.md**, conversion `.xlsx` uniquement à la fin.

## ⚠️ Garde-fous
- Join strictement package-par-package par nom exact — jamais de copie de catégorie en bloc.
- Contenu final propre à la codebase SANTÉ (packages, versions, bannières propres à Brunet/Jean Coutu conservés tels quels).
- Cycle de vie worker complet obligatoire : spawn → attente WORKING → harvest → close (Zero Zombie Policy).