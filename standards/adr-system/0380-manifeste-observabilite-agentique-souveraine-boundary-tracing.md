---
id: "ADR-0380"
title: "Manifeste de l'Observabilité Agentique Souveraine, Boundary Tracing & Immunisation Déterministe"
status: "Accepté"
date: "2026-09-19"
type: "Type 1 — Architecture & Gouvernance Système"
authority: "mLoop Senior Architecture Board"
validation_rules:
  - check_id: "sovereign_observability_no_saas"
    severity: "BLOCKING"
    description: "Interdiction formelle de toute télémétrie distante ou SaaS. Stockage 100% local en JSONL et SQLite."
    params:
      allowed_formats: ["jsonl", "sqlite"]
      forbidden_endpoints: ["langfuse", "datadog", "arize", "weights_biases", "langsmith"]
  - check_id: "ping_pong_guard_deterministic_trip"
    severity: "BLOCKING"
    description: "Interruption déterministe immédiate de toute boucle de délégation atteignant 3 handoffs consécutifs sans livrable sur disque."
    params:
      max_sterile_handoffs: 3
      exception_class: "PingPongRecursionError"
      required_flag: "hitl_required"
  - check_id: "boundary_tracing_auto_offload"
    severity: "BLOCKING"
    description: "Déportation automatique de toute charge utile d'outil supérieure à 2000 caractères vers l'OpaqueArtifactBus."
    params:
      payload_threshold_chars: 2000
      handle_prefix: "mloop://artifacts/"
  - check_id: "context_saturation_3_zones"
    severity: "BLOCKING"
    description: "Surveillance de la saturation du contexte par session selon le zonage dynamique Smart (0-40%), Caution (40-60%) et Dumb Zone (>60%)."
    params:
      smart_zone_max: 0.40
      caution_zone_max: 0.60
      dumb_zone_critical: 0.60
---

# ADR-0380 : Manifeste de l'Observabilité Agentique Souveraine, Boundary Tracing & Immunisation Déterministe

## Statut
**Accepté (SSOT Normatif)** — 19 Septembre 2026

---

## 1. Contexte & Problématique

Dans les systèmes multi-agents modernes, la complexité des interactions engendre des comportements émergents imprévisibles et coûteux :
1. **Délégation Non Bornée (*Infinite Handoffs & Ping-Pong Loops*)** : Lorsque des agents spécialisés (Orchestrateur, Planificateur, Sentinelle, Travailleur) se renvoient mutuellement la charge sans produire de code ni d'artefact concret, la fenêtre de contexte se pollue et le budget de tokens s'évapore silencieusement.
2. **Saturation Contextuelle & Effet d'Amnésie (*The Dumb Zone*)** : Au-delà de 60 % d'utilisation de la fenêtre de contexte maximale d'un modèle, ses capacités de raisonnement se dégradent brutalement (ADR-0324). L'accumulation de sorties d'outils massives précipite l'agent dans la « Dumb Zone ».
3. **Dépendance et Fuite des Métadonnées vers les SaaS Tiers** : Les solutions d'observabilité industrielles courantes (Langfuse, Arize Phoenix, Datadog, LangSmith) imposent des couches lourdes d'export réseau vers des plateformes tierces, violant la souveraineté stricte des données et le paradigme Zéro-Cloud de mLoop.
4. **Opacité des Décisions et Boîtes Noires Cognitives** : Sans un alignement normalisé sur le standard ouvert OpenInference / OTel GenAI au niveau local, il est impossible de tracer les délibérations cognitives (`<thinking>`), les spans d'exécution et les verdicts contradictoires Sentinel de manière unifiée.

---

## 2. Décisions Fondatrices d'Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ MANIFESTE DE L'OBSERVABILITÉ AGENTIQUE SOUVERAINE & BOUNDARY TRACING (ADR-0380)       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [DISJONCTEUR ANTI-BOUCLE DÉTERMINISTE : PING-PONG GUARD]                             │
│   Handoff A -> B -> A -> B (Seuil strict = 3 transferts sans fichier sur disque)       │
│   └──> Interruption Système 1 immédiate                                                │
│   └──> Levée de PingPongRecursionError & Activation du drapeau [HITL REQUIRED]         │
│   └──> Reset automatique lors de toute persistance physique d'artefact                 │
│                                                                                        │
│   [BOUNDARY TRACING & INTERCEPTION AUTOMATIQUE : OPAQUE ARTIFACT BUS]                  │
│   Sortie d'outil > 2 000 caractères ou > 30 lignes                                     │
│   └──> Capture déterministe du payload volumineux                                      │
│   └──> Stockage compressé sous SHA-256 dans memory/artifacts/                          │
│   └──> Remplacement dans le contexte par un pointeur : mloop://artifacts/{sha256}     │
│                                                                                        │
│   [JAUGE DE SATURATION CONTEXTUELLE 3-ZONES PAR SESSION]                               │
│   Monitoring par session active (calé sur la fenêtre réelle du LLM)                    │
│   • 0%  - 40% : 🟢 SMART ZONE     (Raisonnement optimal, plein régime)                 │
│   • 40% - 60% : 🟡 CAUTION ZONE   (Surveillance, élagage proactif des traces)          │
│   • > 60%     : 🔴 DUMB ZONE      (Alerte critique, offload forcé, checkpoint PITR)    │
│                                                                                        │
│   [NORMALISATION LOCALE OPENINFERENCE / OTEL GENAI SANS SAAS]                          │
│   Attributs normalisés émis localement dans memory/events.jsonl et SQLite :            │
│   • openinference.span.kind = 'agent' | 'chain' | 'llm' | 'tool'                       │
│   • gen_ai.prompt / gen_ai.completion / gen_ai.usage.cost                              │
│   • 100% Local, Zéro Dépendance Distante, Confidentialité et Souveraineté Absolues     │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Disjoncteur Déterministe : Ping-Pong Guard
- **Seuil d'Interruption** : Toute alternance ou chaîne de transferts de contrôle entre agents sans écriture concrète sur le système de fichiers est plafonnée à **3 handoffs consécutifs**.
- **Effets Systémiques** :
  1. Consignation d'une entrée critique `circuit_breaker:ping_pong_detected` dans le journal d'état.
  2. Émission d'un événement `circuit_breaker_tripped` dans la télémétrie locale.
  3. Levée de l'exception `PingPongRecursionError` et passage de `LoopState.hitl_required = True`.
- **Réinitialisation sur Preuve de Travail** : L'écriture et la persistance physique sur disque d'un fichier valide (code source, test ou documentation) réinitialise immédiatement le compteur à zéro.

### 2.2 Boundary Tracing & Auto-Offload vers l'OpaqueArtifactBus
- Tout payload ou retour d'outil dépassant **2 000 caractères** (ou 30 lignes) est intercepté par le wrapper de frontière avant son injection dans la mémoire de travail de l'agent.
- Le contenu brut est persisté sous SHA-256 dans le stockage d'artefacts local (`memory/artifacts/`).
- Le prompt de l'agent ne reçoit qu'un résumé succinct et un pointeur déterministe URI : `mloop://artifacts/{sha256}`.

### 2.3 Jauge Contextuelle Dynamique 3-Zones par Session
- La consommation de tokens est tracée en temps réel **par session active** et rapportée à la capacité contextuelle du modèle sélectionné.
- **Zonage Normatif** :
  - **Zone Verte (0 à 40 %)** : Régime nominal d'inférence.
  - **Zone Jaune (40 à 60 %)** : Début de vigilance cognitive.
  - **Zone Rouge (> 60 %)** : Entrée dans la Dumb Zone (ADR-0324) imposant une compaction ou une intervention humaine.

### 2.4 Télémétrie Souveraine Locale OpenInference / OTel GenAI
- Les traces et événements respectent scrupuleusement la nomenclature OpenInference et OpenTelemetry Semantic Conventions for Generative AI.
- Le transport est **100 % local** : fichier d'append-only `memory/events.jsonl` et base relationnelle `memory/token_ledger.db` / `memory/standards_graph.db`.
- Zéro dépendance à des SDKs cloud ou des endpoints SaaS propriétaires.

---

## 3. Conséquences & Impacts

### 3.1 Positives
- Éradication mathématique des boucles infinies entre sous-agents.
- Préservation de la netteté cognitive du LLM en le maintenant hors de la Dumb Zone.
- Garantie de confidentialité absolue (aucun octet d'échange ni de code n'est transmis à un observateur cloud).
- Intégration fluide dans le Cockpit 2.0 (Runway de Handoffs, Trajectory Diff Viewer, Explorateur Graphify & SQLite).

### 3.2 Contraintes & Règles de Développement
- **Règle du Zéro Code Métier** : Les gardes-fous et disjoncteurs interrompent le flux et alertent l'humain, mais ne doivent jamais improviser ou synthétiser du code métier à la place de l'agent ou de l'utilisateur.
- **Plafonds Modulaires (ADR-0202)** : Chaque composant Python d'observabilité doit demeurer $\le 300$ lignes et $\le 15$ Ko.
- **Tolérance et Fail-Open Contrôlé** : En cas de crash du bus d'artefacts ou de fichier temporaire inaccessible, le composant consigne l'erreur sans corrompre le `LoopState`.
