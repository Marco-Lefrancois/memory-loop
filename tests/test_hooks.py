import pytest
from src.engine.hooks.registry import LifecycleHookRegistry, HookEvent


def test_lifecycle_hooks_registration_and_trigger():
    registry = LifecycleHookRegistry()
    called_events = []

    def on_session_start(event: HookEvent):
        called_events.append(f"started:{event.payload.get('project')}")
        return {"status": "ok"}

    registry.register("session_start", on_session_start)
    
    results = registry.trigger("session_start", {"project": "Memory Loop"})
    
    assert len(called_events) == 1
    assert called_events[0] == "started:Memory Loop"
    assert results == [{"status": "ok"}]


def test_lifecycle_hooks_empty_trigger():
    registry = LifecycleHookRegistry()
    results = registry.trigger("unknown_event", {})
    assert results == []
