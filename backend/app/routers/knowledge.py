"""
知识库管理API路由
提供文档上传、管理、查询等RESTful接口
"""

import os
import shutil
from typing import List, Optional
from pathlib import Path
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse

from app.models.knowledge import (
    KnowledgeDocument, KnowledgeCategory, DocumentStatus, DocumentType,
    KnowledgeDocumentCreate, KnowledgeDocumentUpdate,
    KnowledgeCategoryCreate, KnowledgeCategoryUpdate,
    DocumentUploadResponse, DocumentListQuery, DocumentListResponse,
    KnowledgeStats
)
from app.services.knowledge_service import get_knowledge_service, KnowledgeServiceError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Management"],
    responses={404: {"description": "未找到"}}
)

# 支持的文件类型和大小限制
ALLOWED_FILE_TYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt': 'text/plain',
    'md': 'text/markdown',
    'json': 'application/json'
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_current_user_id() -> str:
    """获取当前用户ID（暂时使用固定值，后续集成认证系统）"""
    return "current_user"


def validate_file_type(filename: str) -> DocumentType:
    """验证并返回文件类型"""
    file_ext = Path(filename).suffix.lower().lstrip('.')
    
    if file_ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}. 支持的类型: {', '.join(ALLOWED_FILE_TYPES.keys())}"
        )
    
    return DocumentType(file_ext)


# ========== 分类管理接口 ==========

@router.post("/categories", response_model=KnowledgeCategory)
async def create_category(
    category_data: KnowledgeCategoryCreate,
    user_id: str = Depends(get_current_user_id),
    knowledge_service = Depends(get_knowledge_service)
):
    """创建知识库分类"""
    try:
        return await knowledge_service.create_category(user_id, category_data)
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories", response_model=List[KnowledgeCategory])
async def list_categories(
    user_id: str = Depends(get_current_user_id),
    knowledge_service = Depends(get_knowledge_service)
):
    """获取分类列表"""
    try:
        return await knowledge_service.list_categories(user_id)
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/{category_id}", response_model=KnowledgeCategory)
async def get_category(
    category_id: str,
    knowledge_service = Depends(get_knowledge_service)
):
    """获取分类详情"""
    try:
        category = await knowledge_service.get_category(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        return category
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 文档管理接口 ==========

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_id: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id),
    knowledge_service = Depends(get_knowledge_service)
):
    """上传文档"""
    
    # 验证文件
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 验证文件大小
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE/1024/1024:.1f}MB)"
        )
    
    # 验证文件类型
    file_type = validate_file_type(file.filename)
    
    try:
        # 创建文档记录
        document_data = KnowledgeDocumentCreate(
            filename=file.filename,
            original_filename=file.filename,
            file_type=file_type,
            file_size=file.size or 0,
            category_id=category_id or "default"
        )
        
        document = await knowledge_service.create_document(user_id, document_data)
        
        # 保存文件
        file_path = Path(document.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # 更新文件大小（如果之前为0）
        if document_data.file_size == 0:
            actual_size = file_path.stat().st_size
            # TODO: 更新数据库中的文件大小
        
        logger.info(f"文档上传成功: {file.filename} -> {file_path}")
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            file_size=document.file_size,
            status=document.status,
            message="文档上传成功，正在处理中..."
        )
        
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {e}")


@router.get("/documents", response_model=List[KnowledgeDocument])
async def list_documents(
    category_id: Optional[str] = Query(None, description="分类ID筛选"),
    status: Optional[DocumentStatus] = Query(None, description="状态筛选"),
    file_type: Optional[DocumentType] = Query(None, description="文件类型筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: str = Depends(get_current_user_id),
    knowledge_service = Depends(get_knowledge_service)
):
    """获取文档列表"""
    try:
        # TODO: 实现完整的分页和筛选逻辑
        # 目前先返回简单的列表
        documents = []  # await knowledge_service.list_documents(user_id, query)
        return documents
        
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=KnowledgeDocument)
async def get_document(
    document_id: str,
    knowledge_service = Depends(get_knowledge_service)
):
    """获取文档详情"""
    try:
        document = await knowledge_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        return document
        
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    knowledge_service = Depends(get_knowledge_service)
):
    """删除文档"""
    try:
        success = await knowledge_service.delete_document(document_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在或无权限删除")
        
        return {"message": "文档删除成功"}
        
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    knowledge_service = Depends(get_knowledge_service)
):
    """下载文档"""
    try:
        document = await knowledge_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查权限
        if document.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限下载此文档")
        
        file_path = Path(document.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=document.original_filename,
            media_type='application/octet-stream'
        )
        
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 统计信息接口 ==========

@router.get("/stats", response_model=dict)
async def get_knowledge_stats(
    user_id: str = Depends(get_current_user_id),
    knowledge_service = Depends(get_knowledge_service)
):
    """获取知识库统计信息"""
    try:
        # TODO: 实现统计功能
        stats = {
            "total_documents": 0,
            "total_categories": 0,
            "total_size": 0,
            "documents_by_status": {},
            "documents_by_type": {},
            "documents_by_category": {}
        }
        return stats
        
    except KnowledgeServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 健康检查 ==========

@router.get("/health")
async def health_check():
    """知识库服务健康检查"""
    return {
        "status": "healthy",
        "service": "knowledge_management",
        "message": "知识库管理服务运行正常"
    }