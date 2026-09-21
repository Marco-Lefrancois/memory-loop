# 🏛️ ADR-0383 : Harnais Déterministe de Certification QA Phase 4

- **Statut** : ACCEPTED
- **Date** : 21 septembre 2026
- **Décideurs** : Marco (Utilisateur) & mLoop Agent
- **Amendé par** : ADR-0375 (Cycle de Vie en 5 Phases)

---

## Contexte & Problème

La Phase 4 (VALIDATE / QA) du cycle de vie mLoop nécessite un **harnais de certification déterministe** capable de garantir la véracité factuelle, l'absence de fuites de spécification et la conformité sémantique des récits avant clôture. Sans ce harnais, les contrôles qualité reposent sur des vérifications manuelles sujettes à l'erreur humaine, ce qui compromet l'intégrité de la chaîne de validation.

Le problème se décline en 3 axes :
1. **Véracité Factuelle** : Comment certifier qu'aucune hallucination n'a été injectée dans les récits ?
2. **Intégrité Structurelle** : Comment garantir l'absence de fuites tautologiques et de violations de template ?
3. **Traçabilité** : Comment produire une preuve cryptographique de la certification pour chaque récit ?

---

## Décision Retenue

Adopter un **harnais de certification déterministe en 6 niveaux** pour la Phase 4, chacun couvrant un axe spécifique de qualité.

### Architecture du Harnais en 6 Niveaux

| Niveau | Nom | Type | Description |
|:---:|:---|:---:|:---|
| **L1** | Pytest Unit Gate | Déterministe | Tests unitaires et d'intégration des pipelines Phase 4 (`test_struct_checker.py`, `test_rubber_duck_api_routes.py`, `test_fact_check_engine.py`, `test_nli_polarity.py`, `test_verification_leakage_gate.py`). |
| **L2** | AST Structure Guard | Déterministe | Audit statique des récits via `struct-check --strict` : validation des violations C1-C7, conformité aux gabarits, absence de pseudo-code applicatif. |
| **L3** | CEL Expression Engine | Déterministe | Moteur d'expressions conditionnelles linguistiques pour les critères d'acceptation : vérification que chaque critère est atomique, mesurable et non tautologique. |
| **L4** | NLI Inference Certifier | Semi-déterministe | Moteur d'inférence en langage naturel (NLI) pour certifier la véracité factuelle de chaque énoncé par rapport aux documents sources (`docs/`). Émet un certificat de véracité par récit. |
| **L5** | Leakage Detection Gate | Déterministe | Détection des fuites de spécification : critères qui se vérifient eux-mêmes (tautologies), informations sensibles exposées, références circulaires. |
| **L6** | Sentinel LLM Audit | Non-déterministe | Contre-audit sémantique contradictoire via l'agent Sentinel (Avocat du Diable). Vérifie la cohérence métier, les angles morts et la complétude des 4 Piliers Gherkin. |

### 5 Verrous Bloquants Gate 4

Chaque récit doit satisfaire **les 5 verrous suivants** avant de pouvoir passer la Gate 4 :

1. **Verrou 1 — Pytest Gate** : `uv run pytest tests/test_struct_checker.py tests/test_rubber_duck_api_routes.py tests/test_fact_check_engine.py tests/test_nli_polarity.py tests/test_verification_leakage_gate.py` doit retourner 0 erreurs.

2. **Verrou 2 — AST Gate** : `python src/swarm.py struct-check --story <STORY_ID> --strict` doit retourner `PASS` sans violation bloquante.

3. **Verrou 3 — CEL Gate** : Chaque critère d'acceptation du récit doit être validé par le moteur CEL comme atomique et non tautologique.

4. **Verrou 4 — NLI Gate** : Un certificat de véracité NLI positif doit être émis pour chaque énoncé factuel du récit (`memory/evidence/<STORY_ID>_fact_dossier.md` doit exister et contenir `nli_verdict: SUPPORTED`).

5. **Verrou 5 — Leakage Gate** : `python src/swarm.py check-leakage --story <STORY_ID>` doit retourner `CLEAN` (zéro fuite détectée).

### Modèle GateApprovalRecord

Chaque passage de Gate 4 produit un enregistrement `GateApprovalRecord` avec le schéma suivant :

```json
{
  "gate_id": "GATE_4_QA_CERTIFICATION",
  "story_id": "<STORY_ID>",
  "timestamp": "2026-09-21T14:30:00Z",
  "approver": "QA_Lead@mLoop",
  "verdict": "APPROVED",
  "qa_certification_hash": "sha256:<hash_du_contenu_&_des_preuves>",
  "levels": {
    "L1_pytest": { "status": "PASS", "tests_run": 8, "failures": 0 },
    "L2_ast": { "status": "PASS", "violations": 0 },
    "L3_cel": { "status": "PASS", "criteria_validated": 5 },
    "L4_nli": { "status": "PASS", "certificates_issued": 3, "verdict": "SUPPORTED" },
    "L5_leakage": { "status": "PASS", "leaks_found": 0 }
  },
  "evidence_refs": [
    "memory/evidence/<STORY_ID>_evidence.json",
    "memory/evidence/<STORY_ID>_fact_dossier.md"
  ],
  "notes": "Certification Phase 4 complète. 5/5 verrous Gate 4 satisfaits."
}
```

### Format Handoff Phase 4

Le livrable de clôture Phase 4 pour chaque récit comprend :

1. **Résumé Lisible** : Un bloc Markdown synthétique dans le récit (après `## Scénarios de test`) résumant le résultat de certification :
   ```markdown
   ## Certification Phase 4
   - **Statut** : ✅ CERTIFIÉ
   - **Hash de Certification** : `sha256:...`
   - **Niveaux Validés** : L1 ✅ | L2 ✅ | L3 ✅ | L4 ✅ | L5 ✅ | L6 ✅
   - **Date** : 2026-09-21T14:30:00Z
   ```

2. **Lien Vers Preuves** : Référence vers les artefacts-sidecar :
   - `memory/evidence/<STORY_ID>_evidence.json`
   - `memory/evidence/<STORY_ID>_fact_dossier.md`
   - `memory/plan/implementation_plan_<STORY_ID>.md`

---

## Conséquences

### Positives
- **Zéro Hallucination** : Le niveau NLI (L4) garantit que chaque énoncé factuel est certifié par rapport aux documents sources.
- **Zéro Tautologie** : Le niveau Leakage (L5) élimine les critères d'acceptation qui se vérifient eux-mêmes.
- **Traçabilité Cryptographique** : Le `qa_certification_hash` fournit une preuve non répudiable de la certification.
- **Séparation des Responsabilités** : Chaque niveau a un rôle unique et indépendant, facilitant le diagnostic en cas d'échec.
- **Complémentarité Déterministe/LLM** : Les niveaux L1-L5 sont déterministes (reproductibles), tandis que L6 apporte le jugement sémantique non déterministe nécessaire.

### Négatives / Risques
- **Complexité d'Intégration** : Le harnais en 6 niveaux nécessite une orchestration rigoureuse. Mitigation : `python src/swarm.py qa-certify --story <ID>` centralise l'exécution.
- **Coût NLI** : Le niveau L4 (NLI) nécessite des appels LLM. Mitigation : batch processing et cache des certificats.
- **Maintenance des Seuils** : Les seuils de validation CEL et NLI peuvent nécessiter un étalonnage périodique. Mitigation : `python src/swarm.py doctor --skills` audit les seuils.

---

*Enregistré suite à l'implémentation du harnais de certification Phase 4 (MLOOP-120-BE).*
