"""
PDF Ingestion Service
Reads PDFs from the raw_pdfs directory and converts them to categorised Markdown files.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF
from loguru import logger

from app.core.config import get_settings

CATEGORY_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "residencia": {
        "Residencia Permanente": ["residencia permanente", "permanent residency", "radicación definitiva"],
        "Residencia Temporaria": ["residencia temporaria", "temporary residency", "temporal", "temporaria"],
        "Refugio": ["refugio", "refugee", "asilo", "asylum"],
        "Prórroga de Residencia": ["prórroga", "renovación de residencia", "extension of residency"],
        "Cambio de Categoría": ["cambio de categoría", "category change", "cambio de estatus"],
        "Residencia Legal": ["residencia legal", "legal residency", "migraciones", "ley de migración"],
    },
    "cedula": {
        "Cédula de Identidad para Uruguayos": ["cédula de identidad", "cedula de identidad", "dnic", "documento nacional"],
        "Cédula de Identidad para Extranjeros": ["cédula para extranjeros", "extranjero", "foreigner id", "cedula extranjero"],
        "Renovación de Cédula": ["renovación", "renewal", "vencida", "expired"],
        "Primera vez": ["primera vez", "first time", "nueva cédula", "primera emisión"],
        "Duplicado": ["duplicado", "duplicate", "extravío", "lost"],
    },
}


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract plain text from a PDF file using PyMuPDF."""
    try:
        doc = fitz.open(str(pdf_path))
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n\n".join(pages)
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def detect_category(text: str) -> Tuple[str, str]:
    """Return (category, subcategory) based on keyword matching."""
    text_lower = text.lower()
    best_cat = "residencia"
    best_sub = "Residencia Legal"
    best_score = 0

    for cat, subcats in CATEGORY_KEYWORDS.items():
        for sub, keywords in subcats.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_cat = cat
                best_sub = sub

    return best_cat, best_sub


def text_to_markdown(title: str, text: str, category: str, subcategory: str, source: str) -> str:
    """Wrap extracted text in structured Markdown."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    # Clean up multiple blank lines
    clean = re.sub(r"\n{3,}", "\n\n", text).strip()

    return f"""---
title: "{title}"
category: "{category}"
subcategory: "{subcategory}"
source: "{source}"
index_creation_date: "{date_str}"
---

# {title}

## Información General

**Categoría:** {category.title()}  
**Subcategoría:** {subcategory}  
**Fuente:** {source}  
**Fecha de indexación:** {date_str}

---

## Contenido

{clean}
"""


def ingest_pdfs() -> List[Dict]:
    """Main entry-point: ingest all PDFs and write Markdown files. Returns metadata list."""
    settings = get_settings()
    pdf_dir = Path(settings.paths.raw_pdfs)
    md_dir = Path(settings.paths.markdown_output)
    md_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_dir.exists():
        logger.warning(f"PDF directory does not exist: {pdf_dir}")
        return []

    metadata_list: List[Dict] = []
    pdf_files = list(pdf_dir.glob("**/*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF(s) in {pdf_dir}")

    for pdf_path in pdf_files:
        logger.info(f"Processing: {pdf_path.name}")
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            logger.warning(f"No text extracted from {pdf_path.name}, skipping.")
            continue

        category, subcategory = detect_category(text)
        title = pdf_path.stem.replace("_", " ").replace("-", " ").title()
        source = f"PDF: {pdf_path.name}"

        md_filename = f"{category}_{pdf_path.stem}.md"
        md_path = md_dir / md_filename
        md_content = text_to_markdown(title, text, category, subcategory, source)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        meta = {
            "filename": md_filename,
            "title": title,
            "category": category,
            "subcategory": subcategory,
            "source": source,
            "index_creation_date": datetime.now().strftime("%Y-%m-%d"),
        }
        metadata_list.append(meta)
        logger.success(f"Saved: {md_path}")

    return metadata_list
