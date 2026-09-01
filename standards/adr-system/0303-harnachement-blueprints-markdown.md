# ADR-0303 : Harnachement des Blueprints Markdown (Zero-Drift Formatting)
## Statut : Accepté (Série 03xx - Blueprints)

---

## 1. Contexte

Sans contrainte de structure stricte, les modèles LLM ont tendance à halluciner la mise en page des récits (ex: réinventer des titres de sections), brisant la cohérence documentaire.

---

## 2. Décision

1. **SSOT Structurelle** : Le répertoire `standards/blueprints/` contient le seul gabarit autorisé ([`story_template.md`](file:///c:/Memory%20Loop/standards/blueprints/story_template.md)).

2. **Harnais Cognitif** : Les agents ont l'obligation constitutionnelle d'injecter et de respecter ces blueprints avant toute création/modification de récit.
3. **Tolérance Zéro** : Interdiction formelle de paraphraser ou d'altérer la hiérarchie des en-têtes (H1, H2, H3).

---

## 3. Conséquences

- **Uniformité Visuelle 100%** : Tous les récits partagent exactement le même formatage.
- **Évolutivité Facile** : Modifier un blueprint dans `standards/blueprints/` adapte instantanément le comportement de tous les agents.
