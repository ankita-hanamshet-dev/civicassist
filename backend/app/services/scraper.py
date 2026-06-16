"""
Web Scraping Service
Scrapes gub.uy/tramites for pages related to Residencia and Cédula.
"""
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger

from app.core.config import get_settings
from app.services.ingestion import detect_category, CATEGORY_KEYWORDS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

SEED_URLS: List[str] = []  # populated from settings.scraping.base_urls at runtime


def _is_relevant(text: str, url: str, keywords: List[str]) -> bool:
    combined = (text + " " + url).lower()
    return any(kw.lower() in combined for kw in keywords)


def _clean_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return re.sub(r"\n{3,}", "\n\n", soup.get_text(separator="\n")).strip()


def _page_title(soup: BeautifulSoup, url: str) -> str:
    tag = soup.find("h1") or soup.find("title")
    if tag:
        return tag.get_text(strip=True)
    return urlparse(url).path.split("/")[-1].replace("-", " ").title()


def _url_to_filename(url: str) -> str:
    path = urlparse(url).path.strip("/").replace("/", "_")
    return re.sub(r"[^a-zA-Z0-9_\-]", "", path)[:80]


def _write_markdown(
    title: str,
    text: str,
    url: str,
    category: str,
    subcategory: str,
    md_dir: Path,
) -> Optional[Dict]:
    date_str = datetime.now().strftime("%Y-%m-%d")
    fname = f"web_{category}_{_url_to_filename(url)}.md"
    fpath = md_dir / fname

    content = f"""---
title: "{title}"
category: "{category}"
subcategory: "{subcategory}"
source: "{url}"
index_creation_date: "{date_str}"
---

# {title}

## Información General

**Categoría:** {category.title()}  
**Subcategoría:** {subcategory}  
**Fuente:** [{url}]({url})  
**Fecha de indexación:** {date_str}

---

## Contenido

{text}
"""
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "filename": fname,
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "source": url,
        "index_creation_date": date_str,
    }


def scrape_gub_uy() -> List[Dict]:
    """Scrape gub.uy and related pages, returning metadata for all saved pages."""
    settings = get_settings()
    md_dir = Path(settings.paths.markdown_output)
    md_dir.mkdir(parents=True, exist_ok=True)

    keywords = settings.scraping.target_keywords
    delay = settings.scraping.delay_seconds
    timeout = settings.scraping.timeout_seconds

    visited: set = set()
    to_visit: List[str] = list(settings.scraping.base_urls)
    metadata_list: List[Dict] = []

    session = requests.Session()
    session.headers.update(HEADERS)

    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        logger.info(f"Scraping: {url}")
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        text = _clean_text(soup)

        if _is_relevant(text, url, keywords):
            title = _page_title(soup, url)
            category, subcategory = detect_category(text)
            meta = _write_markdown(title, text, url, category, subcategory, md_dir)
            if meta:
                metadata_list.append(meta)
                logger.success(f"Saved web page: {meta['filename']}")

        # Collect internal links that look relevant
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        for a in soup.find_all("a", href=True):
            href = urljoin(base, a["href"])
            link_text = a.get_text(strip=True).lower()
            if (
                href not in visited
                and href not in to_visit
                and urlparse(href).netloc == urlparse(url).netloc
                and any(kw.lower() in (href + link_text) for kw in keywords)
                and len(to_visit) < 80  # cap crawl depth
            ):
                to_visit.append(href)

        time.sleep(delay)

    logger.info(f"Scraping complete. Saved {len(metadata_list)} pages.")
    return metadata_list
