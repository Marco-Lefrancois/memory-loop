# Checklist Décisionnelle & Rédaction d'ADR (Architecture Decision Records)

Cette checklist régit la création et la révision de tout ADR dans le système de standards de Memory Loop (`standards/adr-system/`).
Elle permet d'éviter l'inflation documentaire tout en sanctuarisant les choix irréversibles.

---

## 1. Les 3 Filtres Inviolables pour Justifier un ADR

Un ADR DOIT satisfaire simultanément aux 3 conditions suivantes :

- [ ] **Filtre 1 : Décision de Type 1 (Porte à sens unique)** :
  - La décision est difficilement réversible sans coût prohibitif (refonte majeure de base de données, choix de framework de base, contrat d'API externe public).
  - *Contre-exemple (Type 2)* : Le renommage d'un composant interne, un choix de couleur ou un format de log standard ne justifient PAS d'ADR.
- [ ] **Filtre 2 : Décision Surprenante Sans Contexte** :
  - Un nouveau développeur ou un agent IA arrivant sur le projet se poserait légitimement la question : *"Pourquoi ont-ils fait ça comme ça au lieu de la méthode conventionnelle ?"*.
  - L'ADR documente la contrainte cachée qui a forcé cette décision non triviale.
- [ ] **Filtre 3 : Arbitrage Réel avec Alternatives Analysées** :
  - La décision résulte d'un choix explicite entre au moins 2 solutions viables, avec une analyse rigoureuse des compromis (*trade-offs*).

---

## 2. Structure Normative de l'ADR

- [ ] **Numérotation Séquentielle Strictement Incrémentale** : Format standard `NNNN-titre-en-kebab-case.md` (ex: `0365-harmonisation-symbiotique-skills.md`).
- [ ] **Statut Explicite** : `PROPOSED`, `ACCEPTED`, `SUPERSEDED`, ou `REJECTED`.
- [ ] **Contexte & Forces en Présence** : Les contraintes métier, techniques et architecturales ayant déclenché le besoin de décision.
- [ ] **Décision Affirmative** : Formulation limpide et sans équivoque de la direction retenue (*« Nous décidons de... »*).
- [ ] **Conséquences & Compromis Assumés** :
  - *Positives* : Gains de performance, découplage, vélocité.
  - *Négatives / Coûts* : Complexité additionnelle, dette technique maîtrisée, contraintes imposées.
- [ ] **Alternatives Rejetées avec Motifs** : Au minimum 1 alternative concrète analysée et la raison objective de son rejet.

---

## 3. Enregistrement & Indexation SSOT

- [ ] **Indexation dans `standards/adr-system/README.md`** : L'ADR est inséré dans la table thématique correspondante.
- [ ] **Cross-Références Validées** : Tout ADR obsolète ou remplacé est tagué avec le lien vers son successeur (`Supersedes ADR-XXXX` / `Superseded by ADR-YYYY`).
