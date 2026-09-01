# ADR-0304 : Gouvernance de Synchronisation Jira Anti-Drift
## Statut : Accepté (Série 03xx - Synchro External Tracking)

---

## 1. Contexte

Pour maintenir la cohérence entre la documentation locale (`backlog/`) et les outils cloud de livraison (Jira, Azure DevOps), un protocole rigoureux de synchronisation est indispensable.

---

## 2. Décision

1. **Séparation des Autorités** :
   - **Autorité de Conception** : Les fichiers Markdown locaux dans `backlog/` sont la Source Unique de Vérité.
   - **Autorité de Livraison** : Jira est la source de vérité pour la planification temporelle et le sprint du client.
2. **Interdiction des Scripts Jetables** : Aucun agent n'est autorisé à créer de script Python ad-hoc ou d'appel `curl` direct vers Jira.
3. **Moteur Unique** : Toute synchronisation transite **exclusivement** par `python src/swarm.py jira_sync --project <nom_projet>`.

---

## 3. Conséquences

- **Zéro Dérive** : Pas de tickets créés sauvagement sans répercussion dans le Markdown local.
- **Indépendance Outillage** : Possibilité de changer de système de suivi cloud sans altérer la mémoire du projet.
