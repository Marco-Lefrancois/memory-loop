"""Schémas d'outils MCP Graphify (handle_tools_list) — MLOOP-145-BE, extraction ADR-0202."""

from __future__ import annotations


def handle_tools_list(req_id):
    return {
        "jsonrpc": "2.0",
        "result": {
            "tools": [
                {
                    "name": "graph_query",
                    "description": "Interroge le sous-graphe de connaissances autour d'un concept métier (RM-XXX), d'une ADR ou d'un composant.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Mot-clé ou concept recherché (ex: 'RM-001' ou 'Ingestion MarkItDown').",
                            },
                            "project": {
                                "type": "string",
                                "description": "Nom optionnel du projet.",
                            },
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "graph_path",
                    "description": "Calcule le chemin de dépendances direct entre deux concepts ou composants d'architecture.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "Nœud source (ex: 'ADR-0101').",
                            },
                            "target": {
                                "type": "string",
                                "description": "Nœud cible (ex: 'docs/00-ingested').",
                            },
                            "project": {
                                "type": "string",
                                "description": "Nom optionnel du projet.",
                            },
                        },
                        "required": ["source", "target"],
                    },
                },
                {
                    "name": "graph_explain",
                    "description": "Génère une explication détaillée d'un nœud d'architecture et de ses 1-hop voisins dans le graphe.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "concept": {
                                "type": "string",
                                "description": "Identifiant ou titre du nœud.",
                            },
                            "project": {
                                "type": "string",
                                "description": "Nom optionnel du projet.",
                            },
                        },
                        "required": ["concept"],
                    },
                },
                {
                    "name": "graph_blast_radius",
                    "description": "Calcule le rayon d'impact (Blast Radius) ascendant et descendant pour un fichier, un concept ou un modèle.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Chemin du fichier ou nom du concept cible (ex: 'US-01' ou 'OneTrustSDK').",
                            },
                            "project": {
                                "type": "string",
                                "description": "Nom optionnel du projet.",
                            },
                        },
                        "required": ["target"],
                    },
                },
                {
                    "name": "graph_status",
                    "description": "Affiche les statistiques et la santé du graphe de connaissances (taille, nœuds, liens, source et fraîcheur).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "Nom optionnel du projet."}
                        },
                    },
                },
            ]
        },
        "id": req_id,
    }
