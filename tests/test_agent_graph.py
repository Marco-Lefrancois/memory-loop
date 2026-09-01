import pytest
from pathlib import Path
import tempfile
from src.engine.agent_graph import AgentGraphStore, ThreadSpawnEdgeStatus


def test_agent_graph_spawn_and_close():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_agent_graph.db"
        store = AgentGraphStore(db_path=db_path)
        
        # 1. Enregistrer un spawn
        edge = store.record_spawn(
            parent_thread_id="main-thread-01",
            child_thread_id="worker-child-01",
            role="sentinel"
        )
        assert edge.status == ThreadSpawnEdgeStatus.OPEN
        assert edge.role == "sentinel"
        
        # Vérifier liste open edges
        open_edges = store.list_open_edges()
        assert len(open_edges) == 1
        assert open_edges[0].child_thread_id == "worker-child-01"
        
        # 2. Fermer l'arête
        closed = store.close_edge("worker-child-01", result_summary="Audit INVEST validé (100%).")
        assert closed is True
        
        # Vérifier qu'il n'y a plus d'arête ouverte
        open_edges_after = store.list_open_edges()
        assert len(open_edges_after) == 0
        
        # Vérifier que les enfants du parent sont listables
        children = store.list_children("main-thread-01")
        assert len(children) == 1
        assert children[0].status == ThreadSpawnEdgeStatus.CLOSED
        assert children[0].result_summary == "Audit INVEST validé (100%)."
