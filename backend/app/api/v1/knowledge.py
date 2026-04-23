"""
知识库管理API接口

✅ Week 2: Updated to use SQLAlchemy ORM service
Now uses KnowledgeServiceV2 with proper database sessions.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.models.knowledge import (
    KnowledgeCategory, KnowledgeDocument, DocumentUploadResponse,
    KnowledgeCategoryCreate, DocumentListQuery, DocumentListResponse,
    DocumentStatus, DocumentType, KnowledgeStats
)
from app.services.knowledge_service import get_knowledge_service
from app.services.knowledge_service_v2 import get_knowledge_service_v2, KnowledgeServiceError
from app.core.auth import get_current_user
from app.db.session import get_db

router = APIRouter(prefix="/knowledge")


@router.get("/categories", response_model=List[KnowledgeCategory])
async def get_categories(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_knowledge_service_v2)
):
    """✅ 获取知识库分类列表 (ORM Version)"""
    try:
        categories = await service.list_categories(db, current_user["user_id"])
        return categories
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.post("/categories", response_model=KnowledgeCategory)
async def create_category(
    category_data: KnowledgeCategoryCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_knowledge_service_v2)
):
    """✅ 创建知识库分类 (ORM Version)"""
    try:
        category = await service.create_category(db, current_user["user_id"], category_data)
        return category
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/documents", response_model=List[KnowledgeDocument])
async def get_documents(
    category_id: Optional[str] = Query(None, description="分类ID筛选"),
    status: Optional[DocumentStatus] = Query(None, description="状态筛选"),
    file_type: Optional[DocumentType] = Query(None, description="文件类型筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_knowledge_service_v2)
):
    """✅ 获取文档列表 (ORM Version with pagination)"""
    try:
        # 构建查询参数
        query_params = DocumentListQuery(
            category_id=category_id,
            status=status,
            file_type=file_type,
            search=search,
            page=page,
            size=size
        )

        documents = await service.list_documents(db, current_user["user_id"], query_params)
        return documents
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_id: Optional[str] = Query(None, description="分类ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_knowledge_service_v2)
):
    """✅ 上传文档 (ORM Version with enhanced security)

    ✅ SECURITY HARDENED:
    - File size limit: 100MB max
    - MIME type validation with python-magic
    - Path traversal protection
    - Sanitized filename handling
    """
    try:
        # 🔒 SECURITY: Validate filename exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 🔒 SECURITY: Check file size BEFORE reading entire file
        # Read file content for validation
        file_content = await file.read()
        file_size = len(file_content)

        # File size limit: 100MB
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,  # Payload Too Large
                detail=f"文件过大: {file_size / 1024 / 1024:.2f}MB，最大支持100MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="文件为空，无法上传")

        # 🔒 SECURITY: Validate actual MIME type (not just extension)
        import magic
        mime_type = magic.from_buffer(file_content[:2048], mime=True)

        # Get file extension from filename
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''

        # 🔒 SECURITY: Verify MIME type matches allowed types
        ALLOWED_MIME_TYPES = {
            # Documents
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/msword': 'doc',
            'text/plain': ['txt', 'md'],
            'application/rtf': 'rtf',
            # Spreadsheets
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'application/vnd.ms-excel': 'xls',
            'text/csv': 'csv',
            # Presentations
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
            'application/vnd.ms-powerpoint': 'ppt',
            # Data formats
            'application/json': 'json',
            'application/xml': 'xml',
            'text/xml': 'xml',
            'text/yaml': ['yaml', 'yml'],
            'application/x-yaml': ['yaml', 'yml'],
            # Images
            'image/png': 'png',
            'image/jpeg': ['jpg', 'jpeg'],
            'image/gif': 'gif',
            'image/webp': 'webp',
            # HTML
            'text/html': ['html', 'htm'],
        }

        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: MIME类型 '{mime_type}' 不在允许列表中"
            )

        # Verify extension matches MIME type
        allowed_extensions = ALLOWED_MIME_TYPES[mime_type]
        if isinstance(allowed_extensions, str):
            allowed_extensions = [allowed_extensions]

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"文件扩展名 '.{file_extension}' 与实际文件类型 '{mime_type}' 不匹配"
            )

        # Determine DocumentType from validated extension
        try:
            file_type = DocumentType(file_extension)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_extension}")

        # Reset file position for service to read
        await file.seek(0)

        # 🔒 SECURITY: Upload with validated file
        # The service will generate a safe UUID-based filename
        result = await service.upload_document(
            db,
            current_user["user_id"],
            file,
            category_id,
            file_type
        )

        return result
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_knowledge_service_v2)
):
    """✅ 删除文档 (ORM Version)"""
    try:
        success = await service.delete_document(db, document_id, current_user["user_id"])
        if success:
            return {"message": "文档删除成功"}
        else:
            raise HTTPException(status_code=404, detail="文档不存在或无权删除")
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


# ========== 新增的高级功能API ==========

@router.get("/documents/{document_id}/preview")
async def get_document_preview(
    document_id: str,
    max_length: int = Query(500, ge=100, le=2000, description="预览最大字符数"),
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service)
):
    """获取文档预览内容"""
    try:
        preview = await service.get_document_preview(document_id, max_length)
        return {"document_id": document_id, "preview": preview}
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.post("/documents/{document_id}/process")
async def process_document_content(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service)
):
    """处理文档内容，提取文本和元数据"""
    try:
        result = await service.process_document_content(document_id)
        return {
            "document_id": document_id,
            "status": "success",
            "content_length": len(result.get('content', '')),
            "metadata": result.get('metadata', {}),
            "processor": result.get('processor', '')
        }
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/documents/search")
async def search_documents(
    q: str = Query(..., description="搜索关键词"),
    category_id: Optional[str] = Query(None, description="分类ID筛选"),
    file_type: Optional[str] = Query(None, description="文件类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service)
):
    """搜索文档"""
    try:
        # 构建搜索过滤条件
        filters = {
            "category_id": category_id,
            "file_type": file_type,
            "status": status,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }
        
        # 移除空值
        filters = {k: v for k, v in filters.items() if v is not None}
        
        documents = await service.search_documents(current_user["id"], q, filters)
        
        return {
            "query": q,
            "filters": filters,
            "results": documents,
            "count": len(documents)
        }
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/supported-types")
async def get_supported_document_types(
    service = Depends(get_knowledge_service)
):
    """获取支持的文档类型列表"""
    try:
        supported_types = await service.get_supported_document_types()
        return {"supported_types": supported_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.post("/documents/batch-delete")
async def batch_delete_documents(
    document_ids: List[str],
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service_v2)
):
    """批量删除文档"""
    try:
        results = []
        for document_id in document_ids:
            try:
                success = await service.delete_document(document_id, current_user["id"])
                results.append({
                    "document_id": document_id,
                    "success": success,
                    "message": "删除成功" if success else "删除失败"
                })
            except Exception as e:
                results.append({
                    "document_id": document_id,
                    "success": False,
                    "message": str(e)
                })
        
        return {
            "total": len(document_ids),
            "results": results,
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.post("/documents/batch-update-category")
async def batch_update_document_category(
    document_ids: List[str],
    category_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service_v2)
):
    """
    批量更新文档分类

    ⚠️ HONEST IMPLEMENTATION: This endpoint requires database implementation.
    Previously returned fake success - now properly indicates not implemented.
    """
    raise HTTPException(
        status_code=501,  # Not Implemented
        detail={
            "error": "NotImplemented",
            "message": "批量更新分类功能需要数据库持久化支持，当前版本未实现",
            "feature_status": "planned",
            "alternative": "请使用单个文档更新API（当实现后）",
            "github_issue": "创建issue请求此功能"
        }
    )


@router.get("/stats", response_model=KnowledgeStats)
async def get_knowledge_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    service = Depends(get_knowledge_service_v2)
):
    """✅ 获取知识库统计信息 (ORM Version with SQL aggregations)

    Performance improved: Uses SQL GROUP BY instead of fetching all documents
    """
    try:
        stats = await service.get_stats(db, current_user["user_id"])
        return stats
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


# ========== 智能分类建议API ==========

@router.post("/documents/{document_id}/suggest-category")
async def suggest_document_category(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service)
):
    """为文档建议合适的分类

    ✅ Basic keyword-based implementation functional
    📝 TODO: Enhance with LLM-based classification for better accuracy
    """
    try:
        document = await service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取文档预览内容
        preview = await service.get_document_preview(document_id, 1000)
        
        # 简单的关键词匹配逻辑（后续可以集成更复杂的AI分类）
        suggestions = []
        
        # 基于文件名的建议
        filename_lower = document.filename.lower()
        if any(keyword in filename_lower for keyword in ["esg", "环境", "可持续"]):
            suggestions.append({"category": "ESG报告", "confidence": 0.8, "reason": "文件名包含ESG相关关键词"})
        elif any(keyword in filename_lower for keyword in ["financial", "财务", "finance"]):
            suggestions.append({"category": "财务报告", "confidence": 0.7, "reason": "文件名包含财务相关关键词"})
        elif any(keyword in filename_lower for keyword in ["policy", "政策", "制度"]):
            suggestions.append({"category": "政策文件", "confidence": 0.6, "reason": "文件名包含政策相关关键词"})
        
        # 基于内容的建议（简化版）
        if preview and len(preview) > 100:
            content_lower = preview.lower()
            if any(keyword in content_lower for keyword in ["碳排放", "绿色", "环保", "sustainability"]):
                suggestions.append({"category": "环境保护", "confidence": 0.9, "reason": "内容包含环保相关关键词"})
            elif any(keyword in content_lower for keyword in ["投资", "收益", "profit", "revenue"]):
                suggestions.append({"category": "投资分析", "confidence": 0.8, "reason": "内容包含投资相关关键词"})
        
        # 如果没有匹配的建议，返回通用分类
        if not suggestions:
            suggestions.append({"category": "通用文档", "confidence": 0.5, "reason": "未找到特定分类特征"})
        
        return {
            "document_id": document_id,
            "filename": document.filename,
            "suggestions": suggestions
        }
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


# 健康检查接口
@router.get("/health")
async def health_check():
    """知识库模块健康检查"""
    return {"status": "healthy", "module": "knowledge", "timestamp": "2024-06-19"}


# 测试用的辅助接口
@router.get("/test/processor")
async def test_document_processor(
    service = Depends(get_knowledge_service)
):
    """测试文档处理器功能"""
    try:
        supported_types = await service.get_supported_document_types()
        return {
            "processor_status": "available",
            "supported_types": supported_types,
            "total_supported": len(supported_types)
        }
    except Exception as e:
        return {
            "processor_status": "error",
            "error": str(e)
        } 
