#!/usr/bin/env python3
"""
mLoop Lite Crawler — Extraction & Normalisation Web vers Markdown
Fait partie de mLoop Lite.
"""
import sys
import re
import urllib.parse
from pathlib import Path

def sanitize_filename(name: str) -> str:
    name = re.sub(r'https?://', '', name)
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    return name[:60] or "page_web"

def crawl_url(url: str, dest_dir: Path = Path("docs")) -> Path:
    try:
        import httpx
        from bs4 import BeautifulSoup
        from markdownify import markdownify as md
    except ImportError:
        print("❌ Modules manquants pour le crawler. Installez-les via : pip install httpx beautifulsoup4 markdownify")
        sys.exit(1)
        
    print(f"🌐 Téléchargement et analyse de : {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        print(f"❌ Échec du téléchargement HTTP : {e}")
        sys.exit(1)
        
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Nettoyage des balises parasites
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "form"]):
        tag.decompose()
        
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    
    # 2. Extraction du corps principal
    main_content = soup.find("main") or soup.find("article") or soup.find("body") or soup
    markdown_text = md(str(main_content), heading_style="ATX").strip()
    
    # Nettoyage des sauts de ligne excessifs
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
    
    output_content = f"""# {title}

> **Source Web** : [{url}]({url})  
> **Date d'ingestion** : {Path.cwd().name}  

---

{markdown_text}
"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_file = dest_dir / f"web_{sanitize_filename(url)}.md"
    out_file.write_text(output_content, encoding="utf-8")
    print(f"✅ Page web convertie avec succès en Markdown : {out_file}")
    return out_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python crawler.py <URL> [dossier_destination]")
        sys.exit(1)
    target_url = sys.argv[1]
    target_dest = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("docs")
    crawl_url(target_url, target_dest)
