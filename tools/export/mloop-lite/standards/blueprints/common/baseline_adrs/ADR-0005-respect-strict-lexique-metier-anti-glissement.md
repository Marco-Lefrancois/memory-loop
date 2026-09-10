# 🏛️ ADR-0005 : Respect Strict du Lexique Métier (Anti-Glissement Lexical)

* **Statut** : ACCEPTÉ (Fondateur)
* **Date** : 2026-09-02
* **Décideurs** : Équipe Cadrage & Analyse d'Affaires Nmédia
* **Domaine** : Vocabulaire Contrôlé & DDD

---

## 1. Contexte & Problématique
Le glissement sémantique (appeler un même concept par 3 noms différents selon qu'on parle au client, au développeur ou au designer) est la source principale d'erreurs de livraison et de reprise de code.

---

## 2. Décision Retenue
* Le fichier `docs/LEXIQUE.md` est le contrat sémantique suprême du projet.
* Chaque terme validé avec le client possède une définition unique.
* Les **Termes Bannis** spécifiés dans le tableau sont formellement interdits dans tous les livrables d'affaires et techniques.

---

## 3. Conséquences
* **Positives** : Clarté absolue des communications, intégration facilitée des nouveaux membres de l'équipe.
* **Compromis** : Obligation d'enrichir le lexique dès qu'un terme nouveau apparaît.
