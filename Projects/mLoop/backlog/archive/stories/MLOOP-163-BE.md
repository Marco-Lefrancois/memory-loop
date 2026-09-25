---
id: MLOOP-163-BE
jira_key: ''
epic_key: EPIC-15-DIRECTIVES-SSOT-ENFORCEMENT
type: Feature
title: Contrôle de Pré-Vol d'Intégrité des Directives Projet et Sémantique Tri-État
  du Score
tags:
- core
- vibe-check
- guardrail
- governance
origin: GRILL_PROJECT
source_ref: epic_project_directives_ssot_enforcement.md
macro_size: M
status: DONE_TESTED
grill_me: DONE
layer: backend
invest_score: 6/6
created_at: '2026-09-22'
blocked_by:
- MLOOP-160-BE
- MLOOP-161-BE
ttl_cycles: 4
---
# Contrôle de Pré-Vol d'Intégrité des Directives Projet et Sémantique Tri-État du Score

---

## Description
**En tant que** Guardrail de pré-vol du framework mLoop,  
**je veux** vérifier, uniquement lorsqu'un projet déclare un répertoire de directives, que ses lois d'affaires et techniques sont non vides et référencent une source de vérité canonique, tout en distinguant trois états de résultat pour ne pas bloquer inutilement,  
**afin de** détecter mécaniquement les projets dont la gouvernance documentaire est incomplète, sans jamais pénaliser les projets qui n'utilisent pas ce standard.

---

## Contexte & Périmètre

### Contexte Métier
Le guardrail de pré-vol exécute une série de contrôles déterministes avant toute action. Aucun de ces contrôles ne vérifie la présence ou la prise en compte des directives d'un projet. Par ailleurs, le calcul actuel du verdict global traite tout état non réussi comme un échec, ce qui empêche d'introduire des contrôles d'avertissement non bloquants. Ce récit ajoute le contrôle des directives et corrige la sémantique du verdict pour distinguer réussite, avertissement et échec.

### In-Scope
- Ajout d'un nouveau contrôle de pré-vol vérifiant l'intégrité des directives projet, conditionnel à leur présence.
- Correction du calcul du verdict global pour distinguer trois états : réussite, avertissement non bloquant, échec bloquant.
- Comportement strictement non régressif pour les projets dépourvus de répertoire de directives.

### Out-of-Scope
- La suite de tests et le réalignement des tests existants (couverts par le récit de tests).
- Le contrôle d'ancrage visuel des récits frontend (couvert par son récit dédié, qui consomme la même sémantique tri-état).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*

#### 1. Contrôle Conditionnel d'Intégrité des Directives
* **Entrée Métier** : Le répertoire du projet actif et son éventuel répertoire de directives.
* **Règles d'admissibilité & Validation** : Si le répertoire de directives est absent, le contrôle réussit immédiatement. S'il est présent, les lois d'affaires et techniques doivent exister, être non vides, et l'une d'elles au moins doit référencer un chemin de source de vérité canonique.
* **Traitement & Algorithme Métier** : Lecture sécurisée des fichiers de directives et du fichier de contexte du projet, détection d'une mention de source de vérité canonique, agrégation du verdict du contrôle.
* **Résultat Métier & Mutations** : Un état de contrôle réussi lorsque tout est conforme ou lorsque les directives sont absentes, un état d'avertissement lorsque des directives présentes sont incomplètes.
* **Cas de Rejet Métier** : Aucun échec bloquant n'est jamais émis par ce contrôle. Une non-conformité produit exclusivement un avertissement.

#### 2. Sémantique Tri-État du Verdict Global
* **Entrée Métier** : L'ensemble des états de contrôle collectés durant le pré-vol.
* **Règles d'admissibilité & Validation** : Le verdict global est considéré valide tant qu'aucun contrôle n'est en échec bloquant, les avertissements n'invalidant pas le verdict.
* **Traitement & Algorithme Métier** : Le calcul distingue les trois états et compte séparément les réussites, les avertissements et les échecs, avec un affichage lisible de la répartition.
* **Résultat Métier & Mutations** : Un verdict global qui n'est plus abaissé par la simple présence d'avertissements, appliqué au fil de l'eau à chaque projet ré-audité.
* **Cas de Rejet Métier** : Un seul contrôle en échec bloquant suffit à invalider le verdict global.

---

## Règles d'affaires

- **[Conditionnalité Stricte Sans Régression]** : Si le répertoire de directives d'un projet est absent, le contrôle réussit immédiatement avec un message indiquant que les directives ne sont pas applicables, sans aucun impact sur les projets existants qui n'ont pas ce répertoire.
- **[Contrôle de Contenu Minimal]** : Lorsque les directives existent, le contrôle vérifie la présence et le caractère non vide des lois d'affaires et techniques, la présence du fichier de contexte du projet, et au moins une mention d'un chemin de source de vérité canonique ou d'une déclaration de hiérarchie.
- **[Sévérité Non Bloquante]** : Toute non-conformité produit un avertissement, jamais un échec, à l'image du contrôle de certification de sprint existant.
- **[Sémantique Tri-État du Verdict]** : Le verdict global distingue réussite, avertissement non bloquant et échec bloquant. Les avertissements ne font pas basculer le verdict global en échec. Le recalcul s'applique projet par projet au fil des ré-audits, sans exigence de parité de score entre projets.
- **[Robustesse d'Exécution]** : Toute lecture de fichier est protégée contre les erreurs, avec journalisation contextualisée, encodage explicite et absence d'accès à une ressource hors d'un gestionnaire de contexte.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit modifie un pipeline interne du guardrail de pré-vol. Aucune API HTTP n'est exposée : les interfaces sont des appels de fonction Python internes. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-163-01**.

| Méthode | Interface interne | Finalité |
|:---|:---|:---|
| Fonction | `src.pipelines.vibe_check:run_vibe_check` | Guardrail de pré-vol ; ajout du contrôle des directives + calcul tri-état du verdict |
| Contrôle | Nouveau bloc de contrôle « Intégrité Directives Projet & SSOT » | Vérification conditionnelle non bloquante |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-163-01** : Ce récit modifie une fonction Python interne du guardrail. Aucune API HTTP n'est exposée ni consommée. La signature de sortie (`dict`) reste inchangée. **[API de soumission à définir — sans objet pour un pipeline interne]**

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Backlog d'Épopée** : [`backlog/epic_project_directives_ssot_enforcement.md`](../epics/epic_project_directives_ssot_enforcement.md)
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-163-BE_fact_dossier.md`](../../memory/evidence/MLOOP-163-BE_fact_dossier.md)
- 📄 **Récits Préalables** : Protocole Normatif de Hiérarchie SSOT et ADR de Boot Enforcement (récits bloquants amont)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Pipeline de Guardrail de Pré-Vol** : [`src/pipelines/vibe_check.py`](../../../../src/pipelines/vibe_check.py)
- 📜 **Standards de Robustesse Python Senior** : [`standards/protocols/PYTHON_SENIOR_CODING_STANDARDS.md`](../../../../standards/protocols/PYTHON_SENIOR_CODING_STANDARDS.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Contrôle de Pré-Vol d'Intégrité des Directives Projet et Sémantique Tri-État

  # CHEMIN NOMINAL
  Scénario: Projet avec directives conformes
    Étant donné un projet dont les directives d'affaires et techniques sont non vides et référencent la source de vérité canonique
    Quand le guardrail de pré-vol est exécuté
    Alors le contrôle d'intégrité des directives réussit
    Et le verdict global reste valide

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Projet avec directives incomplètes
    Étant donné un projet dont les directives existent mais ne déclarent aucune source de vérité canonique
    Quand le contrôle d'intégrité des directives s'exécute
    Alors il émet un avertissement
    Et il ne produit jamais d'échec bloquant

  # RÉSILIENCE TECHNIQUE & NON-RÉGRESSION
  Scénario: Projet sans répertoire de directives
    Étant donné un projet dépourvu de répertoire de directives
    Quand le guardrail de pré-vol est exécuté
    Alors le contrôle réussit avec le message indiquant que les directives ne sont pas applicables
    Et le comportement du guardrail reste inchangé pour ce projet

  # UX, OBSERVABILITÉ & SÉMANTIQUE TRI-ÉTAT
  Scénario: Un avertissement n'invalide pas le verdict global
    Étant donné un pré-vol comportant un contrôle en avertissement et aucun contrôle en échec
    Quand le verdict global est calculé
    Alors le verdict reste valide
    Et la répartition affiche distinctement les réussites, les avertissements et les échecs
```