"""
_lc_manager.py — ProjectLifecycleManager (thin shell)
SSOT Normatif : ADR-0339 / ADR-0375

Assemble TransitionsMixin + GatesMixin en un gestionnaire unique.
Toute la logique métier réside dans les mixins — ce module est un shell pur.
"""

from __future__ import annotations

from ._lc_gates import GatesMixin
from ._lc_transitions import TransitionsMixin


class ProjectLifecycleManager(TransitionsMixin, GatesMixin):
    """
    Gestionnaire de persistance et de contrôle d'accès au cycle de vie projet.

    API publique intacte pour les 10 callers (zéro modification) :
      - get_state_file(project_path)
      - get_state(project_path)
      - save_state(project_path, state, allow_regression=False)
      - init_lifecycle(project_path, initial_stage=None, force=False)
      - can_execute_command(project_path, command_name, task_type=None)
      - approve_gate(project_path, gate_number, approver, notes="")
      - clean_premature_stories(project_path, confirm=False)
      - _compute_file_sha256(file_path)           [méthode statique]
      - _find_qa_certification_report(project_path) [méthode statique]
      - _compute_stage_deliverables_hash(project_path, stage) [méthode de classe]
    """

    STATE_FILE_NAME = "lifecycle_state.json"
