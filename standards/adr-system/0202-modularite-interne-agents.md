# ADR-0202 : Modularité Interne des Agents & Seuils de Complexité
## Statut : Accepté (Série 02xx - Modularité Code)

---

## 1. Contexte

Afin d'éviter que les fichiers Python sous `src/pipelines/` et `src/agents/` ne deviennent monolithiques et inmaintenables, un cadrage strict sur la taille et le découpage modulaire est requis.

---

## 2. Décision

Tout fichier d'agent ou de pipeline doit respecter les plafonds incompressibles suivants :

| Indicateur | Seuil de Déclenchement | Action Requise |
|---|---|---|
| Nombre de lignes | > 300 lignes | Refactoring obligatoire par extraction de sous-modules |
| Méthodes privées | > 5 méthodes `_private` | Extraire les fonctions utilitaires dans un dossier dédié |
| Taille fichier | > 15 Ko | Signal fort de monolithisme à décomposer |

**Pattern de Décomposition :**
Les fonctions auxiliaires sont extraites dans des sous-modules Python purs adjacents (ex: `src/pipelines/jira/client.py`, `adf_converter.py`, `sync_engine.py`).

---

## 3. Conséquences

- **Testabilité Chirurgicale** : Modules purs facilement isolables et testables.
- **Fenêtre de Contexte Optimisée** : Fichiers légers parfaitement assimilés par les LLMs.
