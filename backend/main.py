"""
CivicAssist FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import get_settings
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router

settings = get_settings()

app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description="Legal assistant for Uruguay residency and cédula laws",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix=settings.api.prefix)
app.include_router(admin_router, prefix=settings.api.prefix)


@app.get("/")
async def root():
    return {
        "app": settings.app.name,
        "version": settings.app.version,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.debug,
        log_level="info",
    )
