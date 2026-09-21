# 📋 Checklist d'Audit Phase 4 : VALIDATE / QA — mLoop

**Statut** : Document de Référence Opérationnel
**Norme** : ADR-0383 (Deterministic Phase 4 QA Certification Harness)
**Date de Révision** : 21 septembre 2026

---

## 🎯 Objectif

Cette checklist guide l'audit Phase 4 de chaque récit. Elle couvre les **5 axes d'audit ciblés** et identifie les **red flags** spécifiques à cette phase.

---

## 1. Axes d'Audit Ciblés Phase 4

### Axe 1 : Véracité Factuelle (NLI Gate - L4)
- [ ] Chaque énoncé factuel du récit est étayé par un document source dans `docs/`.
- [ ] Un certificat NLI positif (`nli_verdict: SUPPORTED`) existe dans `memory/evidence/<STORY_ID>_fact_dossier.md`.
- [ ] Aucune hallucination n'a été injectée (confrontation avec `fact-search`).
- [ ] Les références aux APIs et endpoints sont vérifiables dans la documentation source.

### Axe 2 : Intégrité Structurelle (AST Gate - L2)
- [ ] Le récit respecte strictement le gabarit `story_template.md` (4 Piliers Gherkin).
- [ ] Zéro violation C1-C7 détectée par `struct-check --strict`.
- [ ] Zéro pseudo-code applicatif (respect de l'herméticité ADR-0319).
- [ ] Les sections H2 sont complètes et sans omission.

### Axe 3 : Anti-Tautologie (Leakage Gate - L5)
- [ ] Zéro critère d'acceptation qui se vérifie lui-même (tautologie).
- [ ] Zéro fuite de spécification (informations sensibles exposées).
- [ ] Zéro référence circulaire entre critères.
- [ ] Chaque critère est atomique, mesurable et actionnable.

### Axe 4 : Cohérence Métrique (CEL Gate - L3)
- [ ] Chaque critère d'acceptation est validé par le moteur CEL.
- [ ] Les seuils de validation sont cohérents avec la criticité du récit.
- [ ] Les critères UX sont spécifiés (Design-Arrivée-Feedback-Erreur).

### Axe 5 : Contre-Audit Sémantique (Sentinel LLM - L6)
- [ ] L'agent Sentinel (Avocat du Diable) a émis un avis contradictoire.
- [ ] Les angles morts identifiés ont été documentés et traités.
- [ ] La cohérence métier est validée (Ubiquitous Language).
- [ ] Les 4 Piliers Gherkin couvrent tous les scénarios.

---

## 2. Fichiers Critiques du Pipeline Phase 4

| Fichier | Rôle | Commande de Vérification |
|:---|:---|:---|
| `src/pipelines/struct_checker.py` | Gatekeeper structurel Read-Only | `python src/swarm.py struct-check --story <ID> --strict` |
| `src/pipelines/rubber_duck.py` | Agent Sentinel contre-audit | `python src/swarm.py rubber-duck --story <ID>` |
| `src/pipelines/wikifix.py` | Audit cohérence liens/références | `python src/swarm.py wikifix --project <PROJET>` |
| `src/engine/fact_check/` | Moteur NLI certification | `python src/swarm.py fact-check --story <ID>` |
| `src/engine/fact_search/` | Index FTS5 haute précision | `python src/swarm.py fact-search --query "<concept>"` |
| `src/pipelines/completion_gate.py` | Exécution portails acceptation | `python src/swarm.py gate-approve --gate 4` |
| `src/pipelines/vibe_check.py` | Guardrail pré-vol session | `python src/swarm.py vibe-check --project <PROJET>` |
| `memory/evidence/<STORY_ID>_evidence.json` | EvidencePack preuves | Lecture directe |
| `memory/evidence/<STORY_ID>_fact_dossier.md` | Dossier preuves NLI | Lecture directe |

---

## 3. Red Flags Spécifiques Phase 4

### 🚨 Red Flags Critiques (Bloquants Gate 4)

| Red Flag | Symptôme | Action Corrective |
|:---|:---|:---|
| **NLI Verdict REJECTED** | Un énoncé factuel n'est pas supporté par les sources | Confronter avec `fact-search`, corriger ou supprimer l'énoncé |
| **Struct-Check FAIL** | Violation C1-C7 détectée | Corriger la structure selon le gabarit `story_template.md` |
| **Leakage Detected** | Fuite de spécification ou tautologie | Reformuler le critère pour le rendre atomique et mesurable |
| **Sentinel Veto** | L'agent Sentinel émet un veto contradictoire | Traiter l'angle mort identifié et re-soumettre à audit |
| **Missing EvidencePack** | `memory/evidence/<STORY_ID>_evidence.json` inexistant | Générer l'EvidencePack avec `python src/swarm.py evidence-pack --story <ID>` |

### ⚠️ Red Flags de Qualité (À Traiter)

| Red Flag | Symptôme | Action Corrective |
|:---|:---|:---|
| **Critères Vagues** | Critères d'acceptation non mesurables | Reformuler avec des critères SMART (Spécifiques, Mesurables, Atteignables, Réalistes, Temporellement définis) |
| **Piliers Incomplets** | Un des 4 Piliers Gherkin est vide | Rédiger le pilier manquant selon le format standard |
| **Références Cassées** | Liens internes ou externes morts | Corriger les liens avec `python src/swarm.py wikifix` |
| **Hash Invalide** | `qa_certification_hash` non conforme | Régénérer le hash avec la commande `qa-certify` |
| **Timeline Incohérente** | Timestamps incohérents dans les preuves | Vérifier l'ordre chronologique des événements |

---

## 4. Séquence d'Audit Phase 4

```bash
# Étape 1 : Audit Structurel
python src/swarm.py struct-check --story <STORY_ID> --strict

# Étape 2 : Contre-Audit Sentinel
python src/swarm.py rubber-duck --story <STORY_ID>

# Étape 3 : Certification NLI
python src/swarm.py fact-check --story <STORY_ID>

# Étape 4 : Détection Fuites
python src/swarm.py check-leakage --story <STORY_ID>

# Étape 5 : Cohérence Liens
python src/swarm.py wikifix --project <PROJET>

# Étape 6 : Certification Finale
python src/swarm.py qa-certify --story <STORY_ID>
```

---

## 5. Critères de Succès Gate 4

Pour qu'un récit passe la Gate 4, **tous les critères suivants doivent être satisfaits** :

- [ ] **5/5 Verrous Gate 4** validés (Pytest, AST, CEL, NLI, Leakage).
- [ ] **EvidencePack** complet et à jour.
- [ ] **Certificat NLI** positif émis.
- [ ] **Rapport WikiFix** sans lien mort.
- [ ] **Aucun Red Flag Critique** non traité.
- [ ] **Hash de Certification** généré et valide.

---

*Document généré dans le cadre de MLOOP-120-BE — Fondations Normatives Phase 4.*
