# ❓ Registre des Questions Ouvertes & Points Bloquants — <NOM_DU_PROJET>

> **Règle de gouvernance** : Toute incertitude client ou zone d'ombre technique est répertoriée ici.  
> Lorsqu'un arbitrage est rendu par le client, la question passe à `RÉSOLUE` et est reliée à un ADR (`ADR-XXXX`).

---

## 📋 Tableau de Suivi des Questions Ouvertes

| ID | Date | Question / Point Bloquant | Responsable Côté Client | Criticité | Statut | Résolution / ADR Associé |
|:---:|:---:|:---|:---|:---:|:---:|:---|
| **OQ-0001** | <YYYY-MM-DD> | Quel est le comportement attendu si l'API tierce ne répond pas après 3000 ms ? | Tech Lead Client | 🔴 Haute | EN_ATTENTE | — |
| **OQ-0002** | <YYYY-MM-DD> | Le rabais VIP de 15% s'applique-t-il sur les articles en promotion ? | VP Ventes Client | 🟡 Moyenne | RÉSOLUE | ADR-0002 (Non applicable) |
| **OQ-0003** | <YYYY-MM-DD> | Confirmation du fournisseur SSO (Azure AD B2C vs Okta) | Équipe Sécurité | 🔴 Haute | EN_ATTENTE | — |

---

## 🔍 Instructions :
* **Ajouter une question** : `python mloop.py questions add "<Description de la question>" --client "<Nom du responsable>"`
* **Clore une question** : `python mloop.py questions close OQ-XXXX --adr ADR-YYYY`
