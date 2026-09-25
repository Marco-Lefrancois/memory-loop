---
id: MLOOP-241-BE
jira_key: ''
epic_key: EPIC-24-SKILLS-EVAL-HARNESS
type: Feature
title: "Référentiel Golden Datasets d'Évaluation pour les 39 Skills"
tags:
- skills
- eval
- golden-dataset
- test-cases
- backend
origin: SPEC_SLICING
source_ref: EPIC-24-§4.2
macro_size: L
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-24'
layer: backend
blocked_by:
- MLOOP-240-BE
created_at: '2026-09-24'
updated_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-241-BE : Référentiel Golden Datasets d'Évaluation pour les 39 Skills

## Description
**En tant qu'** Évaluateur Qualité de la Plateforme mLoop,
**je veux** un jeu de données de référence (Golden Datasets) constitué d'au minimum 3 cas de test par skill (nominal, limite, adversarial) dans un format uniforme JSON, persisté sous `memory/evals/skills/<skill_name>/cases.json`,
**afin d'** alimenter le `SkillEvalEngine` (MLOOP-240-BE) avec des assertions déterministes reproducibles et d'éviter les régressions silencieuses lors des modifications de manifestes.

---

## Contexte & Périmètre

### Contexte Métier
Sans Golden Datasets concrets, le `SkillEvalEngine` ne peut auditer que la syntaxe statique des manifestes. Ce récit crée le référentiel de vérité terrain : pour chaque des 39 skills sous `.agents/skills/*/SKILL.md`, un fichier `cases.json` décrit les cas de déclenchement attendus, les cas limites et les cas adversariaux.

**Décisions Grill (2026-09-24) :**
- **Format uniforme** pour toutes les skills, avec champ optionnel `category` (`TRIGGER_ONLY`, `EXECUTION_FLOW`, `META_ORCHESTRATION`) pour les 8 `HEAVY_META_SKILLS`.
- **Minimum 3 cas par skill** : 1 nominal, 1 limite, 1 adversarial = 117 cas minimum au total.
- **HEAVY_META_SKILLS** (`zero-blindspot-spec`, `handoff`, `router`, `sentinel`, `rubber-duck`, `calibrate`, `obsidian-canvas`, `visual-excalidraw`, `visual-mermaid`) : couverture **statique seule**, leurs cas `.json` ont le champ `"behavioral": false`.

### In-Scope
- Génération du script `scripts/generate_skill_datasets.py` produisant les squelettes `cases.json` pour les 39 skills.
- Rédaction manuelle ou semi-automatique des cas de test réels pour les 39 skills.
- Format canonique JSON défini et validé par un schéma JSON Schema (`standards/schemas/skill_eval_case_schema.json`).
- Persistance sous `memory/evals/skills/<skill_name>/cases.json`.
- 8 `HEAVY_META_SKILLS` : fichier `cases.json` créé avec `"behavioral": false` et uniquement des assertions statiques sur le manifeste.

### Out-of-Scope
- Exécution de l'évaluation (responsabilité de MLOOP-240-BE).
- Évaluation comportementale LLM (différée à EPIC-24-v2).
- Génération automatique des cas par LLM sans revue humaine.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Schéma Canonique des Cas de Test
* **Entrée Métier** : Manifeste `SKILL.md` d'une compétence.
* **Règles d'admissibilité** : Chaque `cases.json` doit respecter `standards/schemas/skill_eval_case_schema.json` (validé par `jsonschema`).
* **Traitement** : Script `generate_skill_datasets.py` parcourt `.agents/skills/*/` et génère un squelette si `cases.json` absent.
* **Résultat** : Fichier `cases.json` valide pour chacune des 39 skills.
* **Cas de Rejet** : Schéma invalide → erreur bloquante avec message explicite.

#### 2. Structure du fichier cases.json
```json
{
  "skill_name": "grill",
  "version": "1.0",
  "behavioral": true,
  "cases": [
    {
      "id": "TC-GRILL-01",
      "type": "nominal",
      "description": "L'utilisateur demande une session grill sur une épopée",
      "input": "grill EPIC-24",
      "expect_triggered": true,
      "expect_static": {
        "keywords_present": ["grill", "épopée", "EPIC"],
        "keywords_absent": []
      }
    },
    {
      "id": "TC-GRILL-02",
      "type": "limite",
      "description": "Requête ambiguë sans nom d'épopée",
      "input": "analyse cette épopée",
      "expect_triggered": false,
      "expect_static": {}
    },
    {
      "id": "TC-GRILL-03",
      "type": "adversarial",
      "description": "Trigger pollution — requête sur code sans rapport",
      "input": "débogue ce fichier Python",
      "expect_triggered": false,
      "expect_static": {}
    }
  ]
}
```

### Contrats d'Échange API
- Aucun endpoint réseau. Fichiers JSON lus par `SkillEvalEngine`.

---

## Règles d'affaires

- **Couverture minimale obligatoire** : Toute skill sans `cases.json` déclenche un `WARNING` dans `skill-eval` (non bloquant mais signalé).
- **HEAVY_META_SKILLS** : `"behavioral": false` obligatoire dans leur `cases.json`. Toute assertion comportementale dans ces fichiers est ignorée.
- **Immutabilité des cas validés** : Un cas de test ne peut être modifié sans incrémenter `version` dans le JSON et noter le motif dans le commit message.
- **Parité skill count** : Le nombre de dossiers dans `memory/evals/skills/` doit être égal au nombre de skills dans `.agents/skills/` (39/39). Vérifiable par assertion dans les tests.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Skills existantes** : `.agents/skills/*/SKILL.md` (39 skills)
- 🏛️ **ADR** : [ADR-0348](../../../standards/adr-system/0348-wikiskill-tri-layer-evolution.md) · [ADR-0308](../../../standards/adr-system/0308-mcp-prompts-and-evals-engine.md)
- 📋 **Epic** : [`epics/epic_skills_eval_harness.md`](../epics/epic_skills_eval_harness.md)
- 📄 **Dépendance aval** : MLOOP-240-BE (consomme les cases.json)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Référentiel Golden Datasets pour les 39 Skills

  Scénario: Génération des squelettes cases.json pour toutes les skills
    Étant donné 39 dossiers sous .agents/skills/
    Quand j'exécute "python scripts/generate_skill_datasets.py"
    Alors 39 fichiers cases.json sont créés sous memory/evals/skills/
    Et chaque fichier respecte le schéma standards/schemas/skill_eval_case_schema.json
    Et les 8 HEAVY_META_SKILLS ont "behavioral": false

  Scénario: Validation du schéma — cas invalide
    Étant donné un fichier cases.json avec un champ "type" invalide (ex: "random")
    Quand jsonschema valide ce fichier
    Alors une erreur de validation est levée avec message explicite

  Scénario: Parité skill count
    Étant donné 39 skills sous .agents/skills/
    Quand j'audite memory/evals/skills/
    Alors il y a exactement 39 dossiers (1 par skill)
    Et aucune skill n'est absente du référentiel

  Scénario: Cas adversarial détecte trigger pollution
    Étant donné la skill "grill" et le cas adversarial TC-GRILL-03
    Quand SkillEvalEngine exécute l'assertion statique sur "débogue ce fichier Python"
    Alors expect_triggered = false est confirmé (aucun keyword grill présent)
    Et le cas est marqué PASS dans le rapport
```
