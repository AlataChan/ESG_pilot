import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# 核心依赖项应该先导入
from app.core.config import settings
from app.core.logging_config import setup_logging

# 设置日志，这应该是最早执行的操作之一
setup_logging()
logger = logging.getLogger(__name__)

# 现在可以安全地导入其他模块
from app.routers import agents
from app.routers import knowledge
from app.api.routers import reports
from app.api.v1 import api_router
from app.bus.message_bus import get_message_bus
from app.db.session import SessionLocal

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="由AI Agent驱动的ESG智能管理平台",
    version="1.0.0"
)

# 设置CORS中间件
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 包含API路由
app.include_router(agents.router, prefix=f"{settings.API_V1_STR}/agents", tags=["Agents"])
app.include_router(knowledge.router, prefix=f"{settings.API_V1_STR}", tags=["Knowledge Management"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(api_router, prefix=settings.API_V1_STR)


# 定义启动和关闭事件
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup...")
    try:
        # 初始化数据库
        db = SessionLocal()
        
        # 初始化消息总线
        message_bus = get_message_bus()
        
        # 将关键服务存入app.state以便在其他地方访问
        app.state.message_bus = message_bus
        app.state.db = db
        
        logger.info("✅ Application startup complete.")
        
    except Exception as e:
        logger.exception(f"❌ Critical error during application startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown...")
    
    if hasattr(app.state, 'db') and app.state.db:
        app.state.db.close()
        logger.info("✅ Database session closed.")

# 健康检查端点
@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ESG Copilot service is healthy and running."}

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}

# 如果直接运行此文件
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
