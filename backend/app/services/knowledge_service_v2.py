"""
Knowledge Management Service - V2

✅ Week 2: Data Persistence
Complete rewrite using SQLAlchemy ORM instead of raw SQLite.

IMPROVEMENTS:
- Uses SQLAlchemy ORM instead of raw SQL
- Works with both SQLite (dev) and PostgreSQL (production)
- Dependency injection with database sessions
- Proper transaction management
- Type-safe queries
- No hardcoded database paths
"""

import os
import uuid
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.models.knowledge import (
    KnowledgeDocument, KnowledgeCategory, DocumentStatus, DocumentType,
    KnowledgeDocumentCreate, KnowledgeDocumentUpdate,
    KnowledgeCategoryCreate, KnowledgeCategoryUpdate,
    DocumentListQuery, DocumentListResponse, KnowledgeStats,
    DocumentUploadResponse
)
from app.models.knowledge_db import KnowledgeCategoryDB, KnowledgeDocumentDB
from app.services.document_processor import get_document_processor, DocumentProcessorError

logger = logging.getLogger(__name__)


class KnowledgeServiceError(Exception):
    """知识库服务异常"""
    pass


class KnowledgeServiceV2:
    """
    ✅ Knowledge Management Service - SQLAlchemy ORM Version

    This service manages knowledge documents and categories using proper
    database ORM instead of raw SQL queries.
    """

    def __init__(self, upload_dir: str = None):
        """
        Initialize knowledge service

        Args:
            upload_dir: File upload directory
        """
        self.upload_dir = Path(upload_dir or "uploads/knowledge")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Initialize document processor
        self.document_processor = get_document_processor()

        logger.info(f"✅ KnowledgeServiceV2 initialized: upload_dir={self.upload_dir}")

    # ========== Category Management ==========

    async def create_category(
        self,
        db: Session,
        user_id: int,
        category_data: KnowledgeCategoryCreate
    ) -> KnowledgeCategory:
        """
        ✅ Create knowledge category using ORM

        Args:
            db: Database session
            user_id: User ID (numeric)
            category_data: Category creation data

        Returns:
            Created category
        """
        try:
            # Create ORM object
            db_category = KnowledgeCategoryDB(
                id=str(uuid.uuid4()),
                name=category_data.name,
                description=category_data.description,
                color=category_data.color,
                user_id=user_id
            )

            db.add(db_category)
            db.commit()
            db.refresh(db_category)

            logger.info(f"✅ Created category: {category_data.name} (ID: {db_category.id})")

            # Convert to Pydantic model
            return self._db_category_to_pydantic(db_category)

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to create category: {e}")
            raise KnowledgeServiceError(f"创建分类失败: {e}")

    async def get_category(
        self,
        db: Session,
        category_id: str
    ) -> Optional[KnowledgeCategory]:
        """
        ✅ Get category by ID using ORM

        Args:
            db: Database session
            category_id: Category ID

        Returns:
            Category or None if not found
        """
        try:
            db_category = db.query(KnowledgeCategoryDB).filter(
                KnowledgeCategoryDB.id == category_id
            ).first()

            if not db_category:
                return None

            return self._db_category_to_pydantic(db_category)

        except Exception as e:
            logger.error(f"❌ Failed to get category {category_id}: {e}")
            raise KnowledgeServiceError(f"获取分类失败: {e}")

    async def list_categories(
        self,
        db: Session,
        user_id: int
    ) -> List[KnowledgeCategory]:
        """
        ✅ List user categories using ORM

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of categories
        """
        try:
            # Query categories (user's own + system categories)
            db_categories = db.query(KnowledgeCategoryDB).filter(
                or_(
                    KnowledgeCategoryDB.user_id == user_id,
                    KnowledgeCategoryDB.user_id == 0  # System categories
                )
            ).order_by(KnowledgeCategoryDB.created_at).all()

            return [self._db_category_to_pydantic(cat) for cat in db_categories]

        except Exception as e:
            logger.error(f"❌ Failed to list categories: {e}")
            raise KnowledgeServiceError(f"获取分类列表失败: {e}")

    # ========== Document Management ==========

    async def upload_document(
        self,
        db: Session,
        user_id: int,
        file,  # UploadFile from FastAPI
        category_id: Optional[str],
        file_type: DocumentType
    ) -> DocumentUploadResponse:
        """
        ✅ Upload document using ORM

        Args:
            db: Database session
            user_id: User ID
            file: FastAPI UploadFile object
            category_id: Optional category ID
            file_type: Document type

        Returns:
            Upload response
        """
        try:
            # Validate filename
            if not file.filename:
                raise KnowledgeServiceError("文件名不能为空")

            # Generate safe file path
            safe_file_path = self._generate_file_path(user_id, file.filename)

            # Read and save file content
            file_content = await file.read()
            file_size = len(file_content)

            # Write file to disk
            with open(safe_file_path, 'wb') as f:
                f.write(file_content)

            logger.info(f"✅ File saved: {safe_file_path} ({file_size} bytes)")

            # Create database record using ORM
            db_document = KnowledgeDocumentDB(
                id=str(uuid.uuid4()),
                user_id=user_id,
                filename=safe_file_path.name,  # UUID filename
                original_filename=file.filename,  # Original name
                file_path=str(safe_file_path),
                file_type=file_type.value,
                file_size=file_size,
                category_id=category_id,
                status=DocumentStatus.PROCESSING.value
            )

            db.add(db_document)
            db.commit()
            db.refresh(db_document)

            logger.info(f"✅ Document record created: {db_document.id}")

            return DocumentUploadResponse(
                id=db_document.id,
                filename=db_document.original_filename,
                file_size=db_document.file_size,
                status=DocumentStatus(db_document.status),
                message="文档上传成功，正在处理中"
            )

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Upload failed: {e}")

            # Clean up file if created
            if 'safe_file_path' in locals() and safe_file_path.exists():
                try:
                    safe_file_path.unlink()
                except:
                    pass

            raise KnowledgeServiceError(f"上传文档失败: {e}")

    async def get_document(
        self,
        db: Session,
        document_id: str
    ) -> Optional[KnowledgeDocument]:
        """
        ✅ Get document by ID using ORM with eager loading

        Args:
            db: Database session
            document_id: Document ID

        Returns:
            Document or None if not found
        """
        try:
            # Use joinedload to fetch category in same query (avoid N+1)
            db_document = db.query(KnowledgeDocumentDB).options(
                joinedload(KnowledgeDocumentDB.category)
            ).filter(
                KnowledgeDocumentDB.id == document_id
            ).first()

            if not db_document:
                return None

            return self._db_document_to_pydantic(db_document)

        except Exception as e:
            logger.error(f"❌ Failed to get document {document_id}: {e}")
            raise KnowledgeServiceError(f"获取文档详情失败: {e}")

    async def list_documents(
        self,
        db: Session,
        user_id: int,
        query_params: DocumentListQuery
    ) -> List[KnowledgeDocument]:
        """
        ✅ List documents using ORM with filters

        Args:
            db: Database session
            user_id: User ID
            query_params: Query parameters

        Returns:
            List of documents
        """
        try:
            # Base query with eager loading
            query = db.query(KnowledgeDocumentDB).options(
                joinedload(KnowledgeDocumentDB.category)
            ).filter(
                and_(
                    KnowledgeDocumentDB.user_id == user_id,
                    KnowledgeDocumentDB.status != DocumentStatus.DELETED.value
                )
            )

            # Apply filters
            if query_params.category_id:
                query = query.filter(KnowledgeDocumentDB.category_id == query_params.category_id)

            if query_params.status:
                query = query.filter(KnowledgeDocumentDB.status == query_params.status.value)

            if query_params.file_type:
                query = query.filter(KnowledgeDocumentDB.file_type == query_params.file_type.value)

            if query_params.search:
                search_pattern = f"%{query_params.search}%"
                query = query.filter(
                    or_(
                        KnowledgeDocumentDB.filename.like(search_pattern),
                        KnowledgeDocumentDB.original_filename.like(search_pattern)
                    )
                )

            # Apply sorting
            query = query.order_by(KnowledgeDocumentDB.created_at.desc())

            # Apply pagination
            offset = (query_params.page - 1) * query_params.size
            query = query.limit(query_params.size).offset(offset)

            # Execute query
            db_documents = query.all()

            return [self._db_document_to_pydantic(doc) for doc in db_documents]

        except Exception as e:
            logger.error(f"❌ Failed to list documents: {e}")
            raise KnowledgeServiceError(f"获取文档列表失败: {e}")

    async def delete_document(
        self,
        db: Session,
        document_id: str,
        user_id: int
    ) -> bool:
        """
        ✅ Delete document using ORM + Vector Store Cleanup

        Deletes:
        1. Physical file from disk
        2. Database record (ORM)
        3. Vector embeddings from ChromaDB (Week 2 enhancement)

        Args:
            db: Database session
            document_id: Document ID
            user_id: User ID (for permission check)

        Returns:
            True if deleted, False if not found
        """
        try:
            # Fetch document
            db_document = db.query(KnowledgeDocumentDB).filter(
                KnowledgeDocumentDB.id == document_id
            ).first()

            if not db_document:
                logger.warning(f"❌ Document not found: {document_id}")
                return False

            # Check permission
            if db_document.user_id != user_id:
                logger.warning(f"❌ Permission denied for document: {document_id}")
                return False

            # Delete physical file
            file_path = Path(db_document.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"✅ Deleted file: {file_path}")

            # ✅ Week 2: Delete vector embeddings from ChromaDB
            if db_document.vector_indexed:
                try:
                    from app.vector_store.chroma_db import get_chroma_manager
                    chroma_manager = get_chroma_manager()
                    chroma_manager.delete_document(document_id)
                    logger.info(f"✅ Deleted vector embeddings for: {document_id}")
                except Exception as vec_error:
                    logger.error(f"⚠️ Failed to delete vector embeddings: {vec_error}")
                    # Continue with database deletion even if vector cleanup fails

            # Delete database record
            db.delete(db_document)
            db.commit()

            logger.info(f"✅ Deleted document: {document_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to delete document: {e}")
            raise KnowledgeServiceError(f"删除文档失败: {e}")

    # ========== Statistics ==========

    async def get_stats(
        self,
        db: Session,
        user_id: int
    ) -> KnowledgeStats:
        """
        ✅ Get knowledge statistics using ORM aggregations

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Knowledge statistics
        """
        try:
            # Total documents count
            total_documents = db.query(func.count(KnowledgeDocumentDB.id)).filter(
                and_(
                    KnowledgeDocumentDB.user_id == user_id,
                    KnowledgeDocumentDB.status != DocumentStatus.DELETED.value
                )
            ).scalar()

            # Total categories count
            total_categories = db.query(func.count(KnowledgeCategoryDB.id)).filter(
                or_(
                    KnowledgeCategoryDB.user_id == user_id,
                    KnowledgeCategoryDB.user_id == 0
                )
            ).scalar()

            # Total file size
            total_size = db.query(func.sum(KnowledgeDocumentDB.file_size)).filter(
                and_(
                    KnowledgeDocumentDB.user_id == user_id,
                    KnowledgeDocumentDB.status != DocumentStatus.DELETED.value
                )
            ).scalar() or 0

            # Documents by status
            status_counts = db.query(
                KnowledgeDocumentDB.status,
                func.count(KnowledgeDocumentDB.id)
            ).filter(
                and_(
                    KnowledgeDocumentDB.user_id == user_id,
                    KnowledgeDocumentDB.status != DocumentStatus.DELETED.value
                )
            ).group_by(KnowledgeDocumentDB.status).all()

            documents_by_status = {status: count for status, count in status_counts}

            # Documents by type
            type_counts = db.query(
                KnowledgeDocumentDB.file_type,
                func.count(KnowledgeDocumentDB.id)
            ).filter(
                and_(
                    KnowledgeDocumentDB.user_id == user_id,
                    KnowledgeDocumentDB.status != DocumentStatus.DELETED.value
                )
            ).group_by(KnowledgeDocumentDB.file_type).all()

            documents_by_type = {file_type: count for file_type, count in type_counts}

            # Documents by category
            category_counts = db.query(
                KnowledgeCategoryDB.name,
                func.count(KnowledgeDocumentDB.id)
            ).join(
                KnowledgeDocumentDB,
                KnowledgeCategoryDB.id == KnowledgeDocumentDB.category_id,
                isouter=True
            ).filter(
                and_(
                    KnowledgeDocumentDB.user_id == user_id,
                    KnowledgeDocumentDB.status != DocumentStatus.DELETED.value
                )
            ).group_by(KnowledgeCategoryDB.name).all()

            documents_by_category = {name: count for name, count in category_counts if name}

            return KnowledgeStats(
                total_documents=total_documents or 0,
                total_categories=total_categories or 0,
                total_size=int(total_size),
                documents_by_status=documents_by_status,
                documents_by_type=documents_by_type,
                documents_by_category=documents_by_category
            )

        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            raise KnowledgeServiceError(f"获取统计信息失败: {e}")

    # ========== Helper Methods ==========

    def _generate_file_path(self, user_id: int, filename: str) -> Path:
        """
        🔒 Generate safe file path with security protections

        Args:
            user_id: User ID
            filename: Original filename

        Returns:
            Safe file path
        """
        # Sanitize user_id
        safe_user_id = re.sub(r'[^a-zA-Z0-9_-]', '_', str(user_id))
        if not safe_user_id or safe_user_id == '_':
            safe_user_id = 'default_user'

        # Create user directory
        user_dir = self.upload_dir / safe_user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize file extension
        file_ext = Path(filename).suffix.lower()
        safe_ext = re.sub(r'[^a-zA-Z0-9.]', '', file_ext)
        if not safe_ext.startswith('.'):
            safe_ext = f'.{safe_ext}' if safe_ext else ''

        # Generate UUID-based filename
        unique_filename = f"{uuid.uuid4()}{safe_ext}"
        final_path = user_dir / unique_filename

        # Verify path is within upload directory
        try:
            final_path_resolved = final_path.resolve()
            upload_dir_resolved = self.upload_dir.resolve()

            if not str(final_path_resolved).startswith(str(upload_dir_resolved)):
                raise KnowledgeServiceError("安全错误: 检测到路径遍历攻击尝试")
        except Exception as e:
            logger.error(f"❌ Path validation error: {e}")
            raise KnowledgeServiceError(f"文件路径验证失败: {e}")

        return final_path

    def _db_category_to_pydantic(self, db_category: KnowledgeCategoryDB) -> KnowledgeCategory:
        """Convert ORM model to Pydantic model"""
        return KnowledgeCategory(
            id=db_category.id,
            name=db_category.name,
            description=db_category.description,
            color=db_category.color,
            user_id=str(db_category.user_id),  # Convert to string for API
            created_at=db_category.created_at,
            updated_at=db_category.updated_at
        )

    def _db_document_to_pydantic(self, db_document: KnowledgeDocumentDB) -> KnowledgeDocument:
        """Convert ORM model to Pydantic model"""
        # Build category if exists
        category = None
        if db_document.category:
            category = KnowledgeCategory(
                id=db_document.category.id,
                name=db_document.category.name,
                description=db_document.category.description,
                color=db_document.category.color,
                user_id=str(db_document.category.user_id),
                created_at=db_document.category.created_at,
                updated_at=db_document.category.updated_at
            )

        return KnowledgeDocument(
            id=db_document.id,
            user_id=str(db_document.user_id),  # Convert to string for API
            filename=db_document.filename,
            original_filename=db_document.original_filename,
            file_path=db_document.file_path,
            file_type=DocumentType(db_document.file_type),
            file_size=db_document.file_size,
            category_id=db_document.category_id,
            status=DocumentStatus(db_document.status),
            vector_indexed=db_document.vector_indexed,
            chunk_count=db_document.chunk_count,
            processing_error=db_document.processing_error,
            created_at=db_document.created_at,
            updated_at=db_document.updated_at,
            category=category
        )


# ========== Global Service Instance ==========

_knowledge_service_v2: Optional[KnowledgeServiceV2] = None


def get_knowledge_service_v2() -> KnowledgeServiceV2:
    """Get knowledge service V2 instance (singleton)"""
    global _knowledge_service_v2
    if _knowledge_service_v2 is None:
        _knowledge_service_v2 = KnowledgeServiceV2()
    return _knowledge_service_v2
