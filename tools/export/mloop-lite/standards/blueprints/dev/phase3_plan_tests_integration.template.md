# 🧪 Plan de Tests d'Intégration & Recette Dev — <MODULE>

> **Phase** : Phase 3 — Validate  
> **Cible** : Automatisation CI/CD & Tests d'API

---

## 1. Matrice des Tests d'API (End-to-End)
| Route | Cas de Test | Payload / Paramètres | Code HTTP Attendu | Vérification DB |
|---|---|---|:---:|---|
| `POST /orders` | Création nominale | `{ "items": [1, 2] }` | `201 Created` | Enregistrement créé avec status PENDING |
| `POST /orders` | Panier vide | `{ "items": [] }` | `400 Bad Request` | Aucun impact DB |
| `POST /orders` | Coupure réseau en cours | Retry avec Idempotency-Key | `200 OK` | Pas de double-création |

## 2. Critères de Couverture de Code
* [ ] Couverture unitaire minimale des règles d'affaires : ≥ 80%.
* [ ] Zéro avertissement de sécurité critique (SonarQube / Trivy).
