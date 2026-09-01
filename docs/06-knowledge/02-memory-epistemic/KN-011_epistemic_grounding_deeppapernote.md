---
id: KN-011
title: Grounding Épistémique et Découplage des Preuves (DeepPaperNote)
domain: memory-epistemic
status: VALIDATED
confidence_score: 0.97
tags: [epistemic, deeppapernote, fact-search, anti-hallucination, grounding]
related_adrs: [ADR-0326, ADR-0334, ADR-0335]
---

# 🔬 Grounding Épistémique et Découplage des Preuves

> [!ABSTRACT]
> Protocole anti-hallucination imposant de distinguer formellement ce qu'une source technique prouve de manière vérifiable vs ce qui relève de l'extrapolation ou du non-testé.

## 1. Les 3 Dimensions Épistémiques
- **what_it_actually_proves** : Données chiffrées, captures, code source réel validé.
- **what_it_does_not_prove** : Cas limites non testés, hypothèses non vérifiées.
- **claim_boundaries** : Périmètre strict de validité fonctionnelle.
