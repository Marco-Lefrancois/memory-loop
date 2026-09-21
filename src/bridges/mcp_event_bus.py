"""
mcp_event_bus.py — Bus d'événements MCP asynchrone pour diffusion SSE (MLOOP-103-BE).

Gère le pool de connexions SSE et diffuse les notifications MCP :
- notifications/resources/updated lors de mutations de ressources
- notifications/tools/list_changed lors de basculements de phase

Conforme aux contraintes ADR-0202 (≤300 lignes) et ADR-0369 (context managers,
timeout explicite, logs structurés).
"""

import asyncio
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class MCPEventBus:
    """Bus d'événements MCP pour diffusion SSE temps réel."""

    def __init__(self, max_clients: int = 64, heartbeat_interval: float = 15.0):
        self._subscribers: dict[str, asyncio.Queue[str | None]] = {}
        self._max_clients = max_clients
        self._heartbeat_interval = heartbeat_interval
        self._sequence: int = 0
        self._lock = asyncio.Lock()

    @property
    def client_count(self) -> int:
        return len(self._subscribers)

    async def subscribe(self, client_id: str) -> asyncio.Queue[str | None]:
        """Abonne un client et retourne sa file d'attente d'événements."""
        if len(self._subscribers) >= self._max_clients:
            raise RuntimeError(f"Pool SSE plein ({self._max_clients} clients max).")
        async with self._lock:
            queue: asyncio.Queue[str | None] = asyncio.Queue(maxsize=256)
            self._subscribers[client_id] = queue
            logger.info(
                "SSE subscribe",
                extra={"client_id": client_id, "pool_size": len(self._subscribers)},
            )
            return queue

    async def unsubscribe(self, client_id: str) -> None:
        """Désabonne un client du pool."""
        async with self._lock:
            removed = self._subscribers.pop(client_id, None)
        if removed is not None:
            logger.info(
                "SSE unsubscribe",
                extra={"client_id": client_id, "pool_size": len(self._subscribers)},
            )

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Diffuse un événement MCP à tous les abonnés actifs."""
        self._sequence += 1
        frame = self._format_sse_frame(event_type, data)
        dead_clients: list[str] = []

        async with self._lock:
            snapshot = dict(self._subscribers)

        for cid, queue in snapshot.items():
            try:
                queue.put_nowait(frame)
            except asyncio.QueueFull:
                logger.warning(
                    "SSE queue overflow, purging oldest",
                    extra={"client_id": cid},
                )
                try:
                    queue.get_nowait()
                    queue.put_nowait(frame)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    dead_clients.append(cid)

        for cid in dead_clients:
            await self.unsubscribe(cid)

    def build_resource_updated_notification(
        self, uri: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """Construit une notification resources/updated conforme MCP."""
        return {
            "jsonrpc": "2.0",
            "method": "notifications/resources/updated",
            "params": {
                "uri": uri,
                "_meta": {
                    "sequence": self._sequence,
                    "timestamp": time.time(),
                    "sessionId": session_id,
                },
            },
        }

    def build_tools_list_changed_notification(
        self, session_id: str | None = None
    ) -> dict[str, Any]:
        """Construit une notification tools/list_changed conforme MCP."""
        return {
            "jsonrpc": "2.0",
            "method": "notifications/tools/list_changed",
            "params": {
                "_meta": {
                    "sequence": self._sequence,
                    "timestamp": time.time(),
                    "sessionId": session_id,
                },
            },
        }

    async def notify_resource_updated(self, uri: str, session_id: str | None = None) -> None:
        """Diffuse une notification resources/updated."""
        notification = self.build_resource_updated_notification(uri, session_id)
        await self.broadcast("resources/updated", notification)

    async def notify_tools_list_changed(self, session_id: str | None = None) -> None:
        """Diffuse une notification tools/list_changed."""
        notification = self.build_tools_list_changed_notification(session_id)
        await self.broadcast("tools/list_changed", notification)

    async def generate_heartbeat(self, client_id: str) -> str | None:
        """Retourne un heartbeat SSE keepalive ou None si le client est déconnecté."""
        queue = self._subscribers.get(client_id)
        if queue is None:
            return None
        return ": keepalive\n\n"

    @staticmethod
    def _format_sse_frame(event_type: str, data: dict[str, Any]) -> str:
        """Formate un événement au format SSE standard."""
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f"event: {event_type}\ndata: {payload}\n\n"

    def get_session_stats(self) -> dict[str, Any]:
        """Retourne les statistiques du bus pour observabilité."""
        return {
            "active_subscribers": len(self._subscribers),
            "max_clients": self._max_clients,
            "sequence": self._sequence,
            "heartbeat_interval_s": self._heartbeat_interval,
        }


_bus_instance: MCPEventBus | None = None


def get_event_bus() -> MCPEventBus:
    """Retourne l'instance singleton du bus d'événements."""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = MCPEventBus()
    return _bus_instance
