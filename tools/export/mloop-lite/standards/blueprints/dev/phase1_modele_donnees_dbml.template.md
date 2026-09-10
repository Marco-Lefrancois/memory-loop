# 🗄️ Schéma de Données & Contrats DBML — <MODULE>

> **Phase** : Phase 1 — Ingest  
> **Source** : Base de données existante ou spécification du devis fonctionnel.

---

## 1. Schéma Relationnel (DBML)
```dbml
Table users {
  id uuid [pk]
  email varchar [unique, not null]
  created_at timestamp [default: `now()`]
  status varchar
}

Table orders {
  id uuid [pk]
  user_id uuid [ref: > users.id]
  total_amount decimal(10,2) [not null]
  status varchar
}
```

## 2. Dictionnaire des Champs Critiques
* `orders.status` : Valeurs autorisées : `PENDING`, `CONFIRMED`, `CANCELLED`.
* Contraintes d'intégrité et index uniques.
