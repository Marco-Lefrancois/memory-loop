"""
Frontier Rounds, Heuristics & Context Budget - mLoop Grill Package (ADR-0389)
Gestion des formats de questions, du routage des ungrillables et de la Dumb Zone.
"""

from typing import Any, Dict, List

UNGRILLABLE_KEYWORDS = {
    "spatial_layout": [
        "wizard",
        "monopage",
        "accordéon",
        "accordeon",
        "drawer",
        "tiroir",
        "modal",
        "modale",
        "popup",
        "layout",
        "disposition",
        "colonnes",
        "onglets",
        "tabs",
        "stepper",
    ],
    "density_hierarchy": [
        "densité",
        "densite",
        "tableau",
        "cartes",
        "cards",
        "liste condensée",
        "condensee",
        "kanban",
        "hiérarchie visuelle",
    ],
    "micro_interaction": [
        "animation",
        "transition",
        "scroll",
        "pagination",
        "infinite scroll",
        "charger plus",
        "drag and drop",
        "glisser-déposer",
    ],
}


def detect_ungrillable_signals(question: str) -> Dict[str, Any]:
    """
    Analyse le texte d'une question pour détecter si elle relève du domaine 'Ungrillable'
    (haute-fidélité IHM / UX impossible à trancher efficacement en pur texte, ADR-0389 §B).
    """
    lower_q = question.lower()
    matched_categories = []
    matched_keywords = []

    for category, kw_list in UNGRILLABLE_KEYWORDS.items():
        found = [kw for kw in kw_list if kw in lower_q]
        if found:
            matched_categories.append(category)
            matched_keywords.extend(found)

    is_ungrillable = len(matched_categories) > 0
    suggested_proto = (
        "html_tailwind"
        if "spatial_layout" in matched_categories
        or "micro_interaction" in matched_categories
        else "svg_mockup"
    )

    return {
        "is_ungrillable": is_ungrillable,
        "categories": matched_categories,
        "matched_keywords": matched_keywords,
        "recommended_action": "HANDOFF_PROTOTYPE" if is_ungrillable else "CONTINUE_GRILL",
        "suggested_prototype": suggested_proto if is_ungrillable else None,
    }


def format_frontier_round(
    questions: List[Dict[str, Any]], round_num: int = 1, theme: str = ""
) -> str:
    """
    Formate un lot de 2 à 4 questions orthogonales sous forme de Frontier Round (ADR-0389 §A).
    Chaque question doit contenir 'title', 'guess', 'recommendation' et optionnellement 'context'.
    """
    theme_str = f" ({theme})" if theme else ""
    header = f"### 🌐 Round de Frontière #{round_num}{theme_str}\n"
    header += f"> *{len(questions)} questions orthogonales identifiées — Aucune dépendance mutuelle directe.*\n\n---\n"

    parts = [header]
    for idx, q in enumerate(questions, 1):
        q_title = q.get("title", f"Question {idx}")
        q_context = q.get("context", "")
        q_guess = q.get("guess", "À confirmer par le PO.")
        q_rec = q.get("recommendation", "Recommandation mLoop par défaut.")

        block = f"#### ❓ Q{idx}. {q_title}\n"
        if q_context:
            block += f"* **Contexte** : {q_context}\n"
        block += f"* **💡 GUESS** : {q_guess}\n"
        block += f"* **➡️ Recommandation mLoop** : {q_rec}\n\n---\n"
        parts.append(block)

    parts.append(
        "*👉 Réponse attendue : validation globale (« Validé ») ou amendement sélectif (ex: « Q1: option B, Q2: ok »).*\n"
    )
    return "".join(parts)


def check_context_health(estimated_tokens: int) -> Dict[str, Any]:
    """
    Évalue la santé de la fenêtre de contexte de session (ADR-0389 §C).
    Seuils :
    - < 80 000 tokens  : SMART_ZONE (nominal)
    - 80 000 - 120 000 : WARNING_ZONE (point de contrôle in-flight recommandé)
    - > 120 000 tokens : DUMB_ZONE (attention dégradée, forcer clôture ou partitionnement)
    """
    if estimated_tokens < 80000:
        return {
            "zone": "SMART_ZONE",
            "status": "HEALTHY",
            "estimated_tokens": estimated_tokens,
            "message": "Session dans la zone de haute attention cognitive.",
            "action": "CONTINUE",
        }
    elif estimated_tokens <= 120000:
        return {
            "zone": "WARNING_ZONE",
            "status": "WARNING",
            "estimated_tokens": estimated_tokens,
            "message": "Approche du seuil de fatigue cognitive. Point de contrôle recommandé.",
            "action": "TRIGGER_CHECKPOINT",
        }
    else:
        return {
            "zone": "DUMB_ZONE",
            "status": "CRITICAL",
            "estimated_tokens": estimated_tokens,
            "message": "Seuil critique d'attention franchi (>120k tokens). Risque d'incohérence.",
            "action": "FREEZE_BRANCHES_OR_SPLIT",
        }
