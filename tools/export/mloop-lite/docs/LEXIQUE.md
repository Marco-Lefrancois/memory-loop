# 📖 Lexique Métier & Glossaire Ubiquitaire — mLoop Lite

> **Règle d'or** : Chaque terme ici présent a une signification UNIQUE et VALIDÉE avec le client.  
> L'IA et l'équipe humaine ont l'obligation formelle d'utiliser exclusivement ces termes pour éviter tout glissement de sens (*Lexical Drift*).

---

## 📋 Table des Termes Métier Validés

| Terme Officiel Validé | Définition Métier Exacte & Non Ambiguë | Synonymes Tolérés | ⛔ Termes Bannis / À Proscrire | Source / Validé par |
| :--- | :--- | :--- | :--- | :--- |
| **Buggy** | Chariot roulant métallique standardisé contenant 16 800 œufs d'incubation. | Chariot d'incubation | *Rack, Panier, Étagère* | Entretien du 12 mai (Directeur Usine) |
| **Membre VIP** | Client ayant cumulé plus de 500 points au cours des 12 derniers mois. | Client Privilège | *Abonné, Utilisateur Gold* | Document Politique Loyauté (p. 3) |
| **Coup d'incubation** | Groupe d'œufs incubés simultanément dans un même incubateur à une heure fixe. | Lot d'incubation | *Fournée, Vague, Batch* | Spécification Métier v2 |
| **Bannière OneTrust** | Écran modal bloquant de premier niveau présentant le choix de consentement. | Écran de consentement | *Pop-up, Alerte, Cookie box* | Guide Légal Loi 25 (p. 14) |

---

## 🔍 Comment enrichir ce lexique :
1. Ajoutez une ligne dès qu'un mot a plusieurs interprétations possibles.
2. Définissez impérativement les **termes bannis** pour empêcher l'IA d'utiliser du vocabulaire non validé avec le client.
3. Exécutez `python mloop.py ingest` pour réindexer automatiquement le lexique dans la base de recherche FTS5.
