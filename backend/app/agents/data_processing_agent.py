import logging
import os
from typing import Dict, Any

from .base_agent import BaseAgent, AgentProcessingError
from app.bus import A2AMessage
from app.vector_store.chroma_db import get_chroma_manager

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class DocumentProcessingError(AgentProcessingError):
    """文档处理专用异常"""
    def __init__(self, message: str, file_path: str = "", recoverable: bool = True):
        super().__init__(message, recoverable)
        self.file_path = file_path

class DataProcessingAgent(BaseAgent):
    """
    负责处理和索引文档到向量存储的 Agent。
    包含增强的错误处理和文档格式支持。
    """
    def __init__(self, agent_id: str = "data_processing_agent", message_bus=None):
        super().__init__(agent_id)
        if message_bus:
            self.message_bus = message_bus
        
        try:
            self.chroma_manager = get_chroma_manager()
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            
            # 支持的文件格式
            self.supported_formats = {'.pdf', '.txt', '.md', '.docx'}
            
            self.register_handler("process_document", self.handle_process_document)
            
            logging.info(f"DataProcessingAgent {agent_id} initialized successfully")
            
        except Exception as e:
            raise AgentProcessingError(f"Failed to initialize DataProcessingAgent: {e}", recoverable=False)

    async def handle_process_document(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理文档：加载、分块、索引到向量存储
        
        Args:
            message: 包含文件路径的消息
            
        Returns:
            处理结果字典
        """
        file_path = message.payload.get("file_path")
        
        # 类型检查和转换
        if not isinstance(file_path, str):
            raise DocumentProcessingError(
                "File path must be a string",
                recoverable=False
            )
        
        try:
            # 1. 验证输入
            self._validate_file_input(file_path)
            
            # 2. 检查文件格式
            self._validate_file_format(file_path)
            
            # 3. 加载文档
            documents = self._load_document(file_path)
            
            # 4. 分块处理
            chunks = self._split_document(documents, file_path)
            
            # 5. 索引到向量存储
            indexed_count = await self._index_to_vector_store(chunks, file_path)
            
            success_msg = f"Successfully processed and indexed {indexed_count} chunks from {os.path.basename(file_path)}"
            logging.info(success_msg)
            
            return {
                "status": "success",
                "message": success_msg,
                "file_path": file_path,
                "chunks_count": indexed_count,
                "agent_id": self.agent_id
            }
            
        except DocumentProcessingError:
            # 重新抛出已知的文档处理错误
            raise
        except Exception as e:
            # 包装未预期的异常
            raise DocumentProcessingError(
                f"Unexpected error processing document {file_path}: {e}",
                file_path=file_path,
                recoverable=False
            )

    def _validate_file_input(self, file_path: str):
        """验证文件输入"""
        if not file_path:
            raise DocumentProcessingError(
                "File path not provided in message payload",
                recoverable=False
            )
        
        if not os.path.exists(file_path):
            raise DocumentProcessingError(
                f"File not found: {file_path}",
                file_path=file_path,
                recoverable=False
            )
        
        if not os.path.isfile(file_path):
            raise DocumentProcessingError(
                f"Path is not a file: {file_path}",
                file_path=file_path,
                recoverable=False
            )

    def _validate_file_format(self, file_path: str):
        """验证文件格式"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in self.supported_formats:
            raise DocumentProcessingError(
                f"Unsupported file format: {file_ext}. Supported formats: {', '.join(self.supported_formats)}",
                file_path=file_path,
                recoverable=False
            )

    def _load_document(self, file_path: str):
        """加载文档"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
                documents = loader.load()
            elif file_ext in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 创建简单的文档对象
                documents = [Document(page_content=content, metadata={"source": file_path})]
            else:
                raise DocumentProcessingError(
                    f"Document loader not implemented for {file_ext}",
                    file_path=file_path,
                    recoverable=False
                )
            
            if not documents:
                raise DocumentProcessingError(
                    f"No content extracted from file: {file_path}",
                    file_path=file_path,
                    recoverable=False
                )
            
            logging.debug(f"Loaded {len(documents)} document(s) from {file_path}")
            return documents
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to load document {file_path}: {e}",
                file_path=file_path,
                recoverable=True  # 文件加载错误可能是临时的
            )

    def _split_document(self, documents, file_path: str):
        """分块处理文档"""
        try:
            chunks = self.text_splitter.split_documents(documents)
            
            if not chunks:
                raise DocumentProcessingError(
                    f"No chunks generated from document: {file_path}",
                    file_path=file_path,
                    recoverable=False
                )
            
            logging.debug(f"Split document into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to split document {file_path}: {e}",
                file_path=file_path,
                recoverable=True
            )

    async def _index_to_vector_store(self, chunks, file_path: str) -> int:
        """索引到向量存储"""
        try:
            # 准备存储数据
            docs_to_store = [chunk.page_content for chunk in chunks]
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                metadata = chunk.metadata.copy()
                metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "processed_by": self.agent_id,
                    "file_name": os.path.basename(file_path)
                })
                metadatas.append(metadata)
            
            # 创建唯一 ID
            base_id = os.path.basename(file_path)
            ids = [f"{base_id}_chunk_{i}" for i in range(len(chunks))]
            
            # 添加到向量存储
            self.chroma_manager.add_documents(
                documents=docs_to_store,
                metadatas=metadatas,
                ids=ids
            )
            
            logging.info(f"Successfully indexed {len(chunks)} chunks to vector store")
            return len(chunks)
            
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to index document to vector store: {e}",
                file_path=file_path,
                recoverable=True  # 向量存储错误通常可重试
            )

    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        health_status = self.get_health_status()
        
        return {
            **health_status,
            "supported_formats": list(self.supported_formats),
            "vector_store_connected": self.chroma_manager is not None
        } 