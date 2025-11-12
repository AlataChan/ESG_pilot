"""
Monitoring and Health Check Endpoints
Week 3 Day 3: System monitoring, health checks, and performance metrics
"""

import logging
import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.cache import get_cache_stats
from app.core.response import create_response
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Track application start time
_app_start_time = time.time()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint
    Returns 200 if service is operational
    """
    try:
        # Check database connectivity
        db.execute("SELECT 1")

        return create_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "ESG Pilot API",
            "version": getattr(settings, 'VERSION', '1.0.0')
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with component status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # Check database
    try:
        db.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "PostgreSQL" if "postgresql" in str(db.bind.url) else "SQLite"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check cache
    try:
        cache_stats = await get_cache_stats()
        health_status["components"]["cache"] = {
            "status": "healthy",
            "stats": cache_stats
        }
    except Exception as e:
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check vector store
    try:
        from app.vector_store.chroma_db import get_chroma_manager
        chroma_manager = get_chroma_manager()
        collection_count = chroma_manager.collection.count()
        health_status["components"]["vector_store"] = {
            "status": "healthy",
            "documents": collection_count
        }
    except Exception as e:
        health_status["components"]["vector_store"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check LLM service
    try:
        from app.core.llm_factory import llm_factory
        health_status["components"]["llm"] = {
            "status": "healthy",
            "provider": "DeepSeek AI"
        }
    except Exception as e:
        health_status["components"]["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    if health_status["status"] == "degraded":
        return create_response(health_status, status_code=503)

    return create_response(health_status)


@router.get("/metrics")
async def get_metrics():
    """
    System performance metrics
    Returns CPU, memory, disk, and application metrics
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Application uptime
        uptime_seconds = time.time() - _app_start_time

        # Cache metrics
        cache_stats = await get_cache_stats()

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_mb": memory.total / (1024 * 1024),
                    "available_mb": memory.available / (1024 * 1024),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024 * 1024 * 1024),
                    "used_gb": disk.used / (1024 * 1024 * 1024),
                    "free_gb": disk.free / (1024 * 1024 * 1024),
                    "used_percent": disk.percent
                }
            },
            "application": {
                "uptime_seconds": uptime_seconds,
                "uptime_hours": uptime_seconds / 3600,
                "environment": getattr(settings, 'ENV_STATE', 'development'),
                "version": getattr(settings, 'VERSION', '1.0.0')
            },
            "cache": cache_stats
        }

        return create_response(metrics)

    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/metrics/database")
async def get_database_metrics(db: Session = Depends(get_db)):
    """
    Database-specific metrics
    Returns table sizes and row counts
    """
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "tables": {}
        }

        # Get counts for each table
        from app.models.user import User
        from app.models.knowledge_db import KnowledgeCategoryDB, KnowledgeDocumentDB
        from app.models.report_db import ReportDB
        from app.models.conversation import Conversation

        tables = [
            ("users", User),
            ("knowledge_categories", KnowledgeCategoryDB),
            ("knowledge_documents", KnowledgeDocumentDB),
            ("reports", ReportDB),
            ("conversations", Conversation)
        ]

        for table_name, model in tables:
            try:
                count = db.query(model).count()
                metrics["tables"][table_name] = {
                    "row_count": count
                }
            except Exception as e:
                metrics["tables"][table_name] = {
                    "error": str(e)
                }

        return create_response(metrics)

    except Exception as e:
        logger.error(f"Failed to retrieve database metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database metrics")


@router.get("/metrics/performance")
async def get_performance_metrics():
    """
    API performance metrics
    Returns average response times and error rates
    """
    try:
        # Get cache statistics
        cache_stats = await get_cache_stats()

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cache_performance": cache_stats,
            "recommendations": []
        }

        # Add recommendations based on cache hit rate
        if cache_stats.get("hit_rate"):
            hit_rate_str = cache_stats["hit_rate"].rstrip('%')
            hit_rate = float(hit_rate_str) if hit_rate_str else 0

            if hit_rate < 50:
                metrics["recommendations"].append({
                    "severity": "warning",
                    "message": f"Cache hit rate is low ({cache_stats['hit_rate']}). Consider increasing TTL values or reviewing cache strategy."
                })
            elif hit_rate > 80:
                metrics["recommendations"].append({
                    "severity": "success",
                    "message": f"Excellent cache hit rate ({cache_stats['hit_rate']}). Cache is performing well."
                })

        return create_response(metrics)

    except Exception as e:
        logger.error(f"Failed to retrieve performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear all cache entries
    ⚠️ Use with caution in production!
    """
    try:
        from app.core.cache import clear_all_cache
        await clear_all_cache()

        return create_response({
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/status")
async def get_system_status(db: Session = Depends(get_db)):
    """
    Comprehensive system status overview
    Combines health, metrics, and performance data
    """
    try:
        # Get all metrics
        health_check_result = await detailed_health_check(db)
        metrics_result = await get_metrics()
        db_metrics_result = await get_database_metrics(db)

        status = {
            "timestamp": datetime.now().isoformat(),
            "health": health_check_result["data"],
            "system_metrics": metrics_result["data"]["system"],
            "application": metrics_result["data"]["application"],
            "cache": metrics_result["data"]["cache"],
            "database": db_metrics_result["data"]["tables"]
        }

        return create_response(status)

    except Exception as e:
        logger.error(f"Failed to retrieve system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")
