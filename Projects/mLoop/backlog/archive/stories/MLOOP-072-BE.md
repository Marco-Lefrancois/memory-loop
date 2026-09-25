---
id: MLOOP-072-BE
jira_key: '-'
epic_key: EPIC-7-AGENTIC-OBSERVABILITY
status: SHIPPED
type: Feature
title: Normalisation Locale des Événements JSONL OpenInference OTel GenAI
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-7-AGENTIC-OBSERVABILITY] Normalisation Locale des Événements JSONL OpenInference OTel GenAI (MLOOP-072-BE)

## Description
**En tant qu'** Analyste et Développeur du framework mLoop,  
**je veux** que les événements émis dans `memory/events.jsonl` respectent la taxonomie standard OpenInference et OpenTelemetry GenAI tout en restant 100% locaux,  
**afin d'** interroger les traces cognitives avec des moteurs d'analyse modernes (DuckDB, SQLite, Polars) sans aucune fuite de données vers des services tiers.

---

## Contexte
L'industrie de l'observabilité converge vers les conventions sémantiques OpenTelemetry GenAI (`gen_ai.*`) et OpenInference (`openinference.span.kind`).
Actuellement, l'`EventLogger` de mLoop utilise des champs propriétaires (`event_type`, `agent`, `details`).
Ce récit adapte `src/utils/event_logger.py` pour émettre des spans structurés compatibles (types `AGENT`, `TOOL`, `LLM`, `CHAIN`, attributs `gen_ai.agent.name`, `trace_id`, `span_id`) dans notre fichier JSONL local souverain, garantissant l'interopérabilité sans dépendance SaaS.

---

## Opérations API & Logique Backend

### Matrice des Opérations Backend
| Opération Métier | Contrat / Trigger | Validation & Préconditions | Succès Observable | Gestion Erreurs |
| :--- | :--- | :--- | :--- | :--- |
| **[Émission Span Normalisé]** | `log_event(span_kind, agent_id, details, model=None, tokens=None)` | `span_kind` valide dans {AGENT, TOOL, LLM, CHAIN} | Ligne JSONL conforme ajoutée sous `memory/events.jsonl` | Fallback sur span générique si type inconnu |
| **[Propagation Trace W3C]** | `get_current_trace_context()` | Contexte de thread ou session actif | Tuple `(trace_id, parent_span_id)` valide | Génération d'un nouveau `trace_id` si racine |
| **[Requêtage Local Déterministe]** | `query_events(filter_kind=None, limit=50)` | Fichier JSONL existant et intègre | Liste ordonnée antéchronologique des spans | Gestion résiliente sur ligne corrompue |

---

## Règles d'affaires
* **[Souveraineté Pure et Cloisonnement Local]** : Aucune trace, prompt ou métrique d'événement ne doit être transmise par réseau sortant. L'écriture se fait exclusivement en local dans `memory/events.jsonl` et `Projects/<nom>/memory/events.jsonl`.
* **[Conformité des Types de Spans]** : Tout événement doit être qualifié par un `openinference.span.kind` obligatoire parmi `AGENT`, `TOOL`, `LLM`, ou `CHAIN`.
* **[Traçabilité Causale W3C]** : Chaque span fils doit comporter la référence à son `parent_span_id` pour permettre la reconstruction arborescente de la délibération.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Normalisation Locale des Événements JSONL OpenInference OTel GenAI

  # 1. CHEMIN NOMINAL (Happy Path & Attributs Conformes)
  Scénario: Émission d'un span d'outil conforme à la taxonomie OpenInference
    Étant donné un appel d'outil exécuté par l'agent "Sentinel"
    Quand l'EventLogger consigne la fin d'exécution
    Alors la ligne JSONL émise contient "openinference.span.kind" avec la valeur "TOOL"
    Et la ligne contient "gen_ai.agent.name" avec la valeur "Sentinel"
    Et un identifiant W3C "trace_id" et "span_id" est présent

  # 2. EXCEPTIONS & REJETS MÉTIER (Gestion d'un Type de Span Non Répertorié)
  Scénario: Normalisation automatique d'un type d'événement non standard
    Étant donné un composant appelant l'EventLogger avec un type non reconnu
    Quand le logger traite la charge utile
    Alors le champ "openinference.span.kind" est replié proprement sur "CHAIN"
    Et le type d'origine est consigné dans les métadonnées de détail

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Tolérance sur Fichier Verrouillé)
  Scénario: Résilience d'écriture lors d'accès concurrents sur le fichier JSONL
    Étant donné deux agents écrivant simultanément dans memory/events.jsonl
    Quand les écritures se produisent dans le même intervalle de millisecondes
    Alors les lignes sont appendues de manière atomique sans corruption de structure JSON
    Et aucun appel applicatif n'est interrompu

  # 4. UX & OBSERVABILITÉ (Extraction Structurée pour le Tableau de Bord)
  Scénario: Lecture et filtrage des spans récents pour l'interface utilisateur
    Étant donné un historique de 40 événements dans le fichier local
    Quand le tableau de bord interroge les spans filtrés sur le type "AGENT"
    Alors l'API renvoie uniquement les spans de délibération d'agents
    Et la hiérarchie parent-enfant est préservée
```
