"""
知识库增强Agent
集成知识库搜索能力，为Chat模块提供基于私有知识库的智能回答
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.tools.knowledge_search_tool import create_knowledge_search_tool
from app.bus.schemas import A2AMessage, MessageType
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeEnhancedAgent(BaseAgent):
    """
    知识库增强Agent
    
    专门处理需要从私有知识库中检索信息的对话。
    当用户询问关于公司文档、政策或内部资料时，此Agent会搜索知识库并提供准确答案。
    """
    
    def __init__(self, agent_id: str = "knowledge_enhanced_agent"):
        """
        初始化知识库增强Agent
        
        Args:
            agent_id: Agent标识符
        """
        super().__init__(agent_id)
        self.knowledge_search_tool = None
        self.current_user_id = None
        
        # Agent特性
        self.capabilities = [
            "knowledge_search",           # 知识库搜索
            "document_reference",         # 文档引用
            "context_aware_response",     # 上下文感知回答
            "source_citation",           # 来源引用
        ]
        
        self.personality = {
            "helpful": True,              # 乐于助人
            "accurate": True,            # 准确性优先
            "detail_oriented": True,     # 注重细节
            "citation_focused": True,    # 重视引用来源
        }
        
        logger.info(f"🧠 {self.agent_id} initialized with knowledge search capabilities")
    
    async def _setup_tools(self, user_id: Optional[str] = None):
        """
        设置工具，包括知识库搜索工具
        
        Args:
            user_id: 用户ID，用于个性化知识库访问
        """
        try:
            if user_id:
                self.current_user_id = user_id
                self.knowledge_search_tool = create_knowledge_search_tool(user_id)
                logger.info(f"🔧 Knowledge search tool setup for user: {user_id}")
            else:
                logger.warning("⚠️ No user_id provided, knowledge search may be limited")
                
        except Exception as e:
            logger.error(f"❌ Failed to setup tools: {e}")
            raise
    
    async def _process_message(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理消息，重点是知识库相关的查询
        
        Args:
            message: 接收到的消息
            
        Returns:
            处理结果
        """
        try:
            # 获取用户信息并设置工具
            user_id = message.context.get("user_id") or message.payload.get("user_id")
            if user_id and user_id != self.current_user_id:
                await self._setup_tools(user_id)
            
            action = message.action
            payload = message.payload
            
            if action == "search_knowledge":
                return await self._handle_knowledge_search(message)
            elif action == "enhanced_chat":
                return await self._handle_enhanced_chat(message)
            elif action == "get_knowledge_context":
                return await self._handle_get_knowledge_context(message)
            else:
                return await self._handle_general_query(message)
                
        except Exception as e:
            logger.error(f"❌ Message processing failed: {e}")
            return {
                "type": "error",
                "error": f"处理消息时发生错误: {str(e)}",
                "agent_id": self.agent_id
            }
    
    async def _handle_knowledge_search(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理知识库搜索请求
        
        Args:
            message: 包含搜索查询的消息
            
        Returns:
            搜索结果
        """
        try:
            query = message.payload.get("query", "")
            n_results = message.payload.get("n_results", 5)
            document_types = message.payload.get("document_types")
            category_filter = message.payload.get("category_filter")
            
            if not query:
                return {
                    "type": "error",
                    "error": "搜索查询不能为空",
                    "agent_id": self.agent_id
                }
            
            # 检查工具是否已设置
            if not self.knowledge_search_tool:
                return {
                    "type": "error", 
                    "error": "知识库搜索工具未初始化，请先设置用户信息",
                    "agent_id": self.agent_id
                }
            
            # 执行搜索
            search_results = await self.knowledge_search_tool.search(
                query=query,
                n_results=n_results,
                document_types=document_types,
                category_filter=category_filter
            )
            
            return {
                "type": "knowledge_search_result",
                "results": search_results,
                "query": query,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Knowledge search failed: {e}")
            return {
                "type": "error",
                "error": f"知识库搜索失败: {str(e)}",
                "agent_id": self.agent_id
            }
    
    async def _handle_enhanced_chat(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理增强聊天请求（结合知识库的对话）
        
        Args:
            message: 包含用户问题的消息
            
        Returns:
            增强的聊天回答
        """
        try:
            user_question = message.payload.get("question", "")
            if not user_question:
                return {
                    "type": "error",
                    "error": "用户问题不能为空",
                    "agent_id": self.agent_id
                }
            
            # 首先检查是否需要搜索知识库
            if await self._should_search_knowledge(user_question):
                # 执行知识库搜索
                knowledge_context = await self._get_knowledge_context(user_question)
                
                if knowledge_context:
                    # 生成基于知识库的回答
                    enhanced_response = await self._generate_knowledge_based_response(
                        user_question, knowledge_context
                    )
                    
                    return {
                        "type": "enhanced_chat_response",
                        "response": enhanced_response,
                        "has_knowledge_context": True,
                        "knowledge_sources": knowledge_context.get("sources", []),
                        "agent_id": self.agent_id,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 如果不需要知识库搜索，返回常规回答指示
            return {
                "type": "regular_chat_response",
                "message": "此问题不需要查询知识库，可以直接回答",
                "has_knowledge_context": False,
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced chat failed: {e}")
            return {
                "type": "error",
                "error": f"增强聊天处理失败: {str(e)}",
                "agent_id": self.agent_id
            }
    
    async def _should_search_knowledge(self, question: str) -> bool:
        """
        判断问题是否需要搜索知识库
        
        Args:
            question: 用户问题
            
        Returns:
            是否需要搜索知识库
        """
        # 定义需要搜索的关键词和模式
        knowledge_keywords = [
            "文档", "报告", "政策", "规定", "制度", "流程",
            "公司", "企业", "组织", "部门", "团队",
            "ESG", "环境", "社会", "治理", "可持续",
            "合规", "审计", "风险", "内控",
            "什么是", "如何", "为什么", "介绍一下", "详细说明"
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in knowledge_keywords)
    
    async def _get_knowledge_context(self, question: str) -> Optional[Dict[str, Any]]:
        """
        获取问题相关的知识库上下文
        
        Args:
            question: 用户问题
            
        Returns:
            知识库上下文信息
        """
        try:
            if not self.knowledge_search_tool:
                return None
            
            # 搜索知识库
            search_results = await self.knowledge_search_tool.search(
                query=question,
                n_results=3  # 获取最相关的3个结果作为上下文
            )
            
            if "抱歉" in search_results or "没有找到" in search_results:
                return None
            
            return {
                "context": search_results,
                "sources": ["知识库搜索结果"],  # 可以进一步解析具体来源
                "confidence": "high"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get knowledge context: {e}")
            return None
    
    async def _generate_knowledge_based_response(self, question: str, 
                                               knowledge_context: Dict[str, Any]) -> str:
        """
        基于知识库上下文生成回答
        
        Args:
            question: 用户问题
            knowledge_context: 知识库上下文
            
        Returns:
            基于知识库的回答
        """
        try:
            context_text = knowledge_context.get("context", "")
            
            # 构建增强的回答
            response_parts = [
                f"基于您的知识库，我为您找到了以下相关信息：\n",
                context_text,
                "\n📋 **答案总结**:\n",
                "根据上述文档内容，针对您的问题，我可以提供以下回答：",
                "\n💡 **建议**: 如需了解更多详细信息，请查看相关文档或联系相关部门。"
            ]
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"❌ Failed to generate knowledge-based response: {e}")
            return f"基于知识库的回答生成失败: {str(e)}"
    
    async def _handle_get_knowledge_context(self, message: A2AMessage) -> Dict[str, Any]:
        """
        获取知识库上下文信息
        
        Args:
            message: 请求消息
            
        Returns:
            上下文信息
        """
        try:
            query = message.payload.get("query", "")
            context = await self._get_knowledge_context(query)
            
            return {
                "type": "knowledge_context",
                "context": context,
                "query": query,
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            logger.error(f"❌ Get knowledge context failed: {e}")
            return {
                "type": "error",
                "error": f"获取知识库上下文失败: {str(e)}",
                "agent_id": self.agent_id
            }
    
    async def _handle_general_query(self, message: A2AMessage) -> Dict[str, Any]:
        """
        处理一般查询
        
        Args:
            message: 查询消息
            
        Returns:
            查询结果
        """
        return {
            "type": "general_response",
            "message": f"Knowledge Enhanced Agent ({self.agent_id}) 已收到您的查询",
            "capabilities": self.capabilities,
            "agent_id": self.agent_id
        }


def create_knowledge_enhanced_agent(agent_id: str = None) -> KnowledgeEnhancedAgent:
    """
    创建知识库增强Agent实例
    
    Args:
        agent_id: Agent标识符
        
    Returns:
        KnowledgeEnhancedAgent实例
    """
    return KnowledgeEnhancedAgent(agent_id or "knowledge_enhanced_agent") 