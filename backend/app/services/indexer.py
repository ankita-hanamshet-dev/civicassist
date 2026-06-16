"""
Index Builder
Creates and maintains the INDEX.md decision-tree file that maps
categories/subcategories to their Markdown source files.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import re
import yaml
from loguru import logger

from app.core.config import get_settings


def parse_frontmatter(md_path: Path) -> Dict:
    """Extract YAML front-matter from a Markdown file."""
    try:
        content = md_path.read_text(encoding="utf-8")
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                fm = yaml.safe_load(content[3:end])
                return fm or {}
    except Exception as e:
        logger.warning(f"Could not parse front-matter for {md_path}: {e}")
    return {}


def build_index(extra_metadata: List[Dict] = None) -> str:
    """
    Scan the markdown directory, parse all front-matter, and write INDEX.md.
    Returns the path to the written index file.
    """
    settings = get_settings()
    md_dir = Path(settings.paths.markdown_output)
    index_path = Path(settings.paths.index_file)
    md_dir.mkdir(parents=True, exist_ok=True)

    # Collect metadata from disk
    md_files = [f for f in md_dir.glob("*.md") if f.name != "INDEX.md"]
    metadata_map: Dict[str, Dict[str, List[Dict]]] = {}

    for md_file in md_files:
        fm = parse_frontmatter(md_file)
        if not fm:
            continue
        cat = fm.get("category", "uncategorized")
        sub = fm.get("subcategory", "General")
        entry = {
            "filename": md_file.name,
            "title": fm.get("title", md_file.stem),
            "category": cat,
            "subcategory": sub,
            "source": fm.get("source", ""),
            "index_creation_date": fm.get("index_creation_date", ""),
        }
        metadata_map.setdefault(cat, {}).setdefault(sub, []).append(entry)

    # Merge in extra metadata passed at runtime (from ingest / scrape)
    if extra_metadata:
        for item in extra_metadata:
            cat = item.get("category", "uncategorized")
            sub = item.get("subcategory", "General")
            # Avoid duplication
            existing = [
                e["filename"]
                for e in metadata_map.get(cat, {}).get(sub, [])
            ]
            if item.get("filename") not in existing:
                metadata_map.setdefault(cat, {}).setdefault(sub, []).append(item)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# UruguayLex — Índice de Conocimiento Legal",
        "",
        f"> Generado automáticamente el {now}",
        "",
        "---",
        "",
        "## Árbol de Decisión por Categoría",
        "",
        "Este archivo actúa como índice maestro para el sistema RAG.",
        "El motor de consultas lo usa para seleccionar los archivos Markdown relevantes",
        "según la categoría y subcategoría detectadas en la pregunta del usuario.",
        "",
        "---",
        "",
    ]

    # Build decision tree section
    for cat, subcats in sorted(metadata_map.items()):
        lines.append(f"## 📁 {cat.title()}")
        lines.append("")
        for sub, entries in sorted(subcats.items()):
            lines.append(f"### └─ {sub}")
            lines.append("")
            lines.append("| Archivo | Título | Fuente | Fecha |")
            lines.append("|---------|--------|--------|-------|")
            for e in entries:
                src = e["source"][:60] + "…" if len(e["source"]) > 60 else e["source"]
                lines.append(
                    f"| `{e['filename']}` | {e['title']} | {src} | {e['index_creation_date']} |"
                )
            lines.append("")

    # Metadata schema section
    lines += [
        "---",
        "",
        "## Esquema de Metadatos",
        "",
        "Cada archivo Markdown en este corpus tiene los siguientes metadatos en su encabezado YAML:",
        "",
        "| Campo | Descripción |",
        "|-------|-------------|",
        "| `title` | Título descriptivo del documento |",
        "| `category` | Categoría principal: `residencia` o `cedula` |",
        "| `subcategory` | Subcategoría específica del tema |",
        "| `source` | URL o nombre de archivo PDF de origen |",
        "| `index_creation_date` | Fecha en que se generó el archivo Markdown |",
        "",
        "---",
        "",
        "## Estadísticas del Corpus",
        "",
    ]

    total = sum(len(e) for sub in metadata_map.values() for e in sub.values())
    lines.append(f"- **Total de documentos indexados:** {total}")
    lines.append(f"- **Categorías:** {len(metadata_map)}")
    sub_total = sum(len(sub) for sub in metadata_map.values())
    lines.append(f"- **Subcategorías:** {sub_total}")
    lines.append(f"- **Última actualización:** {now}")
    lines.append("")

    index_content = "\n".join(lines)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index_content, encoding="utf-8")
    logger.success(f"INDEX.md written to {index_path} ({total} documents)")
    return str(index_path)
