# Gates: Phase Interrogatoire 1:1 Grill-Me & Arbitrage d'Architecture
OWNS: docs/01-architecture/ADR-*.md, docs/04-transverse/00-questions-ouvertes.md, memory/evidence/**

Scope: Alignement métier 1:1, résolution de l'arbre Frontier Design Tree, création d'ADRs et preuve de non-hallucination

- [ ] G1: Toutes les interrogations ouvertes sont consignées comme OQ-XXX dans 00-questions-ouvertes.md
  CHECK: python -c "from pathlib import Path; oq_file = Path('docs/04-transverse/00-questions-ouvertes.md'); print('OQ_REGISTRY_OK' if oq_file.exists() else 'OQ_REGISTRY_MISSING')"
  EXPECT: OQ_REGISTRY_OK
  EVIDENCE: pending

- [ ] G2: Les décisions d'architecture issues de l'interrogatoire sont formalisées en ADR sous docs/01-architecture/
  CHECK: python -c "from pathlib import Path; adrs = list(Path('docs/01-architecture').glob('ADR-*.md')); print('ADRS_DOCUMENTED' if len(adrs) > 0 else 'NO_ADRS')"
  EXPECT: ADRS_DOCUMENTED
  EVIDENCE: pending

- [ ] G3: Les preuves Fact-Search sont consignées dans les EvidencePacks JSON sans polluer le Markdown
  CHECK: python src/swarm.py vibe-check --project {PROJECT_NAME}
  EXPECT: /Fact-Search FTS5 Before Edit : PASS/
  EVIDENCE: pending

- [ ] G4: Le Dossier de Preuves Documentaires (<STORY_ID>_fact_dossier.md) est formalisé et archivé sous memory/evidence/
  CHECK: python -c "from pathlib import Path; dossiers = list(Path('memory/evidence').glob('*_fact_dossier.md')); print('FACT_DOSSIER_OK' if len(dossiers) > 0 else 'NO_FACT_DOSSIER')"
  EXPECT: FACT_DOSSIER_OK
  EVIDENCE: pending

- [ ] G5: Revue qualitative Sentinel / Rubber-Duck complétée sans objection bloquante (Definition of Ready)
  CHECK: python src/swarm.py rubber-duck --project {PROJECT_NAME}
  EXPECT: /Score INVEST|Revue sémantique terminée|READY/i
  EVIDENCE: pending

- [ ] G6: Handoff Ungrillables (IHM/UX) — Toute décision visuelle ou d'interaction est matérialisée par un prototype ou mockup (ADR-0389 / ADR-013)
  CHECK: python -c "from pathlib import Path; protos = list(Path('scratch/prototypes').glob('*.*')) + list(Path('docs/05-assets/mockups').glob('*.*')); print('HANDOFF_PROTOTYPES_OK' if len(protos) > 0 else 'HANDOFF_SKIPPED_OR_EMPTY')"
  EXPECT: /HANDOFF_PROTOTYPES_OK|HANDOFF_SKIPPED/
  EVIDENCE: pending

- [ ] G7: Context Health & Continuité Cognitive — Respect du budget de tokens (< 120k tokens) et interdiction formelle de purge de contexte post-grill (ADR-0389 / ADR-013)
  CHECK: python src/swarm.py grill --health --project {PROJECT_NAME}
  EXPECT: /SMART_ZONE|WARNING_ZONE|HEALTHY/
  EVIDENCE: pending


