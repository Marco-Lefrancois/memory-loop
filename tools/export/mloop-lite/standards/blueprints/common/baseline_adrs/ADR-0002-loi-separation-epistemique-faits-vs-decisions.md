# 🏛️ ADR-0002 : La Loi de Séparation Épistémique (Faits vs Décisions)

* **Statut** : ACCEPTÉ (Fondateur)
* **Date** : 2026-09-02
* **Décideurs** : Équipe Méthodologie Nmédia
* **Domaine** : Interaction Humain-IA & Cadrage

---

## 1. Contexte & Problématique
Les assistants IA posent fréquemment des questionnaires fleuves ou des questions triviales dont les réponses figurent déjà dans les documents fournis par le client, gaspillant un temps précieux d'analyse.

---

## 2. Décision Retenue
Application stricte de la Loi de Séparation Épistémique :
* **Les Faits (*Look it up*) = Responsabilité 100% IA** : L'IA a l'obligation formelle de fouiller les documents existants via Fact-Search. Il lui est interdit de poser une question sur un fait déjà documenté.
* **Les Décisions (*Ask the User*) = Responsabilité 100% Humain** : L'humain arbitre exclusivement la valeur, les priorités d'affaires et le périmètre.
* **Règle d'Or de l'Interview** : Une seule question d'arbitrage ciblée à la fois, avec Option A (Recommandée) vs Option B.

---

## 3. Conséquences
* **Positives** : Réduction drastique de la fatigue décisionnelle, sessions d'arbitrage chirurgicales.
* **Compromis** : L'IA doit maintenir un index FTS5 rigoureusement synchronisé pour ne rien manquer.
