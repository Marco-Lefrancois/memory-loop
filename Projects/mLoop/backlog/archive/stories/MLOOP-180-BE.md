---
id: MLOOP-180-BE
jira_key: ''
epic_key: EPIC-18-EVIDENCE-PARITY-PHASE3
type: Feature
title: Extension du Schema EvidencePackEngine vers la Parité Phase 2 (5 Champs de
  Richesse)
origin: DIRECT_REQUIREMENT
source_ref: epic_evidence_impl_decisions.md
macro_size: L
status: DONE
grill_me: DONE
invest_score: 0/6
layer: backend
blocked_by: []
created_at: '2026-09-22'
content_hash: a7d2aff6082bfc4e
ttl_cycles: 3
---

# 📖 MLOOP-180-BE : Extension du Schema EvidencePackEngine vers la Parité Phase 2 (5 Champs de Richesse)

## 1. Intention Métier (User Story)
**En tant qu'** Architecte mLoop,  
**je veux** étendre le schema EvidencePackEngine avec les 5 champs manquants de parité (`verbatim_extracts`, `implementation_decisions`, `declarative_contracts`, `epistemic_audit` riche, `conflict_matrix`),  
**afin de** rendre le pack Phase 3 aussi éloquent que le dossier de preuves Phase 2.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `epic_evidence_impl_decisions.md` (Réf : Audit comparatif Phase 2 vs Phase 3 — 22/09/2026)
- **Hypothèse de Chiffrage Retenue** : Extension dataclass/dict + validation + tests unitaires sur 5 champs
- **Enveloppe Macro Estimée** : L (fourchette de 2-3 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Champ `verbatim_extracts` : liste de `{source_file, lines: [start, end], quote, established_fact}`
- Champ `implementation_decisions` : liste de `{decision_id, category, rationale, alternatives_considered, timestamp}`
- Champ `declarative_contracts` : références aux routes/CTA réellement utilisés (zéro invention)
- Enrichissement `epistemic_audit` : exigence de `what_it_does_not_prove` non vide pour `VALIDATED`
- Champ `conflict_matrix` : résolution documentée des divergences récit vs code
- Rétrocompatibilité : les 5 champs `Optional` — packs existants restent valides

### Out-of-Scope (Macro)
- Intégration harnais Phase 3 Build (couvert par MLOOP-181-BE)
- Backfill rétroactif (couvert par MLOOP-182-BE)
- Modification du gabarit story_template.md

---

## 4. Contexte métier

La Phase 3 Build génère actuellement des EvidencePacks qui, bien que structurellement complets, sont **épistémiquement pauvres** : aucune citation verbatim ancrée, aucune décision d'implémentation tracée, aucun contrat déclaratif référencé. Cet écart avec les dossiers de preuves Phase 2 fragilise le Universal Dev Handoff (AGENTS.md §1), viole l'ADR-0361 (interdiction des intentions abstraites) et prive le flow RHO du contexte nécessaire pour proposer des correctifs cohérents.


---

## Critères d'acceptation

- [ ] **CA-1** : Les 5 champs (`verbatim_extracts`, `implementation_decisions`, `declarative_contracts`, `epistemic_audit`, `conflict_matrix`) sont présents dans le schema avec typage strict.
- [ ] **CA-2** : Chaque `verbatim_extracts` porte un ancrage ligne `[start, end]`, une `quote` non vide et un `established_fact`.
- [ ] **CA-3** : Les catégories de `implementation_decisions` sont fermées (rejet hors liste : architecture|pattern|refactoring|performance|security|tooling|testing).
- [ ] **CA-4** : `epistemic_audit.what_it_does_not_prove` non vide exigé pour un pack `VALIDATED`.
- [ ] **CA-5** : Les 71 packs existants sans les 5 champs restent parsables (rétrocompatibilité prouvée par test).
- [ ] **CA-6** : Aucun contrat API n'est inventé — `[API à définir]` + `OQ-001` pour toute route inconnue (Zéro Fausse Route).

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : ce récit est une extension de schema interne (`src/pipelines/evidence_pack.py`) — **aucune route API n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-001` dans `docs/04-transverse/00-questions-ouvertes.md` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

---

## 5. Piliers Gherkinherkin

### Pilier 1 : Nominal
```gherkin
Scénario: Génération d'un pack de parité
  Étant donné un récit Phase 3 avec 2 décisions, 3 citations et 1 contrat
  Quand EvidencePackEngine.extract_evidence est exécuté
  Alors implementation_decisions contient 2 entrées typées
  Et verbatim_extracts contient 3 citations avec leurs numéros de ligne
  Et declarative_contracts référence le contrat sans l'inventer
```

### Pilier 2 : Exceptions
```gherkin
Scénario: Rejet d'une catégorie de décision hors liste fermée
  Étant donné une décision avec category="random_choice"
  Quand la validation du schema est exécutée
  Alors une ValueError est levée mentionnant les catégories autorisées
  Et le pack n'est pas persisté

Scénario: Réjection d'une citation sans ancrage ligne
  Étant donné un verbatim_extract avec lines=null
  Quand la validation est exécutée
  Alors le champ est rejeté avec le message "ancrage ligne obligatoire (ADR-0320)"
```

### Pilier 3 : Résilience & Mode Dégradé
```gherkin
Scénario: Pack sans les 5 champs (rétrocompatibilité legacy)
  Étant donné un pack existant généré avant l'extension (sans implementation_decisions)
  Quand il est parsé par le nouveau schema
  Alors le parsing réussit sans erreur
  Et les 5 champs sont initialisés à null/vide
  Et le hash SHA-256 d'origine est conservé

Scénario: Fichier source citation introuvable sur disque
  Étant donné un verbatim_extract référençant un fichier supprimé
  Quand la réconciliation des sources est exécutée
  Alors le champ confiance est dégradé à LOW (0.25)
  Et une alerte "source_unresolved" est ajoutée au pack
  Et le pack reste parsable (mode dégradé, pas de crash)

Scénario: Timeout de calcul SHA-256 sur source volumineuse
  Étant donné une source de 500 Mo
  Quand le hashage dépasse le timeout autorisé
  Alors le hash est null
  Et un log DEBUG contextualisé est émis (ADR-0369 Zero-Silent-Pass)
  Et la validation continue sans ce hash
```

### Pilier 4 : UX (Retour Utilisateur / Observabilité)
```gherkin
Scénario: Score de confiance reflétant la richesse du pack
  Étant donné un pack avec 0 citation et 0 décision
  Quand confidence_score est calculé
  Alors le score est plafonné à MEDIUM (0.75)
  Et le détail "richness_penalty: no_citations" est exposé dans epistemic_audit

Scénario: Rapport de régénération traçable
  Étant donné un pack régénéré avec les 5 nouveaux champs
  Quand le rapport WikiFix est écrit
  Alors il mentionne le nombre de décisions, citations et contrats injectés
  Et le timestamp UTC de la régénération
```

---

## 6. Décisions du Grill 1:1 Intégrées (6/6)

- **Déc. 1 (Granularité)** : citations **hybrides D** — 1/fichier modifié + 1/décision.
- **Déc. 2 (Sources)** : tournoi + TDD + fact_dossier + plan + hook `record_decision()`.
- **Déc. 3 (Emplacement)** : `implementation_decisions` dans `<SID>_evidence.json`, `verbatim_extracts` dans `<SID>_fact_dossier.md`.
- **Déc. 4 (Gate 5)** : blocking **new only** — legacy EPIC 10→17 exempté (warning), nouveau `DONE_TESTED`+ exige ≥ 1 citation.
- **Déc. 5 (Confiance)** : multiplicateur `score × (0.7 + 0.3 × min(1, richesse/max))` + `richness_penalty` dans `epistemic_audit`.
- **Déc. 6 (Legacy)** : **EPIC 1-9 strictement exclus** — focus prioritaire EPIC 10→18, code parfait exigé.

---

## 7. Zones d'Ombre Restantes (post-Grill)

- ❓ TypedDict strict vs Dict flexible pour les 5 champs ?
- ❓ Hash de cohérence par citation (détection altération) ?
- ❓ Borne max sur `implementation_decisions` (surcharge pack) ?
- ❓ Pack 0 citation : rejet `VALIDATED` ou `VALIDATED_PARTIAL` ?
