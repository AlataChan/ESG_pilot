"""
RAG服务 - 检索增强生成智能问答系统
实现基于文档内容的精准问答，支持文档分块索引、语义匹配、答案生成和引用溯源

✅ Week 3: Enhanced with caching for LLM calls and vector searches
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio

from app.vector_store.chroma_db import get_chroma_manager
from app.services.document_processor import get_document_processor
from app.core.config import settings
from app.core.llm_factory import llm_factory
from app.core.cache import cached  # ✅ Week 3: Add caching support
from langchain.schema import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class DocumentChunk:
    """文档分块数据结构"""
    
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata
        self.chunk_id = metadata.get('chunk_id', '')
        self.document_id = metadata.get('document_id', '')
        self.page_number = metadata.get('page_number', 0)
        self.chunk_index = metadata.get('chunk_index', 0)
        self.similarity_score = 0.0
    
    def __str__(self):
        return f"Chunk({self.chunk_id}): {self.content[:100]}..."


class RAGAnswer:
    """RAG问答结果数据结构"""
    
    def __init__(self, question: str, answer: str, sources: List[DocumentChunk], 
                 confidence: float, reasoning: str = ""):
        self.question = question
        self.answer = answer
        self.sources = sources
        self.confidence = confidence
        self.reasoning = reasoning
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'question': self.question,
            'answer': self.answer,
            'sources': [
                {
                    'content': chunk.content,
                    'document_id': chunk.document_id,
                    'page_number': chunk.page_number,
                    'chunk_index': chunk.chunk_index,
                    'similarity_score': chunk.similarity_score,
                    'metadata': chunk.metadata
                }
                for chunk in self.sources
            ],
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat()
        }


class RAGService:
    """
    RAG服务 - 检索增强生成智能问答系统
    
    核心功能：
    1. 文档分块和索引
    2. 语义检索和匹配
    3. 上下文组装和答案生成
    4. 引用溯源和置信度评估
    """
    
    def __init__(self):
        """初始化RAG服务"""
        self.chroma_manager = None
        self.document_processor = None
        
        # RAG配置参数
        self.chunk_size = 500  # 文档分块大小
        self.chunk_overlap = 50  # 分块重叠大小
        self.max_context_length = 2000  # 最大上下文长度
        self.min_similarity_threshold = 0.3  # 最小相似度阈值
        self.max_retrieved_chunks = 5  # 最大检索分块数
        
        logger.info("🧠 RAG Service initialized")
    
    async def _init_components(self):
        """异步初始化组件"""
        if not self.chroma_manager:
            self.chroma_manager = get_chroma_manager()
        if not self.document_processor:
            self.document_processor = get_document_processor()

    @cached(ttl=3600, prefix="rag_answer")  # ✅ Week 3: Cache for 1 hour (saves 2-5s per request)
    async def answer_question(self, question: str, user_id: str,
                            document_id: Optional[str] = None,
                            document_type: Optional[str] = None) -> RAGAnswer:
        """
        基于文档内容回答问题 - ✅ Week 3: Cached to save expensive LLM calls

        Args:
            question: 用户问题
            user_id: 用户ID
            document_id: 特定文档ID（可选）
            document_type: 文档类型过滤（可选）

        Returns:
            RAGAnswer: 包含答案、来源和置信度的结果
        """
        try:
            await self._init_components()
            
            logger.info(f"🤔 RAG Question: '{question}' (user: {user_id})")
            
            # 1. 检索相关文档片段
            relevant_chunks = await self._retrieve_relevant_chunks(
                question, user_id, document_id, document_type
            )
            
            if not relevant_chunks:
                return self._generate_no_context_answer(question)
            
            # 2. 组装上下文
            context = await self._assemble_context(relevant_chunks, question)
            
            # 3. 生成答案
            answer_text = await self._generate_answer(question, context, relevant_chunks)
            
            # 4. 计算置信度
            confidence = self._calculate_confidence(relevant_chunks, answer_text)
            
            # 5. 生成推理解释
            reasoning = self._generate_reasoning(question, relevant_chunks, confidence)
            
            rag_answer = RAGAnswer(
                question=question,
                answer=answer_text,
                sources=relevant_chunks,
                confidence=confidence,
                reasoning=reasoning
            )
            
            logger.info(f"✅ RAG Answer generated (confidence: {confidence:.2%})")
            return rag_answer
            
        except Exception as e:
            logger.error(f"❌ RAG question answering failed: {e}")
            return self._generate_error_answer(question, str(e))
    
    @cached(ttl=1800, prefix="rag_chunks")  # ✅ Week 3: Cache vector search for 30 min
    async def _retrieve_relevant_chunks(self, question: str, user_id: str,
                                      document_id: Optional[str] = None,
                                      document_type: Optional[str] = None) -> List[DocumentChunk]:
        """
        检索相关文档片段 - ✅ Week 3: Cached to save expensive vector searches

        Args:
            question: 用户问题
            user_id: 用户ID
            document_id: 文档ID过滤
            document_type: 文档类型过滤

        Returns:
            相关文档片段列表
        """
        try:
            # 构建检索过滤条件
            where_filter = {
                "user_id": user_id,
                "status": "completed"
            }
            
            if document_id:
                where_filter["document_id"] = document_id
            
            if document_type:
                where_filter["file_type"] = document_type
            
            # 执行向量检索
            search_results = self.chroma_manager.collection.query(
                query_texts=[question],
                n_results=self.max_retrieved_chunks,
                where=where_filter
            )
            
            # 转换为DocumentChunk对象
            chunks = []
            if search_results.get('documents') and search_results['documents'][0]:
                documents = search_results['documents'][0]
                metadatas = search_results.get('metadatas', [[]])[0]
                distances = search_results.get('distances', [[]])[0]
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    # 计算相似度得分
                    similarity_score = max(0, 1 - distance) if distance is not None else 0
                    
                    # 过滤低相似度的结果
                    if similarity_score < self.min_similarity_threshold:
                        continue
                    
                    chunk = DocumentChunk(content=doc, metadata=metadata)
                    chunk.similarity_score = similarity_score
                    chunks.append(chunk)
            
            # 按相似度排序
            chunks.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"🔍 Retrieved {len(chunks)} relevant chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Chunk retrieval failed: {e}")
            return []
    
    async def _assemble_context(self, chunks: List[DocumentChunk], question: str) -> str:
        """
        组装问答上下文
        
        Args:
            chunks: 相关文档片段
            question: 用户问题
            
        Returns:
            组装后的上下文字符串
        """
        try:
            context_parts = []
            current_length = 0
            
            # 添加问题作为上下文的开头
            context_parts.append(f"问题: {question}\n")
            current_length += len(question) + 10
            
            context_parts.append("相关文档内容:\n")
            current_length += 20
            
            # 按相似度顺序添加文档片段
            for i, chunk in enumerate(chunks):
                # 构建片段信息
                source_info = f"[来源 {i+1}] "
                if chunk.metadata.get('filename'):
                    source_info += f"文档: {chunk.metadata['filename']}"
                if chunk.page_number:
                    source_info += f", 第{chunk.page_number}页"
                source_info += f" (相关度: {chunk.similarity_score:.1%})\n"
                
                chunk_content = f"{source_info}内容: {chunk.content}\n\n"
                
                # 检查长度限制
                if current_length + len(chunk_content) > self.max_context_length:
                    break
                
                context_parts.append(chunk_content)
                current_length += len(chunk_content)
            
            context = "".join(context_parts)
            logger.info(f"📝 Context assembled: {len(context)} characters")
            return context
            
        except Exception as e:
            logger.error(f"❌ Context assembly failed: {e}")
            return f"问题: {question}\n相关文档内容: [上下文组装失败]"
    
    async def _generate_answer(self, question: str, context: str,
                             sources: List[DocumentChunk]) -> str:
        """
        ✅ FIXED: 使用真正的LLM生成答案（DeepSeek AI）

        Args:
            question: 用户问题
            context: 组装的上下文
            sources: 来源文档片段

        Returns:
            生成的答案
        """
        try:
            # 创建LLM实例
            logger.info("🤖 Generating answer using DeepSeek AI...")
            llm = llm_factory.create_deepseek_llm(
                temperature=0.3,  # 较低温度保证准确性
                max_tokens=1500
            )

            # 构建结构化的文档上下文
            documents_context = "\n\n".join([
                f"【文档片段 {i+1}】\n来源: {chunk.metadata.get('filename', '未知')}\n"
                f"相关度: {chunk.similarity_score:.1%}\n"
                f"内容: {chunk.content}"
                for i, chunk in enumerate(sources)
            ])

            # 构建系统提示词
            system_prompt = """你是一位专业的ESG（环境、社会和治理）咨询专家，专门负责分析文档并回答用户关于ESG的问题。

你的职责：
1. 仔细阅读提供的文档内容
2. 基于文档内容准确回答用户问题
3. 如果文档中没有明确答案，坦诚说明并给出合理推断
4. 回答要专业、清晰、有条理
5. 涉及数据时要准确引用原文
6. 适当使用格式化（如项目符号、编号列表）提高可读性

回答要求：
- 直接回答问题，不要重复问题
- 基于事实，避免主观臆断
- 如引用具体数据，说明来源
- 保持专业和客观的语气"""

            user_prompt = f"""请基于以下文档内容回答问题。

# 用户问题
{question}

# 相关文档内容
{documents_context}

# 回答指南
- 综合所有文档片段的信息
- 给出准确、完整的答案
- 如果信息不足，请说明
- 保持逻辑清晰、结构分明"""

            # 调用LLM生成答案
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = llm.invoke(messages)
            answer = response.content.strip()

            logger.info(f"✅ LLM answer generated ({len(answer)} chars)")

            # 添加来源引用
            answer_with_sources = self._add_source_citations(answer, sources)

            return answer_with_sources

        except Exception as e:
            logger.error(f"❌ LLM answer generation failed: {e}")
            # 降级到基础模板回答
            return self._generate_fallback_answer(question, sources)
    
    def _generate_fallback_answer(self, question: str, sources: List[DocumentChunk]) -> str:
        """
        降级回答方法（当LLM调用失败时使用）
        """
        if not sources:
            return "抱歉，我在知识库中没有找到与您的问题相关的文档内容。"

        answer_parts = [
            f"根据知识库文档，关于您的问题「{question}」，我找到以下相关内容：\n"
        ]

        for i, source in enumerate(sources[:3], 1):
            filename = source.metadata.get('filename', '未知文档')
            answer_parts.append(f"**{i}. 来自《{filename}》**")
            answer_parts.append(f"{source.content.strip()}\n")

        answer_parts.append("\n⚠️ 注意：当前使用简化回答模式，可能不够精确。请稍后重试获取AI分析。")

        return "\n".join(answer_parts)
    
    def _add_source_citations(self, answer: str, sources: List[DocumentChunk]) -> str:
        """为答案添加来源引用"""
        if not sources:
            return answer
        
        citation_parts = [
            answer,
            "",
            "📚 **参考来源**:"
        ]
        
        for i, source in enumerate(sources):
            filename = source.metadata.get('filename', '未知文档')
            page_info = f"第{source.page_number}页" if source.page_number else ""
            similarity = f"相关度: {source.similarity_score:.1%}"
            
            citation = f"[{i+1}] {filename}"
            if page_info:
                citation += f" - {page_info}"
            citation += f" ({similarity})"
            
            citation_parts.append(citation)
        
        return "\n".join(citation_parts)
    
    def _calculate_confidence(self, sources: List[DocumentChunk], answer: str) -> float:
        """计算答案置信度"""
        if not sources:
            return 0.0
        
        # 基于多个因素计算置信度
        factors = []
        
        # 1. 平均相似度得分
        avg_similarity = sum(chunk.similarity_score for chunk in sources) / len(sources)
        factors.append(avg_similarity)
        
        # 2. 来源数量因子（更多来源通常意味着更高置信度，但有上限）
        source_count_factor = min(len(sources) / 3.0, 1.0)
        factors.append(source_count_factor)
        
        # 3. 最高相似度得分的权重
        max_similarity = max(chunk.similarity_score for chunk in sources)
        factors.append(max_similarity * 0.8)
        
        # 4. 答案长度因子（过短或过长的答案可能置信度较低）
        answer_length = len(answer)
        if 100 <= answer_length <= 1000:
            length_factor = 1.0
        elif answer_length < 100:
            length_factor = answer_length / 100.0
        else:
            length_factor = max(0.5, 1000.0 / answer_length)
        factors.append(length_factor)
        
        # 计算加权平均置信度
        weights = [0.4, 0.2, 0.3, 0.1]  # 各因子的权重
        confidence = sum(f * w for f, w in zip(factors, weights))
        
        return min(max(confidence, 0.0), 1.0)  # 确保在0-1范围内
    
    def _generate_reasoning(self, question: str, sources: List[DocumentChunk], 
                          confidence: float) -> str:
        """生成推理解释"""
        reasoning_parts = []
        
        if not sources:
            return "无法找到相关文档内容来回答问题。"
        
        # 检索情况说明
        reasoning_parts.append(f"检索到{len(sources)}个相关文档片段")
        
        # 相似度分析
        similarities = [chunk.similarity_score for chunk in sources]
        avg_sim = sum(similarities) / len(similarities)
        max_sim = max(similarities)
        
        reasoning_parts.append(f"平均相关度: {avg_sim:.1%}, 最高相关度: {max_sim:.1%}")
        
        # 置信度解释
        if confidence >= 0.8:
            reasoning_parts.append("高置信度：找到多个高度相关的文档片段")
        elif confidence >= 0.6:
            reasoning_parts.append("中等置信度：找到相关文档片段，但相关性有限")
        elif confidence >= 0.4:
            reasoning_parts.append("低置信度：文档片段相关性较弱")
        else:
            reasoning_parts.append("极低置信度：未找到高度相关的文档内容")
        
        return "；".join(reasoning_parts)
    
    def _generate_no_context_answer(self, question: str) -> RAGAnswer:
        """生成无上下文时的答案"""
        return RAGAnswer(
            question=question,
            answer="抱歉，我在您的知识库中没有找到与此问题相关的文档内容。请确认：\n"
                  "1. 相关文档已经上传并完成处理\n"
                  "2. 问题表述清晰且与文档内容相关\n"
                  "3. 尝试使用不同的关键词重新提问",
            sources=[],
            confidence=0.0,
            reasoning="未找到相关文档内容"
        )
    
    def _generate_error_answer(self, question: str, error_message: str) -> RAGAnswer:
        """生成错误时的答案"""
        return RAGAnswer(
            question=question,
            answer=f"处理您的问题时遇到错误：{error_message}。请稍后重试或联系技术支持。",
            sources=[],
            confidence=0.0,
            reasoning=f"系统错误: {error_message}"
        )


# 全局RAG服务实例
_rag_service_instance = None


def get_rag_service() -> RAGService:
    """获取RAG服务实例（单例模式）"""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService()
    return _rag_service_instance 
