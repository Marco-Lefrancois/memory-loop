import json
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.utils.logger import get_logger

logger = get_logger("state")


class LoopStateError(Exception):
    """Exception de base pour le moteur d'état mLoop."""

    pass


class IntegrityError(LoopStateError):
    """Exception levée en cas de violation d'intégrité de l'état."""

    pass


class MaxRevisionsReached(LoopStateError):
    """Exception levée par le circuit breaker lors d'un cycle infini."""

    pass


class LoopPhase(str, Enum):
    SPEC = "spec"
    PLAN = "plan"
    BUILD = "build"
    VALIDATE = "validate"
    SHIP = "ship"
    ERROR = "error"


class ProjectMode(str, Enum):
    """
    Détermine le cycle de vie applicable au LoopState.

    CLIENT : SPEC → PLAN → VALIDATE (audit WikiFix du backlog).
             BUILD et SHIP sont hors périmètre IA (humain).
    MLOOP  : SPEC → PLAN → BUILD → VALIDATE → SHIP (cycle complet 5 phases).
             Avec boucle de révision VALIDATE → PLAN (max 5 révisions).
    """

    CLIENT = "client"
    MLOOP = "mloop"


class TokenBudget(BaseModel):
    """
    Compteur de consommation de tokens pour le Circuit Breaker Financier.

    Attributes:
        tokens_used: Tokens LLM consommés depuis le début de la session.
        max_tokens: Seuil au-delà duquel le circuit breaker s'active.
                    Par défaut 50 000. Configurable via `MLOOP_MAX_TOKENS`.
    """

    tokens_used: int = 0
    max_tokens: int = Field(
        default_factory=lambda: int(__import__("os").getenv("MLOOP_MAX_TOKENS", "50000"))
    )

    @property
    def is_exhausted(self) -> bool:
        """Retourne True si le budget est épuisé."""
        return self.tokens_used >= self.max_tokens

    def consume(self, tokens: int) -> None:
        """Incrémente le compteur de tokens consommés."""
        self.tokens_used += tokens


from src.core.layout import ProjectLayout, load_adr_contracts as _load_adr_contracts


class Directives(BaseModel):
    tech: str = ""
    business: str = ""


class KnowledgeGraph(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class Clarification(BaseModel):
    question: str
    answer: Optional[str] = None


class StoryType(str, Enum):
    """
    Types officiels de récits dans mLoop.
    Qualifie la nature du livrable (Frontmatter YAML).
    """

    FEATURE = "Feature"
    ARCHITECTURE = "Architecture"
    TECHNICAL_DEBT = "Technical_Debt"
    BUG = "Bug"
    SPIKE = "Spike"

    @classmethod
    def from_raw(cls, raw: str) -> "StoryType":
        """Parse case-insensitive et normalise le type de récit."""
        if not raw:
            return cls.FEATURE
        norm = raw.strip().lower().replace("-", "_").replace(" ", "_")
        mapping = {
            "feature": cls.FEATURE,
            "architecture": cls.ARCHITECTURE,
            "technical_debt": cls.TECHNICAL_DEBT,
            "tech_debt": cls.TECHNICAL_DEBT,
            "debt": cls.TECHNICAL_DEBT,
            "bug": cls.BUG,
            "hotfix": cls.BUG,
            "spike": cls.SPIKE,
        }
        return mapping.get(norm, cls.FEATURE)


class StoryStatus(str, Enum):
    """
    Statuts officiels du cycle de vie d'un récit mLoop.

    Mode CLIENT (SPEC → PLAN → VALIDATE → GROOMING → DEV → QA → ACCEPTED) :
      OPEN → IN_ANALYZE → IN_PLAN → IN_VALIDATE → READY_FOR_GROOMING → READY_FOR_DEV → IN_DEV → IN_QA → ACCEPTED

    Mode MLOOP (SPEC → PLAN → BUILD → VALIDATE → SHIP) :
      OPEN → IN_ANALYZE → IN_PLAN → IN_BUILD → IN_VALIDATE → SHIPPED

    ERROR : état terminal d'échec (circuit breaker, audit bloquant).
    """

    # ─── Commun aux deux modes ──────────────────────────────────────
    DRAFT = "DRAFT"
    BACKLOG = "BACKLOG"
    OPEN = "OPEN"
    IN_ANALYZE = "IN_ANALYZE"
    IN_PLAN = "IN_PLAN"
    IN_REVIEW = "IN_REVIEW"
    IN_VALIDATE = "IN_VALIDATE"
    ON_HOLD = "ON_HOLD"
    ERROR = "ERROR"
    # ─── Mode CLIENT (Handoff & Cycle Dev/QA/Prod) ─────────────
    READY_FOR_GROOMING = "READY_FOR_GROOMING"
    READY_FOR_DEV = "READY_FOR_DEV"
    IN_DEV = "IN_DEV"
    IN_QA = "IN_QA"
    DONE = "DONE"
    ACCEPTED = "ACCEPTED"
    # ─── Mode MLOOP uniquement ─────────────────────────────────
    IN_BUILD = "IN_BUILD"
    SHIPPED = "SHIPPED"

    @classmethod
    def from_raw(cls, raw: str) -> "StoryStatus":
        """
        Parse case-insensitive depuis le frontmatter YAML.
        Retourne OPEN pour toute valeur inconnue (fail-open).
        """
        normalized = raw.strip().upper().replace(" ", "_").replace("-", "_")
        try:
            return cls(normalized)
        except ValueError:
            return cls.OPEN


class SprintBacklogItem(BaseModel):
    id: str
    title: str
    description: str
    type: StoryType = StoryType.FEATURE
    components: List[str] = Field(default_factory=list)
    jira_key: Optional[str] = None
    status: StoryStatus = StoryStatus.OPEN
    invest_score: str = "N/A"
    clarifications: List[Clarification] = Field(default_factory=list)

    @property
    def grilled(self) -> bool:
        """Compatibilité ascendante : True si le récit est prêt pour la revue humaine ou en cours de révision."""
        return self.status in (
            StoryStatus.IN_REVIEW,
            StoryStatus.READY_FOR_GROOMING,
            StoryStatus.READY_FOR_DEV,
            StoryStatus.IN_DEV,
            StoryStatus.IN_QA,
            StoryStatus.DONE,
            StoryStatus.ACCEPTED,
        )

    @property
    def jira_sync_eligible(self) -> bool:
        """Règle mLoop : Les statuts IN_REVIEW, READY_FOR_GROOMING ou READY_FOR_DEV sont synchronisés vers Jira Cloud."""
        return self.status in (
            StoryStatus.IN_REVIEW,
            StoryStatus.READY_FOR_GROOMING,
            StoryStatus.READY_FOR_DEV,
            StoryStatus.IN_DEV,
            StoryStatus.IN_QA,
            StoryStatus.DONE,
            StoryStatus.ACCEPTED,
        )


class AnalysisResult(BaseModel):
    intent: str = ""
    constraints: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)


class PlanStep(BaseModel):
    step_id: int
    action: str
    expected_output: str


class PlanResult(BaseModel):
    steps: List[PlanStep] = Field(default_factory=list)


class QAReport(BaseModel):
    is_valid: bool = True
    score: float = 1.0
    revisions_count: int = 0


class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: f"entry_{int(time.time())}")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    event: str
    details: str
    impacted_nodes: List[str] = Field(default_factory=list)


class SavepointManager:
    """
    Gestionnaire déterministe de points de restauration en cours d'exécution (In-Flight Checkpoints).
    Répond à l'angle mort révélé par HarnessDev (0% de checkpointing sur 26 679 runs).
    Sauvegarde l'état toutes les 60 à 90 secondes ou lors d'actions critiques.
    Maintient une politique FIFO stricte de rétention des 3 derniers instantanés.
    """

    MAX_RETAINED = 3

    @staticmethod
    def get_checkpoints_dir(project_path: Optional[Path] = None) -> Path:
        if project_path:
            target_dir = project_path / "memory" / "checkpoints"
        else:
            target_dir = Path("memory") / "checkpoints"
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    @classmethod
    def save_checkpoint(
        cls,
        state_dict: Dict[str, Any],
        project_path: Optional[Path] = None,
        reason: str = "in_flight",
    ) -> Path:
        target_dir = cls.get_checkpoints_dir(project_path)
        timestamp = int(time.time())
        filename = f"checkpoint_{timestamp}_{reason}.json"
        target_file = target_dir / filename
        tmp_file = target_dir / f"{filename}.tmp"

        payload = {
            "checkpoint_version": "1.0",
            "timestamp": timestamp,
            "datetime_utc": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "state": state_dict,
        }

        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        tmp_file.replace(target_file)

        cls.prune_old_checkpoints(target_dir)
        return target_file

    @classmethod
    def prune_old_checkpoints(cls, target_dir: Path) -> None:
        try:
            checkpoints = sorted(
                target_dir.glob("checkpoint_*.json"), key=lambda p: p.stat().st_mtime
            )
            while len(checkpoints) > cls.MAX_RETAINED:
                oldest = checkpoints.pop(0)
                try:
                    oldest.unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Erreur de nettoyage des checkpoints: {e}")

    @classmethod
    def list_checkpoints(cls, project_path: Optional[Path] = None) -> List[Path]:
        target_dir = cls.get_checkpoints_dir(project_path)
        return sorted(
            target_dir.glob("checkpoint_*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )

    @classmethod
    def load_latest_checkpoint(
        cls, project_path: Optional[Path] = None
    ) -> Optional[Dict[str, Any]]:
        checkpoints = cls.list_checkpoints(project_path)
        if not checkpoints:
            return None
        latest = checkpoints[0]
        try:
            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("state")
        except Exception as e:
            logger.warning(f"Impossible de lire le checkpoint {latest}: {e}")
            return None


class LoopState(BaseModel):
    project_name: str
    project_mode: ProjectMode = ProjectMode.CLIENT
    current_phase: LoopPhase = LoopPhase.SPEC
    previous_phase: Optional[LoopPhase] = None
    current_state_id: Optional[str] = None
    session_start_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # ─── IN-FLIGHT CHECKPOINTING (ADR-0352 / HARNESSDEV) ───
    last_checkpoint_timestamp: float = Field(default_factory=lambda: time.time())
    checkpoint_interval_seconds: int = 60  # Intervalle temporel configurable (60 à 90 secondes)

    # ─── ARTEFACTS FSM ───
    analysis: Optional[AnalysisResult] = None
    plan: Optional[PlanResult] = None
    qa_report: Optional[QAReport] = None

    directives: Directives = Field(default_factory=Directives)
    knowledge_graph: KnowledgeGraph = Field(default_factory=KnowledgeGraph)
    clarifications: List[Clarification] = Field(default_factory=list)
    sprint_backlog: List[SprintBacklogItem] = Field(default_factory=list)

    # ─── ONTOLOGIE COWORKER (L1) ───
    journal: List[JournalEntry] = Field(default_factory=list)

    # ─── NOUVEAUX CHAMPS D'INTÉGRATION ───
    jira_project_key: Optional[str] = None
    jira_epic_key: Optional[str] = None
    jira_default_component_id: Optional[str] = None
    jira_default_billing_id: Optional[str] = None
    jira_default_subtasks: List[str] = Field(default_factory=list)
    jira_subtask_mapping: Dict[str, str] = Field(default_factory=dict)
    ingested_sources: List[Dict[str, Any]] = Field(default_factory=list)

    # ─── INGESTION PAR INITIATIVE / MODULE (Voie B — routage scopé) ───
    # Quand renseigné, l'ingestion scanne uniquement reference/<initiative>/
    # et écrit sous docs/<initiative>/00-ingested/ (projets à structure par module,
    # ex: Metro_FOOD → OneTrust, RBC_Avion, PAPERCUTS). Sinon: comportement ADR-0102 plat.
    ingest_initiative: Optional[str] = None

    token_budget: TokenBudget = Field(default_factory=TokenBudget)
    hitl_required: bool = Field(default=False)

    # ─── GRAPHIFY INTEGRATION (ADR-0018) ─────────────────────────
    graph_path: str = "graphify-out/graph.json"

    def should_checkpoint(self, interval_seconds: Optional[int] = None) -> bool:
        """Vérifie si le délai temporel (60 à 90s) depuis le dernier checkpoint est dépassé."""
        target_interval = interval_seconds or self.checkpoint_interval_seconds
        return (time.time() - self.last_checkpoint_timestamp) >= target_interval

    def checkpoint(
        self, project_path: Optional[Path] = None, reason: str = "in_flight", force: bool = False
    ) -> Optional[Path]:
        """Crée un point de contrôle atomique sur disque si le délai est atteint ou forcé."""
        if not force and not self.should_checkpoint():
            return None

        target_proj = project_path or (
            Path("Projects") / self.project_name if self.project_name else None
        )
        state_data = self.model_dump(exclude={"sprint_backlog", "knowledge_graph"})
        saved_file = SavepointManager.save_checkpoint(
            state_data, project_path=target_proj, reason=reason
        )
        self.last_checkpoint_timestamp = time.time()
        logger.info(
            f"[CHECKPOINT] État in-flight sauvegardé sous {saved_file.name} (Raison: {reason})"
        )
        return saved_file

    def restore_latest_checkpoint(self, project_path: Optional[Path] = None) -> bool:
        """Restaure l'état depuis le plus récent checkpoint valide."""
        target_proj = project_path or (
            Path("Projects") / self.project_name if self.project_name else None
        )
        state_dict = SavepointManager.load_latest_checkpoint(target_proj)
        if not state_dict:
            return False
        try:
            loaded = LoopState.model_validate(state_dict)
            for field in self.__class__.model_fields:
                if field not in ("sprint_backlog", "knowledge_graph"):
                    setattr(self, field, getattr(loaded, field))
            return True
        except Exception as e:
            logger.warning(f"Erreur lors de la validation du checkpoint restauré: {e}")
            return False

    def can_transition_to(self, target_phase: LoopPhase) -> bool:
        """Vérifie si une transition de phase est légale selon le mode et l'état."""
        if target_phase == LoopPhase.ERROR:
            return True
        if self.project_mode == ProjectMode.CLIENT:
            if self.current_phase == LoopPhase.SPEC and target_phase == LoopPhase.PLAN:
                return True
            if self.current_phase == LoopPhase.PLAN and target_phase == LoopPhase.VALIDATE:
                return True
            return False
        elif self.project_mode == ProjectMode.MLOOP:
            if self.current_phase == LoopPhase.SPEC and target_phase == LoopPhase.PLAN:
                return True
            if self.current_phase == LoopPhase.PLAN and target_phase == LoopPhase.BUILD:
                return True
            if self.current_phase == LoopPhase.BUILD and target_phase == LoopPhase.VALIDATE:
                return True
            if self.current_phase == LoopPhase.VALIDATE and target_phase == LoopPhase.SHIP:
                return True
            if self.current_phase == LoopPhase.VALIDATE and target_phase == LoopPhase.PLAN:
                if self.qa_report and self.qa_report.revisions_count > 5:
                    return False
                return True
            return False
        return False

    def transition_to(self, target_phase: LoopPhase) -> None:
        """Effectue une transition de phase avec vérification stricte d'intégrité."""
        if target_phase == LoopPhase.ERROR:
            self.previous_phase = self.current_phase
            self.current_phase = LoopPhase.ERROR
            self.current_state_id = LoopPhase.ERROR.value
            return

        if target_phase == LoopPhase.PLAN:
            if self.current_phase == LoopPhase.SPEC:
                if self.analysis is None:
                    raise IntegrityError("AnalysisResult requis pour passer en phase PLAN.")
                if self.analysis.missing_information:
                    raise IntegrityError(
                        "Des informations manquantes bloquent le passage en phase PLAN."
                    )
            elif (
                self.current_phase == LoopPhase.VALIDATE and self.project_mode == ProjectMode.MLOOP
            ):
                if self.qa_report and self.qa_report.revisions_count > 5:
                    self.current_phase = LoopPhase.ERROR
                    self.current_state_id = LoopPhase.ERROR.value
                    raise MaxRevisionsReached(
                        "Circuit Breaker : Nombre maximal de révisions dépassé (> 5)."
                    )

        if (
            target_phase == LoopPhase.VALIDATE
            and self.current_phase == LoopPhase.PLAN
            and self.project_mode == ProjectMode.CLIENT
        ):
            if self.plan is None:
                raise IntegrityError("PlanResult requis pour passer en phase VALIDATE.")

        if target_phase == LoopPhase.BUILD and self.current_phase == LoopPhase.PLAN:
            if self.project_mode == ProjectMode.CLIENT:
                raise ValueError(
                    "Transition de phase invalide : BUILD est interdit en mode CLIENT."
                )
            if self.plan is None:
                raise IntegrityError("PlanResult requis pour passer en phase BUILD.")

        if not self.can_transition_to(target_phase):
            raise ValueError(
                f"Transition de phase invalide : '{self.current_phase.value}' -> '{target_phase.value}' en mode '{self.project_mode.value}'."
            )

        self.previous_phase = self.current_phase
        self.current_phase = target_phase
        self.current_state_id = target_phase.value

    def query_graph(self, question: str) -> str:
        """Recherche in-memory ultra-rapide (remplace l'appel shell coûteux vers graphify)."""
        from src.loop_mem.db import search_in_memory

        project_path = Path("Projects") / self.project_name
        results = search_in_memory(project_path, question, limit=10)
        if not results:
            return "Aucun résultat trouvé dans la mémoire."

        output = [f"--- Résultats in-memory pour '{question}' ---"]
        for r in results:
            output.append(
                f"[{r.get('category', 'Node')}] {r.get('label', r.get('id'))} (ID: {r['id']}) - Score: {r['score']:.1f}"
            )
            snippet = r.get("snippet", "").replace("\n", " ")
            output.append(f"  > {snippet}")
        return "\n".join(output)

    def explain_node(self, node_label: str) -> str:
        """Explique un nœud via in-memory search."""
        return self.query_graph(node_label)

    def load_from_graph(self, project_path: Path) -> None:
        """Charge l'état depuis le nœud 'ML_ACTIVE_STATE' du graphe Graphify."""
        graph_file = project_path / self.graph_path
        if not graph_file.exists():
            return
        try:
            with open(graph_file, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
                nodes = graph_data.get("nodes", [])

                # Charger l'état global
                state_node = next((n for n in nodes if n.get("label") == "ML_ACTIVE_STATE"), None)
                if state_node and "properties" in state_node:
                    data = state_node["properties"]
                    loaded_state = LoopState.model_validate(data)
                    for field in self.__class__.model_fields:
                        if field not in ("sprint_backlog", "journal", "knowledge_graph"):
                            setattr(self, field, getattr(loaded_state, field))

                # Charger le journal à partir des nœuds JournalEntry
                journal_nodes = [n for n in nodes if n.get("category") == "JournalEntry"]
                journal_entries = []
                for n in journal_nodes:
                    if "properties" in n:
                        try:
                            journal_entries.append(JournalEntry.model_validate(n["properties"]))
                        except:
                            pass

                # Trier chronologiquement (au cas où)
                journal_entries.sort(key=lambda x: x.timestamp)
                self.journal = journal_entries

        except Exception as e:
            print("Erreur de chargement depuis le graphe:", e)

    def add_to_journal(self, event: str, details: str, impacted_nodes: List[str] = None) -> None:
        """Ajoute une entrée au journal et la lie sémantiquement au graphe."""
        entry = JournalEntry(event=event, details=details, impacted_nodes=impacted_nodes or [])
        self.journal.append(entry)

    def save_to_graph(self, project_path: Path) -> None:
        """Sauvegarde l'état actuel et le journal dans le graphe Graphify."""
        graph_file = project_path / self.graph_path

        if not graph_file.parent.exists():
            graph_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Préparation des données (on exclut le backlog lourd)
            state_data = self.model_dump(exclude={"sprint_backlog", "knowledge_graph", "journal"})

            graph_data = {"nodes": [], "edges": []}
            if graph_file.exists():
                try:
                    with open(graph_file, "r", encoding="utf-8") as f:
                        graph_data = json.load(f)
                except Exception:
                    pass

            nodes_list = graph_data.get("nodes", [])
            edges_list = graph_data.get("edges", [])

            # Indexation rapide des IDs existants pour éviter le O(N^2)
            existing_node_ids = {n.get("id") for n in nodes_list}

            # 1. Persistance du State Global
            state_node = next((n for n in nodes_list if n.get("label") == "ML_ACTIVE_STATE"), None)
            if state_node:
                state_node["properties"] = state_data
            else:
                nodes_list.append(
                    {
                        "id": "ml_active_state",
                        "label": "ML_ACTIVE_STATE",
                        "category": "LoopState",
                        "properties": state_data,
                    }
                )

            # 2. Persistance du Journal (Chaque entrée devient un nœud)
            for entry in self.journal:
                entry_id = f"journal_{entry.id}"
                # Vérifier si l'entrée existe déjà
                if entry_id not in existing_node_ids:
                    nodes_list.append(
                        {
                            "id": entry_id,
                            "label": f"Journal: {entry.event}",
                            "category": "JournalEntry",
                            "properties": entry.model_dump(),
                        }
                    )
                    # Création des liens d'impact
                    for node_label in entry.impacted_nodes:
                        edges_list.append(
                            {"source": entry_id, "target": node_label, "relation": "IMPACTS"}
                        )

            graph_data["nodes"] = nodes_list
            graph_data["edges"] = edges_list

            # Sauvegarde atomique avec fichier temporaire pour prévenir toute corruption
            tmp_graph_file = graph_file.with_suffix(".tmp")
            with open(tmp_graph_file, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            tmp_graph_file.replace(graph_file)

            # L'index SQLite FTS5 (graph_index.db) a été retiré au profit du moteur de recherche L3 In-Memory.
            pass

        except Exception as e:
            logger.warning(f"Erreur lors de la sauvegarde dans le graphe ({graph_file}): {e}")

    def search_nodes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recherche rapide en mémoire dans le graphe consolidé."""
        from src.loop_mem.db import search_in_memory

        project_path = Path("Projects") / self.project_name
        return search_in_memory(project_path, query, limit)

    def load_from_audit(self, project_path: Path) -> None:
        """Charge l'état depuis le graphe et la configuration du projet."""
        self.load_from_graph(project_path)
        self.discover_backlog(project_path)

        # Charger la configuration Jira propre au projet (Projects/<p>/jira_config.json)
        jira_cfg = project_path / "jira_config.json"
        if jira_cfg.exists():
            try:
                with open(jira_cfg, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if "jira_project_key" in cfg:
                        self.jira_project_key = cfg["jira_project_key"]
                    if "jira_epic_key" in cfg:
                        self.jira_epic_key = cfg["jira_epic_key"]
                    if "jira_default_billing_id" in cfg:
                        self.jira_default_billing_id = cfg["jira_default_billing_id"]
                    if "jira_default_component_id" in cfg:
                        self.jira_default_component_id = cfg["jira_default_component_id"]
                    if "jira_default_subtasks" in cfg:
                        self.jira_default_subtasks = cfg["jira_default_subtasks"]
                    if "jira_subtask_mapping" in cfg:
                        self.jira_subtask_mapping = cfg["jira_subtask_mapping"]
            except Exception as e:
                logger.debug(f"Lecture jira_config {jira_cfg} ignorée: {e}")

        # Charger le graphe de connaissances local
        kg_file = project_path / "memory" / "knowledge_graph.json"
        if kg_file.exists():
            try:
                with open(kg_file, "r", encoding="utf-8") as f:
                    g_data = json.load(f)
                    self.knowledge_graph = KnowledgeGraph(
                        nodes=g_data.get("nodes", []), edges=g_data.get("edges", [])
                    )
            except Exception as e:
                logger.debug(f"Lecture knowledge_graph {kg_file} ignorée: {e}")

    def save_to_audit(self, project_path: Path) -> None:
        """Sauvegarde l'état dans le graphe."""
        self.save_to_graph(project_path)

    def discover_backlog(self, project_path: Path) -> None:
        """Scans backlog folder and populates sprint_backlog from Markdown Frontmatter (ADR-0011)."""
        import yaml
        import re

        backlog_dir = project_path / "backlog"
        if not backlog_dir.exists():
            return

        discovered_items = []
        for md_file in backlog_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                # Extract YAML block between ---
                match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))

                    # Extract Title (ADR-0011 fallback or pure title)
                    title_match = re.search(r"^#\s*(.*)$", content, re.MULTILINE)
                    raw_title = title_match.group(1).strip() if title_match else md_file.stem
                    # Clean all technical prefixes ( [M], ST-XXX, STORY-REC-XXX-BE ) to keep title pure
                    clean_title = re.sub(
                        r"^(?:\[.*?\]\s*)?(?:STORY|ST|REC)[A-Z0-9\-]*\s*[:\-]\s*",
                        "",
                        raw_title,
                        flags=re.IGNORECASE,
                    ).strip()

                    # Convert to SprintBacklogItem
                    raw_status = str(frontmatter.get("status", "OPEN"))
                    item = SprintBacklogItem(
                        id=frontmatter.get("id", md_file.stem),
                        title=clean_title,
                        description=md_file.relative_to(backlog_dir).as_posix(),
                        components=frontmatter.get("components", []),
                        jira_key=frontmatter.get("jira_key"),
                        status=StoryStatus.from_raw(raw_status),
                        invest_score=str(frontmatter.get("invest_score", "N/A")),
                    )
                    discovered_items.append(item)
            except Exception:
                continue

        self.sprint_backlog = discovered_items
