import uuid
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.schemas import ChatRequest, ChatResponse
from app.services.query import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Accept a user question and return a grounded legal answer.
    Supports multi-turn conversation via conversation_history.
    """
    try:
        history = None
        if request.conversation_history:
            history = [
                {"role": m.role, "content": m.content}
                for m in request.conversation_history
            ]

        result = answer_question(
            question=request.question,
            conversation_history=history,
            language=request.language,
        )

        session_id = request.session_id or str(uuid.uuid4())

        return ChatResponse(
            answer=result["answer"],
            category=result.get("category"),
            subcategory=result.get("subcategory"),
            language=result.get("language", "es"),
            sources=result.get("sources", []),
            chunks_used=result.get("chunks_used", 0),
            session_id=session_id,
        )
    except Exception as e:
        logger.exception(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
