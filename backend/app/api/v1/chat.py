"""
Chat API - 集成知识库搜索的智能聊天接口
支持基于私有知识库的对话增强
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.services.agent_service import get_agent_service, AgentService
from app.agents.knowledge_enhanced_agent import create_knowledge_enhanced_agent
from app.tools.knowledge_search_tool import create_knowledge_search_tool
from app.core.response import APIResponse, create_response
from app.bus.schemas import A2AMessage, MessageType
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


# ========== 请求/响应模型 ==========

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    user_id: str = Field(..., description="用户ID") 
    use_knowledge: bool = Field(True, description="是否启用知识库搜索")
    knowledge_filters: Optional[Dict[str, Any]] = Field(None, description="知识库搜索过滤条件")


class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    user_id: str = Field(..., description="用户ID")
    n_results: int = Field(5, description="返回结果数量", ge=1, le=20)
    document_types: Optional[List[str]] = Field(None, description="文档类型过滤")
    category_filter: Optional[str] = Field(None, description="分类过滤")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: str = Field(..., description="AI回复消息")
    conversation_id: str = Field(..., description="对话ID")
    has_knowledge_context: bool = Field(False, description="是否包含知识库上下文")
    knowledge_sources: List[str] = Field(default=[], description="知识来源")
    suggestions: List[str] = Field(default=[], description="建议问题")
    timestamp: str = Field(..., description="时间戳")


class KnowledgeSearchResponse(BaseModel):
    """知识库搜索响应模型"""
    results: str = Field(..., description="格式化的搜索结果")
    query: str = Field(..., description="搜索查询")
    found_results: bool = Field(..., description="是否找到结果")
    timestamp: str = Field(..., description="时间戳")


# ========== API接口 ==========

@router.post("/send", response_model=APIResponse[ChatResponse])
async def send_chat_message(
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    发送聊天消息
    
    支持知识库增强的智能对话，当用户询问关于公司文档、政策等问题时，
    自动搜索私有知识库并提供基于文档内容的准确回答。
    """
    try:
        conversation_id = request.conversation_id or f"chat_{datetime.now().timestamp()}"
        
        # 创建知识库增强Agent
        knowledge_agent = create_knowledge_enhanced_agent("chat_knowledge_agent")
        
        # 创建消息
        message = A2AMessage(
            message_id=f"chat_{datetime.now().timestamp()}",
            conversation_id=conversation_id,
            task_id=conversation_id,
            from_agent="user",
            to_agent="chat_knowledge_agent",
            message_type=MessageType.REQUEST,
            action="enhanced_chat",
            payload={
                "question": request.message,
                "user_id": request.user_id,
                "use_knowledge": request.use_knowledge,
                "knowledge_filters": request.knowledge_filters or {}
            },
            context={"user_id": request.user_id},
            timestamp=None,
            priority="normal"
        )
        
        # 处理消息
        agent_response = await knowledge_agent._process_message(message)
        
        # 解析响应
        if agent_response.get("type") == "enhanced_chat_response":
            # 知识库增强的回答
            chat_response = ChatResponse(
                message=agent_response.get("response", ""),
                conversation_id=conversation_id,
                has_knowledge_context=True,
                knowledge_sources=agent_response.get("knowledge_sources", []),
                suggestions=_generate_follow_up_suggestions(request.message),
                timestamp=datetime.now().isoformat()
            )
        elif agent_response.get("type") == "regular_chat_response":
            # 常规回答（需要调用基础LLM）
            regular_response = await _handle_regular_chat(request.message, request.user_id)
            chat_response = ChatResponse(
                message=regular_response,
                conversation_id=conversation_id,
                has_knowledge_context=False,
                knowledge_sources=[],
                suggestions=_generate_follow_up_suggestions(request.message),
                timestamp=datetime.now().isoformat()
            )
        else:
            # 错误响应
            error_msg = agent_response.get("error", "处理聊天消息时发生未知错误")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"✅ Chat message processed: {request.message[:50]}...")
        return create_response(chat_response)
        
    except Exception as e:
        logger.error(f"❌ Chat message failed: {e}")
        raise HTTPException(status_code=500, detail=f"聊天消息处理失败: {str(e)}")


@router.post("/search-knowledge", response_model=APIResponse[KnowledgeSearchResponse])
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    搜索知识库
    
    直接搜索用户的私有知识库，获取相关文档信息。
    可以指定文档类型和分类进行精确搜索。
    """
    try:
        # 创建知识库搜索工具
        search_tool = create_knowledge_search_tool(request.user_id)
        
        # 执行搜索
        search_results = await search_tool.search(
            query=request.query,
            n_results=request.n_results,
            document_types=request.document_types,
            category_filter=request.category_filter
        )
        
        # 判断是否找到结果
        found_results = not ("抱歉" in search_results or "没有找到" in search_results)
        
        response = KnowledgeSearchResponse(
            results=search_results,
            query=request.query,
            found_results=found_results,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Knowledge search completed: '{request.query}' -> {found_results}")
        return create_response(response)
        
    except Exception as e:
        logger.error(f"❌ Knowledge search failed: {e}")
        raise HTTPException(status_code=500, detail=f"知识库搜索失败: {str(e)}")


@router.get("/knowledge-context/{user_id}")
async def get_knowledge_context(
    user_id: str,
    query: str,
    n_results: int = 3
):
    """
    获取知识库上下文
    
    为特定查询获取相关的知识库上下文信息，用于增强对话。
    """
    try:
        # 创建知识库增强Agent
        knowledge_agent = create_knowledge_enhanced_agent("context_agent")
        
        # 创建获取上下文的消息
        message = A2AMessage(
            message_id=f"context_{datetime.now().timestamp()}",
            conversation_id=f"context_{user_id}",
            task_id=f"context_{user_id}",
            from_agent="user",
            to_agent="context_agent",
            message_type=MessageType.REQUEST,
            action="get_knowledge_context",
            payload={
                "query": query,
                "user_id": user_id,
                "n_results": n_results
            },
            context={"user_id": user_id},
            timestamp=None,
            priority="normal"
        )
        
        # 处理消息
        agent_response = await knowledge_agent._process_message(message)
        
        logger.info(f"✅ Knowledge context retrieved for: {query}")
        return create_response(agent_response)
        
    except Exception as e:
        logger.error(f"❌ Get knowledge context failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取知识库上下文失败: {str(e)}")


@router.get("/suggestions/{user_id}")
async def get_chat_suggestions(user_id: str):
    """
    获取聊天建议
    
    基于用户的知识库内容，生成相关的问题建议。
    """
    try:
        # 这里可以基于用户的文档内容生成智能建议
        # 暂时返回一些通用建议
        suggestions = [
            "我们公司的ESG政策是什么？",
            "请介绍一下公司的环境保护措施",
            "公司的治理结构是怎样的？",
            "有哪些社会责任项目？",
            "可持续发展目标是什么？"
        ]
        
        return create_response({
            "suggestions": suggestions,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Get chat suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=f"获取聊天建议失败: {str(e)}")


# ========== 辅助函数 ==========

def _generate_follow_up_suggestions(user_message: str) -> List[str]:
    """
    根据用户消息生成后续问题建议
    
    Args:
        user_message: 用户消息
        
    Returns:
        建议问题列表
    """
    # 基于关键词生成相关建议
    if "ESG" in user_message.upper():
        return [
            "ESG评估的具体流程是什么？",
            "公司在ESG方面有哪些改进计划？",
            "如何提高ESG评分？"
        ]
    elif any(keyword in user_message for keyword in ["环境", "环保", "绿色"]):
        return [
            "公司的碳减排目标是什么？",
            "有哪些环保技术和措施？",
            "环境管理体系如何运作？"
        ]
    elif any(keyword in user_message for keyword in ["社会", "员工", "社区"]):
        return [
            "员工培训和发展计划如何？",
            "公司如何参与社区建设？",
            "多元化和包容性政策是什么？"
        ]
    elif any(keyword in user_message for keyword in ["治理", "管理", "风险"]):
        return [
            "公司治理结构是怎样的？",
            "风险管理机制如何？",
            "合规管理体系如何运作？"
        ]
    else:
        return [
            "还有其他相关问题吗？",
            "需要更详细的信息吗？",
            "想了解其他方面的内容吗？"
        ]


async def _handle_regular_chat(message: str, user_id: str) -> str:
    """
    处理常规聊天（不需要知识库的对话）
    
    Args:
        message: 用户消息
        user_id: 用户ID
        
    Returns:
        AI回复
    """
    # 这里可以调用基础的LLM API来生成回答
    # 暂时返回一个简单的回复
    return (
        f"您好！我是ESG智能助手。关于您的问题「{message}」，"
        "我可以为您提供帮助。如果您有关于公司文档、政策或ESG相关的具体问题，"
        "我可以搜索您的知识库来提供更准确的答案。请告诉我您想了解什么？"
    ) 