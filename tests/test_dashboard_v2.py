"""
tests/test_dashboard_v2.py — Tests Unitaires & d'Intégration Dashboard Agentique 2.0.

Valide les endpoints REST modulaires du Cockpit Agentique mLoop :
- /api/overview/stats
- /api/swarm/topology
- /api/traces/tree
- /api/resilience/posture & rollback
- /api/dream-rsi/summary
- /api/governance/gates
- Cache mémoire avec invalidation mtime
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369 (robustesse Python senior).
"""
import pytest
from fastapi.testclient import TestClient

from src.dashboard.cache import clear_dashboard_cache, get_cached_or_compute
from src.dashboard.server import app

client = TestClient(app)


def setup_function():
    """Réinitialise le cache mémoire avant chaque test."""
    clear_dashboard_cache()


def test_dashboard_root_html():
    """Vérifie que la racine du dashboard retourne le code HTML du cockpit 2.0."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "COCKPIT 2.0" in response.text
    assert "mLoop Sovereign Hub" in response.text


def test_overview_stats_endpoint():
    """Vérifie la télémétrie consolidée de l'endpoint Overview."""
    response = client.get("/api/overview/stats?project=mLoop")
    assert response.status_code == 200
    data = response.json()
    assert "resilience" in data
    assert "dream_rsi" in data
    assert "swarm" in data
    assert "lifecycle" in data
    assert data["resilience"]["score"] >= 0
    assert data["dream_rsi"]["gain_vs_pi0"] >= 0.0
    assert data["swarm"]["total_roles"] == 6


def test_swarm_topology_endpoint():
    """Vérifie la cartographie de l'essaim et le calcul du Blast Radius."""
    response = client.get("/api/swarm/topology?project=mLoop")
    assert response.status_code == 200
    data = response.json()
    assert data["total_agents"] >= 6
    assert data["unattended_safe_count"] >= 1
    assert data["hitl_required_count"] >= 1

    roles = [a["role"] for a in data["agents"]]
    assert "orchestrator" in roles
    assert "worker" in roles
    assert "sentinel" in roles

    # Vérification des propriétés de chaque agent
    for ag in data["agents"]:
        assert "blast_radius_level" in ag
        assert "blast_score" in ag
        assert "authorized_write_paths" in ag
        assert "forbidden_paths" in ag


def test_traces_tree_endpoint():
    """Vérifie l'exposition des délibérations cognitives et critiques Sentinel."""
    response = client.get("/api/traces/tree?project=mLoop&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "traces" in data
    assert "stats" in data
    assert len(data["traces"]) <= 10

    if data["traces"]:
        tr = data["traces"][0]
        assert "agent_role" in tr
        assert "thinking" in tr
        assert "critique" in tr
        assert "status" in tr["critique"]


def test_resilience_posture_endpoint():
    """Vérifie la posture de cyber-résilience et les checkpoints horodatés SHA-256."""
    response = client.get("/api/resilience/posture?project=mLoop")
    assert response.status_code == 200
    data = response.json()
    assert "resilience_index" in data
    assert "detailed_checkpoints" in data
    assert "memory_hygiene" in data
    assert "evidence" in data

    if data["detailed_checkpoints"]:
        cp = data["detailed_checkpoints"][0]
        assert "filename" in cp
        assert "sha256" in cp
        assert len(cp["sha256"]) == 64  # Format SHA-256 valide


def test_dream_rsi_summary_endpoint():
    """Vérifie le diagnostic d'isolation du harnais et les méta-politiques."""
    response = client.get("/api/dream-rsi/summary?project=mLoop")
    assert response.status_code == 200
    data = response.json()
    assert "harness_diagnosis" in data
    assert "selected_policy" in data
    assert "candidates_frontier" in data
    assert "tokens_saved_estimate" in data

    diag = data["harness_diagnosis"]
    assert "distribution" in diag
    assert "Memory" in diag["distribution"]
    assert "Tooling" in diag["distribution"]
    assert "Gate" in diag["distribution"]
    assert "Prompt" in diag["distribution"]


def test_governance_gates_endpoint():
    """Vérifie les 6 portes de gouvernance FSM (Gate 0 à Gate 5)."""
    response = client.get("/api/governance/gates?project=mLoop")
    assert response.status_code == 200
    data = response.json()
    assert "current_stage" in data
    assert "gates" in data
    assert len(data["gates"]) == 6

    gate_0 = data["gates"][0]
    assert gate_0["gate_number"] == 0
    assert "name" in gate_0
    assert "is_approved" in gate_0


@pytest.mark.parametrize(
    "role_filter",
    ["sentinel", "worker", "orchestrator"],
)
def test_traces_filtering_by_role(role_filter: str):
    """Vérifie le filtrage des traces par rôle d'agent."""
    response = client.get(f"/api/traces/tree?project=mLoop&role={role_filter}&limit=5")
    assert response.status_code == 200
    data = response.json()
    for tr in data["traces"]:
        assert tr["agent_role"].lower() == role_filter.lower()


def test_dashboard_cache_invalidation():
    """Vérifie le fonctionnement du cache mémoire et du TTL."""
    calls_count = 0

    def compute():
        nonlocal calls_count
        calls_count += 1
        return {"val": calls_count}

    r1 = get_cached_or_compute("test_key", None, compute, ttl_seconds=1.0)
    assert r1["val"] == 1
    assert calls_count == 1

    # Deuxième appel immédiat : doit retourner la valeur en cache sans recalcul
    r2 = get_cached_or_compute("test_key", None, compute, ttl_seconds=1.0)
    assert r2["val"] == 1
    assert calls_count == 1

    # Invalidation manuelle
    clear_dashboard_cache()
    r3 = get_cached_or_compute("test_key", None, compute, ttl_seconds=1.0)
    assert r3["val"] == 2
    assert calls_count == 2


def test_ledger_endpoint():
    """Vérifie la robustesse de l'endpoint Token Ledger et la rétrocompatibilité (by_model & summary)."""
    # 1. Test projet Metro_FOOD
    response = client.get("/api/ledger?project=Metro_FOOD")
    assert response.status_code == 200
    data = response.json()
    assert "filtered_tokens" in data
    assert "filtered_cost_usd" in data
    assert "by_model" in data
    assert "summary" in data
    assert "global_summary" in data
    assert "entries" in data
    assert isinstance(data["by_model"], dict)
    assert isinstance(data["entries"], list)

    # 2. Test ALL
    response_all = client.get("/api/ledger?project=ALL")
    assert response_all.status_code == 200
    data_all = response_all.json()
    assert data_all["total_entries"] >= 0
    assert "by_source" in data_all["global_summary"]
    assert "by_project" in data_all["global_summary"]


def test_business_modules_resolution_and_ledger():
    """Vérifie la prise en compte des modules métiers : Boire & Frères, Metro Commerce, Food, Pharma, Shared."""
    # 1. Vérifier que get_projects expose les modules avec libellés conviviaux
    r_projs = client.get("/api/projects")
    assert r_projs.status_code == 200
    p_data = r_projs.json()
    formatted_dict = {p["id"]: p["name"] for p in p_data["projects_formatted"]}
    assert "Boire & Frères" in formatted_dict.get("BoireFrere_Segment2", "")
    assert "Alimentation" in formatted_dict.get("Metro_FOOD", "")
    assert "Commerce" in formatted_dict.get("Metro_COMMERCE", "")
    assert "Pharma" in formatted_dict.get("Metro_SANTE", "")
    assert "Shared" in formatted_dict.get("Metro_SHARED", "")

    # 2. Vérifier les alias et la télémétrie Ledger de chaque module
    test_cases = [
        ("boire", "BoireFrere_Segment2", True),
        ("BoireFrere_Segment2", "BoireFrere_Segment2", True),
        ("food", "Metro_FOOD", True),
        ("Metro_FOOD", "Metro_FOOD", True),
        ("commerce", "Metro_COMMERCE", True),
        ("Metro_COMMERCE", "Metro_COMMERCE", True),
        ("pharma", "Metro_SANTE", True),
        ("Metro_SANTE", "Metro_SANTE", True),
        ("Metro_SHARED", "Metro_SHARED", False),
    ]

    for query_name, expected_canon, has_data in test_cases:
        res = client.get(f"/api/ledger?project={query_name}")
        assert res.status_code == 200
        payload = res.json()
        assert payload["project"] == expected_canon
        if has_data:
            assert payload["filtered_tokens"] > 0
            assert payload["total_entries"] > 0
        assert "summary" in payload
        assert "by_model" in payload

    # 3. Vérifier les stats Cockpit Overview pour chaque module
    for mod in ["BoireFrere_Segment2", "Metro_FOOD", "Metro_COMMERCE", "Metro_SANTE"]:
        r_stats = client.get(f"/api/overview/stats?project={mod}")
        assert r_stats.status_code == 200
        s_data = r_stats.json()
        assert s_data["project_name"] == mod
        assert "resilience" in s_data
        assert "dream_rsi" in s_data
