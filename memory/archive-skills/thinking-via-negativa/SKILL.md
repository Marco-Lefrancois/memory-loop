---
name: thinking-via-negativa
description: Résolution de problèmes par la soustraction et l'élimination de la dette/complexité accidentelle avant tout ajout de code ou de processus (ADR-0336).
disable-model-invocation: true
---

# ✂️ Via Negativa (Amélioration par Soustraction)

**Règle d'or :** Améliorer un système par la soustraction avant l'addition. Préférer l'élimination des sources d'erreurs, des redondances et de la complexité non essentielle ; n'ajouter de nouveau code ou composant que si un besoin avéré persiste après épuisement des pistes de suppression.

---

## ⚡ Quand l'utiliser (*When to Use*)
- Le premier réflexe face à un problème consiste à ajouter une abstraction, une dépendance externe, un wrapper ou une couche de processus.
- Simplification d'une architecture, d'une suite de tests ou d'un flux de travail devenu lourd et rigide.
- Priorisation de backlog en décidant explicitement ce qu'on ne doit **pas** construire ou maintenir.
- Optimisation de performance ou de fiabilité où couper une branche ou supprimer du code mort surpasse tout ajout de patchs palliatifs.

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- Éléments porteurs de robustesse vitaux : auth, validation de schémas, tests de régression, rate limits, audit logs (présumés nécessaires jusqu'à preuve du contraire).
- Exigence fonctionnelle formalisée ne pouvant être satisfaite par simplification.
- Minimalisme esthétique sans preuve concrète d'inutilité ou d'impact négatif.
- Suppression irréversible sans chemin de retour sécurisé (Type 1 non maîtrisé).

---

## 📋 Procédure de Simplification Soustractive

1. **Stopper le réflexe d'addition (*Pause the Add Reflex*)** :
   - Énoncer le problème en une phrase et nommer l'ajout initialement envisagé.
2. **Poser la question soustractive d'abord** :
   - *« Que pouvons-nous supprimer, désactiver ou arrêter pour atteindre le même objectif avec une surface d'attaque plus réduite ? »*
3. **Inventorier les candidats à la suppression** :
   - Composants inutilisés, logiques dupliquées, micro-wrappers superflus, paramètres de configuration orphelins, étapes de pipeline sans valeur ajoutée.
4. **Vérifier le profil de sécurité de la suppression** :
   - La suppression casse-t-elle un contrat public ? Si oui, prévoir la dépréciation progressive.
5. **Appliquer l'élagage et mesurer le gain** :
   - Valider que le système fonctionne mieux, plus vite et avec moins de maintenance résiduelle.
