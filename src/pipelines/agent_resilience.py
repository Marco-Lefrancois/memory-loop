"""
mLoop Agent Resilience Façade (ADR-0202 & ADR-0371).

Découpage modulaire conforme aux seuils de complexité ADR-0202 (<300 lignes, <15 Ko).
Délègue aux sous-modules du package `src.pipelines.resilience` :
- topology.py : AgentTopology, AgentTopologyMapper, BlastRadiusLevel
- rollback.py : AgentStateRollbackEngine (PITR & Vérification SHA-256)
- audit.py : ResilienceAudit & AgentResilienceStage (PipelineStage composable)
"""
from src.pipelines.resilience.topology import (
    BlastRadiusLevel,
    AgentTopology,
    AgentTopologyMapper,
)
from src.pipelines.resilience.rollback import AgentStateRollbackEngine
from src.pipelines.resilience.audit import ResilienceAudit, AgentResilienceStage

__all__ = [
    "BlastRadiusLevel",
    "AgentTopology",
    "AgentTopologyMapper",
    "AgentStateRollbackEngine",
    "ResilienceAudit",
    "AgentResilienceStage",
]