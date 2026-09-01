# Gates: Phase Découpage Backlog & Slicing Vertical
OWNS: backlog/stories/**, backlog/sprint_backlog.md

Scope: Découpage en User Stories verticales INVEST, Gherkin 4 Piliers et intégrité des liens Jira

- [ ] G1: Le tableau d'avancement sprint_backlog.md existe et contient le tableau de découpage
  CHECK: python -c "from pathlib import Path; sb = Path('backlog/sprint_backlog.md'); print('SPRINT_BACKLOG_OK' if sb.exists() and '|' in sb.read_text(encoding='utf-8') else 'MISSING')"
  EXPECT: SPRINT_BACKLOG_OK
  EVIDENCE: pending

- [ ] G2: Chaque récit vertical respecte le gabarit officiel story_template.md (YAML Frontmatter complet)
  CHECK: python src/swarm.py struct-check --project {PROJECT_NAME} --strict
  EXPECT: /0 erreurs bloquantes|PASS/i
  EVIDENCE: pending

- [ ] G3: Les 4 Piliers Gherkin (1. Nominal, 2. Exceptions, 3. Résilience, 4. UX) sont présents dans chaque story
  CHECK: python -c "from pathlib import Path; stories = list(Path('backlog/stories').glob('*.md')); valid = all(('Nominal' in s.read_text(encoding='utf-8') and 'Exceptions' in s.read_text(encoding='utf-8') and 'Résilience' in s.read_text(encoding='utf-8') and 'UX' in s.read_text(encoding='utf-8')) for s in stories) if stories else True; print('GHERKIN_4_PILIERS_OK' if valid and len(stories) > 0 else 'GHERKIN_INCOMPLETE')"
  EXPECT: GHERKIN_4_PILIERS_OK
  EVIDENCE: pending

- [ ] G4: Référencement inter-récits conforme au standard Jira-Only (zéro chemin local dans le texte fonctionnel)
  CHECK: python src/swarm.py struct-check --project {PROJECT_NAME}
  EXPECT: /0 anomalies de référencement|PASS/i
  EVIDENCE: pending
