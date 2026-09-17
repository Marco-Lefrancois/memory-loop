"""
Topologie agentique et calcul du Blast Radius (ADR-0202 & ADR-0371).
"""
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BlastRadiusLevel(str, Enum):
    MINIMAL = "MINIMAL"
    CONTROLLED = "CONTROLLED"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"


class AgentTopology(BaseModel):
    role: str
    description: str
    authorized_write_paths: List[str] = Field(default_factory=list)
    forbidden_paths: List[str] = Field(default_factory=list)
    connected_memory_partitions: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    blast_radius_level: BlastRadiusLevel = BlastRadiusLevel.MINIMAL
    unattended_safe: bool = True


class AgentTopologyMapper:
    """
    Cartographe déterministe de la topologie agentique et du rayon d'impact (Blast Radius).
    """

    DEFAULT_POLICIES: Dict[str, Dict[str, Any]] = {
        "orchestrator": {
            "description": "Orchestrateur racine mLoop (System 2, FSM, HITL)",
            "authorized_write_paths": ["docs/", "backlog/", "memory/", "reference/"],
            "forbidden_paths": [".env", ".git/"],
            "connected_memory_partitions": ["checkpoints", "evidence", "sessions", "sync"],
            "allowed_tools": ["all"],
            "blast_radius_level": BlastRadiusLevel.ELEVATED,
            "unattended_safe": False,
        },
        "worker": {
            "description": "Agent de build et d'exécution délimité (System 1 / Herdr PTY)",
            "authorized_write_paths": ["docs/", "backlog/stories/", "memory/evidence/"],
            "forbidden_paths": [".env", ".git/", "standards/"],
            "connected_memory_partitions": ["evidence", "execution_traces"],
            "allowed_tools": ["replace_file_content", "write_to_file", "run_command"],
            "blast_radius_level": BlastRadiusLevel.CONTROLLED,
            "unattended_safe": True,
        },
        "research": {
            "description": "Agent d'exploration documentaire, moissonnage et R&D",
            "authorized_write_paths": ["reference/research/", "memory/crawler/cache/"],
            "forbidden_paths": [".env", "src/", "backlog/", "docs/01-architecture/"],
            "connected_memory_partitions": ["crawler_cache", "research_scratchpad"],
            "allowed_tools": ["crawl", "read_url_content", "grep_search", "list_dir"],
            "blast_radius_level": BlastRadiusLevel.MINIMAL,
            "unattended_safe": True,
        },
        "qa": {
            "description": "Agent d'audit qualité, tests et validation Sentinel",
            "authorized_write_paths": ["memory/reports/", "memory/evidence/", "memory/evals/"],
            "forbidden_paths": [".env", "src/", "docs/", "backlog/"],
            "connected_memory_partitions": ["evidence", "evals"],
            "allowed_tools": ["pytest", "ruff", "view_file", "fact-search"],
            "blast_radius_level": BlastRadiusLevel.MINIMAL,
            "unattended_safe": True,
        },
        "crawler": {
            "description": "Système 1 d'ingestion web et extraction LLMs.txt/Markdown Twins",
            "authorized_write_paths": ["memory/crawler/cache/"],
            "forbidden_paths": [".env", "src/", "backlog/", "docs/"],
            "connected_memory_partitions": ["crawler_cache"],
            "allowed_tools": ["httpx", "playwright", "markdownify"],
            "blast_radius_level": BlastRadiusLevel.MINIMAL,
            "unattended_safe": True,
        },
        "sentinel": {
            "description": "Gardien d'intégrité constitutionnelle et WikiFix",
            "authorized_write_paths": ["memory/wikifix_report.md", "memory/audit/"],
            "forbidden_paths": [".env", "src/", "backlog/"],
            "connected_memory_partitions": ["wikifix", "fact_search_hashes"],
            "allowed_tools": ["read_file", "fts5_search", "vibe_check"],
            "blast_radius_level": BlastRadiusLevel.MINIMAL,
            "unattended_safe": True,
        },
    }

    @classmethod
    def get_topology(cls, role: str) -> AgentTopology:
        clean_role = role.strip().lower()
        policy = cls.DEFAULT_POLICIES.get(clean_role)
        if not policy:
            return AgentTopology(
                role=clean_role,
                description=f"Agent personnalisé ({clean_role})",
                authorized_write_paths=["memory/tmp/"],
                forbidden_paths=[".env", "src/", "docs/", "backlog/"],
                connected_memory_partitions=["tmp"],
                allowed_tools=["view_file"],
                blast_radius_level=BlastRadiusLevel.CONTROLLED,
                unattended_safe=False,
            )
        return AgentTopology(role=clean_role, **policy)

    @classmethod
    def list_all_topologies(cls) -> List[AgentTopology]:
        return [cls.get_topology(r) for r in sorted(cls.DEFAULT_POLICIES.keys())]

    @classmethod
    def compute_blast_radius(
        cls, role: str, proposed_writes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        topology = cls.get_topology(role)
        violations: List[str] = []
        in_scope_writes: List[str] = []

        if proposed_writes:
            for write_path in proposed_writes:
                norm_p = Path(write_path).as_posix()
                if any(forbid in norm_p for forbid in topology.forbidden_paths):
                    violations.append(norm_p)
                else:
                    in_scope_writes.append(norm_p)

        score_map = {
            BlastRadiusLevel.MINIMAL: 15,
            BlastRadiusLevel.CONTROLLED: 35,
            BlastRadiusLevel.ELEVATED: 70,
            BlastRadiusLevel.CRITICAL: 95,
        }
        base_score = score_map[topology.blast_radius_level]
        adjusted_score = base_score + (20 if violations else 0)
        adjusted_score = min(100, adjusted_score)

        return {
            "role": topology.role,
            "level": topology.blast_radius_level.value,
            "blast_score": adjusted_score,
            "unattended_authorized": topology.unattended_safe and len(violations) == 0,
            "authorized_paths": topology.authorized_write_paths,
            "forbidden_paths": topology.forbidden_paths,
            "violations": violations,
            "in_scope_writes": in_scope_writes,
        }
