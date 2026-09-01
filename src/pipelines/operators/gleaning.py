"""
Opérateur DocETL : Gleaning (Self-Refinement par Validation Croisée).
Formalisation mathématique : Map => Map_init -> (Validator -> Refiner) <= k
Permet d'éliminer les omissions et hallucinations sur des extractions critiques.
"""

import json
from typing import Any, Dict, List, Optional
from src.core.llm_client import AsyncLLMClient


class GleaningEngine:
    """
    Moteur de Gleaning agentique appliquant un cycle de validation et de correction itérative.
    """

    def __init__(self, client: AsyncLLMClient):
        self.client = client

    async def execute(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        validator_criteria: str,
        response_schema: Optional[Dict[str, Any]] = None,
        max_iterations: int = 1,
        temperature: float = 0.0,
        project_name: str = "mLoop",
    ) -> Dict[str, Any]:
        """
        Exécute le pipeline de Gleaning.
        
        Args:
            model: Modèle cible (ex: 'nmedia_cloud/claude-sonnet-4.6').
            system_prompt: Rôle et directives de l'extracteur.
            user_prompt: Donnée source et consigne d'extraction.
            validator_criteria: Critères formels de validation (ex: complétude, fidélité aux faits).
            response_schema: Schéma JSON attendu.
            max_iterations: Nombre maximal d'itérations de raffinement (k).
            temperature: Température d'inférence.
            project_name: Nom du projet pour TokenLedger.
            
        Returns:
            Dict contenant le résultat final, l'historique des passes et le statut de validation.
        """
        audit_trail: List[Dict[str, Any]] = []

        # 1. Passe Initiale (Map_init)
        init_res = await self.client.complete(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
            temperature=temperature,
            project_name=project_name,
            action_name="gleaning_init",
        )

        current_output = init_res["text"]
        current_json = init_res["json"]
        audit_trail.append({
            "step": "init",
            "output": current_output,
            "json": current_json,
            "cached": init_res.get("cached", False),
        })

        refinements_count = 0
        validation_rounds = 0
        validator_sys = """Tu es un Validateur Critique de Haute Précision.
Ton rôle est d'auditer l'extraction produite par rapport au document source et aux critères donnés.
Tu dois répondre STRICTEMENT au format JSON suivant :
{
  "is_satisfactory": true | false,
  "critique": "Explication concise des lacunes, omissions ou hallucinations constatées (ou 'Conforme' si parfait)",
  "missing_elements": ["Élément manquant 1", "Élément manquant 2"]
}"""

        while validation_rounds < max_iterations:
            validation_rounds += 1

            # 2. Passe de Validation (Validator)
            validator_user = f"""=== DOCUMENT SOURCE ===
{user_prompt}

=== EXTRACTION ACTUELLE À ÉVALUER ===
{current_output}

=== CRITÈRES D'EXACTITUDE ET DE COMPLÉTUDE ===
{validator_criteria}

Vérifie rigoureusement si l'extraction actuelle est exhaustive, factuelle et respecte tous les critères."""

            val_res = await self.client.complete(
                model=model,
                system_prompt=validator_sys,
                user_prompt=validator_user,
                response_schema={"type": "object"},
                temperature=0.0,
                project_name=project_name,
                action_name=f"gleaning_validate_pass_{validation_rounds}",
            )

            val_json = val_res.get("json") or {}
            is_satisfactory = val_json.get("is_satisfactory", True)
            critique = val_json.get("critique", "Conforme")
            missing = val_json.get("missing_elements", [])

            audit_trail.append({
                "step": f"validation_pass_{validation_rounds}",
                "is_satisfactory": is_satisfactory,
                "critique": critique,
                "missing_elements": missing,
            })

            # Si le résultat est validé sans lacune, arrêt immédiat
            if is_satisfactory or (not missing and "conforme" in critique.lower()):
                break

            # 3. Passe de Raffinement (Refiner)
            refinements_count += 1
            refiner_user = f"""=== DOCUMENT SOURCE ===
{user_prompt}

=== PRÉCÉDENTE EXTRACTION ===
{current_output}

=== FEEDBACK DU VALIDATEUR ===
Critique : {critique}
Éléments omis ou à corriger : {missing}

Corrige et enrichis l'extraction pour résoudre intégralement les remarques du validateur."""

            refine_res = await self.client.complete(
                model=model,
                system_prompt=system_prompt,
                user_prompt=refiner_user,
                response_schema=response_schema,
                temperature=temperature,
                project_name=project_name,
                action_name=f"gleaning_refine_pass_{refinements_count}",
            )

            current_output = refine_res["text"]
            current_json = refine_res["json"]

            audit_trail.append({
                "step": f"refine_pass_{refinements_count}",
                "output": current_output,
                "json": current_json,
                "cached": refine_res.get("cached", False),
            })

        return {
            "final_text": current_output,
            "final_json": current_json,
            "refinements_count": refinements_count,
            "validation_rounds": validation_rounds,
            "is_validated": audit_trail[-1].get("is_satisfactory", True) if "validation" in audit_trail[-1]["step"] else True,
            "audit_trail": audit_trail,
        }
