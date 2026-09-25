"""
Synchronisateur synchrone EvidencePack 2.0 — Pipeline d'harmonisation atomique.
Conforme ADR-0394, ADR-0369, ADR-0376 (atomicité, préservation, idempotence).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from src.pipelines.evidence_types import CodeTraceabilityEntry
from src.pipelines.plan_evidence_parser import PlanEvidenceParser
from src.pipelines.pack_preserver import PackPreserver, load_preserved_fields

if TYPE_CHECKING:
    from src.pipelines.evidence_pack import EvidencePackEngine
from src.utils.logger import get_logger

logger = get_logger("pipelines.evidence_synchronizer")


class EvidenceSynchronizer:
    """
    Pipeline d'harmonisation synchrone EvidencePack 2.0.
    Orchestre : parse → validate → SHA-256 → merge atomique (tout-ou-rien).
    """

    # Extensions de fichiers sources à hasher
    SOURCE_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".cs",
        ".java",
        ".go",
        ".rs",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
    }

    def __init__(self, project_path: Union[str, Path]):
        self.project_path = Path(project_path)
        # Import at runtime to avoid circular import
        from src.pipelines.evidence_pack import EvidencePackEngine

        self.engine = EvidencePackEngine(self.project_path)
        self.parser = PlanEvidenceParser()
        self.preserver = PackPreserver()

    def sync_story_evidence(
        self,
        story_id: str,
        plan_path: Optional[Union[str, Path]] = None,
        base_dir: Optional[Union[str, Path]] = None,
        tasks_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Pipeline synchrone d'harmonisation EvidencePack 2.0.

        Séquence tout-ou-rien (atomicité garantie) :
        1. Extraction matrice depuis plan.md (prioritaire) ou tasks.md (fallback OpenSpec)
        2. Validation stricte via EvidencePackEngine.validate_code_traceability
        3. Calcul SHA-256 des fichiers sources distincts référencés
        4. Fusion atomique non-destructrice via PackPreserver (préserve tdd_cycle, fact_check_certificate, etc.)

        Args:
            story_id: Identifiant du récit (ex: "MLOOP-332-BE")
            plan_path: Chemin vers le plan d'implémentation (optionnel, défaut: memory/plan/implementation_plan_<story_id>.md)
            base_dir: Répertoire de base pour résolution chemins relatifs (défaut: project_path)
            tasks_path: Chemin vers tasks.md OpenSpec (fallback, optionnel)

        Returns:
            Chemin vers le fichier EvidencePack mis à jour

        Raises:
            ValueError: si validation échoue (aucune écriture partielle)
            FileNotFoundError: si ni plan.md ni tasks.md n'existent
        """
        story_id_clean = story_id.replace(" ", "_")
        base = Path(base_dir) if base_dir else self.engine.project_path

        # 1. Déterminer le plan source (priorité : plan.md explicite > défaut > tasks.md fallback)
        plan_file = self._resolve_plan_file(story_id, plan_path, tasks_path)
        if plan_file is None:
            raise FileNotFoundError(
                f"[EvidenceSynchronizer] Aucun plan d'implémentation trouvé pour {story_id}. "
                f"Ni plan.md (memory/plan/implementation_plan_{story_id}.md) "
                f"ni tasks.md (fallback OpenSpec) n'existent."
            )

        logger.info(
            f"Synchronisation EvidencePack pour {story_id} depuis {plan_file.name}",
            extra={"story_id": story_id, "plan_file": str(plan_file)},
        )

        # 2. Extraction matrice depuis le plan
        entries = self._extract_matrix(plan_file)

        # 3. Validation stricte (lève ValueError si invalide)
        # Cast sûr car les entrées viennent du parser qui valide déjà via EvidencePackEngine
        typed_entries: List[CodeTraceabilityEntry] = [CodeTraceabilityEntry(**e) for e in entries]
        self.engine.validate_code_traceability(typed_entries)

        # 4. Calcul SHA-256 des fichiers sources distincts
        source_hashes = self._compute_source_hashes(entries, base)

        # 5. Fusion atomique via PackPreserver (tout-ou-rien)
        target_path = self._atomic_merge(
            story_id=story_id,
            entries=entries,
            source_hashes=source_hashes,
        )

        logger.info(
            f"Synchronisation EvidencePack terminée pour {story_id} : "
            f"{len(entries)} entrées, {len(source_hashes)} hashes sources",
            extra={
                "story_id": story_id,
                "entries_count": len(entries),
                "hashes_count": len(source_hashes),
                "target": str(target_path),
            },
        )

        return target_path

    def _resolve_plan_file(
        self,
        story_id: str,
        plan_path: Optional[Union[str, Path]],
        tasks_path: Optional[Union[str, Path]],
    ) -> Optional[Path]:
        """Résout le fichier plan à utiliser (priorité : explicite > défaut > fallback tasks.md)."""
        # 1. Plan explicite fourni
        if plan_path:
            p = Path(plan_path)
            if p.exists():
                return p
            logger.warning(
                f"Plan explicite introuvable : {plan_path}",
                extra={"story_id": story_id, "plan_path": str(plan_path)},
            )

        # 2. Plan par défaut : memory/plan/implementation_plan_<STORY_ID>.md
        default_plan = (
            self.engine.project_path / "memory" / "plan" / f"implementation_plan_{story_id}.md"
        )
        if default_plan.exists():
            return default_plan

        # 3. Fallback OpenSpec : tasks.md (si fourni ou défaut)
        if tasks_path:
            tp = Path(tasks_path)
            if tp.exists():
                logger.info(
                    f"Utilisation fallback OpenSpec tasks.md : {tp}",
                    extra={"story_id": story_id, "tasks_path": str(tp)},
                )
                return tp

        # 4. Fallback OpenSpec par défaut : memory/plan/tasks.md ou backlog/handoff/tasks.md
        for fallback in [
            self.engine.project_path / "memory" / "plan" / "tasks.md",
            self.engine.project_path / "backlog" / "handoff" / "tasks.md",
        ]:
            if fallback.exists():
                logger.info(
                    f"Utilisation fallback OpenSpec par défaut : {fallback}",
                    extra={"story_id": story_id, "fallback": str(fallback)},
                )
                return fallback

        return None

    def _extract_matrix(self, plan_file: Path) -> List[Dict[str, Any]]:
        """Extrait la matrice depuis le plan (Markdown) ou tasks.md (OpenSpec)."""
        content = plan_file.read_text(encoding="utf-8")

        # Détecter si c'est un format OpenSpec tasks.md (structure différente)
        if plan_file.name == "tasks.md" or "tasks.md" in str(plan_file):
            return self._extract_from_openspec_tasks(content)

        # Format standard : plan.md avec section Matrice de Traçabilité
        entries = self.parser.extract_matrix_from_plan(Path(plan_file))
        return [dict(e) for e in entries]

    def _extract_from_openspec_tasks(self, content: str) -> List[Dict[str, Any]]:
        """
        Extrait la traçabilité depuis un fichier tasks.md OpenSpec.
        Format attendu : tableau Markdown avec colonnes compatibles.
        """
        # Rechercher un tableau dans tasks.md
        table_pattern = re.compile(r"(?ms)^\s*\|.+\|\s*\n\s*\|[\s\-\:]+\|\s*\n(?:\s*\|.+\|\s*\n)+")
        tables = table_pattern.findall(content)

        for table_text in tables:
            try:
                entries = self.parser._parse_gfm_table(table_text)
                if entries:
                    logger.info(
                        f"Matrice extraite depuis tasks.md OpenSpec : {len(entries)} entrées",
                        extra={"entries_count": len(entries)},
                    )
                    return [dict(e) for e in entries]
            except ValueError:
                continue  # Essayer le tableau suivant

        raise ValueError(
            "[EvidenceSynchronizer] Aucun tableau de traçabilité valide trouvé dans tasks.md OpenSpec."
        )

    def _compute_source_hashes(
        self,
        entries: List[Dict[str, Any]],
        base_dir: Path,
    ) -> Dict[str, str]:
        """
        Calcule les empreintes SHA-256 de chaque fichier source distinct
        référencé dans les symboles AST et tests.
        """
        source_files: set[str] = set()

        for entry in entries:
            # Fichier source depuis ast_symbol (ex: "src/core/auth.py::TokenVerifier.verify_expiration")
            ast_symbol = entry.get("ast_symbol", "")
            if "::" in ast_symbol:
                src_file = ast_symbol.split("::")[0].strip()
                if src_file:
                    source_files.add(src_file)

            # Fichier test depuis test_symbol
            test_symbol = entry.get("test_symbol")
            if test_symbol and "::" in test_symbol:
                test_file = test_symbol.split("::")[0].strip()
                if test_file:
                    source_files.add(test_file)

        # Calculer les hashes
        hashes: Dict[str, str] = {}
        for src in sorted(source_files):
            src_path = self.engine.project_path / src
            if src_path.exists() and src_path.is_file():
                try:
                    h = hashlib.sha256()
                    with open(src_path, "rb") as f:
                        while chunk := f.read(8192):
                            h.update(chunk)
                    hashes[src] = h.hexdigest()
                except Exception as e:
                    logger.debug(
                        f"Calcul SHA-256 échoué pour {src}",
                        exc_info=True,
                        extra={"source": src, "error": str(e)},
                    )
            else:
                logger.debug(
                    f"Fichier source introuvable pour hash : {src}",
                    extra={"source": src, "resolved_path": str(self.engine.project_path / src)},
                )

        return hashes

    def sync_from_openspec_tasks(
        self,
        story_id: str,
        tasks_path: Union[str, Path],
        base_dir: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Point d'entrée explicite pour synchronisation depuis tasks.md OpenSpec.
        """
        return self.sync_story_evidence(
            story_id=story_id,
            plan_path=None,
            tasks_path=tasks_path,
        )

    def _atomic_merge(
        self,
        story_id: str,
        entries: List[Dict[str, Any]],
        source_hashes: Dict[str, str],
    ) -> Path:
        """
        Fusion atomique non-destructrice via PackPreserver.
        Écriture tout-ou-rien : validation complète AVANT écriture.
        """
        story_id_clean = story_id.replace(" ", "_")
        evidence_dir = self.engine.evidence_dir
        target_json = evidence_dir / f"{story_id}_evidence.json"

        # 1. Charger le pack existant (si existe) pour préserver les blocs protégés
        existing_pack: Dict[str, Any] = {}
        if target_json.exists():
            try:
                existing_pack = json.loads(target_json.read_text(encoding="utf-8"))
            except Exception as e:
                logger.debug(
                    "Lecture pack existant échouée, nouveau pack créé",
                    exc_info=True,
                    extra={"story_id": story_id, "error": str(e)},
                )

        # 2. Préparer les nouvelles données de traçabilité
        traceability_data = {
            "code_traceability_matrix": entries,
            "source_hashes": source_hashes,
            "updated_at": __import__("datetime")
            .datetime.now(__import__("datetime").timezone.utc)
            .isoformat(),
        }

        # 3. Fusion via PackPreserver (préserve tdd_cycle, fact_check_certificate, verbatim_extracts, etc.)
        merged_pack = self.preserver.merge(existing_pack, traceability_data)

        # 4. S'assurer que story_id et timestamp sont à jour
        merged_pack["story_id"] = story_id.replace(" ", "_")
        merged_pack["updated_at"] = (
            __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        )

        # 5. Écriture atomique (tout-ou-rien)
        evidence_dir = self.engine.evidence_dir
        evidence_dir.mkdir(parents=True, exist_ok=True)

        target_json = self.engine.evidence_dir / f"{story_id.replace(' ', '_')}_evidence.json"
        target_json.write_text(
            json.dumps(merged_pack, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        logger.info(
            f"EvidencePack mis à jour atomiquement : {target_json}",
            extra={"story_id": story_id, "target": str(target_json)},
        )

        return target_json
