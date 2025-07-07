"""
Agent 服务的 API 路由
提供Agent操作的RESTful接口
"""
from typing import Dict, List, Any, Optional
try:
    from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
    from pydantic import BaseModel, Field
except ImportError:
    # 备用实现
    class APIRouter:
        def __init__(self, prefix="", tags=None, responses=None):
            self.prefix = prefix
            self.tags = tags or []
            self.responses = responses or {}
    
    class BaseModel:
        pass
    
    def Field(default, description=""):
        return default
    
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
    
    class BackgroundTasks:
        def add_task(self, func, *args):
            pass

try:
    from app.services.agent_service import AgentService, get_agent_service
    from app.core.logging_config import log_performance
except ImportError:
    AgentService = None
    
    async def get_agent_service():
        return None
    
    def log_performance(metric_name: str, value: float, context: Optional[Dict[str, Any]] = None):
        pass

router = APIRouter(
    tags=["agents"],
    responses={404: {"description": "未找到"}}
)

# 请求模型
class ProfileGenerationRequest(BaseModel):
    """企业画像生成请求"""
    user_id: str = Field(..., description="用户ID")
    conversation_id: Optional[str] = Field(None, description="对话ID，如不提供则自动生成")
    company_name: Optional[str] = Field(None, description="公司名称")
    initial_info: Optional[Dict[str, Any]] = Field(None, description="初始企业信息")


class MessageRequest(BaseModel):
    """消息请求"""
    conversation_id: str = Field(..., description="对话ID")
    user_id: str = Field(..., description="用户ID")
    response: str = Field(..., description="用户的回复")
    context: Optional[Dict[str, Any]] = Field(None, description="消息上下文")


# 响应模型
class ProfileResponse(BaseModel):
    """企业画像生成响应"""
    type: str = Field(..., description="响应类型")
    conversation_id: str = Field(..., description="对话ID")
    question: Optional[str] = Field(None, description="下一个问题")
    company_profile: Optional[Dict[str, Any]] = Field(None, description="生成的企业画像")
    progress: Optional[str] = Field(None, description="进度信息")
    stage: str = Field(..., description="当前阶段")
    next_action: Optional[str] = Field(None, description="建议的下一步操作")


class AgentStatusResponse(BaseModel):
    """Agent状态响应"""
    agent_id: str = Field(..., description="Agent ID")
    is_running: bool = Field(..., description="是否运行中")
    error_stats: Dict[str, Any] = Field(..., description="错误统计")
    handlers_count: int = Field(..., description="处理器数量")
    profile_conversations_active: int = Field(..., description="活动中的企业画像对话数量")


@router.post("/profile/start", response_model=ProfileResponse)
async def start_profile_generation(
    request: ProfileGenerationRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    启动企业画像生成流程
    """
    try:
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent服务不可用")
            
        start_response = await agent_service.start_profile_generation(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            company_name=request.company_name,
            initial_info=request.initial_info
        )
        return start_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动企业画像生成失败: {str(e)}")


@router.post("/profile/message", response_model=ProfileResponse)
async def handle_profile_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    处理企业画像生成过程中的消息
    """
    try:
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent服务不可用")
            
        response = await agent_service.handle_profile_message(
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            user_response=request.response,
            context=request.context,
            background_tasks=background_tasks
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")


@router.get("/profile/{conversation_id}/status", response_model=Dict[str, Any])
async def get_profile_status(
    conversation_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    获取企业画像生成状态
    """
    if not agent_service:
        raise HTTPException(status_code=503, detail="Agent服务不可用")
        
    status = await agent_service.get_profile_status(conversation_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"未找到对话 {conversation_id}")
    return status


@router.get("/status", response_model=List[AgentStatusResponse])
async def get_all_agents_status(
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    获取所有Agent的状态
    """
    if not agent_service:
        raise HTTPException(status_code=503, detail="Agent服务不可用")
        
    return await agent_service.get_all_agents_status()


@router.get("/{agent_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    获取指定Agent的状态
    """
    if not agent_service:
        raise HTTPException(status_code=503, detail="Agent服务不可用")
        
    status = await agent_service.get_agent_status(agent_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"未找到Agent {agent_id}")
    return status


@router.post("/{agent_id}/reset", response_model=Dict[str, str])
async def reset_agent(
    agent_id: str,
    background_tasks: BackgroundTasks,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    重置Agent状态
    """
    try:
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent服务不可用")
            
        background_tasks.add_task(agent_service.reset_agent, agent_id)
        return {"message": f"Agent {agent_id} 重置操作已安排"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置Agent失败: {str(e)}")


# 健康检查端点
@router.get("/health")
async def health_check():
    """
    Agent服务健康检查
    """
    return {
        "status": "healthy",
        "service": "agent_service",
        "message": "Agent服务运行正常"
    }
