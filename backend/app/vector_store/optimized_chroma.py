"""
优化的向量数据库接口
包含缓存、批量操作和性能优化
"""
import os
import time
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

try:
    from app.core.cache import cached, memory_cache, CacheKey
    from app.core.logging_config import log_performance, time_it
except ImportError:
    # 备用函数
    def cached(ttl=60, prefix="cache", key_builder=None):
        def decorator(func):
            return func
        return decorator
    
    def log_performance(metric_name: str, value: float, context: Optional[Dict[str, Any]] = None):
        pass
    
    def time_it(name: str):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)

# 优化的Chroma配置
if Settings:
    OPTIMIZED_CHROMA_SETTINGS = Settings(
        anonymized_telemetry=False,
        persist_directory=str(Path(os.environ.get("CHROMA_DB_DIR", "db/chroma_db"))),
        chroma_db_impl="duckdb+parquet",
        persist_directory_auto_create=True,
        allow_reset=True,
    )


class OptimizedChromaStore:
    """优化的ChromaDB接口"""
    
    def __init__(self, persist_directory: Optional[str] = None, 
                collection_name: str = "documents",
                embedding_function = None,
                distance_metric: str = "cosine"):
        """
        初始化ChromaDB存储
        """
        if not chromadb:
            raise ImportError("chromadb is not installed. Please install it with: pip install chromadb")
            
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function
        self.collection_name = collection_name
        self.distance_metric = distance_metric
        
        # 初始化客户端
        if persist_directory:
            settings = Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False,
                chroma_db_impl="duckdb+parquet",
                persist_directory_auto_create=True
            )
            self.client = chromadb.PersistentClient(path=persist_directory, settings=settings)
        else:
            self.client = chromadb.Client(OPTIMIZED_CHROMA_SETTINGS)
        
        # 初始化或获取集合
        try:
            self.collection = self.client.get_collection(
                name=collection_name, 
                embedding_function=embedding_function
            )
            logger.info(f"Found existing collection: {collection_name}")
        except ValueError:
            self.collection = self.client.create_collection(
                name=collection_name, 
                embedding_function=embedding_function,
                metadata={"hnsw:space": distance_metric}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        # 批处理配置
        self.batch_size = 100
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # 查询参数优化
        self.default_query_params = {
            "k": 20,
            "n_results_to_get": 40,
            "fetch_k": 100,
            "min_score": 0.6,
            "alpha": 0.5,
            "include_values": True,
            "max_time_ms": 5000
        }
        
        logger.info(f"OptimizedChromaStore initialized with {collection_name}")

    @cached(ttl=300, prefix="chroma_count")
    async def count(self) -> int:
        """获取集合中的文档数量"""
        start_time = time.time()
        count = self.collection.count()
        duration = time.time() - start_time
        
        log_performance("vector_db_count_time", duration)
        return count

    @cached(ttl=3600, prefix="chroma_get")
    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """获取单个文档"""
        start_time = time.time()
        result = self.collection.get(ids=[document_id], include=["documents", "metadatas", "embeddings"])
        duration = time.time() - start_time
        
        log_performance("vector_db_get_time", duration, {"document_id": document_id})
        
        if not result["ids"]:
            return {}
            
        return {
            "id": result["ids"][0],
            "document": result["documents"][0],
            "metadata": result["metadatas"][0],
            "embedding": result["embeddings"][0] if result["embeddings"] else None
        }

    async def add_documents(self, documents: List[str], 
                          metadatas: Optional[List[Dict[str, Any]]] = None,
                          ids: Optional[List[str]] = None,
                          embeddings: Optional[List[List[float]]] = None) -> List[str]:
        """批量添加文档"""
        if len(documents) == 0:
            return []
            
        # 如果没有提供ID，则生成
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        # 批量处理
        total_docs = len(documents)
        start_time = time.time()
        all_ids = []
        
        for i in range(0, total_docs, self.batch_size):
            batch_docs = documents[i:i+self.batch_size]
            batch_ids = ids[i:i+self.batch_size]
            batch_meta = None if metadatas is None else metadatas[i:i+self.batch_size]
            batch_embeds = None if embeddings is None else embeddings[i:i+self.batch_size]
            
            # 带重试的批量添加
            for retry in range(self.max_retries):
                try:
                    self.collection.add(
                        documents=batch_docs,
                        metadatas=batch_meta,
                        ids=batch_ids,
                        embeddings=batch_embeds
                    )
                    all_ids.extend(batch_ids)
                    break
                except Exception as e:
                    if retry == self.max_retries - 1:
                        logger.error(f"Failed to add documents after {self.max_retries} retries: {e}")
                        raise
                    await asyncio.sleep(self.retry_delay * (retry + 1))
                    
        duration = time.time() - start_time
        
        # 记录性能指标
        log_performance(
            "vector_db_add_time", 
            duration, 
            {"total_docs": total_docs, "batches": (total_docs + self.batch_size - 1) // self.batch_size}
        )
        
        # 提交更改
        self.client.persist()
        
        # 清除相关缓存
        cache_key = CacheKey.generate("chroma_count", collection=self.collection_name)
        await memory_cache.delete(cache_key)
        
        return all_ids

    @time_it("optimized_chroma.similarity_search")
    async def similarity_search(self, 
                              query: Union[str, List[float]], 
                              k: Optional[int] = None,
                              filter: Optional[Dict[str, Any]] = None,
                              **kwargs) -> List[Dict[str, Any]]:
        """相似度搜索"""
        # 合并查询参数
        params = {**self.default_query_params}
        if k is not None:
            params["k"] = k
        params.update(kwargs)
        
        # 最多获取更多结果，用于后处理
        n_results = params.get("n_results_to_get", params["k"] * 2)
        
        try:
            if isinstance(query, str) and self.embedding_function:
                # 文本查询，使用嵌入函数
                embedding = self.embedding_function([query])[0]
                results = self.collection.query(
                    query_embeddings=[embedding],
                    n_results=n_results,
                    where=filter,
                    include=["documents", "metadatas", "distances"]
                )
            elif isinstance(query, list) and all(isinstance(x, (int, float)) for x in query):
                # 向量查询
                results = self.collection.query(
                    query_embeddings=[query],
                    n_results=n_results,
                    where=filter,
                    include=["documents", "metadatas", "distances"]
                )
            else:
                raise ValueError("Query must be either a string or a list of floats")
                
            # 后处理筛选
            documents = []
            min_score = params.get("min_score", 0.0)
            
            # 调整距离值为相似度分数（距离越小，相似度越高）
            for i, (doc_id, document, metadata, distance) in enumerate(zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                # 将距离转换为相似度分数（余弦距离）
                similarity = 1.0 - distance if self.distance_metric == "cosine" else distance
                
                if similarity >= min_score:
                    documents.append({
                        "id": doc_id,
                        "document": document,
                        "metadata": metadata,
                        "score": similarity,
                        "rank": i + 1
                    })
                
                # 限制返回数量    
                if len(documents) >= params["k"]:
                    break
                    
            return documents
                
        except Exception as e:
            logger.error(f"Error during similarity search: {e}")
            return []

    def optimize_index(self):
        """优化索引结构以提高查询性能"""
        start_time = time.time()
        try:
            self.client.persist()
            duration = time.time() - start_time
            log_performance("vector_db_optimize_time", duration)
            return True
        except Exception as e:
            logger.error(f"Error optimizing index: {e}")
            return False

    def clear(self):
        """清空集合"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name, 
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": self.distance_metric}
            )
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False
            
    async def close(self):
        """关闭客户端连接"""
        try:
            self.client.persist()
        except Exception as e:
            logger.error(f"Error closing vector store: {e}")
