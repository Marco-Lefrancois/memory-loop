"""
Moteur d'Extraction Déclarative YAML mLoop (Standard ADR-0342).
Inspiré par le framework Hyper-Extract.

Permet de transformer des documents non structurés ou ingérés en Knowledge Abstracts (KAs)
fortement typés et structurés (Règles Métier, Modèles DDD, Contrats API, Matrices UI).
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class ExtractedEntity:
    """Représente une entité de connaissance extraite avec son ancrage de source."""
    id: str
    entity_type: str
    data: Dict[str, Any]
    source_file: str
    source_heading: Optional[str] = None
    confidence: float = 1.0


@dataclass
class KnowledgeAbstract:
    """Knowledge Abstract (KA) regroupant un ensemble d'entités extraites cohérentes."""
    extractor_id: str
    source_file: str
    entities: List[ExtractedEntity] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extractor_id": self.extractor_id,
            "source_file": self.source_file,
            "total_entities": len(self.entities),
            "metadata": self.metadata,
            "entities": [
                {
                    "id": e.id,
                    "entity_type": e.entity_type,
                    "data": e.data,
                    "source_file": e.source_file,
                    "source_heading": e.source_heading,
                    "confidence": e.confidence
                }
                for e in self.entities
            ]
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class DeclarativeExtractor:
    """Moteur de chargement et d'exécution des blueprints d'extraction déclaratifs."""

    BLUEPRINT_DIR = Path("standards/blueprints/extractors")

    def __init__(self, blueprint_dir: Optional[Path] = None):
        self.blueprint_dir = blueprint_dir or self.BLUEPRINT_DIR

    def list_templates(self) -> List[str]:
        """Retourne la liste des identifiants d'extracteurs disponibles."""
        if not self.blueprint_dir.exists():
            return []
        templates = []
        for file in self.blueprint_dir.glob("*.yaml"):
            name = file.stem.replace("extractor_", "")
            templates.append(name)
        return sorted(templates)

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """Charge un blueprint d'extraction par son nom court ou son nom complet."""
        clean_name = template_name.replace("extractor_", "").replace(".yaml", "")
        file_path = self.blueprint_dir / f"extractor_{clean_name}.yaml"
        
        if not file_path.exists():
            # Essai direct avec le nom fourni
            file_path = self.blueprint_dir / f"{template_name}.yaml"
            if not file_path.exists():
                available = self.list_templates()
                raise FileNotFoundError(
                    f"Template d'extraction '{template_name}' introuvable sous {self.blueprint_dir}. "
                    f"Templates disponibles : {available}"
                )
        
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def extract_from_text(
        self,
        text_content: str,
        template_def: Dict[str, Any],
        source_file: str = "raw_input.md"
    ) -> KnowledgeAbstract:
        """
        Extrait les entités à partir d'un texte source selon les règles du template.
        Combine l'analyse structurelle des sections Markdown, listes et tables.
        """
        extractor_id = template_def.get("extractor_id", "generic")
        id_prefix = template_def.get("id_prefix", "EXT-")
        id_padding = template_def.get("id_padding", 3)
        schema_fields = {f["name"]: f for f in template_def.get("schema", {}).get("fields", [])}

        ka = KnowledgeAbstract(extractor_id=extractor_id, source_file=source_file)
        
        # Découpage par sections (H1, H2, H3)
        sections = re.split(r'(?m)^(?=#{1,3}\s+)', text_content)
        entity_count = 0

        for section in sections:
            section_trimmed = section.strip()
            if not section_trimmed:
                continue

            # Détection du titre de section
            header_match = re.match(r'^(#{1,3})\s+(.+)$', section_trimmed, re.MULTILINE)
            current_heading = header_match.group(2).strip() if header_match else "Section Générale"

            # Recherche de motifs selon le type d'extracteur
            if extractor_id == "business_rules":
                extracted = self._extract_business_rules(section_trimmed, current_heading, source_file, id_prefix, id_padding, entity_count + 1)
                for ent in extracted:
                    entity_count += 1
                    ka.entities.append(ent)

            elif extractor_id == "data_models":
                extracted = self._extract_data_models(section_trimmed, current_heading, source_file, id_prefix, id_padding, entity_count + 1)
                for ent in extracted:
                    entity_count += 1
                    ka.entities.append(ent)

            elif extractor_id == "api_contracts":
                extracted = self._extract_api_contracts(section_trimmed, current_heading, source_file, id_prefix, id_padding, entity_count + 1)
                for ent in extracted:
                    entity_count += 1
                    ka.entities.append(ent)

            elif extractor_id == "ui_matrix":
                extracted = self._extract_ui_matrix(section_trimmed, current_heading, source_file, id_prefix, id_padding, entity_count + 1)
                for ent in extracted:
                    entity_count += 1
                    ka.entities.append(ent)
            else:
                # Extraction générique par blocs de puces
                extracted = self._extract_generic_items(section_trimmed, current_heading, source_file, id_prefix, id_padding, entity_count + 1)
                for ent in extracted:
                    entity_count += 1
                    ka.entities.append(ent)

        return ka

    def _extract_business_rules(self, text: str, heading: str, source_file: str, prefix: str, padding: int, start_idx: int) -> List[ExtractedEntity]:
        results = []
        idx = start_idx
        # Recherche de motifs "Règle", "Condition", "Doit", "Si ... alors"
        lines = text.splitlines()
        for line in lines:
            line_clean = line.strip()
            # Puces avec énoncé de règle
            if re.match(r'^[-*]\s+(.+)$', line_clean):
                content = re.sub(r'^[-*]\s+', '', line_clean)
                if any(kw in content.lower() for kw in ["règle", "rule", "doit", "obligatoire", "interdit", "si ", "calcul", "condition"]):
                    rule_id = f"{prefix}{idx:0{padding}d}"
                    entity_data = {
                        "id": rule_id,
                        "name": content.split(":")[0] if ":" in content else content[:50],
                        "category": "VALIDATION" if "doit" in content.lower() or "valide" in content.lower() else "CALCULATION" if "calcul" in content.lower() else "INTEGRITY",
                        "condition": content.split("alors")[0] if "alors" in content else content,
                        "action": content.split("alors")[1].strip() if "alors" in content else "Application de la règle",
                        "error_code": f"ERR_{rule_id.replace('-', '_')}",
                        "severity": "BLOCKING",
                        "source_anchor": f"Section: {heading} — '{content}'"
                    }
                    results.append(ExtractedEntity(
                        id=rule_id,
                        entity_type="BusinessRule",
                        data=entity_data,
                        source_file=source_file,
                        source_heading=heading
                    ))
                    idx += 1
        return results

    def _extract_data_models(self, text: str, heading: str, source_file: str, prefix: str, padding: int, start_idx: int) -> List[ExtractedEntity]:
        results = []
        idx = start_idx
        # Détection de tables markdown décrivant des champs
        if "|" in text and ("champ" in text.lower() or "type" in text.lower() or "field" in text.lower()):
            model_id = f"{prefix}{idx:0{padding}d}"
            attributes = []
            for line in text.splitlines():
                if "|" in line and not line.strip().startswith("|-") and not "type" in line.lower() and not "---" in line:
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 2:
                        attributes.append({
                            "name": parts[0],
                            "type": parts[1] if len(parts) > 1 else "string",
                            "required": "oui" in parts[2].lower() if len(parts) > 2 else False,
                            "description": parts[3] if len(parts) > 3 else ""
                        })
            if attributes:
                clean_name = re.sub(r'[^a-zA-Z0-9_]', '', heading.title().replace(" ", ""))
                entity_data = {
                    "id": model_id,
                    "entity_name": clean_name or f"Entity_{idx}",
                    "aggregate_root": True if idx == 1 else False,
                    "description": f"Modèle extrait de la section {heading}",
                    "attributes": attributes,
                    "relations": [],
                    "source_anchor": f"Section: {heading}"
                }
                results.append(ExtractedEntity(
                    id=model_id,
                    entity_type="DataModel",
                    data=entity_data,
                    source_file=source_file,
                    source_heading=heading
                ))
        return results

    def _extract_api_contracts(self, text: str, heading: str, source_file: str, prefix: str, padding: int, start_idx: int) -> List[ExtractedEntity]:
        results = []
        idx = start_idx
        pattern = r'(?i)\b(GET|POST|PUT|PATCH|DELETE)\s+([/\w\-{}]+)'
        matches = re.finditer(pattern, text)
        for m in matches:
            api_id = f"{prefix}{idx:0{padding}d}"
            method = m.group(1).upper()
            route = m.group(2)
            entity_data = {
                "id": api_id,
                "route_path": route,
                "http_method": method,
                "summary": f"Opération {method} sur {route}",
                "auth_required": True,
                "request_payload_schema": {},
                "response_statuses": [
                    {"status_code": 200, "description": "Succès", "schema_summary": "Object"},
                    {"status_code": 400, "description": "Paramètres invalides", "schema_summary": "ErrorResponse"}
                ],
                "source_anchor": f"Section: {heading} — '{m.group(0)}'"
            }
            results.append(ExtractedEntity(
                id=api_id,
                entity_type="ApiContract",
                data=entity_data,
                source_file=source_file,
                source_heading=heading
            ))
            idx += 1
        return results

    def _extract_ui_matrix(self, text: str, heading: str, source_file: str, prefix: str, padding: int, start_idx: int) -> List[ExtractedEntity]:
        results = []
        idx = start_idx
        if any(kw in text.lower() or kw in heading.lower() for kw in ["écran", "screen", "modal", "composant", "bouton", "formulaire"]):
            ui_id = f"{prefix}{idx:0{padding}d}"
            clean_screen = re.sub(r'[^a-zA-Z0-9_]', '', heading.title().replace(" ", ""))
            entity_data = {
                "id": ui_id,
                "screen_name": clean_screen or f"Screen_{idx}",
                "macrostructure_type": "Data Form / Action Matrix",
                "primary_cta": "Soumettre / Valider",
                "states": [
                    {"state_name": "DEFAULT", "visual_behavior": "Affichage nominal interactif"},
                    {"state_name": "LOADING", "visual_behavior": "Spinner de chargement avec bouton désactivé"},
                    {"state_name": "ERROR", "visual_behavior": "Bordure rouge et message d'erreur d'accessibilité"}
                ],
                "accessibility_notes": "Conforme WCAG AA, focus visible et navigation clavier complète",
                "source_anchor": f"Section: {heading}"
            }
            results.append(ExtractedEntity(
                id=ui_id,
                entity_type="UiMatrix",
                data=entity_data,
                source_file=source_file,
                source_heading=heading
            ))
        return results

    def _extract_generic_items(self, text: str, heading: str, source_file: str, prefix: str, padding: int, start_idx: int) -> List[ExtractedEntity]:
        results = []
        idx = start_idx
        for line in text.splitlines():
            line_clean = line.strip()
            if re.match(r'^[-*]\s+(.+)$', line_clean):
                item_id = f"{prefix}{idx:0{padding}d}"
                content = re.sub(r'^[-*]\s+', '', line_clean)
                results.append(ExtractedEntity(
                    id=item_id,
                    entity_type="GenericItem",
                    data={"id": item_id, "content": content, "heading": heading},
                    source_file=source_file,
                    source_heading=heading
                ))
                idx += 1
        return results

    def format_markdown(self, entity: ExtractedEntity, template_def: Dict[str, Any]) -> str:
        """Formate une entité extraite en Markdown selon le gabarit de sortie du blueprint."""
        output_template = template_def.get("output_templates", {}).get("markdown")
        if not output_template:
            return f"# {entity.id}\n\n```json\n{json.dumps(entity.data, indent=2, ensure_ascii=False)}\n```\n"

        # Interpolation des variables
        data = entity.data.copy()
        error_code_badge = f"| **Code Erreur :** `{data.get('error_code')}`" if data.get('error_code') else ""
        data["error_code_badge"] = error_code_badge

        # Formatage des attributs pour data_models
        if "attributes" in data and isinstance(data["attributes"], list):
            attr_lines = []
            for attr in data["attributes"]:
                req = "Oui" if attr.get("required") else "Non"
                attr_lines.append(f"| `{attr.get('name')}` | `{attr.get('type')}` | {req} | {attr.get('constraints', '-')} | {attr.get('description', '-')} |")
            data["attributes_table"] = "\n".join(attr_lines) if attr_lines else "| Aucun attribut | - | - | - | - |"

        if "relations" in data and isinstance(data["relations"], list):
            rel_lines = [f"* Vers `{r.get('target_entity')}` ({r.get('cardinality')}) - `{r.get('relation_type')}`" for r in data["relations"]]
            data["relations_list"] = "\n".join(rel_lines) if rel_lines else "* Aucune relation explicite."

        # Formatage pour api_contracts
        if "request_payload_schema" in data:
            data["request_payload_json"] = json.dumps(data.get("request_payload_schema") or {}, indent=2)
        if "response_statuses" in data and isinstance(data["response_statuses"], list):
            resp_lines = [f"| `{r.get('status_code')}` | {r.get('description')} | `{r.get('schema_summary')}` |" for r in data["response_statuses"]]
            data["responses_table"] = "\n".join(resp_lines)

        # Formatage pour ui_matrix
        if "states" in data and isinstance(data["states"], list):
            state_lines = [f"| `{s.get('state_name')}` | {s.get('visual_behavior')} |" for s in data["states"]]
            data["states_table"] = "\n".join(state_lines)

        try:
            return output_template.format(**data)
        except KeyError:
            return f"# {entity.id}\n\n```json\n{json.dumps(entity.data, indent=2, ensure_ascii=False)}\n```\n"
