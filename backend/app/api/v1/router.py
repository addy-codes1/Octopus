"""API v1 router aggregating all endpoints."""
from fastapi import APIRouter

from .endpoints import auth, papers, conversations, chat, citations

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Paper routes
api_router.include_router(papers.router, prefix="/papers", tags=["papers"])

# Conversation routes
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])

# Chat routes
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# Citation routes
api_router.include_router(citations.router, prefix="/citations", tags=["citations"])
