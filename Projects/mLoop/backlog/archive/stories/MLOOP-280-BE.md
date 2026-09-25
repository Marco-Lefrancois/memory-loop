---
id: MLOOP-280-BE
jira_key: ''
epic_key: EPIC-28-ADR-CLEAN-ARCHITECTURE
type: Feature
title: Résolution Dynamique du Gabarit project_adr_template.md
tags:
- grill
- adr
- templates
- clean-architecture
status: SHIPPED
validated_by: "Marco (PO - Feu Vert 2026-09-24)"
validated_at: "2026-09-24"
layer: backend
invest_score: 6/6
macro_size: S
created_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-280-BE : Résolution Dynamique du Gabarit project_adr_template.md

---

## Description
**En tant qu'** Architecte ou Développeur utilisant le moteur de Grilling mLoop,  
**je veux** que `GrillEngine.record_adr()` résolve et charge dynamiquement le template officiel `standards/blueprints/project_adr_template.md` au lieu d'une constante statique codée en dur dans le code source Python,  
**afin de** garantir que les ADRs générés reflètent immédiatement les standards documentaires vivants sans nécessiter de retoucher le code Python du framework.

---

## Contexte & Périmètre

### Contexte Métier
L'architecture de décision mLoop (ADR-0320) s'appuie sur la consignation synchrone et opposable de chaque arbitrage sous forme de document Markdown normalisé. Le gabarit canonique `project_adr_template.md` a été standardisé dans `standards/blueprints/` mais est resté découplé du moteur Python qui utilisait jusqu'ici une chaîne codée en dur. Ce récit établit la passerelle dynamique avec cascade de résolution sécurisée (ADR-012).

### In-Scope
- Implémentation du résolveur de gabarit d'ADR avec cascade à 3 niveaux :
  1. `Projects/<projet>/docs/01-architecture/template.md` (surcharge locale projet).
  2. `standards/blueprints/project_adr_template.md` (source canonique framework).
  3. `EMERGENCY_FALLBACK_TEMPLATE` (constante mémoire de secours avec émission d'un log `WARNING`).
- Moteur de substitution déterministe pour les balises doubles `{{TAG}}` : `{{ADR_ID}}`, `{{TITLE}}`, `{{DATE}}`, `{{CONTEXT}}`, `{{DECISION}}`, `{{POSITIVES}}`, `{{NEGATIVES}}`.
- Substitution de valeurs par défaut intelligentes si des rubriques facultatives sont vides.
- Rétrocompatibilité avec les balises simples `{tag}` si détectées.

### Out-of-Scope
- Modification de la structure des répertoires d'ADRs existants.
- Moteur de templating lourd externe (Jinja2 proscrit).

---

## Critères d'acceptation (Gherkin 4 Piliers)

### 1. Pilier Nominal (Happy Path)
```gherkin
Scénario: Chargement nominal du blueprint canonique standards/blueprints/project_adr_template.md
  Étant donné un projet mLoop actif sans template local d'ADR
  Et le blueprint "standards/blueprints/project_adr_template.md" présent sur le disque
  Quand GrillEngine génère un ADR intitulé "Adoption S3" avec un contexte et une décision
  Alors le fichier généré contient exactement le contenu du blueprint avec les balises {{TAG}} résolues
  Et aucune balise {{...}} résiduelle n'est présente dans le fichier Markdown produit
```

### 2. Pilier Exception & Surcharge Locale
```gherkin
Scénario: Prise en compte de la surcharge locale d'un projet client
  Étant donné un projet client disposant d'un fichier "docs/01-architecture/template.md" personnalisé
  Quand GrillEngine génère un ADR pour ce projet
  Alors le moteur utilise le gabarit local du projet en priorité sur le blueprint global
  Et un log DEBUG confirme l'utilisation de la surcharge locale
```

### 3. Pilier Résilience & Fallback d'Urgence
```gherkin
Scénario: Défaillance d'accès au système de fichiers et repli mémoire
  Étant donné l'absence accidentelle du fichier "standards/blueprints/project_adr_template.md"
  Et l'absence de surcharge locale
  Quand GrillEngine tente de générer un ADR
  Alors le moteur bascule sur le gabarit d'urgence en mémoire (EMERGENCY_FALLBACK_TEMPLATE)
  Et un log WARNING est consigné sans lever d'exception bloquante
  Et l'ADR est correctement écrit sur le disque
```

### 4. Pilier UX & Rétrocompatibilité
```gherkin
Scénario: Substitution tolérante avec valeurs par défaut
  Étant donné un appel à record_adr avec un champ context ou positives vide
  Quand le gabarit est rendu
  Alors les balises correspondantes sont remplacées par les formulations textuelles conventionnelles
  Et aucun message d'erreur n'interrompt le flux de travail de l'utilisateur
```

---

### Contrats d'Échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-280 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — composant Python interne de templating et de génération d'ADRs (`GrillEngine.record_adr()`), sans interface HTTP ni route REST distante `[API de soumission à définir]` (ADR-0319).

**Contrats Python Internes :**
- `resolve_adr_template(project_path: Optional[Path]) -> str`
- `render_adr_content(template_str: str, data: Dict[str, Any]) -> str`

---

## Logique Métier & Algorithme Backend


### `resolve_adr_template(project_path: Optional[Path]) -> str`
1. Vérifier si `project_path / "docs/01-architecture/template.md"` existe. Si oui, lire et retourner en UTF-8.
2. Sinon, localiser la racine du framework mLoop et vérifier `standards/blueprints/project_adr_template.md`. Si oui, lire et retourner.
3. Si échec ou `IOError`, logger `logger.warning("Blueprint ADR introuvable, utilisation du fallback mémoire")` et retourner `EMERGENCY_FALLBACK_TEMPLATE`.

### `render_adr_content(template_str: str, data: Dict[str, Any]) -> str`
1. Normaliser les clés attendues (`ADR_ID`, `TITLE`, `DATE`, `CONTEXT`, `DECISION`, `POSITIVES`, `NEGATIVES`).
2. Appliquer les valeurs par défaut si vide.
3. Exécuter le remplacement direct de `f"{{{{{key}}}}}"` par `str(value)`.
4. Remplacer également `{key.lower()}` pour rétrocompatibilité.
5. Retourner le texte final rendu.

---

## Références
- 🏛️ **ADR Associés** : [ADR-0320](../../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md) · [ADR-012](../../../docs/01-architecture/ADR-012_epic-28_assainissement_generateur_adr_clean_architecture.md)
- 📂 **Blueprint Canonique** : [`standards/blueprints/project_adr_template.md`](../../../../standards/blueprints/project_adr_template.md)
- 📦 **Épopée Parente** : [`EPIC-28-ADR-CLEAN-ARCHITECTURE`](../epics/epic_adr_clean_architecture.md)