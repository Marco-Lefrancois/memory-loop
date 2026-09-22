"""
Graph Router Module - Multi-Agent DAG Execution Engine for mLoop.

This module implements the Graph Engineering topology for mLoop, organizing
specialized agent roles into a Directed Acyclic Graph (DAG) with dependency
resolution, parallel execution support, evidence-pack edge carrying, context isolation,
token budget truncation, state checkpointing & resume, circuit breaker anti-deadlock,
and Herdr multiplexer live broadcasting.
Integrates with Antigravity IDE, Claude Code subagents, and OpenCode ecosystems.
"""

import os
import json
import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.pipelines.evidence import EvidencePack, EvidenceItem, EvidenceReducer
from src.utils.token_budget import TokenBudgetGuard

logger = logging.getLogger("graph_router")

class NodeCategory(str, Enum):
    """Categorizes the execution nature of a node in the graph."""
    LLM_AGENT = "llm_agent"                  # Requires LLM synthesis
    DETERMINISTIC_CODE = "deterministic_code" # Pure Python code execution (0ms LLM overhead)
    HYBRID = "hybrid"                        # Python filter + LLM verification

class RiskLevel(str, Enum):
    """Risk classification for risk-based routing."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class TaskNode:
    """Represents an atomic agent or code node in the Graph Engineering DAG."""
    id: str
    role: str  # 'orchestrator' | 'plan' | 'build' | 'sentinel' | 'critic' | 'reducer' | 'router' | 'worker'
    description: str
    blocked_by: List[str] = field(default_factory=list)
    status: str = "pending"  # 'pending' | 'running' | 'completed' | 'failed' | 'blocked_asymmetry' | 'blocked_deadlock'
    category: NodeCategory = NodeCategory.LLM_AGENT
    risk_level: RiskLevel = RiskLevel.LOW
    context_budget_tokens: int = 8000
    isolated_workspace: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    evidence_pack: Optional[EvidencePack] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class CircuitBreakerGovernor:
    """
    Governor preventing infinite recursive loops and asymmetric deadlocks (Blindspot #3 & #6).
    Enforces a strict deterministic cutoff (default max 2 resolution passes)
    and detects cycle dependencies among DAG nodes.
    """
    def __init__(self, max_attempts: int = 2):
        self.max_attempts = max_attempts
        self.attempts: Dict[str, int] = {}
        self.tripped_nodes: List[str] = []

    def record_attempt(self, node_id: str) -> bool:
        """
        Records an execution or retry attempt for a node.
        Returns True if execution is allowed, False if the circuit breaker trips (Max exceeded).
        """
        current = self.attempts.get(node_id, 0) + 1
        self.attempts[node_id] = current
        if current > self.max_attempts:
            if node_id not in self.tripped_nodes:
                self.tripped_nodes.append(node_id)
            logger.error(f"[CircuitBreaker] CUTOFF TRIPPED for node '{node_id}': {current} attempts exceeds max {self.max_attempts}")
            return False
        return True

    def is_tripped(self, node_id: str) -> bool:
        return node_id in self.tripped_nodes

    def detect_deadlock(self, nodes: Dict[str, TaskNode]) -> List[str]:
        """
        Detects circular dependencies in the DAG among non-completed nodes.
        Returns the list of node IDs involved in deadlocks.
        """
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        deadlock_nodes: List[str] = []

        def dfs(node_id: str, path: List[str]) -> bool:
            visited[node_id] = 1
            node = nodes.get(node_id)
            if not node:
                visited[node_id] = 2
                return False

            for dep_id in node.blocked_by:
                if dep_id not in nodes:
                    continue
                dep_node = nodes[dep_id]
                if dep_node.status == "completed":
                    continue
                if visited.get(dep_id, 0) == 1:
                    cycle = path + [dep_id]
                    logger.critical(f"[CircuitBreaker] DEADLOCK DETECTED: {' -> '.join(cycle)}")
                    deadlock_nodes.extend(cycle)
                    return True
                elif visited.get(dep_id, 0) == 0:
                    if dfs(dep_id, path + [dep_id]):
                        return True

            visited[node_id] = 2
            return False

        for nid in list(nodes.keys()):
            if visited.get(nid, 0) == 0 and nodes[nid].status != "completed":
                dfs(nid, [nid])

        return list(set(deadlock_nodes))


class HerdrSocketAdapter:
    """
    Adapter broadcasting live DAG orchestration events to Herdr multiplexer sockets / TUI (herdr-dagr pattern).
    """
    def __init__(self, project_dir: str, initiative_name: str):
        self.project_dir = project_dir
        self.initiative_name = initiative_name
        self.events_file = os.path.join(project_dir, "memory", "herdr_events.jsonl")
        os.makedirs(os.path.dirname(self.events_file), exist_ok=True)

    def emit_event(self, event_type: str, node_id: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Appends a structured event to herdr_events.jsonl for Herdr TUI ingestion and sends toast notifications."""
        event = {
            "initiative": self.initiative_name,
            "event_type": event_type,
            "node_id": node_id,
            "payload": payload or {},
            "timestamp": time.time()
        }
        try:
            with open(self.events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug(f"[HerdrSocketAdapter] Failed to emit event: {e}")

        # Broadcast toast notification to Herdr UI for critical or milestone events
        try:
            from src.core.herdr_adapter import herdr
            if event_type in ["circuit_breaker_triggered", "deadlock_detected", "node_failed"]:
                herdr.show_notification(
                    title=f"⚠️ mLoop Alert: {event_type.replace('_', ' ').title()}",
                    body=f"Initiative: {self.initiative_name} | Node: {node_id}",
                    sound="request",
                    position="top-right"
                )
            elif event_type in ["node_completed"]:
                herdr.show_notification(
                    title=f"✅ mLoop DAG: Node Complete",
                    body=f"Node '{node_id}' finished successfully.",
                    sound="done",
                    position="bottom-right"
                )
        except Exception as e:
            logger.warning(
                "Notification d'événement DAG non affichée",
                exc_info=True,
                extra={
                    "component": "pipelines.graph_router",
                    "operation": "handle_graph_event",
                    "error": str(e),
                },
            )


class GraphRouter:
    """
    DAG Router and Orchestration Engine for mLoop Graph Engineering.
    Manages dependency graphs, evidence packs on edges, dynamic Fan-Out,
    isolated workspace creation, execution logging, state checkpointing & resume,
    circuit-breaker governor, and Herdr TUI live broadcasting.
    """

    def __init__(self, initiative_name: str, project_dir: str, use_worktree: bool = False, max_attempts: int = 2):
        self.initiative_name = initiative_name
        self.project_dir = project_dir
        self.use_worktree = use_worktree
        self.nodes: Dict[str, TaskNode] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.circuit_breaker = CircuitBreakerGovernor(max_attempts=max_attempts)
        self.herdr_adapter = HerdrSocketAdapter(project_dir=project_dir, initiative_name=initiative_name)
        self.tmp_dir = os.path.join(project_dir, "memory", "tmp", "fanout")
        self.checkpoint_dir = os.path.join(project_dir, "memory", "tmp", "checkpoints")
        os.makedirs(self.tmp_dir, exist_ok=True)
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def add_node(self, node: TaskNode) -> None:
        """Add a task node to the DAG."""
        if not node.evidence_pack:
            node.evidence_pack = EvidencePack(source_node=node.id, initiative_name=self.initiative_name)
        
        # Setup isolated workspace folder under memory/tmp/fanout/node_<id>/
        if not node.isolated_workspace:
            node.isolated_workspace = os.path.join(self.tmp_dir, f"node_{node.id}")
            os.makedirs(node.isolated_workspace, exist_ok=True)

        self.nodes[node.id] = node
        self.herdr_adapter.emit_event("node_registered", node.id, {
            "role": node.role,
            "category": node.category.value,
            "risk_level": node.risk_level.value,
            "blocked_by": node.blocked_by
        })
        logger.debug(f"[GraphRouter] Registered node '{node.id}' (role: {node.role}, category: {node.category.value})")

    def create_ephemeral_subagent(
        self,
        node_id: str,
        role: str,
        description: str,
        blocked_by: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        permissions: Optional[Dict[str, str]] = None,
        model: Optional[str] = None,
        risk_level: RiskLevel = RiskLevel.LOW
    ) -> TaskNode:
        """
        Factory creating a Just-In-Time (JIT) Ephemeral Subagent conforming to Claude Code & Herdr standards.
        Features isolated workspace, scoped tools, permission boundaries, and tiering model.
        """
        inputs = {
            "tools": tools or ["Read", "Grep", "Glob"],
            "permissions": permissions or {"edit": "deny" if role == "sentinel" else "allow"},
            "model": model or ("opencode/nemotron-3-ultra-free" if role in ("orchestrator", "sentinel") else "opencode/deepseek-v4-flash")
        }
        node = TaskNode(
            id=node_id,
            role=role,
            description=description,
            blocked_by=blocked_by or [],
            category=NodeCategory.LLM_AGENT,
            risk_level=risk_level,
            inputs=inputs
        )
        self.add_node(node)
        return node

    def is_completed(self) -> bool:
        """Check if all nodes in the DAG have completed."""
        return all(node.status == "completed" for node in self.nodes.values())

    def check_deadlocks(self) -> List[str]:
        """Detect and escalate deadlocks in the current DAG state."""
        deadlocks = self.circuit_breaker.detect_deadlock(self.nodes)
        if deadlocks:
            for nid in deadlocks:
                if nid in self.nodes and self.nodes[nid].status != "completed":
                    self.nodes[nid].status = "blocked_deadlock"
            self.herdr_adapter.emit_event("deadlock_detected", "system", {"deadlock_nodes": deadlocks})
        return deadlocks

    def detect_file_shift_events(self, active_node_id: str) -> List[Dict[str, Any]]:
        """
        Axe 2 jcode (ADR-0308) : Bus Anti-Collision & Code-Shift Detection dans le Swarm.
        Détecte si le nœud actif modifie des artefacts ou des règles métier ciblés par d'autres nœuds en parallèle.
        """
        collisions = []
        active_node = self.nodes.get(active_node_id)
        if not active_node:
            return collisions

        active_targets = set()
        if active_node.inputs.get("target_files"):
            active_targets.update(active_node.inputs["target_files"])
        if active_node.evidence_pack:
            for item in active_node.evidence_pack.items:
                if item.target_file:
                    active_targets.add(item.target_file)

        for other_id, other_node in self.nodes.items():
            if other_id == active_node_id or other_node.status not in ("running", "completed"):
                continue

            other_targets = set()
            if other_node.inputs.get("target_files"):
                other_targets.update(other_node.inputs["target_files"])
            if other_node.evidence_pack:
                for item in other_node.evidence_pack.items:
                    if item.target_file:
                        other_targets.add(item.target_file)

            overlap = active_targets.intersection(other_targets)
            if overlap:
                event = {
                    "event_type": "file_shift_event",
                    "active_node": active_node_id,
                    "colliding_node": other_id,
                    "overlapping_files": list(overlap),
                    "timestamp": time.time()
                }
                collisions.append(event)
                logger.warning(f"[Swarm Anti-Collision] file_shift_event entre '{active_node_id}' et '{other_id}' sur {overlap}")

        return collisions

    def mark_running(self, node_id: str) -> bool:
        """
        Mark a node as running, checking Circuit Breaker limits first.
        Returns True if execution can proceed, False if tripped.
        """
        if node_id in self.nodes:
            allowed = self.circuit_breaker.record_attempt(node_id)
            if not allowed:
                self.nodes[node_id].status = "blocked_asymmetry"
                self.nodes[node_id].error = f"Circuit Breaker tripped: exceeded {self.circuit_breaker.max_attempts} attempts."
                self.herdr_adapter.emit_event("circuit_breaker_triggered", node_id, {
                    "attempts": self.circuit_breaker.attempts.get(node_id, 0),
                    "max_attempts": self.circuit_breaker.max_attempts
                })
                self.save_checkpoint()
                return False

            self.nodes[node_id].status = "running"
            self.nodes[node_id].started_at = time.time()
            self.detect_file_shift_events(node_id)
            self.herdr_adapter.emit_event("node_started", node_id, {
                "role": self.nodes[node_id].role,
                "attempt": self.circuit_breaker.attempts.get(node_id, 1)
            })
            logger.info(f"[GraphRouter] Node '{node_id}' started execution.")
            return True
        return False

    def mark_completed(self, node_id: str, outputs: Optional[Dict[str, Any]] = None, evidence_pack: Optional[EvidencePack] = None) -> None:
        """Mark a node as successfully completed, record evidence, emit Herdr event, and save checkpoint."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.status = "completed"
            node.completed_at = time.time()
            if outputs:
                node.outputs.update(outputs)
            if evidence_pack:
                node.evidence_pack = evidence_pack

            elapsed = (node.completed_at - node.started_at) if node.started_at else 0
            
            # Log execution entry
            self.execution_log.append({
                "node_id": node.id,
                "role": node.role,
                "category": node.category.value,
                "status": "completed",
                "elapsed_seconds": round(elapsed, 3),
                "highest_risk": node.evidence_pack.get_highest_risk() if node.evidence_pack else "LOW",
                "evidence_items_count": len(node.evidence_pack.items) if node.evidence_pack else 0
            })
            self.herdr_adapter.emit_event("node_completed", node_id, {
                "elapsed_seconds": round(elapsed, 3),
                "evidence_count": len(node.evidence_pack.items) if node.evidence_pack else 0
            })
            logger.info(f"[GraphRouter] Node '{node_id}' completed in {elapsed:.2f}s.")
            
            # Save state checkpoint after each node completion
            self.save_checkpoint()

    def mark_failed(self, node_id: str, error: str) -> None:
        """Mark a node as failed with an error message."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.status = "failed"
            node.error = error
            node.completed_at = time.time()
            elapsed = (node.completed_at - node.started_at) if node.started_at else 0

            self.execution_log.append({
                "node_id": node.id,
                "role": node.role,
                "status": "failed",
                "elapsed_seconds": round(elapsed, 3),
                "error": error
            })
            self.herdr_adapter.emit_event("node_failed", node_id, {
                "error": error,
                "elapsed_seconds": round(elapsed, 3)
            })
            logger.error(f"[GraphRouter] Node '{node_id}' FAILED: {error}")
            self.save_checkpoint()

    def save_checkpoint(self) -> str:
        """Saves current DAG execution state to memory/tmp/checkpoints/<initiative>.json."""
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{self.initiative_name}.json")
        checkpoint_data = {
            "initiative": self.initiative_name,
            "timestamp": time.time(),
            "nodes": {
                nid: {
                    "role": n.role,
                    "category": n.category.value,
                    "status": n.status,
                    "blocked_by": n.blocked_by,
                    "outputs": n.outputs,
                    "evidence_pack": n.evidence_pack.to_dict() if n.evidence_pack else None,
                    "started_at": n.started_at,
                    "completed_at": n.completed_at,
                    "error": n.error
                }
                for nid, n in self.nodes.items()
            },
            "execution_log": self.execution_log
        }
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        logger.debug(f"[GraphRouter] Checkpoint saved to '{checkpoint_path}'")
        return checkpoint_path

    def load_checkpoint(self) -> bool:
        """
        Restores completed nodes from memory/tmp/checkpoints/<initiative>.json.
        Returns True if a checkpoint was successfully loaded, False otherwise.
        """
        checkpoint_path = os.path.join(self.checkpoint_dir, f"{self.initiative_name}.json")
        if not os.path.exists(checkpoint_path):
            logger.info(f"[GraphRouter] No checkpoint found for '{self.initiative_name}'.")
            return False

        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            restored_count = 0
            for nid, ndata in data.get("nodes", {}).items():
                if nid in self.nodes and ndata.get("status") == "completed":
                    node = self.nodes[nid]
                    node.status = "completed"
                    node.outputs = ndata.get("outputs", {})
                    node.started_at = ndata.get("started_at")
                    node.completed_at = ndata.get("completed_at")
                    if ndata.get("evidence_pack"):
                        node.evidence_pack = EvidencePack.from_dict(ndata["evidence_pack"])
                    restored_count += 1

            self.execution_log = data.get("execution_log", [])
            logger.info(f"[GraphRouter] RESUME OK: Restored {restored_count} completed node(s) from checkpoint.")
            return True
        except Exception as e:
            logger.warning(f"[GraphRouter] Failed to load checkpoint: {e}")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Return a structured summary of the DAG execution state."""
        return {
            "initiative": self.initiative_name,
            "total_nodes": len(self.nodes),
            "completed": sum(1 for n in self.nodes.values() if n.status == "completed"),
            "running": sum(1 for n in self.nodes.values() if n.status == "running"),
            "pending": sum(1 for n in self.nodes.values() if n.status == "pending"),
            "failed": sum(1 for n in self.nodes.values() if n.status == "failed"),
            "blocked_asymmetry": sum(1 for n in self.nodes.values() if n.status == "blocked_asymmetry"),
            "blocked_deadlock": sum(1 for n in self.nodes.values() if n.status == "blocked_deadlock"),
            "nodes": {
                nid: {
                    "role": n.role,
                    "category": n.category.value,
                    "status": n.status,
                    "blocked_by": n.blocked_by,
                    "risk_level": n.risk_level.value,
                    "evidence_count": len(n.evidence_pack.items) if n.evidence_pack else 0,
                    "error": n.error,
                }
                for nid, n in self.nodes.items()
            },
        }
