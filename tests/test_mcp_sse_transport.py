"""
Tests d'intégration pour MLOOP-103-BE : Transport MCP SSE et Event Bus.
"""

import asyncio
import json
import pytest
from unittest.mock import patch

from src.bridges.mcp_event_bus import MCPEventBus, get_event_bus
from src.bridges.mcp_loop_mem import process_message


class TestMCPEventBus:
    """Tests du bus d'événements MCP asynchrone."""

    def setup_method(self):
        self.bus = MCPEventBus(max_clients=8, heartbeat_interval=15.0)

    def test_initial_state(self):
        assert self.bus.client_count == 0
        stats = self.bus.get_session_stats()
        assert stats["active_subscribers"] == 0
        assert stats["max_clients"] == 8
        assert stats["sequence"] == 0

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self):
        queue = await self.bus.subscribe("client-1")
        assert self.bus.client_count == 1
        assert isinstance(queue, asyncio.Queue)

        await self.bus.unsubscribe("client-1")
        assert self.bus.client_count == 0

    @pytest.mark.asyncio
    async def test_subscribe_max_clients_exceeded(self):
        for i in range(8):
            await self.bus.subscribe(f"client-{i}")
        assert self.bus.client_count == 8

        with pytest.raises(RuntimeError, match="Pool SSE plein"):
            await self.bus.subscribe("client-overflow")

    @pytest.mark.asyncio
    async def test_broadcast_delivers_to_subscribers(self):
        q1 = await self.bus.subscribe("c1")
        q2 = await self.bus.subscribe("c2")

        await self.bus.broadcast("test_event", {"key": "value"})

        frame1 = q1.get_nowait()
        frame2 = q2.get_nowait()
        assert frame1 is not None
        assert frame2 is not None
        assert "event: test_event" in frame1
        assert '"key"' in frame1 and '"value"' in frame1
        assert "event: test_event" in frame2

    @pytest.mark.asyncio
    async def test_broadcast_purges_dead_client(self):
        await self.bus.subscribe("dead-client")
        await self.bus.unsubscribe("dead-client")

        await self.bus.broadcast("test", {"x": 1})
        assert self.bus.client_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_increments_sequence(self):
        await self.bus.subscribe("c1")
        await self.bus.broadcast("ev1", {"a": 1})
        await self.bus.broadcast("ev2", {"b": 2})
        assert self.bus._sequence == 2

    @pytest.mark.asyncio
    async def test_notify_resource_updated(self):
        q = await self.bus.subscribe("c1")
        await self.bus.notify_resource_updated(
            uri="mloop://project/test/observation/1", session_id="sess-1"
        )

        frame = q.get_nowait()
        assert frame is not None
        assert "resources/updated" in frame
        data_str = frame.split("data: ", 1)[1].split("\n\n")[0]
        data = json.loads(data_str)
        assert data["method"] == "notifications/resources/updated"
        assert data["params"]["uri"] == "mloop://project/test/observation/1"

    @pytest.mark.asyncio
    async def test_notify_tools_list_changed(self):
        q = await self.bus.subscribe("c1")
        await self.bus.notify_tools_list_changed(session_id="sess-1")

        frame = q.get_nowait()
        assert frame is not None
        assert "tools/list_changed" in frame
        data_str = frame.split("data: ", 1)[1].split("\n\n")[0]
        data = json.loads(data_str)
        assert data["method"] == "notifications/tools/list_changed"

    @pytest.mark.asyncio
    async def test_heartbeat_returns_keepalive(self):
        await self.bus.subscribe("c1")
        hb = await self.bus.generate_heartbeat("c1")
        assert hb is not None
        assert ": keepalive" in hb

    @pytest.mark.asyncio
    async def test_heartbeat_returns_none_for_unknown_client(self):
        hb = await self.bus.generate_heartbeat("unknown")
        assert hb is None

    def test_format_sse_frame(self):
        frame = MCPEventBus._format_sse_frame("ping", {"ts": 123})
        assert frame == 'event: ping\ndata: {"ts":123}\n\n'

    def test_singleton_get_event_bus(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2


class TestMCPSSEServer:
    """Tests du serveur SSE avec test client FastAPI."""

    def setup_method(self):
        self.bus = MCPEventBus(max_clients=4)
        from src.bridges.mcp_sse_server import _create_app

        self.app = _create_app(self.bus)

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "active_subscribers" in data

    @pytest.mark.asyncio
    async def test_messages_endpoint_valid_jsonrpc(self):
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/messages",
                content=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {},
                    }
                ),
                headers={"Content-Type": "application/json"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "serverInfo" in data["result"]

    @pytest.mark.asyncio
    async def test_messages_endpoint_malformed_json(self):
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/messages",
                content="not json at all",
                headers={"Content-Type": "application/json"},
            )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == -32700

    @pytest.mark.asyncio
    async def test_messages_endpoint_ping(self):
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/messages",
                content=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "ping",
                        "params": {},
                    }
                ),
                headers={"Content-Type": "application/json"},
            )
        assert resp.status_code == 200
        assert resp.json().get("ok") is True

    @pytest.mark.asyncio
    async def test_messages_endpoint_tools_list(self):
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/messages",
                content=json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 10,
                        "method": "tools/list",
                        "params": {},
                    }
                ),
                headers={"Content-Type": "application/json"},
            )
        assert resp.status_code == 200
        data = resp.json()
        tools = data["result"]["tools"]
        names = {t["name"] for t in tools}
        assert "loop_mem_search" in names


class TestProcessMessageNotifications:
    """Tests que process_message émet bien les notifications via le bus."""

    def setup_method(self):
        self.bus = MCPEventBus(max_clients=4)

    @pytest.mark.asyncio
    async def test_set_phase_emits_tools_list_changed(self):
        q = await self.bus.subscribe("test-client")

        with patch("src.bridges.mcp_loop_mem.get_event_bus", return_value=self.bus):
            req = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": "set_phase", "arguments": {"phase": "BUILD"}},
                }
            )
            raw_res = process_message(req)

        assert raw_res is not None
        await asyncio.sleep(0.1)

        assert q.qsize() > 0
        frame = q.get_nowait()
        assert frame is not None
        assert "tools/list_changed" in frame


class TestSSEHandshake:
    """Tests du handshake SSE et de la réception des trames."""

    def setup_method(self):
        self.bus = MCPEventBus(max_clients=4)

    @pytest.mark.asyncio
    async def test_subscribe_and_receive_broadcast(self):
        q = await self.bus.subscribe("handshake-client")

        welcome = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "test-server", "version": "1.0.0"},
            },
        }
        welcome_frame = self.bus._format_sse_frame("initialized", welcome)
        q.put_nowait(welcome_frame)

        await self.bus.notify_resource_updated(uri="mloop://project/test/observation/42")

        frames = []
        while not q.empty():
            frames.append(q.get_nowait())

        assert len(frames) == 2
        assert "initialized" in frames[0]
        assert "resources/updated" in frames[1]

    @pytest.mark.asyncio
    async def test_multiple_subscribers_receive_same_event(self):
        queues = []
        for i in range(3):
            q = await self.bus.subscribe(f"multi-{i}")
            queues.append(q)

        await self.bus.broadcast("shared_event", {"msg": "hello"})

        for q in queues:
            frame = q.get_nowait()
            assert "shared_event" in frame
            assert '"msg"' in frame and '"hello"' in frame
