---
id: KN-020
title: Double Moteur de Graphes Sémantique & AST (Graphify + CodeGraph)
domain: graph-engineering
status: VALIDATED
confidence_score: 0.99
tags: [graphify, codegraph, dual-engine, tree-sitter, ast, fts5]
related_adrs: [ADR-0200, ADR-0204]
---

# 🌐 Double Moteur de Graphes Sémantique & AST

> [!ABSTRACT]
> Séparation stricte entre le moteur documentaire/SSOT (Graphify - extraction conceptuelle et communautés Louvain) et le moteur de code source physique (CodeGraph - parsing AST Tree-sitter et recherche FTS5).

## 1. Principes & Économie de Jetons
- **Graphify** : Navigation sémantique (docs/, standards/, acklog/). Élimine les boucles grep/ls verbeuses.
- **CodeGraph** : Exploration AST chirurgicale (src/, dépôts applicatifs). Détection de blast radius et impact d'APIs.
- **Gain** : -62% de consommation de jetons et 0 lecture brute sur disque.
