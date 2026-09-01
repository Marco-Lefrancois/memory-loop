"""
Actor-Model Swarm Engine — Concurrence et Boîtes aux Lettres Asynchrones.

Inspiré de l'architecture Actor-Model (Erlang OTP / Ray / AutoGen 0.4) :
- Chaque agent (orchestrator, plan, build, sentinel) possède une Mailbox typée.
- Traitement asynchrone non-bloquant avec bus d'événements interne en mémoire (`asyncio.Queue`).
- Supporte le travail simultané sur plusieurs Stories en parallèle.
"""
from __future__ import annotations

import asyncio
import json
import uuid
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field


@dataclass
class SwarmMessage:
    """Message typé échangé entre agents du Swarm."""
    sender: str
    recipient: str
    message_type: str  # e.g., "TASK_REQUEST", "PLAN_PROPOSAL", "SENTINEL_REVIEW", "GATE_APPROVAL"
    payload: Dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


class SwarmActor:
    """Acteur indépendant au sein du Swarm Memory Loop."""

    def __init__(self, name: str, role: str) -> None:
        self.name = name
        self.role = role
        self.mailbox: asyncio.Queue[SwarmMessage] = asyncio.Queue()
        self.processed_messages: List[SwarmMessage] = []
        self._running = False

    async def send(self, message: SwarmMessage) -> None:
        """Dépose un message dans la boîte aux lettres de l'acteur."""
        await self.mailbox.put(message)

    async def process_next(self, handler: Callable[[SwarmMessage], Awaitable[Optional[SwarmMessage]]]) -> Optional[SwarmMessage]:
        """Dépile et traite le message suivant de la boîte aux lettres."""
        if self.mailbox.empty():
            return None
        msg = await self.mailbox.get()
        self.processed_messages.append(msg)
        response = await handler(msg)
        self.mailbox.task_done()
        return response


class SwarmActorCoordinator:
    """Coordinateur du Swarm d'acteurs asynchrones."""

    def __init__(self) -> None:
        self.actors: Dict[str, SwarmActor] = {
            "orchestrator": SwarmActor("orchestrator", "COORDINATION"),
            "plan": SwarmActor("plan", "ANALYSIS_AND_ARCHI"),
            "build": SwarmActor("build", "IMPLEMENTATION"),
            "sentinel": SwarmActor("sentinel", "QA_AND_INVEST_GATE"),
        }

    def get_actor(self, name: str) -> SwarmActor:
        if name not in self.actors:
            self.actors[name] = SwarmActor(name, "WORKER")
        return self.actors[name]

    async def dispatch(self, message: SwarmMessage) -> None:
        """Route un message vers le destinataire approprié."""
        target = self.get_actor(message.recipient)
        await target.send(message)

    def get_swarm_status(self) -> Dict[str, Any]:
        """Retourne l'état et la charge de chaque acteur."""
        return {
            actor_name: {
                "role": actor.role,
                "pending_messages": actor.mailbox.qsize(),
                "processed_count": len(actor.processed_messages),
            }
            for actor_name, actor in self.actors.items()
        }
