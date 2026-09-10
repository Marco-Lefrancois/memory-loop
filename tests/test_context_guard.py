from src.utils.context_guard import ContextGuard
from src.bridges.mcp_proxy_router import validate_tool_registry

def test_context_guard_valid_pairing():
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "call", "tool_calls": [{"id": "call_1", "name": "search"}]},
        {"role": "tool", "tool_call_id": "call_1", "content": "result"}
    ]
    assert ContextGuard.validate_tool_message_pairing(messages) is True

def test_context_guard_dangling_tool_call():
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "call", "tool_calls": [{"id": "call_1", "name": "search"}]},
        # Missing tool result
        {"role": "user", "content": "next prompt"}
    ]
    assert ContextGuard.validate_tool_message_pairing(messages) is False

def test_context_guard_truncate_tool_output():
    long_output = "\n".join([f"line {i}" for i in range(200)])
    truncated = ContextGuard.truncate_tool_output(long_output, max_lines=70, head_lines=50, tail_lines=20)
    assert len(truncated.splitlines()) < 100
    assert "SHA256:" in truncated
    assert "line 0" in truncated
    assert "line 199" in truncated

def test_mcp_tool_registry_neutrality():
    assert validate_tool_registry() is True
