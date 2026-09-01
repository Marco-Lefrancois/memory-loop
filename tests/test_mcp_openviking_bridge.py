"""
Tests unitaires pour le pont MCP OpenViking.
"""
import pytest
from src.bridges.mcp_openviking import (
    OpenVikingBridgeClient,
    handle_initialize,
    handle_tools_list,
    handle_tools_call
)


def test_openviking_client_graceful_unavailable():
    client = OpenVikingBridgeClient(endpoint_url="http://127.0.0.1:59999")
    status = client.status()
    assert status.get("error") is True
    assert status.get("status") == "UNAVAILABLE"


def test_openviking_mcp_protocol_initialize():
    res = handle_initialize(1)
    assert res["jsonrpc"] == "2.0"
    assert res["result"]["serverInfo"]["name"] == "mloop-openviking-bridge-mcp"


def test_openviking_mcp_protocol_tools_list():
    res = handle_tools_list(2)
    assert res["jsonrpc"] == "2.0"
    tools = res["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "openviking_find" in tool_names
    assert "openviking_tree" in tool_names
    assert "openviking_overview" in tool_names
    assert "openviking_read" in tool_names
    assert "openviking_status" in tool_names


def test_openviking_mcp_protocol_tools_call_unavailable():
    res = handle_tools_call(3, {"name": "openviking_status", "arguments": {}})
    assert res["jsonrpc"] == "2.0"
    assert len(res["result"]["content"]) == 1
    assert "UNAVAILABLE" in res["result"]["content"][0]["text"]
