"""Métadonnées UI des modules métiers (MLOOP-145-BE — extraction ADR-0202 depuis module_utils)."""

from __future__ import annotations

from typing import Dict

from src.dashboard.project_utils import canonical_key

MODULE_METADATA: Dict[str, Dict[str, str]] = {
    "01-reception": {
        "label": "🐣 Réception & Quai",
        "description": "Réception des œufs, traçabilité camions, pesées et quai de déchargement",
        "category": "core",
    },
    "02-incubation": {
        "label": "🥚 Incubation & Mirage",
        "description": "Salles d'incubation, chariots, sondes thermiques et mirage",
        "category": "core",
    },
    "03-ventes": {
        "label": "🤝 Ventes & Expéditions",
        "description": "Commandes couvoir, ventilation poussins, bons de livraison et facturation",
        "category": "core",
    },
    "onetrust_food": {
        "label": "🔒 OneTrust Alimentation",
        "description": "Bannière cookies, conformité Loi 25 et télémétrie e-commerce alimentaire",
        "category": "compliance",
    },
    "papercuts": {
        "label": "✂️ Papercuts (Gate 0)",
        "description": "Optimisations UX, leaderboard Criteo sur PLP et suivi de commande",
        "category": "ux",
    },
    "metro_food_offers": {
        "label": "🏷️ Offres & Rabais",
        "description": "Circulaires, coupons personnalisés et moteur de promotions Metro Food",
        "category": "feature",
    },
    "rbc_avion": {
        "label": "✈️ RBC Avion",
        "description": "Intégration du programme de points et récompenses RBC Avion",
        "category": "loyalty",
    },
    "onetrust_commerce": {
        "label": "🔒 OneTrust E-Commerce",
        "description": "Gestion des consentements et pixels tiers sur le portail e-commerce",
        "category": "compliance",
    },
    "onetrust_sante": {
        "label": "🔒 OneTrust Santé / Pharma",
        "description": "Consentements et confidentialité des dossiers santé (Jean Coutu & Brunet)",
        "category": "compliance",
    },
    "accesdossier": {
        "label": "🩺 Accès Dossier Patient",
        "description": "Interopérabilité dossiers patients et prescription RxPro",
        "category": "health",
    },
    "onetrust": {
        "label": "🔒 OneTrust Socle",
        "description": "Composants partagés et intégration SDK OneTrust transversale",
        "category": "compliance",
    },
    "loi25-rgpd": {
        "label": "⚖️ Loi 25 & RGPD",
        "description": "Règles d'anonymisation et gouvernance légale des données clients",
        "category": "compliance",
    },
    "programme-moi": {
        "label": "💳 Programme Moi",
        "description": "Identité numérique et programme de fidélité transverse",
        "category": "loyalty",
    },
    "sdk-maui": {
        "label": "📱 SDK MAUI",
        "description": "Composants mobiles natifs .NET MAUI pour les applications Metro",
        "category": "tech",
    },
}


def normalize_module_id(module_id: str) -> str:
    """Normalise un identifiant de module pour la comparaison tolérante."""
    if not module_id:
        return ""
    return module_id.strip().replace("\\", "/").split("/")[-1].strip().lower()


def get_module_friendly_info(module_id: str, project_name: str = "") -> Dict[str, str]:
    """Retourne les métadonnées UI pour un module donné."""
    norm = normalize_module_id(module_id)
    if norm in MODULE_METADATA:
        return MODULE_METADATA[norm]

    ck = canonical_key(norm)
    for k, v in MODULE_METADATA.items():
        if ck == canonical_key(k):
            return v

    pretty = module_id.replace("_", " ").replace("-", " ").title()
    return {
        "label": f"📁 {pretty}",
        "description": f"Module {module_id} ({project_name or 'actif'})",
        "category": "module",
    }
