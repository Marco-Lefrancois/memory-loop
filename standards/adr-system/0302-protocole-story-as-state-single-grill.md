# ADR-0302 : Protocole Story-as-State & Single-Grill
## Statut : Accepté (Série 03xx - Workflow & Grill)

---

## 1. Contexte

Afin de prévenir l'Agent Drift vers la phase de dev sans cadrage approprié, l'avancement d'un récit doit être auto-porté par le fichier Markdown lui-même.

---

## 2. Décision

1. **Story-as-State** : Le champ `status` dans le YAML Frontmatter de chaque récit est l'unique machine à états de son évolution :
   - `OPEN` : Récit identifié au backlog.
   - `IN_ANALYZE` : Récit en cours d'analyse et d'interview `/grill-me`.
   - `READY_FOR_GROOMING` : Analyse validée par l'auto-audit `wikifix`.
   - `READY_FOR_DEV` : Validation finale par l'équipe produit.
2. **Règle de l'Interview `/grill-me`** :
   - Poser **une seule question recommandée à la fois** par tour de parole.
   - Poser des questions fermées sur les arbitrages et consigner les questions irrésolues sous `OQ-XXX`.

---

## 3. Conséquences

- **Traçabilité Transparente** : L'état d'avancement est lisible directement dans le frontmatter.
- **Grilling Approfondi** : Dialogue contrôlé et cadré.
