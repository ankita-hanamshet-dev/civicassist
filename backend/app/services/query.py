"""
Query Service
1. Classifies the user query against the INDEX to find category/subcategory.
2. Retrieves relevant chunks from ChromaDB.
3. Calls Claude to generate a grounded bilingual response.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import anthropic
from langdetect import detect as detect_lang
from loguru import logger

from app.core.config import get_settings
from app.services.vectorstore import retrieve

SYSTEM_PROMPT = """Eres CivicAssist, un asistente legal especializado en leyes y trámites de Uruguay, específicamente en:
- **Residencia** (permanente, temporaria, refugio, prórrogas, cambios de categoría)
- **Cédula de Identidad** (uruguayos y extranjeros, renovación, duplicados, primera vez)

Responde SIEMPRE en el mismo idioma que el usuario (español o inglés).
Basa tus respuestas ÚNICAMENTE en el contexto proporcionado.
Si la información no está en el contexto, indícalo claramente y sugiere consultar con las autoridades uruguayas competentes (DNIC, Migraciones, etc.).
Sé preciso, claro y empático. Cuando corresponda, menciona los organismos responsables y los pasos a seguir.
NO inventes información legal. Si hay dudas, recomienda consultar a un profesional o al organismo oficial."""

CLASSIFICATION_PROMPT = """Analiza la siguiente pregunta del usuario y devuelve un JSON con la clasificación.

Pregunta: {question}

Devuelve SOLO un JSON (sin markdown, sin explicaciones) con este formato exacto:
{{
  "category": "residencia" | "cedula" | "unknown",
  "subcategory": "<nombre de subcategoría específica o null>",
  "language": "es" | "en",
  "keywords": ["keyword1", "keyword2"]
}}

Categorías disponibles:
- residencia: Residencia Permanente, Residencia Temporaria, Residencia Legal, Refugio, Prórroga de Residencia, Cambio de Categoría
- cedula: Cédula de Identidad para Uruguayos, Cédula de Identidad para Extranjeros, Renovación de Cédula, Primera vez, Duplicado
"""


def _call_claude_json(prompt: str) -> Optional[Dict]:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic.api_key)
    try:
        msg = client.messages.create(
            model=settings.anthropic.model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        # Strip markdown fences if present
        text = re.sub(r"^```json\s*|^```\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Classification call failed: {e}")
        return None


def classify_query(question: str) -> Dict:
    """Use Claude to classify the query into category/subcategory."""
    prompt = CLASSIFICATION_PROMPT.format(question=question)
    result = _call_claude_json(prompt)
    if not result:
        # Fallback: simple keyword detection
        q = question.lower()
        category = "unknown"
        if any(w in q for w in ["residencia", "residency", "migraciones", "radicación"]):
            category = "residencia"
        elif any(w in q for w in ["cédula", "cedula", "identidad", "dni", "dnic", "documento"]):
            category = "cedula"
        try:
            lang = detect_lang(question)
        except Exception:
            lang = "es"
        return {"category": category, "subcategory": None, "language": lang, "keywords": []}
    return result


def build_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks into a readable context block."""
    if not chunks:
        return "No se encontró contexto relevante en la base de conocimiento."

    parts = []
    seen_sources = set()
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        src = meta.get("source", "")
        title = meta.get("title", "")
        key = f"{meta.get('filename', '')}_{i}"
        if key not in seen_sources:
            seen_sources.add(key)
            parts.append(
                f"--- [Fuente {i}: {title} | {src}] ---\n{chunk['text']}"
            )
    return "\n\n".join(parts)


def answer_question(
    question: str,
    conversation_history: Optional[List[Dict]] = None,
) -> Dict:
    """
    Full pipeline: classify → retrieve → generate.
    Returns dict with keys: answer, category, subcategory, language, sources.
    """
    settings = get_settings()

    # 1. Classify
    classification = classify_query(question)
    category = classification.get("category")
    subcategory = classification.get("subcategory")
    language = classification.get("language", "es")
    logger.info(f"Classified: category={category}, subcategory={subcategory}, lang={language}")

    # 2. Retrieve chunks
    cat_filter = category if category != "unknown" else None
    chunks = retrieve(
        query=question,
        category_filter=cat_filter,
        subcategory_filter=subcategory,
        n_results=8,
    )

    # If filtered results are thin, broaden search
    if len(chunks) < 3 and cat_filter:
        chunks = retrieve(query=question, n_results=8)

    context = build_context(chunks)
    sources = list({
        c["metadata"].get("source", "")
        for c in chunks
        if c["metadata"].get("source")
    })

    # 3. Generate answer
    client = anthropic.Anthropic(api_key=settings.anthropic.api_key)
    messages: List[Dict] = []

    if conversation_history:
        messages.extend(conversation_history[-6:])  # last 3 turns

    user_message = (
        f"CONTEXTO LEGAL RELEVANTE:\n{context}\n\n"
        f"---\n\nPREGUNTA DEL USUARIO:\n{question}"
    )
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model=settings.anthropic.model,
            max_tokens=settings.anthropic.max_tokens,
            temperature=settings.anthropic.temperature,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        answer = response.content[0].text
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = (
            "Lo siento, ocurrió un error al procesar su consulta. "
            "Por favor, intente nuevamente."
        )

    return {
        "answer": answer,
        "category": category,
        "subcategory": subcategory,
        "language": language,
        "sources": sources,
        "chunks_used": len(chunks),
    }
