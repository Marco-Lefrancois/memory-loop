"""
Classe de base pour les agents mLoop.
"""
from abc import ABC, abstractmethod
from src.state import LoopState


class BaseAgent(ABC):
    """Interface abstraite commune à tous les agents (Système 1 et Système 2)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom canonique de l'agent."""
        pass

    @abstractmethod
    def execute(self, state: LoopState) -> LoopState:
        """Exécute l'action de l'agent sur l'état courant et retourne l'état mis à jour."""
        pass
