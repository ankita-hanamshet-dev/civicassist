"""
Generic LLM service for chat and embeddings.
Supports on-prem/cloud Ollama, OpenAI, and Claude-compatible endpoints.
"""
from typing import Any, Dict, List, Optional, Sequence, Union

import httpx
from loguru import logger

from app.core.config import get_settings


def _build_url(base: str, path: str) -> str:
    if not path:
        raise ValueError("LLM endpoint path is not configured.")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not base:
        return path
    return base.rstrip("/") + "/" + path.lstrip("/")


def _provider_name() -> str:
    settings = get_settings()
    endpoint = (settings.llm.api_endpoint or settings.llm.chat_endpoint or "").lower()
    if "openai.com" in endpoint:
        return "openai"
    if "ollama" in endpoint:
        return "ollama"
    if "anthropic" in endpoint or "claude" in endpoint:
        return "anthropic"
    return "generic"


def _build_headers() -> Dict[str, str]:
    settings = get_settings()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if settings.llm.api_key:
        provider = _provider_name()
        if provider == "anthropic":
            headers["x-api-key"] = settings.llm.api_key
        else:
            headers["Authorization"] = f"Bearer {settings.llm.api_key}"
    return headers


def _parse_chat_response(data: Any) -> str:
    if isinstance(data, dict):
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message") or first
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                    if isinstance(content, dict):
                        return content.get("content", str(content))
                if isinstance(message, str):
                    return message
        if "response" in data and isinstance(data["response"], str):
            return data["response"]
        if "completion" in data and isinstance(data["completion"], str):
            return data["completion"]
        if "text" in data and isinstance(data["text"], str):
            return data["text"]
    if isinstance(data, str):
        return data
    return str(data)


def _parse_embedding_response(data: Any) -> List[float]:
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list) and data["data"]:
            item = data["data"][0]
            if isinstance(item, dict):
                if "embedding" in item and isinstance(item["embedding"], list):
                    return item["embedding"]
                if "embeddings" in item and isinstance(item["embeddings"], list):
                    return item["embeddings"][0]
        if "embeddings" in data and isinstance(data["embeddings"], list) and data["embeddings"]:
            if isinstance(data["embeddings"][0], list):
                return data["embeddings"][0]
        if "embedding" in data and isinstance(data["embedding"], list):
            return data["embedding"]
    raise ValueError(f"Unable to parse embedding response: {data}")


def create_chat_completion(
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> str:
    settings = get_settings()
    provider = _provider_name()
    url = _build_url(settings.llm.api_endpoint, settings.llm.chat_endpoint)
    payload: Dict[str, Any] = {
        "model": model or settings.llm.model_name,
        "messages": messages,
    }
    if temperature is not None:
        payload["temperature"] = temperature

    if provider == "anthropic":
        if max_tokens is not None:
            payload["max_tokens_to_sample"] = max_tokens
        if system_prompt is not None:
            payload["system"] = system_prompt
    else:
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if system_prompt is not None:
            payload["messages"] = [{"role": "system", "content": system_prompt}] + messages

    try:
        response = httpx.post(url, headers=_build_headers(), json=payload, timeout=30)
        response.raise_for_status()
        return _parse_chat_response(response.json())
    except Exception as e:
        logger.error(f"LLM chat request failed: {e}")
        raise


def create_embedding(input_texts: Union[str, Sequence[str]], model: Optional[str] = None) -> List[List[float]]:
    settings = get_settings()
    if not settings.llm.embedding_endpoint:
        raise ValueError("LLM embedding endpoint is not configured.")

    url = _build_url(settings.llm.api_endpoint, settings.llm.embedding_endpoint)
    payload: Dict[str, Any] = {
        "model": model or settings.llm.model_name,
        "input": input_texts,
    }

    try:
        response = httpx.post(url, headers=_build_headers(), json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        embeddings = result.get("data")
        if isinstance(embeddings, list):
            parsed = []
            for item in embeddings:
                if isinstance(item, dict) and "embedding" in item:
                    parsed.append(item["embedding"])
                elif isinstance(item, list):
                    parsed.append(item)
            if parsed:
                return parsed
        # fallback for single embedding response shape
        return [_parse_embedding_response(result)]
    except Exception as e:
        logger.error(f"LLM embedding request failed: {e}")
        raise
