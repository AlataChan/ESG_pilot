"""
知识库搜索工具
为Agent提供从私有知识库中检索相关信息的能力
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from app.vector_store.chroma_db import get_chroma_manager
from app.services.knowledge_service import get_knowledge_service

logger = logging.getLogger(__name__)


class KnowledgeSearchTool:
    """
    知识库搜索工具
    
    允许Agent从私有知识库中搜索相关信息来回答用户问题。
    使用向量相似度搜索和元数据过滤来提供精准的检索结果。
    """
    
    def __init__(self, user_id: Optional[str] = None):
        """
        初始化知识库搜索工具
        
        Args:
            user_id: 用户ID，用于访问用户特定的知识库
        """
        self.user_id = user_id
        self.name = "knowledge_search"
        self.description = """
        搜索私有知识库以获取相关信息。
        
        使用这个工具当：
        1. 用户询问关于公司特定文档、政策或报告的问题
        2. 需要引用内部知识库中的具体信息
        3. 回答需要基于已上传文档的内容
        
        输入应该是用户问题的核心关键词或短语。
        """
        self.chroma_manager = None
        self.knowledge_service = None
        
    async def _ainit_components(self):
        """异步初始化组件"""
        if not self.chroma_manager:
            self.chroma_manager = get_chroma_manager()
        if not self.knowledge_service:
            self.knowledge_service = get_knowledge_service()
    
    async def search(self, query: str, n_results: int = 5,
                    document_types: Optional[List[str]] = None,
                    category_filter: Optional[str] = None) -> str:
        """
        执行知识库搜索
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            document_types: 文档类型过滤
            category_filter: 分类过滤
            
        Returns:
            格式化的搜索结果字符串
        """
        try:
            await self._ainit_components()
            
            logger.info(f"🔍 Knowledge search initiated: '{query}' (n_results={n_results})")
            
            # 执行向量搜索
            search_results = await self._vector_search(
                query, n_results, document_types, category_filter
            )
            
            if not search_results or len(search_results.get('documents', [[]])[0]) == 0:
                logger.info(f"📭 No relevant documents found for query: '{query}'")
                return self._format_no_results_response(query)
            
            # 格式化搜索结果
            formatted_results = await self._format_search_results(search_results, query)
            
            logger.info(f"✅ Knowledge search completed: {len(search_results['documents'][0])} results found")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Knowledge search failed: {e}")
            return f"抱歉，在搜索知识库时遇到错误：{str(e)}"
    
    async def _vector_search(self, query: str, n_results: int,
                           document_types: Optional[List[str]] = None,
                           category_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        执行向量相似度搜索
        
        Args:
            query: 搜索查询
            n_results: 结果数量
            document_types: 文档类型过滤
            category_filter: 分类过滤
            
        Returns:
            ChromaDB查询结果
        """
        try:
            # 构建查询过滤条件
            where_filter = {}
            
            if self.user_id:
                where_filter["user_id"] = self.user_id
            
            if document_types:
                where_filter["file_type"] = {"$in": document_types}
            
            if category_filter:
                where_filter["category_id"] = category_filter
            
            # 只搜索已完成处理的文档
            where_filter["status"] = "completed"
            
            # 执行向量搜索
            if where_filter:
                results = self.chroma_manager.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter
                )
            else:
                results = self.chroma_manager.query(query, n_results)
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def _format_search_results(self, search_results: Dict[str, Any], query: str) -> str:
        """
        格式化搜索结果为可读的文本
        
        Args:
            search_results: ChromaDB搜索结果
            query: 原始查询
            
        Returns:
            格式化的结果字符串
        """
        try:
            documents = search_results.get('documents', [[]])[0]
            metadatas = search_results.get('metadatas', [[]])[0]
            distances = search_results.get('distances', [[]])[0]
            
            if not documents:
                return self._format_no_results_response(query)
            
            # 构建结果字符串
            result_parts = [
                f"基于知识库搜索 \"{query}\"，找到以下相关信息：\n"
            ]
            
            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                # 计算相似度得分（距离越小，相似度越高）
                similarity_score = max(0, 1 - distance) if distance is not None else 0
                
                # 获取文档信息
                filename = metadata.get('filename', '未知文档')
                doc_type = metadata.get('file_type', '').upper()
                page_info = f"第{metadata.get('page_number', 'N/A')}页" if metadata.get('page_number') else ""
                
                # 截断文档内容
                content = doc[:500] + "..." if len(doc) > 500 else doc
                
                result_parts.append(
                    f"📄 **来源{i+1}**: {filename} ({doc_type}) {page_info}\n"
                    f"🎯 **相关度**: {similarity_score:.2%}\n"
                    f"📝 **内容摘录**:\n{content}\n"
                    f"{'─' * 50}\n"
                )
            
            # 添加使用说明
            result_parts.append(
                "\n💡 **说明**: 以上信息来自您的私有知识库。"
                "如需查看完整文档或更多详细信息，请使用文档管理功能。"
            )
            
            return "\n".join(result_parts)
            
        except Exception as e:
            logger.error(f"格式化搜索结果失败: {e}")
            return f"搜索到相关信息，但格式化时遇到错误：{str(e)}"
    
    def _format_no_results_response(self, query: str) -> str:
        """格式化无结果的响应"""
        return (
            f"抱歉，在您的知识库中没有找到与 \"{query}\" 相关的信息。\n\n"
            "💡 **建议**:\n"
            "• 尝试使用不同的关键词或表达方式\n"
            "• 确认相关文档已经上传并完成处理\n"
            "• 检查文档分类和访问权限设置\n"
            "• 可以先上传相关文档到知识库，然后再次提问"
        )


def create_knowledge_search_tool(user_id: Optional[str] = None) -> KnowledgeSearchTool:
    """
    创建知识库搜索工具实例
    
    Args:
        user_id: 用户ID
        
    Returns:
        KnowledgeSearchTool实例
    """
    return KnowledgeSearchTool(user_id=user_id) 