import os
import re
import json
import yaml
import unicodedata
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from src.utils.logger import get_logger

logger = get_logger("lexicon_resolver")


class SemanticLexiconResolver:
    """
    Moteur de résolution sémantique DYNAMIQUE et AGNOSTIQUE (mLoop Core - ADR-0327).
    Zéro dictionnaire codé en dur : extrait dynamiquement le vocabulaire, les titres,
    les tags et les métadonnées depuis le système de fichiers, le graphe et les fichiers Markdown.
    """

    @classmethod
    def normalize_string(cls, text: str) -> str:
        """Supprime accents, ponctuation et espaces pour comparaison floue uniforme."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFD", str(text))
        clean = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-zA-Z0-9]", "", clean).lower()

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Découpe un texte en jetons de mots signifiants normalisés (support CamelCase, symboles, tirets)."""
        if not text:
            return []
        # 1. Découpage CamelCase (ex: BoireEtFrere -> Boire Et Frere, MetroFoodOffers -> Metro Food Offers)
        text_str = str(text)
        spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text_str)
        spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)

        # 2. Normalisation accents & minuscules
        normalized = unicodedata.normalize("NFD", spaced)
        clean = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

        # 3. Extraction des tokens alphanumériques
        tokens = re.findall(r"[a-zA-Z0-9]+", clean.lower())
        stopwords = {
            "de",
            "la",
            "le",
            "les",
            "du",
            "des",
            "et",
            "un",
            "une",
            "en",
            "pour",
            "au",
            "aux",
            "and",
            "the",
            "of",
            "in",
            "for",
            "to",
            "with",
            "a",
            "an",
        }
        return [t for t in tokens if len(t) > 1 and t not in stopwords]

    # ──────────────────────────────────────────────────────────────────────────
    # 1. RÉSOLUTION DYNAMIQUE DU PROJET (Zéro Hardcoding & Support Lexique)
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def resolve_project_alias(
        cls, raw_name: str, base_dir: str = "Projects"
    ) -> Optional[str]:
        """
        Découvre dynamiquement les projets sous Projects/ et analyse leurs métadonnées
        (nom de dossier, CONTEXT.md, lexique FTS5, sprint_backlog.md, README.md, jira_config.json)
        pour faire correspondre le prompt avec pondération SSOT et pénalité de dossier fantôme.
        """
        projects_dir = Path(base_dir)
        if not projects_dir.exists():
            return None

        clean_query = cls.normalize_string(raw_name)
        query_tokens = set(cls.tokenize(raw_name))

        # 0-bis. Correspondance exacte case-insensitive directe sur le nom de dossier (priorité absolue)
        # Exclure les dossiers _DEPRECATED pour éviter les collisions
        for p in projects_dir.iterdir():
            if not p.is_dir() or p.name.startswith("."):
                continue
            if p.name.endswith("_DEPRECATED"):
                continue
            if raw_name.lower() == p.name.lower():
                return p.name

        candidates: List[Tuple[int, str]] = []

        # Interroger la base SQLite FTS5 (project_lexicon) si disponible
        fts_hits_by_project = {}
        try:
            from src.loop_mem.db import search_lexicon_terms

            db_hits = search_lexicon_terms(raw_name, limit=10)
            for hit in db_hits:
                p_name = hit.get("project_name")
                if p_name:
                    fts_hits_by_project[p_name] = fts_hits_by_project.get(p_name, 0) + 1
        except Exception as e:
            logger.debug(f"Recherche FTS5 lexique non disponible ou échouée: {e}")

        for p in projects_dir.iterdir():
            if not p.is_dir() or p.name.startswith("."):
                continue
            # Ignorer les projets archivés (suffixe _DEPRECATED)
            if p.name.endswith("_DEPRECATED"):
                continue

            score = 0
            folder_name = p.name
            norm_folder = cls.normalize_string(folder_name)
            folder_tokens = set(cls.tokenize(folder_name))

            # 1. Correspondance exacte normalisée (Priorité absolue)
            if clean_query == norm_folder:
                return folder_name

            # 2. Recouvrement des tokens du nom de dossier (CamelCase-aware)
            token_overlap = query_tokens.intersection(folder_tokens)
            if query_tokens and len(token_overlap) == len(query_tokens):
                # Tous les tokens de la requête sont dans le dossier (ex: ["boire", "frere"] dans ["boire", "frere", "reception"])
                score += 80
            elif token_overlap:
                score += len(token_overlap) * 25

            # 3. Correspondance par sous-chaîne
            if clean_query in norm_folder:
                score += 40
            elif (
                norm_folder in clean_query
                and len(norm_folder) >= 4
                and len(norm_folder) >= 0.7 * len(clean_query)
            ):
                score += 20

            # 4. Bonus Dictionnaire de Lexique FTS5 (ADR-0327)
            if folder_name in fts_hits_by_project:
                score += min(fts_hits_by_project[folder_name] * 20, 40)

            # 5. Inspection dynamique de CONTEXT.md (Lexique de domaine)
            context_file = p / "CONTEXT.md"
            if context_file.exists():
                try:
                    ctx_head = context_file.read_text(encoding="utf-8")[:1000]
                    ctx_tokens = set(cls.tokenize(ctx_head))
                    ctx_overlap = query_tokens.intersection(ctx_tokens)
                    score += len(ctx_overlap) * 15
                except Exception as e:
                    logger.debug(f"Lecture context {context_file} ignorée: {e}")

            # 6. Inspection des métadonnées (README.md, jira_config.json)
            jira_cfg = p / "jira_config.json"
            if jira_cfg.exists():
                try:
                    cfg_text = jira_cfg.read_text(encoding="utf-8")
                    if clean_query in cls.normalize_string(cfg_text):
                        score += 20
                except Exception as e:
                    logger.debug(f"Lecture jira_config {jira_cfg} ignorée: {e}")

            readme_file = p / "README.md"
            if readme_file.exists():
                try:
                    head = readme_file.read_text(encoding="utf-8")[:500]
                    head_tokens = set(cls.tokenize(head))
                    if query_tokens.intersection(head_tokens):
                        score += 15
                except Exception as e:
                    logger.debug(f"Lecture readme {readme_file} ignorée: {e}")

            # 6b. Inspection des documents ingérés (docs/00-ingested/) — comble
            # l'angle mort de désambiguïsation entre sous-projets modulaires
            # (ex: Metro_COMMERCE/FOOD/SANTE partageant le token "metro" mais
            # portant des SDKs/contenus distincts comme "OneTrust"). Chaque
            # token de requête réellement couvert par le contenu ingéré pèse
            # plus qu'une simple correspondance de nom de dossier tronqué.
            ingested_dir = p / "docs" / "00-ingested"
            if ingested_dir.exists() and query_tokens:
                try:
                    ingested_overlap: set = set()
                    for md_file in ingested_dir.glob("*.md"):
                        try:
                            head = md_file.read_text(encoding="utf-8", errors="ignore")[
                                :2000
                            ]
                        except Exception:
                            continue
                        ingested_overlap |= query_tokens.intersection(
                            cls.tokenize(head)
                        )
                        if ingested_overlap == query_tokens:
                            break  # Couverture totale déjà atteinte, inutile de continuer.
                    score += len(ingested_overlap) * 18
                except Exception as e:
                    logger.debug(f"Inspection ingested {ingested_dir} ignorée: {e}")

            # 7. Bonus de Viabilité SSOT & Pénalité Coquille Vide
            has_backlog = (p / "backlog" / "sprint_backlog.md").exists() or (
                p / "backlog" / "stories"
            ).is_dir()
            has_docs = (p / "docs").is_dir()
            has_agents = (p / "AGENTS.md").exists()

            if has_backlog:
                score += 40
            if has_agents or context_file.exists():
                score += 15

            # Pénalité sévère si dossier fantôme (aucun pilier SSOT)
            if (
                not has_backlog
                and not has_docs
                and not has_agents
                and not context_file.exists()
            ):
                score -= 50

            if score > 0:
                candidates.append((score, folder_name))

        if candidates:
            # Tri déterministe : score décroissant, puis nom de dossier croissant
            # (alphabétique) en cas d'égalité stricte — élimine toute dépendance
            # à l'ordre non garanti de Path.iterdir() sur le filesystem.
            candidates.sort(key=lambda x: (-x[0], x[1]))
            best_score, best_project = candidates[0]
            if best_score >= 30:
                return best_project

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # 2. RÉSOLUTION DYNAMIQUE DES RÉCITS & MOTS-CLÉS (Zéro Hardcoding)
    # ──────────────────────────────────────────────────────────────────────────
    @classmethod
    def resolve_story_query(cls, query: str, stories_dir: Path) -> Optional[Path]:
        """
        Interroge d'abord la base SQLite FTS5 (project_lexicon),
        puis effectue un fallback dynamique sur les fichiers Markdown sous backlog/stories/.
        """
        if not stories_dir.exists():
            return None

        # 0. Recherche ultra-rapide dans la base de données SQLite FTS5 (Indexée)
        try:
            from src.loop_mem.db import search_lexicon_terms

            project_name = stories_dir.parent.parent.name
            db_hits = search_lexicon_terms(query, project_name=project_name, limit=3)
            if db_hits:
                src_rel = db_hits[0].get("source_file")
                if src_rel:
                    candidate_file = stories_dir.parent.parent / src_rel
                    if candidate_file.exists():
                        return candidate_file
        except Exception:
            pass

        clean_query = cls.normalize_string(query)
        query_tokens = set(cls.tokenize(query))
        num_matches = re.findall(r"\d+", query)
        target_num = int(num_matches[0]) if num_matches else None

        # Préfixe alphabétique explicite de la requête (ex: "INC" dans
        # "INC-004-BE"). Deux familles d'identifiants mLoop (ex: INC-xxx pour
        # Incubation, REC-xxx pour Réception) ne doivent JAMAIS se confondre
        # uniquement parce qu'elles partagent un même suffixe numérique — bug
        # constaté en session réelle (INC-004-BE résolu à tort vers
        # REC-004-BE.md). `None` si la requête ne porte pas de préfixe alpha
        # explicite (ex: requête purement numérique "14").
        prefix_match = re.match(r"^([A-Za-z]{2,})[-_]", query.strip())
        query_prefix = prefix_match.group(1).upper() if prefix_match else None

        candidates: List[Tuple[int, Path]] = []

        for f in stories_dir.rglob("*.md"):
            try:
                score = 0
                filename_norm = cls.normalize_string(f.name)
                content = f.read_text(encoding="utf-8", errors="ignore")

                # Extraction du Frontmatter YAML et Titre H1
                frontmatter = {}
                h1_title = ""

                fm_match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
                if fm_match:
                    try:
                        frontmatter = yaml.safe_load(fm_match.group(1)) or {}
                    except Exception:
                        pass

                h1_match = re.search(r"^#\s*(.*)$", content, re.MULTILINE)
                if h1_match:
                    h1_title = h1_match.group(1).strip()

                story_id = str(frontmatter.get("id", ""))
                jira_key = str(frontmatter.get("jira_key", ""))
                title_text = str(frontmatter.get("title", "")) or h1_title
                tags = [str(t) for t in frontmatter.get("tags", [])]

                # 1. Correspondance exacte sur ID logique ou Clé Jira
                if clean_query in cls.normalize_string(
                    story_id
                ) or clean_query in cls.normalize_string(jira_key):
                    score += 100

                # 2. Correspondance numérique stricte (ex: "14" -> REC-014 ou COUVBOIRE-975)
                # Si la requête porte un préfixe alphabétique explicite (ex: "INC"
                # dans "INC-004-BE"), ce préfixe DOIT être retrouvé dans l'ID ou le
                # nom de fichier du candidat pour que le bonus numérique s'applique
                # — sinon deux familles d'IDs distinctes partageant un même suffixe
                # numérique (INC-004 vs REC-004) se confondraient à tort.
                if target_num is not None:
                    prefix_ok = True
                    if query_prefix is not None:
                        candidate_prefixes = {
                            m.group(0).upper()
                            for m in re.finditer(
                                r"[A-Za-z]{2,}", f"{story_id} {f.name}"
                            )
                        }
                        prefix_ok = query_prefix in candidate_prefixes

                    if prefix_ok:
                        # Vérifier si le numéro apparaît dans le nom de fichier ou l'ID
                        num_in_id = re.findall(r"\d+", story_id)
                        num_in_jira = re.findall(r"\d+", jira_key)
                        num_in_file = re.findall(r"\d+", f.name)
                        all_nums = [
                            int(n) for n in (num_in_id + num_in_jira + num_in_file)
                        ]
                        if target_num in all_nums:
                            score += 80

                # 3. Correspondance sémantique sur le Titre Métier & H1
                title_tokens = set(cls.tokenize(title_text))
                title_overlap = query_tokens.intersection(title_tokens)
                score += len(title_overlap) * 25

                # 4. Correspondance sur les Tags et Mots-clés Frontmatter
                tag_tokens = set()
                for tag in tags:
                    tag_tokens.update(cls.tokenize(tag))
                tag_overlap = query_tokens.intersection(tag_tokens)
                score += len(tag_overlap) * 20

                # 5. Recherche textuelle dans la Description
                desc_match = re.search(
                    r"## Description(.*?)(?:---|\Z)", content, re.DOTALL
                )
                if desc_match:
                    desc_tokens = set(cls.tokenize(desc_match.group(1)))
                    desc_overlap = query_tokens.intersection(desc_tokens)
                    score += len(desc_overlap) * 10

                if score > 0:
                    candidates.append((score, f))

            except Exception:
                continue

        if candidates:
            # Trier par score décroissant
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_file = candidates[0]
            if best_score >= 20:
                return best_file

        return None
