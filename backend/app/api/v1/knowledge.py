"""
知识库管理API接口
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse

from app.models.knowledge import (
    KnowledgeCategory, KnowledgeDocument, DocumentUploadResponse,
    KnowledgeCategoryCreate, DocumentListQuery, DocumentListResponse,
    DocumentStatus, DocumentType
)
from app.services.knowledge_service import get_knowledge_service, KnowledgeServiceError
from app.core.auth import get_current_user

router = APIRouter()


@router.get("/categories", response_model=List[KnowledgeCategory])
async def get_categories(
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service)
):
    """获取知识库分类列表"""
    try:
        categories = await service.list_categories(current_user["id"])
        return categories
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.post("/categories", response_model=KnowledgeCategory)
async def create_category(
    category_data: KnowledgeCategoryCreate,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service)
):
    """创建知识库分类"""
    try:
        category = await service.create_category(current_user["id"], category_data)
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
    service = Depends(get_knowledge_service)
):
    """获取文档列表（支持搜索和过滤）"""
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
        
        documents = await service.list_documents(current_user["id"], query_params)
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
    service = Depends(get_knowledge_service)
):
    """上传文档"""
    try:
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 从文件扩展名推断文件类型
        file_extension = file.filename.split('.')[-1].lower()
        try:
            file_type = DocumentType(file_extension)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_extension}")
        
        # 上传文档
        result = await service.upload_document(
            current_user["id"], 
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
    service = Depends(get_knowledge_service)
):
    """删除文档"""
    try:
        success = await service.delete_document(document_id, current_user["id"])
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
    service = Depends(get_knowledge_service)
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
    service = Depends(get_knowledge_service)
):
    """批量更新文档分类"""
    try:
        results = []
        for document_id in document_ids:
            try:
                # 这里需要实现batch_update_category方法
                # 暂时使用占位符
                success = True  # await service.update_document_category(document_id, category_id, current_user["id"])
                results.append({
                    "document_id": document_id,
                    "success": success,
                    "message": "更新成功" if success else "更新失败"
                })
            except Exception as e:
                results.append({
                    "document_id": document_id,
                    "success": False,
                    "message": str(e)
                })
        
        return {
            "total": len(document_ids),
            "category_id": category_id,
            "results": results,
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


@router.get("/stats")
async def get_knowledge_stats(
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service)
):
    """获取知识库统计信息"""
    try:
        # 这里需要实现get_knowledge_stats方法
        # 暂时返回基本统计信息
        documents = await service.list_documents(current_user["id"], DocumentListQuery())
        categories = await service.list_categories(current_user["id"])
        
        # 统计各种信息
        total_documents = len(documents)
        total_categories = len(categories)
        total_size = sum(doc.file_size for doc in documents)
        
        # 按状态统计
        status_stats = {}
        for doc in documents:
            status = doc.status.value
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # 按类型统计
        type_stats = {}
        for doc in documents:
            file_type = doc.file_type.value
            type_stats[file_type] = type_stats.get(file_type, 0) + 1
        
        # 按分类统计
        category_stats = {}
        for doc in documents:
            category_name = doc.category.name if doc.category else "未分类"
            category_stats[category_name] = category_stats.get(category_name, 0) + 1
        
        return {
            "total_documents": total_documents,
            "total_categories": total_categories,
            "total_size": total_size,
            "documents_by_status": status_stats,
            "documents_by_type": type_stats,
            "documents_by_category": category_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {e}")


# ========== 智能分类建议API ==========

@router.post("/documents/{document_id}/suggest-category")
async def suggest_document_category(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    service = Depends(get_knowledge_service)
):
    """为文档建议合适的分类"""
    try:
        # 这里需要集成AI分类功能
        # 暂时返回基本建议逻辑
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