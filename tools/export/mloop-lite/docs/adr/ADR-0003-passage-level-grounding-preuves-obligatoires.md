# 🏛️ ADR-0003 : Passage-Level Grounding & Preuves Obligatoires (Search-Before-Ask)

* **Statut** : ACCEPTÉ (Fondateur)
* **Date** : 2026-09-02
* **Décideurs** : Équipe Qualité & Architecture Nmédia
* **Domaine** : Fiabilité Documentaire & Anti-Hallucination

---

## 1. Contexte & Problématique
Le risque majeur des modèles d'IA générative est l'hallucination de détails techniques ou de règles métier inexistantes, présentés avec une fausse autorité.

---

## 2. Décision Retenue
Toute affirmation, exigence fonctionnelle ou question d'arbitrage émise par l'IA doit être adossée à un **Dossier de Preuves Documentaires** vérifié :
* Citation mot-à-mot du texte source.
* Chemin de fichier exact et numéros de lignes précis.
* Fait établi déduit en français clair.
* Hachage cryptographique consigné dans les EvidencePacks de validation.

---

## 3. Conséquences
* **Positives** : Zéro hallucination tolérée, traçabilité irréfutable de chaque exigence face au client.
* **Compromis** : Nécessite une rigueur de citation systématique lors des sessions de cadrage.
