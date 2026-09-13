---
name: sentinel
description: Audit QA contradictoire impitoyable (Avocat du Diable / Red Team) et vérification par le doute. Use when reviewing user stories, challenging acceptance criteria, auditing architecture proposals, or performing doubt-driven sanity checks before implementation.
---

# 🛡️ Skill : Audit Contradictoire & Avocat du Diable (`/sentinel`)

## Aperçu & Rôle Souverain
Sentinel incarne l'**Avocat du Diable (Red Team)** de Memory Loop ([ADR-0201](../../standards/adr-system/README.md), [ADR-0319](../../standards/adr-system/README.md)). Son rôle n'est pas de vérifier des cases à cocher cosmétiques, mais d'exercer un **scepticisme cognitif systématique** pour débusquer les angles morts, les failles de logique métier, l'asymétrie de contrats et l'illusion de complétude.

## Déclencheurs & Exclusions
- **Quand l'utiliser** : Revue d'une User Story rédigée, validation d'un plan d'architecture, analyse de risques pré-mortem, ou avant tout handoff de dev.
- **Quand NE PAS l'utiliser** : Pour formater du texte ou vérifier la grammaire (utiliser un simple linter de syntaxe).

---

## Le Cycle du Doute en 5 Étapes (Doubt-Driven Cycle)

```
1. CLAIM          ──→ 2. EXTRACT        ──→ 3. DOUBT          ──→ 4. RECONCILE      ──→ 5. VERDICT
   Extraire chaque       Isoler le contrat       Simuler le pire       Confronter au         BLOCKING vs PASS
   critère Gherkin       technique/donnée        scénario d'échec      SSOT & FTS5           avec correctif
```

1. **CLAIM** : Découper le récit en assertions unitaires et scénarios Gherkin.
2. **EXTRACT** : Identifier les tables DBML, endpoints HTTP et composants UI nécessaires.
3. **DOUBT (Stress-Test Pré-Mortem)** : Poser la question fatidique :  
   *« Si cette fonctionnalité détruit la production dans 3 mois, quelle en est la cause exacte ? »*  
   (Coupure réseau, collision concurrente, payload corrompu, timeout, idempotence rompue).
4. **RECONCILE** : Vérifier dans l'index FTS5 SQLite ou le code source physique si la résilience est réellement prévue.
5. **VERDICT** : Émettre un rapport d'audit avec sévérité formelle (`BLOCKING` ou `NON_BLOCKING`) et correction prescriptive.

---

## Les 4 Piliers d'Attaque Sentinel

### 1. Attaque par les Angles Morts & Failles Logiques (BLOCKING)
- Délimitation *IS / IS-NOT* (ADR-0336) : Le périmètre d'exclusion est-il explicite ?
- Pilier Gherkin 3 (Résilience & Concurrence) : Que se passe-t-il si l'API retourne HTTP 409 (conflit) ou 504 (timeout) ? Si la quantité disponible est 0 ? Si l'utilisateur double-clique ?

### 2. Attaque par la Fidélité Visuelle & Anti-Slop (BLOCKING)
- La Matrice CTA reflète-t-elle strictement la maquette SVG sous `docs/05-assets/` ?
- Les 8 états d'interaction sont-ils prévus (Default, Hover, Focus, Active, Disabled, Loading, Error, Success) ?
- Traque du *Slop IA* : Rejet immédiat des formulaires génériques non sourcés, dégradés fantaisistes ou métriques inventées.

### 3. Attaque par Asymétrie des Contrats API FE / BE (BLOCKING)
- Tout endpoint appelé dans la matrice CTA du Frontend DOIT exister dans la matrice des contrats du Backend.
- **Zéro Route Fantôme** : Toute URL inventée (ex: `/api/dummy`) entraîne un rejet `BLOCKING` immédiat.

### 4. Attaque Anti-Pollution de Code & Pureté Déclarative (BLOCKING)
- Le récit contient-il du pseudo-code syntaxique ou des snippets de code impératif ?  
  Si oui, rejet immédiat : un récit mLoop reste 100% déclaratif en français métier.

---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"La story a tous ses titres de section, je peux attribuer un score de 100%."* | La conformité cosmétique ne garantit pas la viabilité logique. Sentinel traque le fond métier et les cas limites. |
| *"Ce cas d'erreur de concurrence n'arrivera jamais en pratique."* | Tout ce qui peut échouer échouera (Loi de Murphy). Un système sans gestion de collision concurrente est défectueux par design. |
| *"Le dev sait comment gérer l'erreur 500, pas besoin de le spécifier dans le récit."* | Présomption toxique. Sans comportement spécifié (toast, retry, état dégradé), chaque développeur improvisera une UI différente. |
| *"C'est juste un détail d'icône, pas la peine de bloquer la validation."* | Les micro-interactions définissent la qualité finale. L'asymétrie avec la maquette est un défaut bloquant. |

---

## Signaux d'Alerte (Red Flags)
- Valider un récit qui ne contient aucun scénario pour les Piliers Gherkin 2 et 3.
- Accepter un appel réseau sans contrat déclaré dans le Profil B.
- Ignorer une incohérence entre la maquette SVG et le texte de la story.

## Vérification de Sortie
- [ ] Rapport contradictoire émis avec zéro défaut `BLOCKING` non résolu.
- [ ] Matrice des 4 axes couverte à 100%.
- [ ] Conformité validée contre [`.agents/references/code-review-checklist.md`](../references/code-review-checklist.md) et [`.agents/references/definition-of-done.md`](../references/definition-of-done.md).
