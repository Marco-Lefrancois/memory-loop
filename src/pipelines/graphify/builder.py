import networkx as nx
import json
from pathlib import Path

class GraphBuilder:
    """Construit et fusionne le graphe sémantique (NetworkX -> JSON)."""
    
    def __init__(self):
        self.tech_lexicon = {
            "postgres": ("Database", "Systeme de gestion de base de donnees relationnelle PostgreSQL.", "PostgreSQL"),
            "postgresql": ("Database", "Systeme de gestion de base de donnees relationnelle PostgreSQL.", "PostgreSQL"),
            "sqlite": ("Database", "Base de donnees relationnelle legere stockee localement dans un fichier.", "SQLite"),
            "mysql": ("Database", "Systeme de gestion de base de donnees relationnelle MySQL.", "MySQL"),
            "redis": ("Cache", "Systeme de stockage de donnees en memoire ultra-rapide utilise comme cache.", "Redis"),
            "mongodb": ("Database", "Base de donnees orientee documents NoSQL.", "MongoDB"),
            "fastapi": ("Backend Framework", "Framework web moderne et rapide pour concevoir des APIs avec Python 3.8+.", "FastAPI"),
            "flask": ("Backend Framework", "Micro-framework web leger pour Python.", "Flask"),
            "django": ("Backend Framework", "Framework web Python complet et structure.", "Django"),
            "react": ("Frontend Library", "Bibliotheque JavaScript pour la conception d'interfaces utilisateur reactives.", "React"),
            "vue": ("Frontend Framework", "Framework JavaScript evolutif pour batir des interfaces utilisateur.", "Vue"),
            "nextjs": ("Frontend Framework", "Framework React avec rendu cote serveur et generation de sites statiques.", "Next.js"),
            "next.js": ("Frontend Framework", "Framework React avec rendu cote serveur et generation de sites statiques.", "Next.js"),
            "python": ("Programming Language", "Langage de programmation oriente objet dynamique et polyvalent.", "Python"),
            "javascript": ("Programming Language", "Langage de programmation de scripts principalement utilise cote client.", "JavaScript"),
            "typescript": ("Programming Language", "Sur-ensemble typé de JavaScript developpe par Microsoft.", "TypeScript"),
            "c#": ("Programming Language", "Langage de programmation orienté objet developpe par Microsoft.", "C#"),
            "docker": ("DevOps tool", "Plateforme de conteneurisation d'applications.", "Docker"),
            "kubernetes": ("DevOps tool", "Plateforme d'orchestration de conteneurs open-source.", "Kubernetes"),
            "pydantic": ("Data Validation", "Bibliotheque de validation de donnees et gestion de configurations basee sur les types Python.", "Pydantic"),
            "networkx": ("Graph Library", "Bibliotheque Python pour la creation, la manipulation et l'etude de graphes complexes.", "NetworkX"),
            "rich": ("CLI Styling", "Bibliotheque Python pour l'affichage de texte enrichi et de styles dans le terminal.", "Rich"),
            "maestro": ("Testing Framework", "Framework moderne de tests mobiles et e2e.", "Maestro"),
            "zephyr": ("Test Management", "Outil de gestion et de suivi de campagnes de tests.", "Zephyr"),
            "pytest": ("Testing Library", "Framework de test unitaire robuste pour Python.", "Pytest")
        }
        self.g = nx.DiGraph()
        self.detected_entities = {}

    def enrich_lexicon(self, global_docs_cache_dir: Path):
        if global_docs_cache_dir.exists():
            for f in global_docs_cache_dir.glob("context7_*.md"):
                lib_name = f.name.replace("context7_", "").replace(".md", "").strip().lower()
                if lib_name not in self.tech_lexicon:
                    self.tech_lexicon[lib_name] = ("ExternalAPI", f"Documentation technique de la librairie '{lib_name}' importee dynamiquement depuis Context7.", lib_name.capitalize())

    def add_text_nodes(self, text_sources: list):
        full_text = "\n".join(text_sources).lower()
        for keyword, tech_info in self.tech_lexicon.items():
            category, default_desc, normalized_name = tech_info
            if keyword in full_text:
                self.detected_entities[keyword] = normalized_name
                text_chunk = ""
                sentences = full_text.replace("\n", " ").split(".")
                for sentence in sentences:
                    if keyword in sentence:
                        text_chunk = sentence.strip() + "."
                        break
                self.g.add_node(normalized_name, category=category, description=default_desc, text_chunk=text_chunk if len(text_chunk) < 300 else text_chunk[:297] + "...")
        
        # Extraction des dépendances sémantiques
        sentences = full_text.split(".")
        for sentence in sentences:
            found_keys = [k for k in self.detected_entities if k in sentence]
            if len(found_keys) >= 2:
                for i in range(len(found_keys)):
                    for j in range(i + 1, len(found_keys)):
                        k1, k2 = found_keys[i], found_keys[j]
                        n1, n2 = self.detected_entities[k1], self.detected_entities[k2]
                        if any(w in sentence for w in ["depends on", "uses", "queries", "calls", "connects to", "imports"]):
                            pos1, pos2 = sentence.find(k1), sentence.find(k2)
                            if pos1 < pos2:
                                self.g.add_edge(n1, n2, type="dependency")
                            else:
                                self.g.add_edge(n2, n1, type="dependency")
                        else:
                            self.g.add_edge(n1, n2, type="association")

    def merge_and_serialize(self, physical_nodes: list, physical_edges: list, graph_file: Path) -> tuple:
        # Fallback si vide
        if len(self.g.nodes) == 0 and len(physical_nodes) == 0:
            self.g.add_node("CLI Engine", category="Engine", description="Moteur de commande textuelle Memory Loop.")
            self.g.add_node("State Machine", category="Cognition", description="Graphe d'etats unifie LoopState.")
            self.g.add_edge("CLI Engine", "State Machine", type="dependency")

        nodes_list = []
        for node, data in self.g.nodes(data=True):
            nodes_list.append({"id": node, "category": data.get("category", "General"), "properties": {"description": data.get("description", ""), "text_chunk": data.get("text_chunk", "")}})

        edges_list = []
        for u, v, data in self.g.edges(data=True):
            edges_list.append({"source": u, "target": v, "type": data.get("type", "dependency"), "properties": {"client_library": "redis-py" if u == "Fastapi" and v == "Redis" else ""}})

        existing_node_ids = {n["id"] for n in nodes_list}
        for pn in physical_nodes:
            if pn["id"] not in existing_node_ids:
                nodes_list.append(pn)
                existing_node_ids.add(pn["id"])

        for pe in physical_edges:
            if pe["target"] in existing_node_ids:
                edges_list.append(pe)

        # Enregistrement
        graph_file.parent.mkdir(parents=True, exist_ok=True)
        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump({"nodes": nodes_list, "edges": edges_list}, f, indent=2, ensure_ascii=False)

        return nodes_list, edges_list
