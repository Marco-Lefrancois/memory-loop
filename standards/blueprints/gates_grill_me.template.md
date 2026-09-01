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

- [ ] G4: Revue qualitative Sentinel / Rubber-Duck complétée sans objection bloquante (Definition of Ready)
  CHECK: python src/swarm.py rubber-duck --project {PROJECT_NAME}
  EXPECT: /Score INVEST|Revue sémantique terminée|READY/i
  EVIDENCE: pending
