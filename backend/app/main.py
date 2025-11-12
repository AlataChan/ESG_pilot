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
from app.api.v1 import api_router
from app.bus.message_bus import get_message_bus
from app.db.session import create_tables, close_database

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

# ✅ Week 3 Day 3: Add performance monitoring middleware
from app.middleware import PerformanceMiddleware, ErrorTrackingMiddleware
app.add_middleware(ErrorTrackingMiddleware)
app.add_middleware(PerformanceMiddleware, log_slow_requests=True, slow_threshold=1.0)
logger.info("✅ Performance monitoring middleware enabled")

# 包含API路由 - 统一通过api_router注册，避免重复
# 所有v1 API路由都在 app/api/v1/__init__.py 中注册
app.include_router(api_router, prefix=settings.API_V1_STR)


# 定义启动和关闭事件
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Application startup...")
    try:
        # 1. 初始化数据库表（如果不存在）
        logger.info("📊 Initializing database tables...")
        try:
            create_tables()
            logger.info("✅ Database tables ready")
        except Exception as db_error:
            logger.warning(f"⚠️  Database initialization warning: {db_error}")
            # Continue even if database fails (for development without DB)

        # 2. 初始化并启动消息总线
        logger.info("📨 Initializing message bus...")
        message_bus = get_message_bus()
        await message_bus.start()  # ✅ CRITICAL FIX: Start the message bus!
        app.state.message_bus = message_bus
        logger.info("✅ Message bus started and ready")

        logger.info("✅ Application startup complete!")

    except Exception as e:
        logger.exception(f"❌ Critical error during application startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🔌 Application shutdown...")

    try:
        # 1. 停止消息总线
        if hasattr(app.state, 'message_bus') and app.state.message_bus:
            logger.info("📨 Stopping message bus...")
            await app.state.message_bus.stop()
            logger.info("✅ Message bus stopped")

        # 2. 关闭数据库连接
        logger.info("📊 Closing database connections...")
        close_database()
        logger.info("✅ Database connections closed")

    except Exception as e:
        logger.error(f"⚠️  Error during shutdown: {e}")

    logger.info("✅ Application shutdown complete")

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
