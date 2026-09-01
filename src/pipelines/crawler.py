import asyncio
import hashlib
import json
import os
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import httpx
except ImportError:
    httpx = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from markdownify import markdownify as md
except ImportError:
    md = None

from src.state import LoopState, ProjectLayout
from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("crawler")

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "ref_src",
    "fbclid",
    "gclid",
    "dclid",
    "msclkid",
    "mc_eid",
    "_hsenc",
    "_hsmi",
    "session_id",
    "sessionId",
}


def strip_tracking_params(raw_url: str) -> str:
    """Supprime les paramètres de tracking connus d'une URL."""
    try:
        parsed = urllib.parse.urlparse(raw_url)
        query_dict = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        filtered = {k: v for k, v in query_dict.items() if k not in TRACKING_PARAMS and not k.startswith("utm_")}
        new_query = urllib.parse.urlencode(filtered, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=new_query, fragment=""))
    except Exception:
        return raw_url


def normalize_url(raw_url: str, base_url: Optional[str] = None, ignore_query: bool = False) -> Optional[str]:
    """Normalise et dédoublonne une URL."""
    try:
        if base_url:
            resolved = urllib.parse.urljoin(base_url, raw_url)
        else:
            resolved = raw_url

        parsed = urllib.parse.urlparse(resolved)
        if not parsed.scheme or not parsed.netloc:
            return None

        if ignore_query:
            clean_url = urllib.parse.urlunparse(parsed._replace(query="", fragment=""))
        else:
            clean_url = strip_tracking_params(resolved)

        if clean_url.endswith("/") and len(clean_url) > len(f"{parsed.scheme}://{parsed.netloc}/"):
            clean_url = clean_url[:-1]
        return clean_url
    except Exception:
        return None


def is_path_allowed(
    url: str,
    include_paths: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
) -> bool:
    """Vérifie si le chemin d'une URL respecte les motifs include et exclude."""
    try:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or "/"

        if exclude_paths:
            for pattern in exclude_paths:
                if re.search(pattern, path):
                    return False

        if include_paths:
            matched = any(re.search(pattern, path) for pattern in include_paths)
            if not matched:
                return False

        return True
    except Exception:
        return False


def is_domain_allowed(target_url: str, base_url: str, allow_subdomains: bool = False) -> bool:
    """Vérifie l'appartenance au domaine principal ou aux sous-domaines."""
    try:
        target = urllib.parse.urlparse(target_url).netloc.lower()
        base = urllib.parse.urlparse(base_url).netloc.lower()

        if target == base:
            return True

        if allow_subdomains:
            target_parts = target.split(".")
            base_parts = base.split(".")
            if len(target_parts) >= 2 and len(base_parts) >= 2:
                target_root = ".".join(target_parts[-2:])
                base_root = ".".join(base_parts[-2:])
                return target_root == base_root

        return False
    except Exception:
        return False


def is_external_link_allowed(target_url: str, base_url: str, allow_external: bool = False) -> bool:
    """Vérifie les liens externes 1-hop en ignorant automatiquement les homepages racines."""
    if not allow_external:
        return False
    try:
        target = urllib.parse.urlparse(target_url)
        base = urllib.parse.urlparse(base_url)
        if target.netloc.lower() == base.netloc.lower():
            return False
        # Ignore external root homepages (ex: https://example.com/ or https://example.com)
        if target.path in ("", "/"):
            return False
        return True
    except Exception:
        return False


class WebCrawlerAgent:
    """
    Système 1 : Smart Web Crawler Agent Asynchrone (Smart Discovery & Traversal - ADR-0336).
    Détecte automatiquement llms.txt, applique un cache déterministe avec TTL (max_age),
    filtre les chemins par regex, normalise les paramètres de tracking et supporte l'extraction structurée LLM.
    """

    def __init__(
        self,
        max_concurrency: int = 5,
        max_age: Optional[int] = None,
        max_depth: int = 0,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        allow_subdomains: bool = False,
        allow_external_links: bool = False,
        llms_txt: bool = True,
        ignore_query_parameters: bool = False,
        json_schema_path: Optional[str] = None,
    ):
        self.name = "Web Crawler"
        self.max_concurrency = max_concurrency
        self.max_age = max_age
        self.max_depth = max_depth
        self.include_paths = include_paths
        self.exclude_paths = exclude_paths
        self.allow_subdomains = allow_subdomains
        self.allow_external_links = allow_external_links
        self.llms_txt = llms_txt
        self.ignore_query_parameters = ignore_query_parameters
        self.json_schema_path = json_schema_path

    def _html_to_clean_markdown(self, html_content: str, url: str = None) -> str:
        """Convertit le HTML brut en Markdown lisible sans scripts ni styles parasites."""
        if BeautifulSoup is None:
            text = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            return re.sub(r'\s+', ' ', text).strip()

        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in ["script", "style", "noscript", "iframe", "svg", "header", "footer", "nav"]:
            for el in soup.find_all(tag):
                el.decompose()

        if md:
            markdown_text = md(str(soup), heading_style="ATX", bullets="-", strip=["img"])
        else:
            markdown_text = soup.get_text(separator="\n\n")

        return re.sub(r'\n{3,}', '\n\n', markdown_text).strip()

    def _extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Extrait les liens valides d'une page HTML en respectant les filtres de domaine et de chemin."""
        if BeautifulSoup is None:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        found_links = []

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue

            normalized = normalize_url(href, base_url, ignore_query=self.ignore_query_parameters)
            if not normalized:
                continue

            is_domain = is_domain_allowed(normalized, base_url, self.allow_subdomains)
            is_ext = is_external_link_allowed(normalized, base_url, self.allow_external_links)

            if not is_domain and not is_ext:
                continue

            if not is_path_allowed(normalized, self.include_paths, self.exclude_paths):
                continue

            found_links.append(normalized)

        return list(set(found_links))

    async def _fetch_llms_txt(
        self,
        client: "httpx.AsyncClient",
        url: str,
        docs_cache_dir: Path,
        headers: Dict[str, str],
    ) -> Optional[Path]:
        """Sonde et récupère llms.txt ou llms-full.txt si disponible sur le domaine racine."""
        try:
            parsed = urllib.parse.urlparse(url)
            origin = f"{parsed.scheme}://{parsed.netloc}"

            candidates = [
                (f"{origin}/llms-full.txt", "llms-full.txt"),
                (f"{origin}/llms.txt", "llms.txt"),
                (f"{origin}/.well-known/llms.txt", "well-known-llms.txt"),
            ]

            for cand_url, cand_type in candidates:
                try:
                    res = await client.get(cand_url, headers=headers, timeout=5.0, follow_redirects=True)
                    if res.status_code == 200:
                        ct = res.headers.get("content-type", "").lower()
                        text = res.text
                        if ("text" in ct or "markdown" in ct or text.startswith("#") or "http" in text) and len(text.strip()) > 30:
                            url_hash = hashlib.sha256(cand_url.encode("utf-8")).hexdigest()[:12]
                            domain = parsed.netloc.replace(".", "_")
                            out_file = docs_cache_dir / f"crawl_{domain}_{url_hash}.md"
                            out_file.write_text(f"sha256: {url_hash}\nsource: {cand_url}\ntype: {cand_type}\n\n{text}", encoding="utf-8")
                            ZeroFluffConsole.success(f"[LLMS-TXT] Fast-Path découvert : {cand_type} ({len(text)} octets) sauvegardé sous {out_file.name}")
                            return out_file
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Vérification llms.txt ignorée pour {url}: {e}")
        return None

    def _check_max_age_cache(self, output_file: Path) -> bool:
        """Vérifie si le fichier de cache est encore valide selon le TTL max_age."""
        if not self.max_age or not output_file.exists():
            return False
        try:
            mtime = output_file.stat().st_mtime
            age = time.time() - mtime
            if age <= self.max_age:
                ZeroFluffConsole.info(f"[CACHE] Hit valide pour {output_file.name} (âge: {int(age)}s <= TTL: {self.max_age}s)")
                return True
        except Exception:
            pass
        return False

    async def _crawl_single_url(
        self,
        client: "httpx.AsyncClient",
        semaphore: asyncio.Semaphore,
        url: str,
        project_path: Path,
        state: LoopState,
    ) -> Tuple[Optional[Path], List[str]]:
        """Télécharge et convertit une URL unique sous contrôle de sémaphore."""
        url_clean = normalize_url(url.rstrip(".,;:\"'`)"), ignore_query=self.ignore_query_parameters) or url
        is_local = "localhost" in url_clean or state.project_name.lower() in url_clean
        docs_cache_dir = project_path / ProjectLayout.MEMORY / "docs_cache" if is_local else Path(ProjectLayout.MEMORY) / "crawler" / "cache"
        docs_cache_dir.mkdir(parents=True, exist_ok=True)

        url_hash = hashlib.sha256(url_clean.encode("utf-8")).hexdigest()[:12]
        domain = urllib.parse.urlparse(url_clean).netloc.replace(".", "_")
        output_file = docs_cache_dir / f"crawl_{domain}_{url_hash}.md"

        # 1. Vérification du cache TTL
        if self._check_max_age_cache(output_file):
            return output_file, []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
            "Accept": "text/markdown, text/x-markdown, text/plain;q=0.9, text/html;q=0.8",
        }

        # 2. Fast-Path LLMs.txt
        if self.llms_txt:
            llms_file = await self._fetch_llms_txt(client, url_clean, docs_cache_dir, headers)
            if llms_file and self.max_depth <= 0:
                return llms_file, []

        # Conversion automatique des URLs GitHub vers raw README
        fetch_url = url_clean
        if "github.com" in url_clean and "github.blog" not in url_clean and "/tree/" not in url_clean and "/blob/" not in url_clean:
            parts = url_clean.rstrip("/").split("/")
            if len(parts) == 5:
                user = parts[3]
                repo = parts[4]
                fetch_url = f"https://raw.githubusercontent.com/{user}/{repo}/main/README.md"

        discovered_links: List[str] = []

        async with semaphore:
            try:
                ZeroFluffConsole.info(f"Crawling {url_clean}...")
                response = await client.get(fetch_url, headers=headers, timeout=12.0, follow_redirects=True)

                # Fallback master branch sur GitHub
                if response.status_code == 404 and "main/README.md" in fetch_url:
                    fetch_url = fetch_url.replace("main/README.md", "master/README.md")
                    response = await client.get(fetch_url, headers=headers, timeout=12.0, follow_redirects=True)

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "").lower()
                    is_doc_ext = any(fetch_url.lower().endswith(ext) for ext in [".pdf", ".docx", ".xlsx", ".pptx", ".zip"])
                    is_doc_ct = any(ct in content_type for ct in ["application/pdf", "application/vnd", "application/msword", "application/zip"])

                    if is_doc_ext or is_doc_ct:
                        try:
                            from markitdown import MarkItDown
                            md_converter = MarkItDown()
                            temp_bin = docs_cache_dir / f"temp_{url_hash}"
                            temp_bin.write_bytes(response.content)
                            res = md_converter.convert(str(temp_bin))
                            content_md = res.text_content
                            if temp_bin.exists():
                                temp_bin.unlink()
                            ZeroFluffConsole.info(f"Conversion par MarkItDown appliquée pour {url_clean}")
                        except Exception as ex:
                            logger.warning(f"Fallback MarkItDown vers HTML/Texte basique pour {url_clean}: {ex}")
                            content_md = self._html_to_clean_markdown(response.text, url_clean)

                    elif fetch_url.endswith(".md") or "raw.githubusercontent" in fetch_url or "text/plain" in content_type or "text/markdown" in content_type:
                        content_md = response.text

                    else:
                        # RÈGLE 3 : Détection Markdown Twin URL
                        is_markdown_twin_used = False
                        if not fetch_url.endswith(".md"):
                            try:
                                md_twin_url = f"{fetch_url.rstrip('/')}.md"
                                response_twin = await client.get(md_twin_url, headers=headers, timeout=5.0, follow_redirects=True)
                                twin_ct = response_twin.headers.get("content-type", "").lower()
                                if response_twin.status_code == 200 and ("text/markdown" in twin_ct or "text/plain" in twin_ct or response_twin.text.startswith("#")):
                                    content_md = response_twin.text
                                    is_markdown_twin_used = True
                                    ZeroFluffConsole.info(f"Markdown Twin auto-détecté pour {url_clean} ({md_twin_url})")
                            except Exception as e:
                                logger.debug(f"Markdown twin non disponible sur {url_clean}: {e}")

                        if not is_markdown_twin_used:
                            content_md = self._html_to_clean_markdown(response.text, url_clean)
                            if self.max_depth > 0:
                                discovered_links = self._extract_links(response.text, url_clean)

                    output_file.write_text(f"sha256: {url_hash}\nsource: {url_clean}\n\n{content_md}", encoding="utf-8")
                    ZeroFluffConsole.success(f"Sauvegarde du crawl sous {output_file.name}")
                    return output_file, discovered_links
                else:
                    ZeroFluffConsole.warning(f"Échec du crawl ({response.status_code}) pour {url_clean}")
                    return None, []
            except Exception as e:
                logger.warning(f"Erreur lors du crawl de {url_clean} : {e}")
                return None, []

    async def _execute_async(self, state: LoopState, explicit_url: Optional[str] = None) -> LoopState:
        """Exécute le crawl des URLs avec support de la découverte récursive (max_depth)."""
        if httpx is None:
            ZeroFluffConsole.warning("httpx n'est pas installé dans l'environnement Python.")
            return state

        crawler_dir = Path(ProjectLayout.MEMORY) / "crawler"
        for subdir in ["cache", "debug", "sessions", "workspace"]:
            (crawler_dir / subdir).mkdir(parents=True, exist_ok=True)

        project_path = Path("Projects") / state.project_name
        sources_text = ""

        for d in [ProjectLayout.DOCS, ProjectLayout.DIRECTIVES, ProjectLayout.REFERENCE, ProjectLayout.BACKLOG]:
            dir_path = project_path / d
            if dir_path.exists():
                for ext in ["*.md", "*.txt"]:
                    for f in dir_path.rglob(ext):
                        try:
                            sources_text += f.read_text(encoding="utf-8") + "\n"
                        except Exception as e:
                            logger.debug(f"Lecture ignorée sur {f}: {e}")

        initial_urls = list(set(re.findall(r'https?://[^\s)\]]+', sources_text)))
        if explicit_url:
            initial_urls.append(explicit_url)
        initial_urls = list(set(initial_urls))

        if not initial_urls:
            ZeroFluffConsole.step_s1(self.name, "Aucune URL externe détectée.")
            return state

        ZeroFluffConsole.info(f"Lancement du crawl asynchrone pour {len(initial_urls)} URL(s) (concurrence max: {self.max_concurrency}, profondeur: {self.max_depth})...")
        semaphore = asyncio.Semaphore(self.max_concurrency)

        try:
            client_ctx = httpx.AsyncClient(http2=True, verify=False)
        except Exception:
            client_ctx = httpx.AsyncClient(http2=False, verify=False)

        visited: Set[str] = set()
        current_queue: List[str] = initial_urls

        async with client_ctx as client:
            for current_depth in range(self.max_depth + 1):
                if not current_queue:
                    break

                to_fetch = [u for u in current_queue if u not in visited]
                for u in to_fetch:
                    visited.add(u)

                if not to_fetch:
                    break

                ZeroFluffConsole.info(f"[Depth {current_depth}] Traitement de {len(to_fetch)} URL(s)...")
                tasks = [self._crawl_single_url(client, semaphore, url, project_path, state) for url in to_fetch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                next_queue: List[str] = []
                for res in results:
                    if isinstance(res, tuple) and len(res) == 2:
                        _, discovered = res
                        for link in discovered:
                            if link not in visited:
                                next_queue.append(link)

                current_queue = list(set(next_queue))

        return state

    def execute(self, state: LoopState, explicit_url: Optional[str] = None) -> LoopState:
        """Point d'entrée synchrone compatible pour la machine à états mLoop."""
        ZeroFluffConsole.step_s1(self.name, "Démarrage du crawler Web asynchrone...")
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self._execute_async(state, explicit_url))
            else:
                return asyncio.run(self._execute_async(state, explicit_url))
        except Exception as e:
            logger.warning(f"Erreur d'exécution du crawler asynchrone: {e}")
            return state

