"""
Diagnostics Pipeline - mLoop
Génération et gestion des harnais de reproduction déterministes et rouge-capables.
"""

from pathlib import Path
import datetime
from typing import Dict, List, Optional

HARNESS_TEMPLATE = """# 🧪 Diagnostic Harness : {symptom_name}

> [!WARNING]
> Règle mLoop : Aucun code correctif ne doit être appliqué tant que ce harnais n'est pas exécuté et confirmé ROUGE sur le symptôme.

## Symptôme Rapporté
{symptom_description}

## Invocations du Harnais (Red-Capable & Deterministic)
```bash
{command_invocation}
```

## Résultats Observés
- [ ] **Rouge Initial (Pass/Fail Signal)** : {initial_output}
- [ ] **Vert post-correctif (Validation)** : En attente

---
*Généré par mLoop Diagnostic Engine le {date}.*
"""

class DiagnosticEngine:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.scratch_dir = project_path / "scratch" / "diagnostics"

    def create_harness(self, symptom_name: str, symptom_description: str, command_invocation: str, initial_output: str) -> Path:
        """Génère une fiche de harnais de reproduction sous scratch/diagnostics/."""
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"harness_{symptom_name.lower().replace(' ', '_')}.md"
        harness_path = self.scratch_dir / filename
        
        date_str = datetime.date.today().isoformat()
        content = HARNESS_TEMPLATE.format(
            symptom_name=symptom_name,
            symptom_description=symptom_description,
            command_invocation=command_invocation,
            initial_output=initial_output,
            date=date_str
        )
        harness_path.write_text(content, encoding="utf-8")
        return harness_path
