"""
mLoop Engine - Opaque Artifact Bus (ADR-0354)
Gestion découplée des artefacts volumineux par handles immuables.
Inspiré du Planetary Prediction Engine (Google Earth AI / arXiv:2608.26088v1).
"""

from .bus import ArtifactHandle, OpaqueArtifactBus
from .boundary_wrapper import (
    ArtifactBusProtocol,
    BoundaryToolTimeoutError,
    boundary_trace,
    get_artifact_slice,
    offload_if_exceeds,
)

__all__ = [
    "ArtifactHandle",
    "OpaqueArtifactBus",
    "ArtifactBusProtocol",
    "BoundaryToolTimeoutError",
    "boundary_trace",
    "get_artifact_slice",
    "offload_if_exceeds",
]

