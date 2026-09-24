# System Patterns — Memory Loop (mLoop)

## 1. Architecture Globale
- Orchestration Bimodale : OpenCode (Headless/CI/Fast) + Cline (Plan-Lock/Teams/IDE).
- Isolation Out-of-Process : Herdr gère les sessions dans des fenêtres PTY isolées (ADR-0346).
- Fallback Déterministe : OpenCode est le filet de sécurité inviolable advenant un échec de Cline.

## 2. Key Architecture Decision Records (ADRs)
- ADR-0202 : Modularité interne et plafond strict de 300 lignes par fichier.
- ADR-0346 : Registre multi-runtimes des workers Herdr.
- ADR-0375 : Réalignement du cycle de vie en 5 phases universelles et EvidencePacks.
- ADR-0376 : Standard de rigueur d'ingénierie et audit 360° Zéro Blindspot en 7 couches.
- ADR-0377 : Sonde et diagnostic déterministe des runtimes agents aval.

## 3. Invariants Inviolables
- Pas de suppression silencieuse de code.
- Pas de saut de phase : mode --plan obligatoire en Phase 2.
- Typage strict et gestion des shims Windows (`.cmd` / `.ps1`).
