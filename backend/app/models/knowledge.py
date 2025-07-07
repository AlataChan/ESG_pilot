"""
知识库管理相关的数据模型
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class DocumentStatus(str, Enum):
    """文档处理状态枚举"""
    UPLOADING = "uploading"      # 上传中
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 处理完成
    FAILED = "failed"           # 处理失败
    DELETED = "deleted"         # 已删除


class DocumentType(str, Enum):
    """支持的文档类型"""
    # 文档类型
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    RTF = "rtf"
    ODT = "odt"
    
    # 表格类型
    XLS = "xls"
    XLSX = "xlsx"
    CSV = "csv"
    ODS = "ods"
    
    # 演示文稿类型
    PPT = "ppt"
    PPTX = "pptx"
    ODP = "odp"
    
    # 数据格式
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    YML = "yml"
    
    # 图片类型 (OCR文档识别)
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    GIF = "gif"
    WEBP = "webp"
    
    # 其他格式
    HTML = "html"
    HTM = "htm"


class KnowledgeCategory(BaseModel):
    """知识库分类模型"""
    id: str
    name: str = Field(..., description="分类名称")
    description: Optional[str] = Field(None, description="分类描述")
    color: str = Field("#1976d2", description="分类颜色")
    user_id: str = Field(..., description="用户ID")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeCategoryCreate(BaseModel):
    """创建知识库分类的请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    color: str = Field("#1976d2", pattern=r"^#[0-9A-Fa-f]{6}$", description="分类颜色")


class KnowledgeCategoryUpdate(BaseModel):
    """更新知识库分类的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="分类颜色")


class KnowledgeDocument(BaseModel):
    """知识库文档模型"""
    id: str
    user_id: str = Field(..., description="用户ID")
    filename: str = Field(..., description="文件名")
    original_filename: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="文件路径")
    file_type: DocumentType = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小(字节)")
    category_id: Optional[str] = Field(None, description="分类ID")
    status: DocumentStatus = Field(DocumentStatus.PROCESSING, description="处理状态")
    vector_indexed: bool = Field(False, description="是否已向量化索引")
    chunk_count: int = Field(0, description="文档块数量")
    processing_error: Optional[str] = Field(None, description="处理错误信息")
    created_at: datetime
    updated_at: datetime
    
    # 关联的分类信息
    category: Optional[KnowledgeCategory] = None

    class Config:
        from_attributes = True


class KnowledgeDocumentCreate(BaseModel):
    """创建知识库文档的请求模型"""
    filename: str = Field(..., description="文件名")
    original_filename: str = Field(..., description="原始文件名")
    file_type: DocumentType = Field(..., description="文件类型")
    file_size: int = Field(..., gt=0, description="文件大小")
    category_id: Optional[str] = Field(None, description="分类ID")


class KnowledgeDocumentUpdate(BaseModel):
    """更新知识库文档的请求模型"""
    filename: Optional[str] = Field(None, description="文件名")
    category_id: Optional[str] = Field(None, description="分类ID")
    status: Optional[DocumentStatus] = Field(None, description="处理状态")


class DocumentUploadResponse(BaseModel):
    """文档上传响应模型"""
    id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名") 
    file_size: int = Field(..., description="文件大小")
    status: DocumentStatus = Field(..., description="处理状态")
    message: str = Field(..., description="响应消息")


class DocumentListQuery(BaseModel):
    """文档列表查询参数"""
    category_id: Optional[str] = Field(None, description="分类ID筛选")
    status: Optional[DocumentStatus] = Field(None, description="状态筛选")
    file_type: Optional[DocumentType] = Field(None, description="文件类型筛选")
    search: Optional[str] = Field(None, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")


class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    items: List[KnowledgeDocument] = Field(..., description="文档列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class KnowledgeStats(BaseModel):
    """知识库统计信息"""
    total_documents: int = Field(..., description="文档总数")
    total_categories: int = Field(..., description="分类总数") 
    total_size: int = Field(..., description="总文件大小")
    documents_by_status: dict = Field(..., description="按状态统计的文档数")
    documents_by_type: dict = Field(..., description="按类型统计的文档数")
    documents_by_category: dict = Field(..., description="按分类统计的文档数")