# 📂 Dossier de Preuves Documentaires — `MLOOP-324-FULL` : Harnais de Non-Régression & Tests Pytest

---

### 1. 📜 Sources Physiques Normatives & Extraits Verbatim

#### Source 1 : [`tests/test_grill_engine.py`](file:///C:/Memory%20Loop/tests/test_grill_engine.py#L14-L38)
> **Extrait 1 — Modèle de Fixture Projet Temporaire :**  
> ```python
> @pytest.fixture
> def temp_project(tmp_path):
>     """Crée une arborescence projet mLoop temporaire."""
>     project_dir = tmp_path / "test_project"
>     project_dir.mkdir(parents=True)
>     ...
> ```  
> ➔ **Fait établi** : Le standard de test mLoop pour le moteur de grill s'appuie sur des fixtures hermétiques `tmp_path` créant une arborescence complète en mémoire/disque temporaire.

---

#### Source 2 : [`src/pipelines/state_machine.py`](file:///C:/Memory%20Loop/src/pipelines/state_machine.py#L197-L206)
> **Extrait 2 — Hiérarchie d'Exceptions FSM :**  
> `StateTransitionError(ValueError)` et `ContentTamperingError(ValueError)` sont les exceptions fondamentales.  
> ➔ **Fait établi** : `LifecycleAuthorityError` doit être testée unitairement pour vérifier son héritage de `StateTransitionError` et son comportement fail-closed.

---

#### Source 3 : [`standards/protocols/CLI_PIPELINE_GUIDE.md`](file:///C:/Memory%20Loop/standards/protocols/CLI_PIPELINE_GUIDE.md) et [`src/pipelines/guide_data.py`](file:///C:/Memory%20Loop/src/pipelines/guide_data.py)
> **Extrait 3 — Parité Documentaire CLI (ADR-0370) :**  
> Le guide CLI documente chaque commande (`grill`, `grill-project`) avec ses options.  
> ➔ **Fait établi** : L'introduction de `--format` et `--scope` impose la mise à jour synchronisée de `CLI_PIPELINE_GUIDE.md` et `guide_data.py` pour éviter toute dérive au Check 15.

---

#### Source 4 : [`Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md`](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md#L20-L32)
> **Extrait 4 — Décisions d'Architecture Scellées d'EPIC-32 :**  
> MLOOP-320 (Normes), MLOOP-321 (Skill), MLOOP-322 (FSM / Engine), MLOOP-323 (CLI / Check 28).  
> ➔ **Fait établi** : `MLOOP-324-FULL` est le vérificateur triangulé de la cohérence de l'ensemble de ces quatre briques.

---

### 2. 🎯 Contrat Déclaratif Cible (Harnais de Tests)
1. **`tests/test_grill_modality_decoupling.py`** :
   - Test 1 : Découplage Format (`atomic` vs `round`) sur story unitaire.
   - Test 2 : Découplage Format sur projet transverse (`grill-project`).
   - Test 3 : Levée de `LifecycleAuthorityError` lors d'une tentative d'écriture dans `backlog/stories/` en mode macro.
   - Test 4 : Levée de `LifecycleAuthorityError` lors d'une tentative d'auto-promotion vers `READY_FOR_DEV` sans validation humaine nominative.
   - Test 5 : Sonde Check 28 : détection de cascade non étayée (FAIL en Phase 4, WARNING en Phase 2) et validation PASS si dossiers de preuves présents.
   - Test 6 : Priorité CLI : résolution déterministe `--format` vs `--mode`.
2. **Synchronisation Documentation & Guide CLI** :
   - Mise à jour de `CLI_PIPELINE_GUIDE.md` et `src/pipelines/guide_data.py`.
3. **Exécution Pytest Globale** :
   - 100% de tests verts sur `tests/test_grill_modality_decoupling.py`.

---

### 3. 🔍 Frontière Active & Questions d'Arbitrage pour `MLOOP-324-FULL`
- **Question 1** : Stratégie d'isolation des tests (Fixtures hermétiques `tmp_path` 100% isolées vs interaction avec le workspace réel).
- **Question 2** : Couverture des tests de compatibilité multi-OS (chemins Windows `\` et POSIX `/` dans les assertions).
