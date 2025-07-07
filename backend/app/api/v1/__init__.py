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

# 注册各个模块的路由
api_router.include_router(agents_router)
api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
api_router.include_router(rag_router)
api_router.include_router(extraction_router)
api_router.include_router(dashboard_router)
api_router.include_router(esg_router)
api_router.include_router(reports_router)

__all__ = ["api_router"]