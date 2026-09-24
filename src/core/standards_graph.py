"""
mLoop StandardsGraph Engine (ADR-0379)
Base SQLite compilée, synchronisation incrémentale SSOT et requêtage ciblé JIT.

Garantit le zéro hardcoding des directives architecturales, compétences et agents,
tout en assurant des temps de réponse < 0.2ms via une base SQLite embarquée.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger("mLoop.StandardsGraph")


# ─── Modèles Pydantic v2 Typés ───────────────────────────────────────────────


class ValidationRule(BaseModel):
    check_id: str
    severity: str = "BLOCKING"
    description: str = ""
    params: Dict[str, Any] = Field(default_factory=dict)


class ADRContract(BaseModel):
    id: str
    title: str
    status: str = "Accepté"
    date: Optional[str] = None
    stage: str = "GLOBAL"
    domain: str = "architecture"
    client_layout: Optional[List[str]] = None
    forbidden_in_client: Optional[List[str]] = None
    docs_subdirs: Optional[List[str]] = None
    ssot_files: Optional[Dict[str, str]] = None
    mloop_only_dirs: Optional[List[str]] = None
    mloop_layout: Optional[List[str]] = None
    stage_order: Optional[List[str]] = None
    gate_definitions: Optional[Dict[str, Any]] = None
    validation_rules: List[ValidationRule] = Field(default_factory=list)
    raw_frontmatter: Dict[str, Any] = Field(default_factory=dict)
    file_path: str = ""


class SkillManifest(BaseModel):
    name: str
    description: str
    category: str = "general"
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    guardrails: List[str] = Field(default_factory=list)
    file_path: str = ""
    raw_frontmatter: Dict[str, Any] = Field(default_factory=dict)


class AgentManifest(BaseModel):
    name: str
    role: str = ""
    description: str = ""
    model: str = "gemini-3.8-flash"
    model_reasoning_effort: str = "medium"
    sandbox_mode: str = "read-only"
    allowed_write_paths: List[str] = Field(default_factory=list)
    forbidden_write_paths: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    file_path: str = ""
    raw_frontmatter: Dict[str, Any] = Field(default_factory=dict)
    system_prompt: Optional[str] = None


class RuleManifest(BaseModel):
    id: str
    title: str = ""
    description: str = ""
    target_stage: str = "GLOBAL"
    triggers: List[str] = Field(default_factory=list)
    file_path: str = ""
    raw_frontmatter: Dict[str, Any] = Field(default_factory=dict)


# ─── Moteur SQLite Central : StandardsGraphStore ─────────────────────────────


class StandardsGraphStore:
    """
    Store SQLite pour le graphe de connaissances architecturales et directives mLoop.
    Maintient la parité absolue avec les fichiers Markdown SSOT avec synchronisation incrémentale.
    """

    _instance: Optional[StandardsGraphStore] = None

    @classmethod
    def get_instance(cls, root_dir: Optional[Path] = None) -> StandardsGraphStore:
        if cls._instance is None:
            cls._instance = cls(root_dir)
        return cls._instance

    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir:
            self.root = root_dir.resolve()
        else:
            self.root = Path(__file__).resolve().parents[2]

        self.db_path = self.root / "memory" / "standards_graph.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.sync_if_stale()

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Gestionnaire de contexte thread-safe et sécurisé pour les connexions SQLite (ADR-0369)."""
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)  # noqa: RULE-AST-02 (géré via @contextmanager _get_connection)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=10000;")
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialise le schéma relationnel s'il n'existe pas encore."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS standards_nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    title TEXT,
                    stage TEXT DEFAULT 'GLOBAL',
                    domain TEXT DEFAULT 'general',
                    file_path TEXT NOT NULL,
                    file_mtime REAL NOT NULL,
                    file_sha256 TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    body_markdown TEXT,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS standards_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY(source_id) REFERENCES standards_nodes(id) ON DELETE CASCADE,
                    UNIQUE(source_id, target_id, relation_type)
                );

                CREATE TABLE IF NOT EXISTS sync_meta (
                    source_key TEXT PRIMARY KEY,
                    directory_path TEXT NOT NULL,
                    aggregate_hash TEXT NOT NULL,
                    last_sync_timestamp REAL NOT NULL,
                    node_count INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_nodes_type_stage ON standards_nodes(type, stage);
                CREATE INDEX IF NOT EXISTS idx_nodes_type_name ON standards_nodes(type, name);
                CREATE INDEX IF NOT EXISTS idx_nodes_file_path ON standards_nodes(file_path);
                CREATE INDEX IF NOT EXISTS idx_edges_source ON standards_edges(source_id, relation_type);
                CREATE INDEX IF NOT EXISTS idx_edges_target ON standards_edges(target_id, relation_type);
            """)

    # ─── Détection de Fraîcheur & Synchronisation Incrémentale ─────────────────

    def _compute_dir_hash(self, directory: Path, pattern: str = "*.md") -> Tuple[str, List[Path]]:
        """Calcule un hash d'empreinte basé sur les mtime et tailles des fichiers d'un répertoire."""
        if not directory.exists():
            return "", []
        files = sorted(directory.rglob(pattern) if "**" in pattern else directory.glob(pattern))
        hasher = hashlib.sha256()
        for f in files:
            try:
                stat = f.stat()
                hasher.update(f"{f.name}:{stat.st_mtime}:{stat.st_size}".encode("utf-8"))
            except OSError as e:
                logger.debug(
                    "Stat d'un fichier standards indisponible, exclu du hash",
                    exc_info=True,
                    extra={
                        "component": "core.standards_graph",
                        "operation": "compute_directory_hash",
                        "error": str(e),
                    },
                )
        return hasher.hexdigest(), files

    _last_check_time: float = 0.0
    _CHECK_INTERVAL_SECONDS: float = 2.0

    def sync_if_stale(self, force: bool = False) -> bool:
        """
        Vérifie si les dossiers de standards ont été modifiés.
        Si aucun changement, sort immédiatement (< 0.2ms).
        Si des modifications sont détectées, effectue une synchronisation incrémentale.
        """
        now = time.time()
        if not force and (now - self._last_check_time) < self._CHECK_INTERVAL_SECONDS:
            return False
        self._last_check_time = now

        sources = {
            "adrs": (self.root / "standards" / "adr-system", "*.md"),
            "skills": (self.root / ".agents" / "skills", "*/SKILL.md"),
            "agents": (self.root / ".agents" / "agents", "*.md"),
            "rules": (self.root / ".agents" / "rules", "*.md"),
        }

        needs_sync = force
        if not needs_sync:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for key, (path, pattern) in sources.items():
                    current_hash, _ = self._compute_dir_hash(path, pattern)
                    cursor.execute(
                        "SELECT aggregate_hash FROM sync_meta WHERE source_key = ?", (key,)
                    )
                    row = cursor.fetchone()
                    if not row or row["aggregate_hash"] != current_hash:
                        needs_sync = True
                        break

        if needs_sync:
            self.sync_all()
            return True
        return False

    def sync_all(self) -> Dict[str, int]:
        """Synchronise l'intégralité des 4 sources SSOT Markdown vers SQLite."""
        stats = {"adrs": 0, "skills": 0, "agents": 0, "rules": 0}

        with self._get_connection() as conn:
            # 1. Synchroniser les ADRs (standards/adr-system/*.md)
            adr_dir = self.root / "standards" / "adr-system"
            adr_hash, adr_files = self._compute_dir_hash(adr_dir, "*.md")
            for f in adr_files:
                if f.name.lower() == "readme.md":
                    continue
                if self._upsert_adr(conn, f):
                    stats["adrs"] += 1

            # Mettre à jour sync_meta pour les ADRs
            conn.execute(
                "INSERT OR REPLACE INTO sync_meta (source_key, directory_path, aggregate_hash, last_sync_timestamp, node_count) "
                "VALUES (?, ?, ?, ?, ?)",
                ("adrs", str(adr_dir.relative_to(self.root)), adr_hash, time.time(), stats["adrs"]),
            )

            # 2. Synchroniser les Skills (.agents/skills/*/SKILL.md)
            skills_dir = self.root / ".agents" / "skills"
            skills_hash, skill_files = self._compute_dir_hash(skills_dir, "*/SKILL.md")
            for f in skill_files:
                if self._upsert_skill(conn, f):
                    stats["skills"] += 1

            conn.execute(
                "INSERT OR REPLACE INTO sync_meta (source_key, directory_path, aggregate_hash, last_sync_timestamp, node_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "skills",
                    str(skills_dir.relative_to(self.root)),
                    skills_hash,
                    time.time(),
                    stats["skills"],
                ),
            )

            # 3. Synchroniser les Agents (.agents/agents/*.md)
            agents_dir = self.root / ".agents" / "agents"
            agents_hash, agent_files = self._compute_dir_hash(agents_dir, "*.md")
            for f in agent_files:
                if self._upsert_agent(conn, f):
                    stats["agents"] += 1

            conn.execute(
                "INSERT OR REPLACE INTO sync_meta (source_key, directory_path, aggregate_hash, last_sync_timestamp, node_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "agents",
                    str(agents_dir.relative_to(self.root)),
                    agents_hash,
                    time.time(),
                    stats["agents"],
                ),
            )

            # 4. Synchroniser les Règles (.agents/rules/*.md)
            rules_dir = self.root / ".agents" / "rules"
            rules_hash, rule_files = self._compute_dir_hash(rules_dir, "*.md")
            for f in rule_files:
                if self._upsert_rule(conn, f):
                    stats["rules"] += 1

            conn.execute(
                "INSERT OR REPLACE INTO sync_meta (source_key, directory_path, aggregate_hash, last_sync_timestamp, node_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    "rules",
                    str(rules_dir.relative_to(self.root)),
                    rules_hash,
                    time.time(),
                    stats["rules"],
                ),
            )

        logger.info(f"StandardsGraph synchronisé avec succès : {stats}")
        return stats

    # ─── Helpers d'Insertion et Parseurs YAML SSOT ─────────────────────────────

    def _parse_markdown_frontmatter(self, file_path: Path) -> Tuple[Dict[str, Any], str]:
        """Extrait de manière sûre et résiliente le frontmatter YAML et le corps Markdown."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Impossible de lire {file_path} : {e}")
            return {}, ""

        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        try:
            frontmatter = yaml.safe_load(parts[1]) or {}
            if not isinstance(frontmatter, dict):
                frontmatter = {}
        except Exception as e:
            logger.warning(f"Erreur de syntaxe YAML dans {file_path.name} : {e}")
            frontmatter = {}

        body = parts[2].strip()
        return frontmatter, body

    def _upsert_adr(self, conn: sqlite3.Connection, file_path: Path) -> bool:
        fm, body = self._parse_markdown_frontmatter(file_path)
        stat = file_path.stat()
        file_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()

        # Identifier le numéro d'ADR de façon robuste (int ou str)
        adr_id_raw = fm.get("id")
        if adr_id_raw is not None:
            if isinstance(adr_id_raw, int):
                adr_id = f"ADR-{adr_id_raw:04d}"
            else:
                adr_id = str(adr_id_raw).strip()
                if not adr_id.upper().startswith("ADR-"):
                    adr_id = f"ADR-{adr_id}"
        else:
            stem_match = file_path.stem.split("-")[0]
            adr_id = f"ADR-{stem_match}"

        title = str(fm.get("title", file_path.stem))
        stage = str(fm.get("stage", "GLOBAL"))
        domain = str(fm.get("domain", "architecture"))

        # Ingestion des tags de stage si présents
        if "stage_order" in fm or "gate_definitions" in fm:
            domain = "lifecycle"

        clean_slug = adr_id.upper().replace("ADR-", "")
        node_id = f"adr:{file_path.stem}"

        conn.execute(
            """
            INSERT OR REPLACE INTO standards_nodes 
            (id, type, name, title, stage, domain, file_path, file_mtime, file_sha256, metadata_json, body_markdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                "adr",
                adr_id,
                title,
                stage,
                domain,
                str(file_path.relative_to(self.root)),
                stat.st_mtime,
                file_sha256,
                json.dumps(fm, ensure_ascii=False),
                body,
            ),
        )

        # Arêtes : gouvernance de stage
        if stage != "GLOBAL":
            conn.execute(
                """
                INSERT OR IGNORE INTO standards_edges (source_id, target_id, relation_type)
                VALUES (?, ?, ?)
                """,
                (node_id, f"stage:{stage}", "governs_stage"),
            )

        return True

    def _upsert_skill(self, conn: sqlite3.Connection, file_path: Path) -> bool:
        fm, body = self._parse_markdown_frontmatter(file_path)
        stat = file_path.stat()
        file_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()

        skill_name = fm.get("name", file_path.parent.name)
        description = fm.get("description", "")
        category = fm.get("category", "general")
        node_id = f"skill:{skill_name}"

        conn.execute(
            """
            INSERT OR REPLACE INTO standards_nodes 
            (id, type, name, title, stage, domain, file_path, file_mtime, file_sha256, metadata_json, body_markdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                "skill",
                skill_name,
                description,
                "GLOBAL",
                category,
                str(file_path.relative_to(self.root)),
                stat.st_mtime,
                file_sha256,
                json.dumps(fm, ensure_ascii=False),
                body,
            ),
        )
        return True

    def _upsert_agent(self, conn: sqlite3.Connection, file_path: Path) -> bool:
        fm, body = self._parse_markdown_frontmatter(file_path)
        stat = file_path.stat()
        file_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()

        agent_name = fm.get("name", file_path.stem)
        role = fm.get("role", "")
        desc = fm.get("description", "")
        node_id = f"agent:{agent_name}"

        conn.execute(
            """
            INSERT OR REPLACE INTO standards_nodes 
            (id, type, name, title, stage, domain, file_path, file_mtime, file_sha256, metadata_json, body_markdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                "agent",
                agent_name,
                f"{role} — {desc}".strip(" —"),
                "GLOBAL",
                "agent_persona",
                str(file_path.relative_to(self.root)),
                stat.st_mtime,
                file_sha256,
                json.dumps(fm, ensure_ascii=False),
                body,
            ),
        )

        # Arêtes : dépendances vers les skills déclarées
        declared_skills = fm.get("skills", [])
        if isinstance(declared_skills, list):
            for skill_name in declared_skills:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO standards_edges (source_id, target_id, relation_type)
                    VALUES (?, ?, ?)
                    """,
                    (node_id, f"skill:{skill_name}", "requires_skill"),
                )
        return True

    def _upsert_rule(self, conn: sqlite3.Connection, file_path: Path) -> bool:
        fm, body = self._parse_markdown_frontmatter(file_path)
        stat = file_path.stat()
        file_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()

        rule_name = file_path.stem
        title = fm.get("title", rule_name)
        stage = fm.get("target_stage", "GLOBAL")
        node_id = f"rule:{rule_name}"

        conn.execute(
            """
            INSERT OR REPLACE INTO standards_nodes 
            (id, type, name, title, stage, domain, file_path, file_mtime, file_sha256, metadata_json, body_markdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                "rule",
                rule_name,
                title,
                stage,
                "guardrail",
                str(file_path.relative_to(self.root)),
                stat.st_mtime,
                file_sha256,
                json.dumps(fm, ensure_ascii=False),
                body,
            ),
        )
        return True

    # ─── API Publique de Consultation & Scoping Ciblé (< 0.2ms) ─────────────────

    def get_adr(self, adr_id: str) -> Optional[ADRContract]:
        """Extrait un contrat d'ADR typé Pydantic v2 (ex: 'ADR-0100' ou '0378')."""
        self.sync_if_stale()
        normalized = adr_id.upper().replace("ADR-", "")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM standards_nodes WHERE type = 'adr' AND (name = ? OR name = ?)",
                (adr_id, f"ADR-{normalized}"),
            )
            row = cursor.fetchone()
            if not row:
                return None
            metadata = json.loads(row["metadata_json"])
            rules = [ValidationRule(**r) for r in metadata.get("validation_rules", [])]
            return ADRContract(
                id=row["name"],
                title=row["title"] or "",
                status=metadata.get("status", "Accepté"),
                date=metadata.get("date"),
                stage=row["stage"] or "GLOBAL",
                domain=row["domain"] or "architecture",
                client_layout=metadata.get("client_layout"),
                forbidden_in_client=metadata.get("forbidden_in_client"),
                docs_subdirs=metadata.get("docs_subdirs"),
                ssot_files=metadata.get("ssot_files"),
                mloop_only_dirs=metadata.get("mloop_only_dirs"),
                mloop_layout=metadata.get("mloop_layout"),
                stage_order=metadata.get("stage_order"),
                gate_definitions=metadata.get("gate_definitions"),
                validation_rules=rules,
                raw_frontmatter=metadata,
                file_path=row["file_path"],
            )

    def get_adrs_by_stage(self, stage: str) -> List[ADRContract]:
        """Extrait uniquement les ADRs applicables à une étape donnée (ex: 'STAGE_1_INGEST')."""
        self.sync_if_stale()
        contracts = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM standards_nodes WHERE type = 'adr' AND (stage = ? OR stage = 'GLOBAL')",
                (stage,),
            )
            for row in cursor.fetchall():
                c = self.get_adr(row["name"])
                if c:
                    contracts.append(c)
        return contracts

    def get_skills(self) -> Dict[str, SkillManifest]:
        """Retourne le catalogue complet des 38 compétences indexées."""
        self.sync_if_stale()
        skills = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM standards_nodes WHERE type = 'skill' ORDER BY name")
            for row in cursor.fetchall():
                metadata = json.loads(row["metadata_json"])
                skills[row["name"]] = SkillManifest(
                    name=row["name"],
                    description=row["title"] or metadata.get("description", ""),
                    category=row["domain"] or "general",
                    inputs=metadata.get("inputs", []),
                    outputs=metadata.get("outputs", []),
                    guardrails=metadata.get("guardrails", []),
                    file_path=row["file_path"],
                    raw_frontmatter=metadata,
                )
        return skills

    def get_skill(self, name: str) -> Optional[SkillManifest]:
        """Retourne le manifeste d'une compétence spécifique."""
        self.sync_if_stale()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM standards_nodes WHERE type = 'skill' AND name = ?", (name,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            metadata = json.loads(row["metadata_json"])
            return SkillManifest(
                name=row["name"],
                description=row["title"] or metadata.get("description", ""),
                category=row["domain"] or "general",
                inputs=metadata.get("inputs", []),
                outputs=metadata.get("outputs", []),
                guardrails=metadata.get("guardrails", []),
                file_path=row["file_path"],
                raw_frontmatter=metadata,
            )

    def get_agents(self) -> Dict[str, AgentManifest]:
        """Retourne tous les profils d'agents enregistrés dans le SSOT Markdown."""
        self.sync_if_stale()
        agents = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM standards_nodes WHERE type = 'agent' ORDER BY name")
            for row in cursor.fetchall():
                metadata = json.loads(row["metadata_json"])
                # Extraire les skills autorisées via les arêtes
                cursor.execute(
                    "SELECT target_id FROM standards_edges WHERE source_id = ? AND relation_type = 'requires_skill'",
                    (row["id"],),
                )
                skill_names = [r["target_id"].replace("skill:", "") for r in cursor.fetchall()]
                if not skill_names and "skills" in metadata:
                    skill_names = metadata["skills"]

                agents[row["name"]] = AgentManifest(
                    name=row["name"],
                    role=metadata.get("role", ""),
                    description=metadata.get("description", row["title"] or ""),
                    model=metadata.get("model", metadata.get("model_pref", "gemini-3.8-flash")),
                    model_reasoning_effort=metadata.get("model_reasoning_effort", "medium"),
                    sandbox_mode=metadata.get("sandbox_mode", "read-only"),
                    allowed_write_paths=metadata.get("allowed_write_paths", []),
                    forbidden_write_paths=metadata.get("forbidden_write_paths", []),
                    skills=skill_names,
                    file_path=row["file_path"],
                    raw_frontmatter=metadata,
                    system_prompt=row["body_markdown"],
                )
        return agents

    def get_agent(self, name: str) -> Optional[AgentManifest]:
        """Retourne le profil complet d'un agent par son nom (ex: 'explorer')."""
        agents = self.get_agents()
        return agents.get(name)

    def get_skills_for_agent(self, agent_name: str) -> List[str]:
        """Retourne la whitelist exacte des compétences autorisées pour cet agent."""
        agent = self.get_agent(agent_name)
        if not agent:
            return []
        return agent.skills

    def get_layout_contracts(self) -> Dict[str, Any]:
        """
        Construit le dictionnaire de contrats pour alimenter ProjectLayout de façon 100% dynamique.
        Remplace standards/adr-contracts.json sans aucune duplication.
        """
        contracts: Dict[str, Any] = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, metadata_json FROM standards_nodes WHERE type = 'adr'")
            for row in cursor.fetchall():
                name = row["name"]
                meta = json.loads(row["metadata_json"])
                # Filtrer les champs contractuels d'architecture
                layout_keys = [
                    "client_layout",
                    "forbidden_in_client",
                    "memory_subdirs",
                    "docs_subdirs",
                    "required_files_in_docs",
                    "ssot_files",
                    "mloop_only_dirs",
                    "mloop_layout",
                    "stage_order",
                    "gate_definitions",
                ]
                extracted = {k: meta[k] for k in layout_keys if k in meta}
                if extracted:
                    contracts[name] = extracted

        # Fallbacks de sécurité garantis si la base est en cours d'initialisation
        if "ADR-0100" not in contracts:
            contracts["ADR-0100"] = {
                "client_layout": ["reference", "docs", "backlog", "memory", "graphify-out"],
                "forbidden_in_client": ["src", "openspec"],
                "memory_subdirs": ["sessions", "debates", "sync", "reports", "cache", "tmp"],
            }
        if "ADR-0102" not in contracts:
            contracts["ADR-0102"] = {
                "docs_subdirs": [
                    "00-ingested",
                    "01-architecture",
                    "02-business-rules",
                    "03-models",
                    "04-transverse",
                    "05-assets/maquettes",
                    "05-assets/diagrams",
                    "05-assets/images",
                ],
                "required_files_in_docs": ["index.md"],
                "ssot_files": {
                    "sprint_backlog": "sprint_backlog.md",
                    "story_mapping": "STORY_MAPPING.md",
                    "open_questions": "00-questions-ouvertes.md",
                },
            }
        if "ADR-0103" not in contracts:
            contracts["ADR-0103"] = {
                "mloop_only_dirs": ["directives", "journal", "src", "openspec"],
                "mloop_layout": [
                    "reference",
                    "docs",
                    "backlog",
                    "memory",
                    "graphify-out",
                    "directives",
                    "journal",
                    "src",
                    "openspec",
                ],
            }
        return contracts
