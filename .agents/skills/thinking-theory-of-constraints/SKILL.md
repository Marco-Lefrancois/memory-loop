---
name: thinking-theory-of-constraints
description: Identification et résolution du goulet d'étranglement critique dans les flux, pipelines et graphes de dépendance mLoop (ADR-0336).
disable-model-invocation: true
---

# ⛓️ Theory of Constraints (ToC — Goulots d'Étranglement)

**Règle d'or :** Un système limité en débit ou en latence ne possède qu'**une seule contrainte active** (*Binding Constraint*). Concentrer 100% de l'effort d'optimisation sur cette contrainte ; toute optimisation locale sur un composant non-contraint est un gaspillage d'énergie et augmente souvent l'encours inutile (*WIP*).

---

## ⚡ Quand l'utiliser (*When to Use*)
- Le débit de livraison du backlog ou la latence d'un pipeline logiciel est bloqué par une étape dominante.
- L'accumulation de travail (bloquants, stories en attente, files d'attente) se produit systématiquement avant un composant précis tandis que l'aval chôme.
- L'ajout de parallélisme ou de sous-agents n'augmente pas la vitesse de traitement globale.
- Cadrage et ordonnancement du DAG de dépendances du Backlog (`sprint_backlog.md`).

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- La charge est répartie harmonieusement et aucune étape n'est saturée.
- Le problème est un bug de justesse fonctionnelle et non une question de débit ou de goulot.
- Le goulot d'étranglement saute aléatoirement d'un composant à un autre en raison de concurrences non déterministes (utiliser `blindspot-scan` ou conception système).
- La contrainte est déjà connue et un correctif direct et peu coûteux est disponible.

---

## 📋 Procédure des 5 Étapes de Focalisation (Goldratt)

1. **Identifier la contrainte active (*Identify*)** :
   - Observer où le travail s'accumule (file d'attente la plus longue, taux d'utilisation saturé à ~100%, étape avec le temps de cycle le plus lent).
   - Se baser sur des métriques réelles (temps d'exécution, nombre de dépendances bloquantes) plutôt que des suppositions.
2. **Exploiter la contrainte au maximum (*Exploit*)** :
   - Éliminer tout temps mort ou gaspillage sur la contrainte sans dépense majeure (ex: éviter de faire attendre le goulot sur des inputs non préparés, filtrer les tâches inutiles).
3. **Subordonner tout le reste à la contrainte (*Subordinate*)** :
   - Ajuster la cadence de l'ensemble des étapes amont et aval pour qu'elles produisent exactement au rythme absorbable par la contrainte (ni plus, ni moins).
4. **Élever la contrainte (*Elevate*)** :
   - Si le débit reste insuffisant après exploitation et subordination, allouer des ressources supplémentaires structurelles (plus de CPU/workers, refactorisation lourde, mise en cache amont).
5. **Prévenir l'inertie & Réitérer (*Prevent Inertia*)** :
   - Dès que la contrainte actuelle est levée, le goulot d'étranglement s'est déplacé ailleurs. Identifier immédiatement la nouvelle contrainte sans laisser l'inertie s'installer.
