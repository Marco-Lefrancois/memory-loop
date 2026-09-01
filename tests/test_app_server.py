import pytest
import json
from src.daemon.app_server import AppServerProtocol


def test_app_server_initialize():
    server = AppServerProtocol()
    req = json.dumps({"method": "initialize", "id": 1})
    res = json.loads(server.handle_request(req))
    
    assert res["id"] == 1
    assert "result" in res
    assert res["result"]["serverInfo"]["name"] == "mloop_app_server"


def test_app_server_thread_lifecycle():
    server = AppServerProtocol()
    # 1. Thread start
    req1 = json.dumps({"method": "thread/start", "params": {"project": "Memory Loop"}, "id": 2})
    res1 = json.loads(server.handle_request(req1))
    thread_id = res1["result"]["threadId"]
    assert thread_id.startswith("mloop-th-")
    
    # 2. Turn start
    req2 = json.dumps({"method": "turn/start", "params": {"threadId": thread_id, "input": "Check stories"}, "id": 3})
    res2 = json.loads(server.handle_request(req2))
    assert res2["result"]["turnId"].startswith("turn-")
    assert res2["result"]["status"] == "completed"


def test_app_server_roles_list():
    server = AppServerProtocol()
    req = json.dumps({"method": "roles/list", "id": 4})
    res = json.loads(server.handle_request(req))
    roles = res["result"]["roles"]
    role_names = [r["name"] for r in roles]
    assert "sentinel" in role_names
    assert "plan" in role_names
