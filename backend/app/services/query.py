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

from langdetect import detect as detect_lang
from loguru import logger

from app.core.config import get_settings
from app.services.llm import create_chat_completion, LLMNotConnectedError
from app.services.vectorstore import retrieve

NO_LLM_MESSAGE = {
    "en": "No LLM connected. Configure an LLM provider (LLM_API_KEY and LLM_API_ENDPOINT) "
          "in backend/.env, then restart the backend to enable answers.",
    "es": "No hay un LLM conectado. Configure un proveedor de LLM (LLM_API_KEY y LLM_API_ENDPOINT) "
          "en backend/.env y reinicie el backend para habilitar las respuestas.",
}

SYSTEM_PROMPT_ES = """Eres CivicAssist, un asistente legal especializado en leyes y tramites de Uruguay, especificamente en:
- **Residencia** (permanente, temporaria, refugio, prorrogas, cambios de categoria)
- **Cedula de Identidad** (uruguayos y extranjeros, renovacion, duplicados, primera vez)

DEBES responder SIEMPRE en espanol, independientemente del idioma de la pregunta.
Basa tus respuestas UNICAMENTE en el contexto proporcionado.
Si la informacion no esta en el contexto, indicalo claramente y sugiere consultar con las autoridades uruguayas competentes (DNIC, Migraciones, etc.).
Se preciso, claro y empatico. Cuando corresponda, menciona los organismos responsables y los pasos a seguir.
NO inventes informacion legal. Si hay dudas, recomienda consultar a un profesional o al organismo oficial."""

SYSTEM_PROMPT_EN = """You are CivicAssist, a legal assistant specializing in Uruguayan laws and procedures, specifically:
- **Residency** (permanent, temporary, refugee status, extensions, category changes)
- **Identity Card / Cedula** (for Uruguayans and foreigners, renewal, duplicates, first-time)

You MUST always respond in English, regardless of the language of the question OR the language of the provided context.
The context documents may be written in Spanish — that is expected. Extract the relevant information from them and present it in English.
Base your answers ONLY on the provided context.
If the information is not in the context, clearly say so and suggest consulting the competent Uruguayan authorities (DNIC, Migraciones, etc.).
Be precise, clear and empathetic. Where appropriate, mention the responsible agencies and steps to follow.
Do NOT invent legal information. When in doubt, recommend consulting a professional or the official agency."""


def _get_system_prompt(language: str) -> str:
    return SYSTEM_PROMPT_EN if language == "en" else SYSTEM_PROMPT_ES


CLASSIFICATION_PROMPT = """Analyze the following user question and return a JSON classification.

Question: {question}

Return ONLY a JSON object (no markdown, no explanation) in this exact format:
{{
  "category": "residencia" | "cedula" | "unknown",
  "subcategory": "<specific subcategory name or null>",
  "language": "es" | "en",
  "keywords": ["keyword1", "keyword2"]
}}

Available categories:
- residencia: Residencia Permanente, Residencia Temporaria, Residencia Legal, Refugio, Prorroga de Residencia, Cambio de Categoria
- cedula: Cedula de Identidad para Uruguayos, Cedula de Identidad para Extranjeros, Renovacion de Cedula, Primera vez, Duplicado
"""


def _call_llm_json(prompt: str) -> Optional[Dict]:
    settings = get_settings()
    try:
        text = create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=settings.llm.temperature,
            model=settings.llm.model_name,
        )
        text = text.strip()
        text = re.sub(r"^```json\s*|^```\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Classification call failed: {e}")
        return None


def classify_query(question: str) -> Dict:
    """Use the configured LLM to classify the query into category/subcategory."""
    prompt = CLASSIFICATION_PROMPT.format(question=question)
    result = _call_llm_json(prompt)
    if not result:
        q = question.lower()
        category = "unknown"
        if any(w in q for w in ["residencia", "residency", "migraciones", "radicacion"]):
            category = "residencia"
        elif any(w in q for w in ["cedula", "identidad", "dni", "dnic", "documento"]):
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
        return "No relevant context found in the knowledge base."

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
                f"--- [Source {i}: {title} | {src}] ---\n{chunk['text']}"
            )
    return "\n\n".join(parts)


def answer_question(
    question: str,
    conversation_history: Optional[List[Dict]] = None,
    language: Optional[str] = None,
) -> Dict:
    """
    Full pipeline: classify -> retrieve -> generate.
    language param (from UI) takes precedence over auto-detection.
    Returns dict with keys: answer, category, subcategory, language, sources.
    """
    settings = get_settings()

    # 1. Classify
    classification = classify_query(question)
    category = classification.get("category")
    subcategory = classification.get("subcategory")
    detected_lang = classification.get("language", "es")
    # Explicit UI language overrides auto-detection
    resolved_language = language if language in ("es", "en") else detected_lang
    logger.info(f"Classified: category={category}, subcategory={subcategory}, lang={resolved_language}")

    # 2. Retrieve chunks
    cat_filter = category if category != "unknown" else None
    chunks = retrieve(
        query=question,
        category_filter=cat_filter,
        subcategory_filter=subcategory,
        n_results=8,
    )

    if len(chunks) < 3 and cat_filter:
        chunks = retrieve(query=question, n_results=8)

    context = build_context(chunks)
    sources = list({
        c["metadata"].get("source", "")
        for c in chunks
        if c["metadata"].get("source")
    })

    # 3. Generate answer
    messages: List[Dict] = []

    if conversation_history:
        messages.extend(conversation_history[-6:])

    lang_reminder = (
        "IMPORTANT: Your response MUST be in English."
        if resolved_language == "en"
        else "IMPORTANTE: Tu respuesta DEBE estar en español."
    )
    user_message = (
        f"RELEVANT LEGAL CONTEXT:\n{context}\n\n"
        f"---\n\nUSER QUESTION:\n{question}\n\n"
        f"{lang_reminder}"
    )
    messages.append({"role": "user", "content": user_message})

    system_prompt = _get_system_prompt(resolved_language)

    try:
        answer = create_chat_completion(
            messages=messages,
            max_tokens=settings.llm.max_tokens,
            temperature=settings.llm.temperature,
            model=settings.llm.model_name,
            system_prompt=system_prompt,
        )
    except LLMNotConnectedError as e:
        logger.warning(f"LLM not connected: {e}")
        answer = NO_LLM_MESSAGE["en"] if resolved_language == "en" else NO_LLM_MESSAGE["es"]
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = (
            "Sorry, an error occurred while processing your query. Please try again."
            if resolved_language == "en"
            else "Lo siento, ocurrio un error al procesar su consulta. Por favor, intente nuevamente."
        )

    return {
        "answer": answer,
        "category": category,
        "subcategory": subcategory,
        "language": resolved_language,
        "sources": sources,
        "chunks_used": len(chunks),
    }
