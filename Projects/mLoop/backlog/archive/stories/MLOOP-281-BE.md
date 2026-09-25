---
id: MLOOP-281-BE
jira_key: ""
epic_key: EPIC-28-ADR-CLEAN-ARCHITECTURE
type: Feature
title: "Calculateur d'ID ADR Robuste par Regex Anti-Collision"
tags: [grill, adr, id-generator, regex, anti-collision]
status: SHIPPED
validated_by: "Marco (PO - Feu Vert 2026-09-24)"
validated_at: "2026-09-24"
layer: backend
invest_score: 6/6
macro_size: S
created_at: "2026-09-24"
---

# 📖 MLOOP-281-BE : Calculateur d'ID ADR Robuste par Regex Anti-Collision

---

## Description
**En tant qu'** Orchestrateur mLoop consignant des arbitrages techniques,  
**je veux** que le calcul du prochain identifiant d'ADR analyse tous les numéros existants par expression régulière pour déterminer le `max(ids) + 1`,  
**afin d'** éliminer définitivement les risques de collision ou d'écrasement de fichiers lorsque la numérotation n'est pas strictement contiguë.

---

## Contexte & Périmètre

### Contexte Métier
Dans l'ancienne implémentation (`src/pipelines/grill_engine.py:180`), le numéro d'ADR était calculé via `next_id = len(existing_adrs) + 1`. Si un répertoire contenait `ADR-001.md` et `ADR-005.md` (suite à la suppression ou au renommage d'anciens fichiers), la longueur valait 2 et le prochain fichier généré écrasait ou télescopait la séquence. L'ADR-012 impose un calcul mathématique déterministe basé sur l'identifiant maximum effectif.

### In-Scope
- Fonction pure `get_next_adr_id(docs_dir: Path) -> Tuple[int, str]`.
- Regex d'extraction universelle insensible à la casse : `re.compile(r"^ADR-(\d+)", re.IGNORECASE)`.
- Parcours des fichiers directs de `docs/01-architecture/` correspondants au motif `ADR-*.md`.
- Calcul du prochain identifiant via `max(ids, default=0) + 1`.
- Formatage dynamique du préfixe :
  - Par défaut : 3 chiffres (`ADR-001`, `ADR-042`).
  - Si le max existant dépasse 999 : 4 chiffres (`ADR-1000`).
  - Détection automatique du séparateur dominant (`_` ou `-`).

### Out-of-Scope
- Renommage ou renumérotation automatique des anciens fichiers existants.
- Modification des chemins répertoires.

---

## Critères d'acceptation (Gherkin 4 Piliers)

### 1. Pilier Nominal (Happy Path)
```gherkin
Scénario: Calcul nominal contigu dans un projet standard
  Étant donné un dossier docs/01-architecture contenant "ADR-001.md" et "ADR-002_focus.md"
  Quand le calculateur d'identifiant est invoqué
  Alors le prochain identifiant numérique retourné est 3
  Et la chaîne de préfixe formatée est "ADR-003"
```

### 2. Pilier Exception & Trous de Numérotation
```gherkin
Scénario: Présence de trous de numérotation sans collision
  Étant donné un dossier docs/01-architecture contenant uniquement "ADR-001.md" et "ADR-011_lock.md"
  Quand le calculateur d'identifiant est invoqué
  Alors le calcul ignore la quantité de fichiers (2) et retient le maximum (11)
  Et le prochain identifiant numérique retourné est obligatoirement 12
  Et le fichier généré est "ADR-012"
```

### 3. Pilier Résilience & Répertoire Vierge ou Bruit
```gherkin
Scénario: Répertoire vide ou contenant des fichiers non conformes
  Étant donné un dossier docs/01-architecture vide ou ne contenant que "README.md" et "notes.txt"
  Quand le calculateur d'identifiant est invoqué
  Alors le prochain identifiant retourné est 1
  Et la chaîne de préfixe formatée est "ADR-001"
  Et aucune exception n'est levée
```

### 4. Pilier UX & Tolérance Multi-Chiffres
```gherkin
Scénario: Transition automatique vers les formats à 4 chiffres
  Étant donné un dossier de standards framework contenant "ADR-0389_grill_v2.md"
  Quand le calculateur d'identifiant est invoqué
  Alors le prochain identifiant est 390
  Et le formatage préserve la lisibilité sans tronquer les chiffres
```

---

### Contrats d'Échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-281 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — composant Python interne de calcul d'identifiants d'ADR (`get_next_adr_id()`), sans interface HTTP ni route REST distante `[API de soumission à définir]` (ADR-0319).

**Contrats Python Internes :**
- `get_next_adr_id(docs_dir: Path) -> int`

---

## Logique Métier & Algorithme Backend


### `get_next_adr_id(docs_dir: Path) -> int`
```python
def get_next_adr_id(docs_dir: Path) -> int:
    if not docs_dir.exists():
        return 1
    
    pattern = re.compile(r"^ADR-(\d+)", re.IGNORECASE)
    ids: List[int] = []
    
    for entry in docs_dir.glob("ADR-*.md"):
        if not entry.is_file():
            continue
        match = pattern.match(entry.name)
        if match:
            try:
                ids.append(int(match.group(1)))
            except ValueError:
                continue
                
    return max(ids, default=0) + 1
```

---

## Références
- 🏛️ **ADR Associés** : [ADR-0320](../../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md) · [ADR-012](../../../docs/01-architecture/ADR-012_epic-28_assainissement_generateur_adr_clean_architecture.md)
- 📂 **Code Source Cible** : `src/pipelines/grill/_adr_writer.py`
- 📦 **Épopée Parente** : [`EPIC-28-ADR-CLEAN-ARCHITECTURE`](../epics/epic_adr_clean_architecture.md)