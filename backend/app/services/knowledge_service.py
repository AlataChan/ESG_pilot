"""
知识库管理服务
提供文档上传、管理、查询等核心功能
"""

import os
import uuid
import shutil
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import logging

from app.models.knowledge import (
    KnowledgeDocument, KnowledgeCategory, DocumentStatus, DocumentType,
    KnowledgeDocumentCreate, KnowledgeDocumentUpdate,
    KnowledgeCategoryCreate, KnowledgeCategoryUpdate,
    DocumentListQuery, DocumentListResponse, KnowledgeStats
)
from app.core.config import settings
from app.services.document_processor import get_document_processor, DocumentProcessorError

logger = logging.getLogger(__name__)


class KnowledgeServiceError(Exception):
    """知识库服务异常"""
    pass


class KnowledgeService:
    """知识库管理服务"""
    
    def __init__(self, db_path: str = None, upload_dir: str = None):
        """
        初始化知识库服务
        
        Args:
            db_path: 数据库路径
            upload_dir: 文件上传目录
        """
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), "../../esg_copilot_dev.db"
        )
        self.upload_dir = Path(upload_dir or "uploads/knowledge")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化文档处理器
        self.document_processor = get_document_processor()
        
        logger.info(f"知识库服务初始化: db={self.db_path}, upload_dir={self.upload_dir}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使用Row对象便于字典访问
        return conn
    
    # ========== 分类管理 ==========
    
    async def create_category(self, user_id: str, category_data: KnowledgeCategoryCreate) -> KnowledgeCategory:
        """创建知识库分类"""
        try:
            category_id = str(uuid.uuid4())
            now = datetime.now()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO knowledge_categories 
                    (id, name, description, color, user_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    category_id, category_data.name, category_data.description,
                    category_data.color, user_id, now, now
                ))
                conn.commit()
            
            logger.info(f"创建分类成功: {category_data.name} (ID: {category_id})")
            return await self.get_category(category_id)
            
        except Exception as e:
            logger.error(f"创建分类失败: {e}")
            raise KnowledgeServiceError(f"创建分类失败: {e}")
    
    async def get_category(self, category_id: str) -> Optional[KnowledgeCategory]:
        """获取分类详情"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM knowledge_categories WHERE id = ?',
                    (category_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return KnowledgeCategory(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    color=row['color'],
                    user_id=row['user_id'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
        except Exception as e:
            logger.error(f"获取分类失败: {e}")
            raise KnowledgeServiceError(f"获取分类失败: {e}")
    
    async def list_categories(self, user_id: str) -> List[KnowledgeCategory]:
        """获取用户的分类列表"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM knowledge_categories 
                    WHERE user_id = ? OR user_id = 'system'
                    ORDER BY created_at
                ''', (user_id,))
                rows = cursor.fetchall()
                
                categories = []
                for row in rows:
                    categories.append(KnowledgeCategory(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        color=row['color'],
                        user_id=row['user_id'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    ))
                
                return categories
                
        except Exception as e:
            logger.error(f"获取分类列表失败: {e}")
            raise KnowledgeServiceError(f"获取分类列表失败: {e}")
    
    # ========== 文档管理 ==========

    async def upload_document(
        self,
        user_id: str,
        file,  # UploadFile from FastAPI
        category_id: Optional[str],
        file_type: DocumentType
    ):
        """上传文档文件

        ✅ SECURITY HARDENED:
        This method works with pre-validated files from the API endpoint.
        Path traversal protection is enforced in _generate_file_path.

        Args:
            user_id: 用户ID
            file: FastAPI UploadFile对象
            category_id: 分类ID (可选)
            file_type: 文档类型

        Returns:
            DocumentUploadResponse: 上传响应
        """
        from app.models.knowledge import DocumentUploadResponse

        try:
            # Validate filename
            if not file.filename:
                raise KnowledgeServiceError("文件名不能为空")

            # 🔒 SECURITY: Generate safe file path (with path traversal protection)
            safe_file_path = self._generate_file_path(user_id, file.filename)

            # Read and save file content
            file_content = await file.read()
            file_size = len(file_content)

            # Write file to disk
            with open(safe_file_path, 'wb') as f:
                f.write(file_content)

            logger.info(f"文件已保存: {safe_file_path} ({file_size} bytes)")

            # Create document record in database
            from app.models.knowledge import KnowledgeDocumentCreate

            document_data = KnowledgeDocumentCreate(
                filename=safe_file_path.name,  # Use the safe UUID filename
                original_filename=file.filename,  # Keep original for display
                file_type=file_type,
                file_size=file_size,
                category_id=category_id
            )

            document = await self.create_document(user_id, document_data)

            return DocumentUploadResponse(
                id=document.id,
                filename=document.original_filename,
                file_size=document.file_size,
                status=document.status,
                message="文档上传成功，正在处理中"
            )

        except Exception as e:
            logger.error(f"上传文档失败: {e}")
            # Clean up file if it was created
            if 'safe_file_path' in locals() and safe_file_path.exists():
                try:
                    safe_file_path.unlink()
                except:
                    pass
            raise KnowledgeServiceError(f"上传文档失败: {e}")

    async def create_document(self, user_id: str, document_data: KnowledgeDocumentCreate) -> KnowledgeDocument:
        """创建文档记录"""
        try:
            document_id = str(uuid.uuid4())
            now = datetime.now()
            
            # 生成文件存储路径
            file_path = self._generate_file_path(user_id, document_data.filename)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO knowledge_documents 
                    (id, user_id, filename, original_filename, file_path, file_type, 
                     file_size, category_id, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document_id, user_id, document_data.filename, 
                    document_data.original_filename, str(file_path),
                    document_data.file_type.value, document_data.file_size,
                    document_data.category_id, DocumentStatus.PROCESSING.value,
                    now, now
                ))
                conn.commit()
            
            logger.info(f"创建文档记录成功: {document_data.filename} (ID: {document_id})")
            return await self.get_document(document_id)
            
        except Exception as e:
            logger.error(f"创建文档记录失败: {e}")
            raise KnowledgeServiceError(f"创建文档记录失败: {e}")
    
    async def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        """获取文档详情"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT d.*, c.name as category_name, c.description as category_description,
                           c.color as category_color
                    FROM knowledge_documents d
                    LEFT JOIN knowledge_categories c ON d.category_id = c.id
                    WHERE d.id = ?
                ''', (document_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # 构建文档对象
                document = KnowledgeDocument(
                    id=row['id'],
                    user_id=row['user_id'],
                    filename=row['filename'],
                    original_filename=row['original_filename'],
                    file_path=row['file_path'],
                    file_type=DocumentType(row['file_type']),
                    file_size=row['file_size'],
                    category_id=row['category_id'],
                    status=DocumentStatus(row['status']),
                    vector_indexed=bool(row['vector_indexed']),
                    chunk_count=row['chunk_count'],
                    processing_error=row['processing_error'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                )
                
                # 添加分类信息
                if row['category_id'] and row['category_name']:
                    document.category = KnowledgeCategory(
                        id=row['category_id'],
                        name=row['category_name'],
                        description=row['category_description'],
                        color=row['category_color'],
                        user_id='',  # 这里不需要完整信息
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                
                return document
                
        except Exception as e:
            logger.error(f"获取文档详情失败: {e}")
            raise KnowledgeServiceError(f"获取文档详情失败: {e}")
    
    def _generate_file_path(self, user_id: str, filename: str) -> Path:
        """生成文件存储路径

        🔒 SECURITY: Path traversal protection
        - Sanitizes user_id to prevent directory traversal
        - Uses UUID for unique filenames
        - Validates final path is within upload directory
        """
        import re

        # 🔒 SECURITY: Sanitize user_id - remove any path traversal characters
        # Only allow alphanumeric, dash, underscore
        safe_user_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)

        # 🔒 SECURITY: Prevent empty user_id after sanitization
        if not safe_user_id or safe_user_id == '_':
            safe_user_id = 'default_user'

        # 创建用户专属目录
        user_dir = self.upload_dir / safe_user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # 🔒 SECURITY: Sanitize file extension - only keep the last extension
        # Extract extension safely
        file_ext = Path(filename).suffix.lower()

        # 🔒 SECURITY: Validate extension doesn't contain dangerous characters
        safe_ext = re.sub(r'[^a-zA-Z0-9.]', '', file_ext)
        if not safe_ext.startswith('.'):
            safe_ext = f'.{safe_ext}' if safe_ext else ''

        # 🔒 SECURITY: Generate completely random filename using UUID
        unique_filename = f"{uuid.uuid4()}{safe_ext}"

        # Construct final path
        final_path = user_dir / unique_filename

        # 🔒 SECURITY: Verify the final path is within the upload directory
        # Resolve both paths to absolute paths and check containment
        try:
            final_path_resolved = final_path.resolve()
            upload_dir_resolved = self.upload_dir.resolve()

            # Check if final path starts with upload directory path
            if not str(final_path_resolved).startswith(str(upload_dir_resolved)):
                raise KnowledgeServiceError(
                    "安全错误: 检测到路径遍历攻击尝试"
                )
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            raise KnowledgeServiceError(f"文件路径验证失败: {e}")

        return final_path
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """删除文档"""
        try:
            # 先获取文档信息
            document = await self.get_document(document_id)
            if not document:
                logger.warning(f"文档不存在: {document_id}")
                return False
            
            # 检查权限
            if document.user_id != user_id:
                logger.warning(f"无权限删除文档: {document_id}")
                return False
            
            # 删除物理文件
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"删除物理文件: {file_path}")
            
            # 删除数据库记录
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM knowledge_documents WHERE id = ?',
                    (document_id,)
                )
                conn.commit()
            
            logger.info(f"删除文档成功: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            raise KnowledgeServiceError(f"删除文档失败: {e}")

    async def list_documents(
        self,
        user_id: str,
        query_params: 'DocumentListQuery'
    ) -> List[KnowledgeDocument]:
        """获取文档列表（支持分页和过滤）

        Args:
            user_id: 用户ID
            query_params: 查询参数

        Returns:
            文档列表
        """
        try:
            # 构建SQL查询
            sql_parts = ['''
                SELECT d.*, c.name as category_name, c.description as category_description,
                       c.color as category_color
                FROM knowledge_documents d
                LEFT JOIN knowledge_categories c ON d.category_id = c.id
                WHERE d.user_id = ? AND d.status != ?
            ''']
            params = [user_id, DocumentStatus.DELETED.value]

            # 添加分类过滤
            if query_params.category_id:
                sql_parts.append('AND d.category_id = ?')
                params.append(query_params.category_id)

            # 添加状态过滤
            if query_params.status:
                sql_parts.append('AND d.status = ?')
                params.append(query_params.status.value)

            # 添加文件类型过滤
            if query_params.file_type:
                sql_parts.append('AND d.file_type = ?')
                params.append(query_params.file_type.value)

            # 添加搜索条件
            if query_params.search:
                sql_parts.append('AND (d.filename LIKE ? OR d.original_filename LIKE ?)')
                search_pattern = f'%{query_params.search}%'
                params.extend([search_pattern, search_pattern])

            # 添加排序
            sql_parts.append('ORDER BY d.created_at DESC')

            # 添加分页
            limit = query_params.size
            offset = (query_params.page - 1) * query_params.size
            sql_parts.append('LIMIT ? OFFSET ?')
            params.extend([limit, offset])

            # 执行查询
            sql = ' '.join(sql_parts)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                documents = []
                for row in rows:
                    documents.append(self._row_to_document(row))

                return documents

        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            raise KnowledgeServiceError(f"获取文档列表失败: {e}")

    # ========== 文档处理方法 ==========
    
    async def process_document_content(self, document_id: str) -> Dict[str, Any]:
        """
        处理文档内容，提取文本和元数据
        
        Args:
            document_id: 文档ID
            
        Returns:
            处理结果包含内容和元数据
        """
        try:
            # 获取文档信息
            document = await self.get_document(document_id)
            if not document:
                raise KnowledgeServiceError(f"文档不存在: {document_id}")
            
            # 检查文件是否存在
            if not os.path.exists(document.file_path):
                raise KnowledgeServiceError(f"文档文件不存在: {document.file_path}")
            
            # 处理文档内容
            try:
                result = self.document_processor.process_document(
                    document.file_path, 
                    document.file_type
                )
                
                # 更新文档状态和处理结果
                await self._update_document_processing_result(
                    document_id, 
                    result, 
                    DocumentStatus.COMPLETED
                )
                
                logger.info(f"文档内容处理成功: {document_id}")
                return result
                
            except DocumentProcessorError as e:
                # 处理失败，更新错误状态
                await self._update_document_status(
                    document_id, 
                    DocumentStatus.FAILED, 
                    str(e)
                )
                raise KnowledgeServiceError(f"文档处理失败: {e}")
                
        except Exception as e:
            logger.error(f"处理文档内容失败 {document_id}: {e}")
            raise KnowledgeServiceError(f"处理文档内容失败: {e}")
    
    async def get_document_preview(self, document_id: str, max_length: int = 500) -> str:
        """
        获取文档预览内容
        
        Args:
            document_id: 文档ID
            max_length: 预览最大字符数
            
        Returns:
            文档预览文本
        """
        try:
            document = await self.get_document(document_id)
            if not document:
                return "文档不存在"
            
            if not os.path.exists(document.file_path):
                return "文档文件不存在"
            
            # 获取文档预览
            preview = self.document_processor.get_document_preview(
                document.file_path,
                document.file_type,
                max_length
            )
            
            return preview
            
        except Exception as e:
            logger.error(f"获取文档预览失败 {document_id}: {e}")
            return f"预览生成失败: {e}"
    
    async def get_supported_document_types(self) -> List[str]:
        """获取支持的文档类型列表"""
        supported_types = self.document_processor.get_supported_types()
        return [doc_type.value for doc_type in supported_types]
    
    async def _update_document_processing_result(
        self, 
        document_id: str, 
        processing_result: Dict[str, Any], 
        status: DocumentStatus = DocumentStatus.COMPLETED
    ) -> None:
        """更新文档处理状态和结果"""
        try:
            # 计算内容统计信息
            content = processing_result.get('content', '')
            metadata = processing_result.get('metadata', {})
            
            # 简单的分块统计（这里可以集成更复杂的分块逻辑）
            chunk_count = max(1, len(content) // 1000) if content else 0
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE knowledge_documents 
                    SET status = ?, chunk_count = ?, updated_at = ?, processing_error = NULL
                    WHERE id = ?
                ''', (status.value, chunk_count, datetime.now(), document_id))
                conn.commit()
                
            logger.info(f"更新文档处理结果成功: {document_id}")
            
        except Exception as e:
            logger.error(f"更新文档处理结果失败: {e}")
            raise KnowledgeServiceError(f"更新文档处理结果失败: {e}")
    
    async def _update_document_status(
        self, 
        document_id: str, 
        status: DocumentStatus, 
        error_message: str = None
    ) -> None:
        """更新文档状态"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE knowledge_documents 
                    SET status = ?, processing_error = ?, updated_at = ?
                    WHERE id = ?
                ''', (status.value, error_message, datetime.now(), document_id))
                conn.commit()
                
        except Exception as e:
            logger.error(f"更新文档状态失败: {e}")
            raise KnowledgeServiceError(f"更新文档状态失败: {e}")
    
    # ========== 搜索和过滤功能 ==========
    
    async def search_documents(
        self, 
        user_id: str, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[KnowledgeDocument]:
        """
        搜索文档
        
        Args:
            user_id: 用户ID
            query: 搜索关键词
            filters: 搜索过滤条件
            
        Returns:
            匹配的文档列表
        """
        try:
            filters = filters or {}
            
            # 构建SQL查询
            sql_parts = ['''
                SELECT d.*, c.name as category_name, c.description as category_description,
                       c.color as category_color
                FROM knowledge_documents d
                LEFT JOIN knowledge_categories c ON d.category_id = c.id
                WHERE d.user_id = ? AND d.status != ?
            ''']
            params = [user_id, DocumentStatus.DELETED.value]
            
            # 添加搜索条件
            if query:
                sql_parts.append('AND (d.filename LIKE ? OR d.original_filename LIKE ?)')
                query_pattern = f'%{query}%'
                params.extend([query_pattern, query_pattern])
            
            # 添加分类过滤
            if filters.get('category_id'):
                sql_parts.append('AND d.category_id = ?')
                params.append(filters['category_id'])
            
            # 添加文件类型过滤
            if filters.get('file_type'):
                sql_parts.append('AND d.file_type = ?')
                params.append(filters['file_type'])
            
            # 添加状态过滤
            if filters.get('status'):
                sql_parts.append('AND d.status = ?')
                params.append(filters['status'])
            
            # 添加排序
            sort_by = filters.get('sort_by', 'created_at')
            sort_order = filters.get('sort_order', 'desc')
            sql_parts.append(f'ORDER BY d.{sort_by} {sort_order.upper()}')
            
            # 添加分页
            limit = filters.get('limit', 50)
            offset = filters.get('offset', 0)
            sql_parts.append('LIMIT ? OFFSET ?')
            params.extend([limit, offset])
            
            # 执行查询
            sql = ' '.join(sql_parts)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                documents = []
                for row in rows:
                    documents.append(self._row_to_document(row))
                
                return documents
                
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            raise KnowledgeServiceError(f"搜索文档失败: {e}")
    
    def _row_to_document(self, row) -> KnowledgeDocument:
        """将数据库行转换为文档对象"""
        # 构建分类对象
        category = None
        if row['category_id']:
            category = KnowledgeCategory(
                id=row['category_id'],
                name=row['category_name'] or '',
                description=row['category_description'] or '',
                color=row['category_color'] or '#1976d2',
                user_id='',  # 这里可以根据需要获取
                created_at=datetime.now(),  # 简化处理
                updated_at=datetime.now()
            )
        
        return KnowledgeDocument(
            id=row['id'],
            user_id=row['user_id'],
            filename=row['filename'],
            original_filename=row['original_filename'],
            file_path=row['file_path'],
            file_type=DocumentType(row['file_type']),
            file_size=row['file_size'],
            category_id=row['category_id'],
            status=DocumentStatus(row['status']),
            vector_indexed=bool(row.get('vector_indexed', False)),
            chunk_count=row.get('chunk_count', 0),
            processing_error=row.get('processing_error'),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            category=category
        )


# 全局服务实例
_knowledge_service: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    """获取知识库服务实例"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service