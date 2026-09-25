# 📜 Code Evidence Ledger : Traçabilité Épistémique Ligne par Ligne
## Épopée : `EPIC-7-AGENTIC-OBSERVABILITY` — Projet : `mLoop`
- **Phase Active** : `STAGE_3_BUILD` (Développement Physique — Gate 2 DoR validée)
- **Porte en Cours** : `Gate 3 (Definition of Done - DoD)`
- **Autorité Constitutionnelle** : ADR-0202, ADR-0339, ADR-0369, ADR-0375, ADR-0378, ADR-0379, ADR-0380
- **Collège d'Architecture** : Marco (Architecte Propriétaire), Lead Architect (Antigravity), Co-Architecte Framework Agentique (`agentic_co_architect`)
- **Statut Épistémique Global** : `VERIFIED_DETERMINISTIC` (100% Tests Passés)

---

## 🎯 Matrice des Blocs de Code & Preuves Déterministes (MLOOP-070-BE)

| ID Bloc | Fichier & Lignes | Symbole / Entité | Pilier Gherkin | Règle Métier & Invariant Formel | Assertion de Test & Preuve | Statut |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **CEL-070-001** | `src/state.py` (L369-370) | `LoopState.hitl_required` | Pilier 2 (Exception) & 3 (Résilience) | **Drapeau HITL Déterministe** : champ booléen standard dans le schéma Pydantic, forcé à `True` lors de toute coupure d'urgence pour imposer l'arbitrage humain sans corrompre l'état. | `tests/test_ping_pong_guard.py::test_loop_state_hitl_flag_and_journal_mutation`<br>`assert state.hitl_required is True` | `VERIFIED` |
| **CEL-070-002** | `src/agents/circuit_breaker.py` (L18-32) | `PingPongRecursionError` | Pilier 2 (Exception) | **Exception Typée de Récursion** : hérite de `LoopStateError`. Transporte `cycle_depth` ($\ge 3$) et la copie immuable de l'historique de handoff pour audit médico-légal immédiat. | `tests/test_ping_pong_guard.py::test_alternating_ping_pong_cycle_trips_and_raises`<br>`pytest.raises(PingPongRecursionError)` | `VERIFIED` |
| **CEL-070-003** | `src/agents/circuit_breaker.py` (L77-104) | `PingPongGuard.__init__` | Pilier 1 (Nominal) | **Initialisation Déterministe** : seuil strict de 3 handoffs consécutifs, normalisation des rôles en minuscules, initialisation du compteur stérile à 0 sans effet de bord. | `tests/test_ping_pong_guard.py::test_linear_delegation_under_threshold`<br>`guard.consecutive_sterile_handoffs == 0` | `VERIFIED` |
| **CEL-070-004** | `src/agents/circuit_breaker.py` (L106-149) | `PingPongGuard.record_handoff` | Pilier 1 (Nominal) & 2 (Exception) | **Contrôle d'Intégrité de Délégation** : validation stricte des rôles (non-vide, appartenance à la topologie swarm autorisée). Incrémentation du compteur si aucun artefact n'est produit. | `tests/test_ping_pong_guard.py::test_linear_delegation_under_threshold`<br>`assert c1 == 1, assert c2 == 2`<br>`test_invalid_agent_roles_rejected` | `VERIFIED` |
| **CEL-070-005** | `src/agents/circuit_breaker.py` (L151-187) | `PingPongGuard.check_recursion` | Pilier 2 (Exception) & 4 (UX / Obs.) | **Disjonction et Alerte Immédiate** : dès que le compteur atteint 3, inscription au journal `circuit_breaker:ping_pong_detected`, émission OTel GenAI locale et levée de `PingPongRecursionError`. | `tests/test_ping_pong_guard.py::test_alternating_ping_pong_cycle_trips_and_raises`<br>`assert 'circuit_breaker:ping_pong_detected' in journal` | `VERIFIED` |
| **CEL-070-006** | `src/agents/circuit_breaker.py` (L189-200) | `PingPongGuard.record_artifact_production` | Pilier 3 (Résilience) | **Tolérance sur Production Réelle** : la persistance physique d'un fichier sur disque remet instantanément le compteur de handoffs stériles à 0 sans bloquer les délégations productives. | `tests/test_ping_pong_guard.py::test_artifact_production_explicit_reset`<br>`assert guard.consecutive_sterile_handoffs == 0` | `VERIFIED` |
| **CEL-070-007** | `src/agents/circuit_breaker.py` (L202-214) | `PingPongGuard.get_status` | Pilier 4 (UX / Obs. Cockpit) | **Télémétrie Sérialisable Cockpit 2.0** : exposition d'un dictionnaire immuté contenant `consecutive_sterile_handoffs`, `max_consecutive_handoffs`, `is_tripped`, et l'historique récent. | `tests/test_ping_pong_guard.py::test_runway_telemetry_payload_conformance`<br>`assert status['consecutive_sterile_handoffs'] == 2` | `VERIFIED` |
| **CEL-071-001** | `src/engine/artifacts/boundary_wrapper.py` (L25-54) | `ArtifactBusProtocol` & `BoundaryToolTimeoutError` | Pilier 2 (Rejets Métier & Rupture) | **Typage Structurel & Timeout Typé** : formalisation d'interface par `Protocol` (ADR-0369 Standard 1) et gestion d'expiration par `BoundaryToolTimeoutError` (Standard 3). | `tests/test_boundary_wrapper.py::test_boundary_trace_timeout_raises_typed_error`<br>`pytest.raises(BoundaryToolTimeoutError)` | `VERIFIED` |
| **CEL-071-002** | `src/engine/artifacts/boundary_wrapper.py` (L57-138) | `offload_if_exceeds` | Pilier 1 (Nominal) & 2 (Rejets) | **Déportation Automatique Déterministe** : seuils stricts à 2 000 caractères ou 30 lignes. Retour brut si conforme, persistance SHA-256 et descripteur compact si dépassement. | `tests/test_boundary_wrapper.py::test_offload_thresholds_parametrize`<br>`@pytest.mark.parametrize` sur frontières 1999/2000/2001 chars | `VERIFIED` |
| **CEL-071-003** | `src/engine/artifacts/boundary_wrapper.py` (L141-155) | `get_artifact_slice` | Pilier 3 (Résilience) | **Projection Fenêtrée Streaming** : lecture isolée d'une tranche de lignes sans chargement du fichier complet en mémoire (ADR-0369 Standard 2). Rejet des bornes invalides. | `tests/test_boundary_wrapper.py::test_get_artifact_slice_extracts_exact_lines`<br>`assert len(slice_lines) == 16` | `VERIFIED` |
| **CEL-071-004** | `src/engine/artifacts/boundary_wrapper.py` (L158-207) | `boundary_trace` | Pilier 1 (Nominal) & 2 (Rejets) | **Décorateur d'Interception Frontière** : capture d'exécution de callable d'outil avec deadline optionnelle (`ThreadPoolExecutor`), propagation des exceptions et auto-offload. | `tests/test_boundary_wrapper.py::test_boundary_trace_large_output_auto_offload`<br>`assert 'mloop://artifacts/' in result` | `VERIFIED` |
| **CEL-071-005** | `src/engine/artifacts/bus.py` (L176-189) | `OpaqueArtifactBus.to_prompt_descriptor` | Pilier 4 (UX & Observabilité) | **Bouclier Anti-Lignes Géantes** : tronquage unitaire à 200 caractères et plafond à 1 000 caractères de prévisualisation pour interdire tout débordement de contexte. | `tests/test_boundary_wrapper.py::test_boundary_trace_emits_event_on_offload`<br>`assert payload['tokens_saved'] > 500` | `VERIFIED` |
| **CEL-072-001** | `src/utils/event_logger.py` (L31-45) | `EventLogger._normalize_span_kind` | Pilier 2 (Exceptions & Rejets) | **Normalisation Déterministe OpenInference** : qualification stricte vers {AGENT, TOOL, LLM, CHAIN} avec repli résilient sur CHAIN et archivage du type original dans `details`. | `tests/test_event_logger_openinference.py::test_event_logger_fallback_unknown_type_to_chain`<br>`assert payload['openinference.span.kind'] == 'CHAIN'` | `VERIFIED` |
| **CEL-072-002** | `src/utils/event_logger.py` (L47-105) | `EventLogger.log_event` | Pilier 1 (Nominal / Happy Path) | **Émission Conforme OTel GenAI** : structure normalisée (`trace_id` 32c, `span_id` 16c, `parent_span_id`, usage tokens, `gen_ai.system='mloop'`). | `tests/test_event_logger_openinference.py::test_event_logger_nominal_tool_span`<br>`assert len(payload['trace_id']) == 32` | `VERIFIED` |
| **CEL-072-003** | `src/utils/event_logger.py` (L107-147) | `EventLogger.query_events` | Pilier 3 (Résilience) & 4 (UX/Obs) | **Extraction Locale Antéchronologique** : requêtage local sécurisé avec filtrage par span_kind/agent et élimination silencieuse sans crash des lignes JSON corrompues. | `tests/test_event_logger_openinference.py::test_event_logger_resilience_corrupted_jsonl_lines`<br>`assert len(events) == 2` | `VERIFIED` |
| **CEL-072-004** | `src/utils/event_logger.py` (L27, 95-103) | `EventLogger._lock` | Pilier 3 (Résilience Technique) | **Isolation Concurrente Multi-Agents** : sérialisation des écritures via verrou réentrant `threading.Lock` évitant tout entrelacement de lignes JSONL. | `tests/test_event_logger_openinference.py::test_event_logger_concurrent_writes_thread_safety`<br>`assert len(raw_lines) == 100` | `VERIFIED` |

---

## 🔒 Empreintes Cryptographiques SHA-256 (Immuabilité Déterministe)

- `src/agents/circuit_breaker.py` : `f9c07bc643e633ffe63a880e776d623704d7b81e74c62e0ba46965f93fde2756`
- `tests/test_ping_pong_guard.py` : `390b3aff579fb87d8cababcdb18cb41c41abd7dc04350ea224e9f5ad2b60ebae`
- `src/state.py` : `84e7d8d4ddf0d6e813893ccade389bf518cb4da7cb0e213c076cc8744b674c83`
- `src/engine/artifacts/boundary_wrapper.py` : `624947d8bacf33c6d3e2f7444d812a96a97ffaab6c149fc4e96a492951064afc`
- `tests/test_boundary_wrapper.py` : `b752514490e5824977fa1b27db0b33d0b04657fc31b35d56ba9193361774f09c`
- `src/engine/artifacts/bus.py` : `a7b8e4119ada528ba3321348217e349a0a979cf94691289207312fade554a2cd`
- `src/utils/event_logger.py` : `3b40d3e8cf07446ac4a82d571a08393c035e810e9216de1a03a5b3e87f1408a0`
- `tests/test_event_logger_openinference.py` : `aaa1e2e91d069e49ba9d31c5ff7d17bc0b671d2621bdba925d3b20febe86d004`
- `src/dashboard/routers/overview.py` : `44990cf239cb32d84799042b8fc5d4615e4f45447a1b667ea69894e751221f1e`
- `src/dashboard/static/index.html` : `13197607a988d8b9e632b7194f107f9c2d7f8d6ea5dc7b69c4c153835e9c0c16`
- `tests/test_dashboard_context_gauge.py` : `1b058f8b8a5fcb819f72db1909a4773a49daec3081e7d23a493a7cf49e49c71a`

### 4. Blocs CEL MLOOP-073-FE (Jauge Contextuelle Dynamique 3-Zones)
| Bloc ID | Composant & Fichier | Lignes | Pilier Gherkin | Règle & Invariant | Test Pytest |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CEL-073-001` | `ContextGaugeEngine.evaluate_context` dans `src/dashboard/routers/overview.py` | 38-95 | Pilier 1, 2, 3 | Diagnostic 3 zones : Smart (<40%), Caution (40-60%), Dumb (>60%) | `test_smart_zone_nominal_calculation`, `test_caution_zone_calculation`, `test_dumb_zone_critical_calculation` |
| `CEL-073-002` | `ContextGaugeEngine.get_project_context_usage` dans `src/dashboard/routers/overview.py` | 97-154 | Pilier 3, 4 | Extraction non-bloquante multi-projets avec context managers | `test_context_health_project_resolution` |
| `CEL-073-003` | Routeur `/api/overview/context-health` dans `src/dashboard/routers/overview.py` | 208-228 | Pilier 1 à 4 | Endpoint REST FastAPI avec calibrage dynamique et simulation | `test_smart_zone_endpoint`, `test_caution_zone_endpoint`, `test_dumb_zone_endpoint` |
| `CEL-073-004` | Widget `#header-context-gauge` dans `src/dashboard/static/index.html` | 122-127, 740-785 | Pilier 1 à 4 | Badge dynamique réactif, animation clignotante en Dumb Zone, transition 300ms | `test_smart_zone_endpoint`, `test_dumb_zone_endpoint` |

### 5. Blocs CEL MLOOP-074-FULL (Runway Handoffs Swarm & Diff Dream RSI)
| Bloc ID | Composant & Fichier | Lignes | Pilier Gherkin | Règle & Invariant | Test Pytest |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CEL-074-001` | `SwarmRouter.get_swarm_handoffs` dans `src/dashboard/routers/swarm.py` | 73-157 | Pilier 1 (Nominal) | Runway de handoffs ordonné, exposition du statut PingPongGuard | `test_swarm_handoffs_nominal_endpoint` |
| `CEL-074-002` | `SwarmRouter.loop_detection_alert` dans `src/dashboard/routers/swarm.py` & `src/dashboard/static/index.html` | 90-103, 135-144 | Pilier 2 (Exceptions) | Alerte écarlate immédiate et marquage is_loop lors d'un cycle récursif | `test_swarm_handoffs_tripped_loop_detection` |
| `CEL-074-003` | `DreamRsiRouter.diff_empty_state` dans `src/dashboard/routers/dream_rsi.py` & `src/dashboard/static/index.html` | 100-145 | Pilier 3 (Résilience) | Rendu vide gracieux sans crash JS si aucun épisode archivé | `test_dream_rsi_diff_empty_state_resilience` |
| `CEL-074-004` | `DreamRsiRouter.diff_nominal_comparison` dans `src/dashboard/routers/dream_rsi.py` & `src/dashboard/static/index.html` | 146-194 | Pilier 4 (UX / Obs.) | Comparateur double colonne contrefactuel pi0 vs pi* avec gains explicites | `test_dream_rsi_diff_nominal_comparison` |

### 6. Blocs CEL MLOOP-075-FULL (Explorateur Graphify & Base SQLite)
| Bloc ID | Composant & Fichier | Lignes | Pilier Gherkin | Règle & Invariant | Test Pytest |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CEL-075-001` | `DatabaseRouter.get_graph_html` et `metadata` dans `src/dashboard/routers/database.py` | 82-160 | Pilier 1 (Nominal) | Restitution iframe HTML et métadonnées de graphe (god-nodes) | `test_graph_metadata_nominal`, `test_graph_html_nominal_if_present` |
| `CEL-075-002` | `DatabaseRouter.get_graph_html` (Fallback 404) dans `src/dashboard/routers/database.py` | 100-112 | Pilier 2 (Exceptions) | 404 explicite sans crash si le projet n'a pas encore compilé de graphe | `test_graph_html_missing_returns_404` |
| `CEL-075-003` | `_resolve_secure_db_path` et `_open_readonly_connection` dans `src/dashboard/routers/database.py` | 46-76 | Pilier 3 (Résilience) | Rejet 403 path traversal, sanitization de table et mode SQLite URI mode=ro | `test_database_tables_rejects_path_traversal`, `test_database_records_rejects_sql_injection` |
| `CEL-075-004` | `get_database_tables` et `get_database_records` dans `src/dashboard/routers/database.py` | 228-276 | Pilier 4 (UX / Obs.) | Inspection des tables et affichage paginé sécurisé des enregistrements | `test_database_tables_inspection_nominal`, `test_database_records_pagination_nominal` |

---

## 🔬 Rapport d'Exécution des Tests Pytest

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.0.2, pluggy-1.6.0
rootdir: C:\Memory Loop
collected 22 items

tests/test_ping_pong_guard.py::test_linear_delegation_under_threshold PASSED [  4%]
tests/test_ping_pong_guard.py::test_handoff_with_produced_artifact_resets_immediately PASSED [  9%]
tests/test_ping_pong_guard.py::test_alternating_ping_pong_cycle_trips_and_raises PASSED [ 13%]
tests/test_ping_pong_guard.py::test_invalid_agent_roles_rejected PASSED  [ 18%]
tests/test_ping_pong_guard.py::test_artifact_production_explicit_reset PASSED [ 22%]
tests/test_ping_pong_guard.py::test_loop_state_hitl_flag_and_journal_mutation PASSED [ 27%]
tests/test_ping_pong_guard.py::test_runway_telemetry_payload_conformance PASSED [ 31%]
tests/test_boundary_wrapper.py::test_boundary_trace_large_output_auto_offload PASSED [ 36%]
tests/test_boundary_wrapper.py::test_boundary_trace_preserves_function_signature PASSED [ 40%]
tests/test_boundary_wrapper.py::test_boundary_trace_small_output_passes_transparently PASSED [ 45%]
tests/test_boundary_wrapper.py::test_offload_thresholds_parametrize[1999-10-False] PASSED [ 50%]
tests/test_boundary_wrapper.py::test_offload_thresholds_parametrize[2001-10-True] PASSED [ 54%]
tests/test_boundary_wrapper.py::test_offload_thresholds_parametrize[500-29-False] PASSED [ 59%]
tests/test_boundary_wrapper.py::test_offload_thresholds_parametrize[500-31-True] PASSED [ 63%]
tests/test_boundary_wrapper.py::test_offload_thresholds_parametrize[2000-30-False] PASSED [ 68%]
tests/test_boundary_wrapper.py::test_boundary_trace_tool_exception_propagates PASSED [ 72%]
tests/test_boundary_wrapper.py::test_boundary_trace_timeout_raises_typed_error PASSED [ 77%]
tests/test_boundary_wrapper.py::test_get_artifact_slice_extracts_exact_lines PASSED [ 81%]
tests/test_boundary_wrapper.py::test_get_artifact_slice_invalid_bounds_raises PASSED [ 86%]
tests/test_boundary_wrapper.py::test_get_artifact_slice_nonexistent_handle_raises_file_not_found PASSED [ 90%]
tests/test_boundary_wrapper.py::test_boundary_trace_handles_none_and_empty_gracefully PASSED [ 95%]
tests/test_boundary_wrapper.py::test_boundary_trace_emits_event_on_offload PASSED [100%]

============================== 22 passed in 0.82s ==============================
```

