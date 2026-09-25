---
id: MLOOP-320-BE
jira_key: ''
epic_key: EPIC-32
type: Enabler
title: Formalisation Normative & Triangulation des Standards
tags:
- governance
- standards
- lifecycle
- fsm
status: DONE_TESTED
layer: backend
invest_score: 6/6
macrostructure: ''
ttl_cycles: 3
validated_by: 'PO (Marco)'
validated_at: '2026-09-25T08:10:18-04:00'
content_hash: 2c686b023c53d24d
---
# Formalisation Normative & Triangulation des Standards

---

## Description
**En tant qu'** Architecte Système et Product Owner mLoop,  
**je veux** inscrire au plus haut niveau normatif le découplage strict entre la modalité d'interaction (Format: `ATOMIC` vs `ROUND`) et le périmètre d'arbitrage (Scope: `STORY` vs `EPIC/PROJECT`), ainsi que la règle d'arrêt formel post-grill et la sanction d'invalidation de cascade,  
**afin d'** interdire définitivement toute dérive cognitive où un agent IA auto-déclencherait la rédaction de multiples récits en cascade suite à un round de questions.

---

## Contexte & Périmètre

### Contexte Métier
Dans le cadre de la gouvernance agentique mLoop, l'élicitation des besoins et l'alignement préalable via le protocole Grill-with-Docs doivent impérativement respecter les frontières d'attention et le budget de contexte. Une ambiguïté sémantique sur le terme « Macro » a conduit les agents à interpréter un format de questions groupées comme un ordre d'écriture en bloc de tout le backlog, contournant l'autorité humaine exclusive de la Gate 2. Ce récit scelle dans les textes normatifs suprêmes les garde-fous interdisant toute cascade non sollicitée et instaurant un mandat unitaire strict d'écriture.

### In-Scope
- Formalisation et publication officielle du standard système [`ADR-0393`](../../../../standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md).
- Amendement de [`STORY_LIFECYCLE_PROTOCOL.md`](../../../../standards/protocols/STORY_LIFECYCLE_PROTOCOL.md) :
  - Définition de la règle d'arrêt formel post-grill (cessation d'écriture et menu d'orientation fermé).
  - Principe du mandat unitaire strict déclenché exclusivement par un choix explicite dans le menu.
  - Sanction de rétrogradation déterministe en `DRAFT` avec invalidation du hash en cas de mutation sauvage.
- Amendement de [`AGENTS.md`](../../../../AGENTS.md) dans la section 4.1 :
  - Consigne inviolable sur l'orthogonalité Format $\times$ Scope.
  - Interdiction absolue d'auto-promotion vers `READY_FOR_DEV`.
- Amendement de [`ADR-0320`](../../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md) (§F) restreignant l'avancement automatique au rituel de grooming unitaire consenti.

### Out-of-Scope
- Modifications du code moteur Python (`GrillEngine`, FSM) déléguées à `MLOOP-322-BE`.
- Sondes Vibe-Check déléguées à `MLOOP-323-BE`.
- Modification du skill grill déléguée à `MLOOP-321-BE`.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Triangulation Normative & Gating de Consentement d'Écriture
* **Entrée Métier** : Les directives issues de l'ADR-0393 et de la session Macro-Grill validée le 25/09/2026.
* **Règles d'admissibilité & Validation** : Conformité stricte aux 7 couches de l'ADR-0376, zéro contradiction avec la machine à états canonique en 5 phases de l'ADR-0391.
* **Traitement & Algorithme Métier** :
  1. Inscrire la définition de l'autorité exclusive de Gate 2 interdisant toute promotion machine vers `READY_FOR_DEV`.
  2. Spécifier la structure de la barrière active post-round : clôture de session d'arbitrage ➔ mise à jour ADR ➔ affichage du menu d'orientation à 3 choix fermés ➔ arrêt des appels d'outils.
  3. Définir le mandat unitaire d'écriture : seul le choix explicite d'un récit par le PO autorise l'écriture de ce seul récit (mono-récit strict).
  4. Spécifier la sanction déterministe : toute story modifiée sans mandat est immédiatement rétrogradée en `DRAFT` avec purge de hash.
* **Résultat Métier & Mutations** : Protocoles et directives suprêmes mis à jour et consolidés sous Git.
* **Cas de Rejet Métier** : Tout texte ou directive laissant entendre qu'un mode de grill autorise la rédaction autonome de stories en série est formellement rejeté.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des interfaces normatives de gouvernance.*

#### Matrice des Contrats API
> 📌 **Clause d'Exemption (ADR-0319 / OQ-320-01)** : Récit d'habilitation normative et constitutionnelle pure modifiant les fichiers Markdown du framework (`standards/adr-system/`, `standards/protocols/`, `AGENTS.md`). Aucune route API HTTP REST exposée, interfaces de transport réseau déclarées à définir comme sans objet externe.

| Contrat / Interface | Type | Direction | Format / Schéma | Description |
| :--- | :---: | :---: | :--- | :--- |
| `RuleEngine.validate_all` | Méthode Python | Interne | `target="standards_protocols"` | Contrôle d'adhérence des règles déclaratives |
| `WikiFixCore.audit_protocols` | Méthode Python | Interne | `strict=True` | Vérification de cohérence documentaire |

---

## Règles d'affaires

- **Orthogonalité Forme et Périmètre** : Le choix d'un format de dialogue groupé en rounds de 2 à 4 questions ne modifie en aucun cas le périmètre de la décision et ne constitue jamais un mandat d'écriture de récits ou de code.
- **Mandat Unitaire Strict d'Écriture** : Après un round macro, l'agent ne dispose d'aucun mandat d'écriture par défaut. Seule la sélection explicite d'une story par l'humain dans le menu d'orientation confère le mandat d'instruire et rédiger ce récit unique.
- **Rétrogradation Déterministe en Cas d'Infraction** : Tout récit promu ou rédigé sans mandat unitaire valide est automatiquement rétrogradé en `DRAFT`, son hash est invalidé, et la session est consignée comme non fiable.
- **Inviolabilité de l'Autorité Gate 2** : Aucun agent, pipeline ou script n'est autorisé à promouvoir un récit au statut `READY_FOR_DEV`. Ce statut est réservé exclusivement à l'arbitrage humain explicite.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-320-BE_fact_dossier.md`](../../memory/evidence/MLOOP-320-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Standard Système Découplage & Anti-Cascade** : [ADR-0393](../../standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md)
- 🏛️ **Protocole de Cycle de Vie des Récits** : [STORY_LIFECYCLE_PROTOCOL.md](../../standards/protocols/STORY_LIFECYCLE_PROTOCOL.md)
- 📋 **Constitution Agentique mLoop** : [AGENTS.md](../../AGENTS.md)
- 🧭 **Alignement Design Tree** : [ADR-0320](../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Formalisation Normative & Triangulation des Standards Anti-Cascade

  # CHEMIN NOMINAL (Happy Path & Arrêt Déterministe)
  Scénario: Clôture de round macro avec arrêt formel et proposition de menu d'orientation
    Étant donné un agent exécutant une session de Grill-Me au format Round sur une épopée
    Et que l'utilisateur a arbitré l'ensemble des questions de la frontière active
    Quand l'agent enregistre les décisions dans l'ADR d'architecture transverse
    Alors l'agent cesse immédiatement tout appel d'outil d'écriture
    Et l'agent affiche le menu d'orientation fermé proposant le découpage DRAFT ou l'analyse d'un récit précis
    Et aucun récit du backlog ne voit son statut promu de manière autonome

  # EXCEPTIONS & REJETS MÉTIER (Tentative de Cascade Non Sollicitée)
  Scénario: Rétrogradation automatique lors d'une tentative de promotion en série
    Étant donné un processus autonome tentant de modifier plusieurs récits à la suite d'un round macro
    Mais qu'aucun mandat unitaire explicite n'a été accordé par le PO
    Quand le contrôle de gouvernance audite les récits altérés
    Alors chaque récit altéré sans mandat est immédiatement rétrogradé au statut DRAFT
    Et le hash cryptographique anti-altération est purgé
    Et une infraction bloquante UNAUTHORIZED_CASCADE_MUTATION est consignée

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Anti-Rebond, Concurrence & Timeouts)
  Scénario: Protection anti-rebond lors de commandes multiples sous 500 millisecondes et perte réseau
    Étant donné un utilisateur confirmant son choix d'orientation au clavier
    Mais qu'un double-clic rapide ou des requêtes consécutives sous 500 millisecondes sont émises
    Quand le système traite l'instruction de déverrouillage
    Alors une seule commande d'analyse unitaire est initiée avec un jeton d'idempotence
    Et l'interface bloque toute seconde exécution concurrente
    Et en cas de timeout réseau, l'état local des documents est préservé sans altération partielle

  # UX, OBSERVABILITÉ & VALIDATION DES SAISIES (Validation des Entrées Incomplètes)
  Scénario: Rejet de saisie incomplète et blocage de l'auto-promotion directe
    Étant donné un utilisateur formulant une réponse ambiguë ou un identifiant de story inexistant
    Quand l'agent évalue la réponse par rapport au menu d'orientation
    Alors l'agent réitère la demande de clarification sans écrire sur disque
    Et le statut du récit demeure sous READY_FOR_GROOMING tant qu'aucun arbitrage humain explicite Gate 2 n'est formulé
    Et un journal d'audit trace l'événement d'attente d'approbation
```
