# ADR-0373 : Génération Multi-Branches (Multi-Draft Challenge) & Auto-Évaluation Déterministe Locale

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-17
- **Auteurs** : Équipe mLoop Swarm & Lead Architecte Agentique
- **Périmètre** : Pipeline de génération multi-drafts (`src/pipelines/multi_draft.py`), Gestionnaire des brouillons physiques (`Projects/<P>/memory/drafts/<STORY>/`), Moteur d'évaluation contradictoire local (struct-check + rubber-duck), Commande CLI `multi-draft`
- **Autorité** : [ADR-0001](0001-python-state-graph.md), [ADR-0201](0201-orchestration-dag-multi-agents.md), [ADR-0319](0319-purete-fonctionnelle-zero-code-physique.md), [ADR-0326](0326-revue-semantique-sentinel-substantive.md), [ADR-0370](0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md), [ADR-0371](0371-paradigme-dual-harnais-preventif-et-point-in-time-recovery-agentique.md), [ADR-0372](0372-replay-simulator-hors-ligne-et-auto-amelioration-recursive-du-harnais.md)

---

## 1. Contexte & Problématique

Dans les flux de génération agentique traditionnels, l'agent produit souvent un récit en tir unique (*single-shot generation*). Cette approche présente plusieurs faiblesses critiques :
1. **Biais d'ancrage prématuré** : L'agent adopte la première hypothèse d'implémentation sans explorer les alternatives architecturales.
2. **Absence de matérialité contradictoire** : Les comparaisons « en mémoire » ne laissent aucune trace vérifiable.
3. **Fragilité de la validation** : Sans challenge comparatif chiffré, le récit final peut contenir des angles morts que seul un audit contrastif révèle.

Règle constitutionnelle établie sur REC-009-BE, REC-010-BE et REC-011-BE :
> *« Il faut que le multi-draft soit toujours généré physiquement pour prendre une décision. »*

---

## 2. Décisions d'Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               MULTI-DRAFT CHALLENGE & LOCAL AUTO-EVALUATION (ADR-0373)                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ÉTAPE 1 : GÉNÉRATION MULTI-BRANCHES PHYSIQUE SUR DISQUE]                            │
│   ├──> memory/drafts/<STORY>/draft_A_<focus_1>.md  (ex: Transactionnelle Pure)         │
│   ├──> memory/drafts/<STORY>/draft_B_<focus_2>.md  (ex: Événementielle / Outbox)       │
│   └──> memory/drafts/<STORY>/draft_C_<focus_3>.md  (ex: HACCP / Résilience Réseau)     │
│                                                                                        │
│   [ÉTAPE 2 : HARNAIS D'AUTO-ÉVALUATION DÉTERMINISTE LOCALE]                            │
│   ├──> Gatekeeper Structurel : struct-check --strict (0 violation tolérée)             │
│   └──> Revue Sémantique Sentinel : rubber-duck (Trust Score, Rigueur, Cohérence)       │
│                                                                                        │
│   [ÉTAPE 3 : MATRICE COMPARATIVE & SYNTHÈSE PARETO]                                    │
│   ├──> challenge_matrix.json  (scores bruts par branche)                               │
│   ├──> challenge_report.md    (tableau comparatif humain-lisible)                      │
│   └──> Golden Master : backlog/stories/<module>/<STORY>.md                             │
│                                                                                        │
│   [GARDES DE SÉCURITÉ]                                                                 │
│   ├──> Refus READY_FOR_DEV si drafts/ < 2 branches physiques                          │
│   └──> Refus sync Jira si statut FERMÉ (statusCategory.key = "done")                  │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Obligation de Matérialisation Physique

Toute décision d'élaboration d'un récit requiert la création préalable d'au moins deux (idéalement trois) fichiers physiques sous `Projects/<P>/memory/drafts/<STORY_ID>/draft_{A,B,C}_<angle>.md`. Aucune histoire canonique ne peut être déclarée `READY_FOR_DEV` sans ces fichiers sur disque.

### 2. Challenge d'Évaluation Locale Automatisée

Commande : `python src/swarm.py multi-draft --project <P> --story <ID>`

- **`struct-check --strict`** : hiérarchie titres, format listes, zéro lien relatif.
- **`rubber-duck` (DevilAdvocateCritic)** : Discernement Métier, Cohérence Écosystème, Rigueur Technique (503, concurrence, 401, 400 données partielles) → **Trust Score Global**.

| Statut Sentinel | Signification | Éligibilité Pareto |
| :--- | :--- | :---: |
| `APPROVED` | Aucun avertissement ni défaut | ✅ |
| `ACTION_REQUIRED` | Warns non-bloquants, score élevé possible | ✅ |
| `REJECTED` | Défauts critiques bloquants | ❌ |

### 3. Matrice de Challenge & Synthèse Golden Master

Les résultats sont consolidés dans `memory/drafts/<STORY_ID>/challenge_matrix.json` et `challenge_report.md`. L'agent retient les points forts de chaque branche pour forger le **Golden Master** final sous `backlog/stories/<module>/<STORY_ID>.md`.

### 4. Un Seul Modèle, Plusieurs Angles Architecturaux

Le multi-draft utilise **un seul modèle LLM** (le modèle courant). La diversité repose sur des **angles architecturaux intentionnellement différents** :
- **Draft A** → Transactionnel pur (flux heureux d'abord)
- **Draft B** → Événementiel / EDA (outbox pattern)
- **Draft C** → HACCP / Résilience (failure modes prioritaires)

Utiliser 3 LLMs distincts relèverait du paradigme Dream-RSI multi-modèles (ADR-0372) — orthogonal au multi-draft.

### 5. Garde Constitutionnelle Jira — Statut FERMÉ

Tout ticket dont `statusCategory.key == "done"` est **strictement exclu** de toute synchronisation, en double garde :
1. **Pré-rejet préemptif** dans `handle_jira_sync` via `GET /rest/api/3/issue/{key}?fields=status`.
2. **Garde d'exécution** dans `sync_targeted_to_jira` via `is_jira_status_closed()` — détection multilingue (FR: `Fermée`, EN: `Done`, `Closed`, `Resolved`).

---

## 3. Conséquences & Bénéfices

- **Traçabilité totale** : Les compromis architecturaux et les alternatives explorées restent consultables dans l'historique du projet.
- **Zéro Régression & Zéro Fluff** : L'auto-évaluation locale élimine les formulations floues avant la présentation à l'humain.
- **Rigueur Déterministe** : Le système s'interdit d'approuver une histoire sans confrontation chiffrée préalable.
- **Sécurité Jira** : Aucun ticket clôturé ne peut être réouvert accidentellement par une synchronisation agentique.
