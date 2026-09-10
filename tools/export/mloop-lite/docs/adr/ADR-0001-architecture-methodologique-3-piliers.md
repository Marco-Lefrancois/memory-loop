# 🏛️ ADR-0001 : Architecture Méthodologique des 3 Piliers (Staging, SSOT, Livrables)

* **Statut** : ACCEPTÉ (Fondateur)
* **Date** : 2026-09-02
* **Décideurs** : Équipe Méthodologie & Architecture Nmédia
* **Domaine** : Gouvernance & Organisation des Connaissances

---

## 1. Contexte & Problématique
Dans les projets d'agence, les documents client (notes d'ateliers, PDFs, courriels, schémas) sont fréquemment dispersés. Cette dispersion entraîne des versions contradictoires, des pertes d'informations critiques et empêche l'IA d'avoir une source de vérité unique (SSOT).

---

## 2. Décision Retenue
Chaque projet mLoop Lite adopte une organisation hermétique en 3 Piliers fondamentaux :
1. **`reference/` (Pylône Staging)** : Espace de réception des fichiers bruts non versionnés (Word, PDFs, enregistrements, scans).
2. **`docs/` (Pylône SSOT)** : Base de vérité officielle en Markdown normalisé, indexée par SQLite FTS5 (Lexique, ADRs, Questions Ouvertes).
3. **`deliverables/` (Pylône Livrables)** : Documents d'affaires officiels validés destinés au client ou à l'équipe (Devis Fonctionnel, Business Case, Spécifications).
4. **`memory/` (Pylône Preuves)** : Artefacts techniques, EvidencePacks SHA-256 et base de données FTS5.

---

## 3. Conséquences
* **Positives** : Zéro document égaré, intégrité garantie de la base de connaissances, recherche plein-texte instantanée.
* **Compromis** : Obligation de lancer `mloop ingest` dès qu'un nouveau document est déposé dans `reference/`.
