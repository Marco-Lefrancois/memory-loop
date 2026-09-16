# 🐍 Protocole Normatif : Standards de Robustesse Python Senior (mLoop Engineering Standards)

- **Statut** : SSOT Normatif
- **Date d'effet** : 15 septembre 2026
- **Domaine** : Ingénierie logicielle, Robustesse du runtime, Gestion des ressources, Concurrence, Typage structurel, Observabilité
- **Référence Constitutionnelle** : [ADR-0369](../adr-system/0369-python-senior-robustness-and-resource-governance.md)
- **Source R&D** : [KDnuggets — 7 Python Best Practices Senior Developers Follow](../../docs/00-ingested/kdnuggets_7_python_best_practices.md)

---

## 1. Axiome Fondamental : « Rendre Chaque Hypothèse Inspectable »

> **Axiome de Nahla Davies (KDnuggets 2026)** :  
> *« Le code qui survit à la maintenance est celui qui déplace les hypothèses implicites de la tête du développeur vers un endroit où un autre développeur, un test unitaire ou un opérateur peut les inspecter. »*

Dans le framework Memory Loop (mLoop), chaque ligne de code Python écrite dans `src/` ou exécutée dans les pipelines d'agents doit rendre explicites :
1. Ses dépendances et collaborateurs (via `typing.Protocol` et injection de paramètres).
2. Le propriétaire du cycle de vie de ses ressources (via des gestionnaires de contexte `with`).
3. Sa date limite d'attente (via des `timeout` obligatoires sur tout appel réseau/subprocess).
4. Le contexte nécessaire à son diagnostic à 2h du matin (via `extra={...}` et `LoggerAdapter`).
5. Son contrat de rupture et de gestion des pannes (via des tests paramétrés `@pytest.mark.parametrize` et `pytest.raises`).
6. Les exigences de son environnement d'exécution (via `pyproject.toml` déclaratif).
7. La trajectoire de migration de ses APIs publiques (via `warnings.warn(..., DeprecationWarning, stacklevel=2)`).

---

## 2. La Matrice des 7 Standards Senior mLoop

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               LES 7 STANDARDS DE ROBUSTESSE PYTHON SENIOR (mLoop SSOT)                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. INJECTION DE DÉPENDANCES  │ typing.Protocol au lieu de mocks profonds               │
│ 2. CONTEXT MANAGERS D'ÉTAT   │ Zero connexion/descripteur sans bloc with               │
│ 3. TIMEOUT OBLIGATOIRE       │ Zéro appel subprocess/réseau sans deadline explicite    │
│ 4. LOGS STRUCTURÉS           │ logger.info(msg, extra={...}) & zéro 'except: pass' nu  │
│ 5. TESTS D'ÉCHEC PARAMÉTRÉS  │ @pytest.mark.parametrize sur entrées limites & pannes   │
│ 6. CONTRAT PYPROJECT.TOML    │ PEP 621, [project.optional-dependencies] & tool configs │
│ 7. DÉPRÉCIATION EXPLICITE    │ warnings.warn(..., DeprecationWarning, stacklevel=2)    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Standard 1 : Injection de Dépendances via `typing.Protocol`

- **Principe** : Ne jamais instancier un client réseau lourd (`httpx.Client`, `AsyncOpenAI`) ou un moteur de stockage à l'intérieur d'une méthode sans permettre son injection par l'appelant.
- **Patron mLoop** : Utiliser `typing.Protocol` pour formaliser la forme attendue (*duck typing vérifié statiquement*) sans forcer un arbre d'héritage lourd.

```python
from typing import Protocol, Dict, Any, Optional

class LLMTransport(Protocol):
    async def complete(self, prompt: str, **kwargs) -> Dict[str, Any]: ...

class PipelineExecutor:
    def __init__(self, transport: Optional[LLMTransport] = None):
        # Le collaborateur est inspectable et remplaçable sans monkeypatching
        self.transport = transport or DefaultLLMTransport()
```

- **Anti-pattern banni** :
  ```python
  # INTERDIT : Constructeur fermé forçant le réseau réel dans les tests unitaires
  class PipelineExecutor:
      def __init__(self):
          self.client = httpx.Client()  # Cache sa dépendance, oblige à monkeypatcher
  ```

---

### Standard 2 : Gestion des Ressources Détenue par les Context Managers

- **Principe** : *« Trusting garbage collection to close things eventually is not a cleanup strategy; it's a cleanup lottery with bad odds. »* Toute ressource nécessitant une fermeture (connexion SQLite, session HTTP, descripteur de fichier, répertoire temporaire, verrou) DOIT être gouvernée par un bloc `with` ou `async with`.
- **Patron mLoop** :

```python
from contextlib import contextmanager
import sqlite3

@contextmanager
def get_db_session(db_path: Path):
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()  # Garantie absolue de libération même en cas de crash
```

- **Anti-pattern banni** :
  ```python
  # INTERDIT : Connexion nue retournée sans bloc with
  conn = _get_raw_connection()
  conn.execute(...)
  # Omission de conn.close() -> verrou WAL SQLite maintenu et fuite de socket
  ```

---

### Standard 3 : Date Limite (*Deadline / Timeout*) sur Toute Attente Externe

- **Principe** : Une attente sans limite est un mode de défaillance non déclaré. Tout appel synchrone (`subprocess.run`, client HTTP) ou asynchrone (`asyncio`) doit posséder une date d'expiration explicite et une politique de recouvrement décidée.
- **Patron mLoop** :
  - **Synchrone** :
    ```python
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30.0)
    except subprocess.TimeoutExpired as e:
        logger.error("Commande externe interrompue", extra={"cmd": cmd, "timeout": 30.0})
        raise ExternalToolTimeoutError(f"Délai de 30s expiré pour {cmd[0]}") from e
    ```
  - **Asynchrone** :
    ```python
    async with asyncio.timeout(10.0):
        res = await client.fetch()
    ```
- **Anti-pattern banni** :
  ```python
  # INTERDIT : Subprocess sans timeout pouvant geler le pipeline indéfiniment
  subprocess.run(full_cmd, capture_output=True, text=True)
  ```

---

### Standard 4 : Journalisation Contextuelle & Banishment du `except: pass` Silencieux

- **Principe** : Un message de log doit contenir les paires clé-valeur nécessaires pour rejouer l'incident sans devoir interroger l'équipe d'astreinte.
- **Patron mLoop** : Passer les attributs contextuels via `extra={...}` et formater automatiquement via `MLoopFormatter`.

```python
logger.info(
    "Synchronisation story terminée",
    extra={"project": project_name, "story_id": story_id, "duration_ms": 142}
)
```

- **Règle sur les exceptions** :
  ```python
  # INTERDIT : Engloutir silencieusement l'erreur sans trace
  try:
      record_ledger(...)
  except Exception:
      pass

  # EXIGÉ : Journalisation en niveau DEBUG avec contexte même si non bloquant
  try:
      record_ledger(...)
  except Exception as e:
      logger.debug("Échec non bloquant du ledger", exc_info=True, extra={"target": target})
  ```

---

### Standard 5 : Tester le Contrat de Rupture (*Failure Contract*), Pas Seulement le Happy Path

- **Principe** : Valider une entrée nominale ne renseigne en rien sur la tenue sous pression. Les tests doivent systématiquement vérifier les erreurs aux frontières (entrées vides, types invalides, erreurs HTTP, timeouts).
- **Patron mLoop** : Utilisation conjointe de `@pytest.mark.parametrize` et `pytest.raises`.

```python
import pytest

@pytest.mark.parametrize("invalid_status", [400, 401, 403, 429, 500, 504])
def test_sync_engine_handles_http_errors(invalid_status):
    mock_client = MockClient(status_code=invalid_status)
    with pytest.raises(JiraSyncError, match="Échec de synchronisation"):
        sync_story_to_jira(story_data={}, client=mock_client)
```

---

### Standard 6 : Métadonnées du Paquet comme Contrat de Code (`pyproject.toml`)

- **Principe** : Le projet doit déclarer de façon unifiée et lisible par les machines sa configuration de build, ses dépendances d'exécution, ses dépendances d'outillage de dev (`dev = [...]`) et ses tables d'outils (`[tool.pytest]`, `[tool.ruff]`, `[tool.mypy]`).
- **Patron mLoop** :
  - `pyproject.toml` en tant que SSOT déclaratif PEP 621.
  - Zéro dépendance cachée ou documentation tribale pour faire tourner la suite de tests.

---

### Standard 7 : Dépréciation Explicite avec `stacklevel=2` Avant Suppression

- **Principe** : Les modifications de signatures ou fonctions dépréciées doivent alerter l'appelant sans casser l'exécution avant une suppression planifiée.
- **Patron mLoop** :

```python
import warnings

def legacy_helper(*args, **kwargs):
    warnings.warn(
        "legacy_helper() est déprécié ; utilisez new_helper() à la place.",
        DeprecationWarning,
        stacklevel=2,  # Pointe la ligne du code appelant, non la définition
    )
    return new_helper(*args, **kwargs)
```

---

## 3. Checklist de Revue de Code & Pull Request

Avant de fusionner du code Python dans `src/`, tout développeur ou agent IA doit répondre à ces 5 questions de contrôle :

- [ ] **1. Dépendances** : Ce composant peut-il être testé sans accès réseau ni patch profond ?
- [ ] **2. Ressources** : Chaque connexion SQLite, session HTTP ou fichier est-elle libérée dans un bloc `with` ?
- [ ] **3. Délais** : Existe-t-il un appel `subprocess.run` ou réseau sans `timeout` explicite ?
- [ ] **4. Observabilité** : Les erreurs non bloquantes sont-elles loggées avec du contexte (`extra={...}`) plutôt que masquées par `pass` ?
- [ ] **5. Robustesse aux tests** : Les cas d'erreurs (codes HTTP inattendus, payloads corrompus) sont-ils couverts par `@pytest.mark.parametrize` ?
