---
id: MLOOP-303-BE
jira_key: ""
epic_key: EPIC-30-MULTIMODAL-ARTIFACT-HARNESS
type: Feature
title: "Grille d'Audit Architectural Découplée : Structure Sémantique vs Rendu (ArchitecturalAuditDecoupler)"
tags: [core, audit, topology, scoring, backend]
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: "2026-09-25"
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# Grille d'Audit Architectural Découplée : Structure Sémantique vs Rendu (ArchitecturalAuditDecoupler)

---

## Description
**En tant qu'** Auditeur Qualité Logicielle ou Juge Automatisé Sentinel,  
**je veux** disposer d'un algorithme de notation découplé appliquant une barrière multiplicative stricte entre la conformité topologique du graphe de dépendances et le rendu esthétique de l'artefact,  
**afin d'** interdire à tout livrable dont les flux causaux sont manquants ou inversés d'obtenir la moyenne, éliminant définitivement l'illusion cosmétique.

---

## Contexte & Périmètre

### Contexte Métier
L'un des constats scientifiques les plus frappants de ReFigBench est que les métriques d'évaluation visuelles (telles que SSIM, CLIP ou VQA) attribuent des scores flatteurs (> 85/100) à des schémas d'architecture dont les flèches sont inversées ou dont des dépendances vitales sont rompues. Pour mLoop, un schéma d'architecture dont un flux de données est inversé constitue une faute critique d'ingénierie. La grille d'audit doit donc mathématiquement subordonner la note globale à la vérité topologique.

### In-Scope
- Implémentation du moteur de calcul dans `src/pipelines/audit_decoupler.py` (strictement ≤ 300L, `RULE-AST-01`).
- Moteur d'évaluation `calculate_decoupled_architecture_score(topology_score: float, visual_score: float) -> AuditScoreResult`.
- Application de la formule mathématique à barrière multiplicative :
  $$\text{Score} = S_{\text{topo}} \times (0.7 + 0.3 \times S_{\text{visuel}})$$
  avec $S_{\text{topo}} \in [0.0, 1.0]$ et $S_{\text{visuel}} \in [0.0, 1.0]$.
- Sanction éliminatoire immédiate : si $S_{\text{topo}} < 1.0$ (inversion causale ou arête manquante), le score s'effondre mécaniquement, interdisant le passage de la Gate 2 ou Gate 4.
- Détection et diagnostic explicite des inversions causales de flux (`CAUSAL_FLOW_INVERSION`).

### Out-of-Scope
- Génération d'images ou calcul du score visuel bas niveau (fourni en entrée par les sondes de rendu).
- Arbitrage humain subjectif sur les couleurs ou le choix de palette.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Calcul du Score Découplé (`calculate_decoupled_score`)
* **Entrée Métier** : Note topologique $S_{\text{topo}} \in [0.0, 1.0]$, note visuelle $S_{\text{visuel}} \in [0.0, 1.0]$, liste des anomalies topologiques relevées.
* **Règles d'admissibilité & Validation** : Les notes d'entrée doivent être bornées entre 0.0 et 1.0.
* **Traitement & Algorithme Métier** :
  1. Vérification de l'absence d'inversion causale de flux.
  2. Si une inversion causale est présente, forçage de $S_{\text{topo}} = 0.0$.
  3. Calcul de la note composite selon la formule à barrière : $\text{Score} = S_{\text{topo}} \times (0.7 + 0.3 \times S_{\text{visuel}})$.
  4. Comparaison du score avec les seuils d'admissibilité (Seuil Gate 2 / Gate 4 : Score $\ge 0.85$).
* **Résultat Métier & Mutations** : Objet `AuditScoreResult(composite_score: float, is_approved: bool, topological_penalty: float, details: dict)`.
* **Cas de Rejet Métier** : Rejet éliminatoire avec code `CAUSAL_FLOW_INVERSION_DETECTED` ou `TOPOLOGY_INTEGRITY_DEFICIT`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- **Calcul Découplé Python** : `src.pipelines.audit_decoupler:calculate_decoupled_architecture_score`.
- **Intégration Rapport** : Inscription des métriques dans `memory/evidence/<STORY_ID>_evidence.json`.

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `calculate_decoupled_architecture_score` | `src.pipelines.audit_decoupler:calculate_decoupled_architecture_score` | Calcul composite découplé topologie vs rendu visuel | `(topology_score: float, visual_score: float) -> AuditScoreResult` |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-303-01** : Ce composant backend est une fonction de calcul analytique pure intégrée aux pipelines Sentinel (aucune interface HTTP/REST distante exposée). `[API de soumission à définir]` — toute exposition future via micro-service est reportée et à confirmer dans un récit dédié.

- **Admission of Limits & Résilience Système** :
  - **Absence de réseau / Timeout** : Moteur de calcul mathématique 100 % in-memory, insensible aux coupures réseau et timeouts distants (503/408).
  - **Concurrence & Anti-Rebond** : Protection contre les exécutions concurrentes ou invocations multiples rapides via fonction pure sans état mutable ni verrou bloquant.
  - **Session & Authentification** : Composant headless sans session utilisateur ni token d'authentification (hors domaine 401/session expirée).
  - **Validation des Entrées Extrêmes** : Tout score hors bornes, champ vide, entrée avec caractère spécial ou valeur null est clampé ou rejeté proprement avec exception typée sans crash.

---

## Règles d'affaires

- **Primauté Absolue de la Topologie** : Aucune perfection esthétique ne peut compenser une défaillance de structure relationnelle ($S_{\text{topo}}$ est un multiplicateur strict).
- **Zéro Tolérance aux Inversions Causales** : Un schéma qui inverse le sens d'un pipeline ou d'un flux de données reçoit une note finale de 0/100.
- **Transparence d'Audit** : Le rapport de calcul détaille distinctement la contribution topologique ($S_{\text{topo}}$) et la composante visuelle ($S_{\text{visuel}}$).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-303-BE_fact_dossier.md`](../../memory/evidence/MLOOP-303-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **ADR Projet** : [ADR-016 : Harnais de Fidélité Visuelle](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md)
- 📜 **ADR Système** : [ADR-0392 : Standard Topologique des Artefacts](../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md)
- 🔬 **Référence Scientifique** : *ReFigBench* (arXiv:2609.18844, Découplage Topologique).

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Grille d'Audit Architectural Découplée (ArchitecturalAuditDecoupler)

  # CHEMIN NOMINAL (Excellence Topologique et Visuelle)
  Scénario: Calcul nominal avec topologie parfaite et rendu visuel satisfaisant
    Étant donné un score topologique S_topo de 1.0 (aucune anomalie relationnelle)
    Et un score visuel S_visuel de 0.90
    Quand le moteur de calcul évalue la note composite
    Alors le score final calculé est de 0.97 (1.0 * (0.7 + 0.3 * 0.90))
    Et le livrable est approuvé pour la Gate

  # EXCEPTIONS & REJETS MÉTIER (Effondrement par Barrière Multiplicative)
  Scénario: Effondrement du score malgré un rendu visuel parfait suite à une arête manquante
    Étant donné un score visuel exceptionnel S_visuel de 1.0
    Mais un score topologique dégradé S_topo de 0.40 suite à des dépendances non reliées
    Quand le moteur calcule la note composite
    Alors le score final s'effondre à 0.40 (0.40 * (0.7 + 0.3 * 1.0))
    Et la validation est rejetée avec le statut "TOPOLOGY_INTEGRITY_DEFICIT"

  # SANCTION ÉLIMINATOIRE (Inversion Causale)
  Scénario: Note zéro éliminatoire lors d'une inversion de flux de données
    Étant donné un diagramme présentant une inversion causale entre l'API et la base de données
    Quand le moteur évalue le schéma
    Alors le score topologique S_topo est forcé à 0.0
    Et le score composite final est de 0.0
    Et l'alerte bloquante "CAUSAL_FLOW_INVERSION_DETECTED" est consignée

  # UX, OBSERVABILITÉ & LOGS (Bilan Détaillé)
  Scénario: Restitution du double score dans les métriques d'audit
    Étant donné l'évaluation d'un artefact d'architecture
    Quand le rapport est généré
    Alors le détail présente S_topo, S_visuel, le score composite et le verdict de Gate
```