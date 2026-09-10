# 🛡️ Matrice de Cadrage du Périmètre (In-Scope vs Out-of-Scope) — <PROJET>

> **Objectif** : Verrouiller formellement les frontières du mandat pour protéger le budget et les délais.

## 1. Périmètre Inclus (In-Scope — Garanti dans l'enveloppe actuelle)
| # | Domaine / Module | Fonctionnalité Incluse | Condition / Règle de Clôture |
|---|---|---|---|
| IN-01 | Authentification | Connexion courriel / mot de passe | Avec réinitialisation par courriel |
| IN-02 | Gestion de profil | Modification des coordonnées personnelles | Validation en temps réel |

## 2. Périmètre Exclu (Out-of-Scope — Formellement exclu du mandat actuel)
| # | Élément Demandé mais Exclu | Rationale d'Exclusion | Recommandation |
|---|---|---|---|
| OUT-01 | Connexion SSO Azure AD | Non prioritaire pour le MVP | À planifier en Phase 2 |
| OUT-02 | Migration des archives historiques > 5 ans | Volume trop incertain | Prestation séparée au temps réel |

## 3. Dépendances Critiques sous Responsabilité du Client
* [ ] Fourniture de la clé d'accès API avant le : `<Date>`
* [ ] Validation formelle des maquettes sous 5 jours ouvrés suivant livraison.
