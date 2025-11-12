"""
API v1模块初始化
注册所有API路由
"""

from fastapi import APIRouter
from .chat import router as chat_router
from .knowledge import router as knowledge_router
from .rag import router as rag_router
from .extraction import router as extraction_router
from .dashboard import router as dashboard_router
from .esg import router as esg_router
from .reports import router as reports_router
from app.routers.agents import router as agents_router

# 创建v1路由器
api_router = APIRouter()

# 注册各个模块的路由（添加适当的前缀避免冲突）
api_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_router.include_router(chat_router, tags=["Chat"])
api_router.include_router(knowledge_router, tags=["Knowledge"])
api_router.include_router(rag_router, tags=["RAG"])
api_router.include_router(extraction_router, tags=["Extraction"])
api_router.include_router(dashboard_router, tags=["Dashboard"])
api_router.include_router(esg_router, tags=["ESG"])
api_router.include_router(reports_router, tags=["Reports"])

__all__ = ["api_router"]