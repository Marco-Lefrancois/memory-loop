# 📂 Dossier de Preuves Documentaires — `MLOOP-323-BE` : Contrôle de Gating CLI & Sonde de Détection de Cascade (Check 28)

---

### 1. 📜 Sources Physiques Normatives & Extraits Verbatim

#### Source 1 : [`src/commands/_registry/_reg_pipelines_arch.py`](file:///C:/Memory%20Loop/src/commands/_registry/_reg_pipelines_arch.py#L185-L211)
> **Extrait 1 — Déclaration des Arguments CLI de Grill (Lignes 194-196 et 208-209) :**  
> ```python
> {"name": "--story", "type": str, "help": "Identifiant du récit pour analyse micro 1:1"},
> {"name": "--mode", "type": str, "help": "Mode d'interrogation : round ou atomic"},
> ```  
> ➔ **Fait établi** : L'option `--mode` amalgame le format et le scope. Le CLI ne permet pas encore de spécifier indépendamment `--format` et `--scope`.

---

#### Source 2 : [`src/pipelines/vibe_check/_vc_governance.py`](file:///C:/Memory%20Loop/src/pipelines/vibe_check/_vc_governance.py#L280-L297)
> **Extrait 2 — Périmètre des Contrôles de Gouvernance Existants :**  
> `_vc_governance.py` contient les sondes Check 10, Check 11, Check 12, Check 13 et Check 25 (`check_25_story_state_lock`).  
> ➔ **Fait établi** : Aucune sonde ne vérifie actuellement la vélocité anormale d'apparition des récits en Palier 2 ni l'existence de dossiers de preuves individuels horodatés pour prévenir les promotions industrielles en batch.

---

#### Source 3 : [`Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md`](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md#L25-L27)
> **Extrait 3 — Décision d'Architecture 2 (Sonde Check 28) :**  
> *« 2. Sonde Check 28 dans vibe-check (MLOOP-323-BE) : Déclenchement d'un FAIL bloquant si $\ge 3$ récits sont promus en Palier 2 dans un intervalle $< 60$ secondes sans dossiers de preuves distincts et horodatés individuellement. »*  
> ➔ **Fait établi** : Le contrat d'acceptation du Check 28 est fondé sur l'absence de preuves unitaires pour un lot de récits promus rapidement.

---

### 2. 🎯 Contrat Déclaratif Cible (Gating CLI & Sonde Check 28)
1. **`src/commands/_registry/_reg_pipelines_arch.py`** :
   - Ajout des arguments `--format` (`round` | `atomic`) et `--scope` (`story` | `epic` | `project`).
   - Maintien de `--mode` comme alias rétrocompatible.
2. **`src/pipelines/vibe_check/_vc_governance.py`** :
   - Implémentation de la fonction `check_28_story_cascade_drift(project_dir, ...)` :
     - Analyse des récits en `READY_FOR_GROOMING` et `READY_FOR_DEV`.
     - Vérification de la présence d'un fichier `memory/evidence/<ID>_fact_dossier.md` dédié et horodaté pour chaque récit.
     - Détection des grappes de récits promus en série sans preuve unitaire.
3. **`src/pipelines/vibe_check/__init__.py`** :
   - Enregistrement du Check 28 dans la chaîne d'exécution pré-vol de Vibe-Check.

---

### 3. 🔍 Frontière Active & Questions d'Arbitrage pour `MLOOP-323-BE`
- **Question 1** : Sévérité du Check 28 selon le cycle de vie (WARNING préventif en Phase 2 vs FAIL bloquant en Phase 4).
- **Question 2** : Comportement de substitution en cas d'utilisation conjointe de `--mode` et `--format`.
