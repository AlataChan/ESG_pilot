"""
Agent服务层 - 使用真正的AI Agent架构
提供Agent操作的高级接口和业务逻辑，完全移除硬编码逻辑
"""
import logging
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Union, Type
from fastapi import Depends

from app.bus import get_message_bus
from app.agents.base_agent import BaseAgent, AgentProcessingError
from app.agents.company_profile_agent import CompanyProfileAgent
from app.agents.esg_assessment_agent import ESGAssessmentAgent
from app.agents.esg_report_agent import ESGReportAgent
from app.bus import MessageBus, A2AMessage
from app.bus.schemas import MessageType
from app.core.logging_config import get_agent_logger, time_it
from app.core.cache import cached

try:
    from app.agents.base_agent import BaseAgent
    from app.agents.company_profile_agent import CompanyProfileAgent
    from app.agents.esg_assessment_agent import ESGAssessmentAgent
    from app.agents.esg_report_agent import ESGReportAgent
    from app.bus import MessageBus, A2AMessage
    from app.bus.schemas import MessageType
    from app.core.logging_config import get_agent_logger, time_it
    from app.core.cache import cached
except ImportError as e:
    # 备用实现
    logging.warning(f"Failed to import Agent modules: {e}")
    BaseAgent = None
    CompanyProfileAgent = None
    ESGAssessmentAgent = None
    ESGReportAgent = None
    MessageBus = None
    A2AMessage = None
    
    def get_agent_logger(agent_id: str):
        return logging.getLogger(agent_id)
    
    def time_it(func_name: str):
        def decorator(func):
            return func
        return decorator
    
    def cached(ttl=60, prefix="cache", key_builder=None):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)

# 使用类型别名以方便管理
AgentTypes = Union[Type[CompanyProfileAgent], Type[ESGAssessmentAgent], Type[ESGReportAgent]]

class AgentService:
    """
    Agent服务层 - 真正的AI-first架构
    
    提供Agent操作的高级接口，使用智能LLM驱动的Agent系统
    """
    
    def __init__(self, message_bus: Optional[MessageBus] = None):
        self.message_bus = message_bus
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = get_agent_logger("agent_service")
        self.logger.info("🚀 AgentService initialized with AI-first architecture")
        
    @time_it("agent_service.start_profile_generation")
    async def start_profile_generation(self, 
                                    user_id: str,
                                    conversation_id: Optional[str] = None,
                                    company_name: Optional[str] = None,
                                    initial_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        启动企业画像生成流程 - 使用智能CompanyProfileAgent
        
        Args:
            user_id: 用户ID
            conversation_id: 对话ID，如果未提供则自动生成
            company_name: 公司名称
            initial_info: 初始企业信息
            
        Returns:
            包含智能生成的第一个问题的响应
        """
        try:
            # 如果未提供对话ID，则生成一个
            if not conversation_id:
                conversation_id = f"profile_{uuid.uuid4()}"
            
            # 获取智能企业画像Agent
            profile_agent = await self._get_or_create_agent("company_profile")
            
            # 创建启动消息
            start_message = A2AMessage(
                message_id=f"start_{uuid.uuid4()}",
                conversation_id=conversation_id,
                task_id=str(uuid.uuid4()),
                from_agent="user",
                to_agent="company_profile",
                message_type=MessageType.REQUEST,
                action="start_profile_generation",
                payload={
                    "user_id": user_id,
                    "company_name": company_name,
                    "initial_info": initial_info or {}
                },
                context={"user_id": user_id},
                timestamp=None,
                priority="high"
            )
            
            # 处理启动请求
            response = await profile_agent._process_message(start_message)
            
            self.logger.info(
                f"✅ Started intelligent profile generation",
                extra={
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "company_name": company_name,
                    "agent_type": "CompanyProfileAgent"
                }
            )
            
            return response or {
                "type": "question",
                "conversation_id": conversation_id,
                "question": "我是您的AI企业画像顾问。让我们开始了解您的企业吧！请简单介绍一下您的公司：主要业务是什么？",
                "progress": "1/10 智能分析中",
                "stage": "开始阶段",
                "next_action": "回答问题"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start profile generation: {e}")
            return {
                "type": "error",
                "conversation_id": conversation_id,
                "error": str(e),
                "stage": "错误"
            }
    
    @time_it("agent_service.handle_profile_message")
    async def handle_profile_message(self,
                                   conversation_id: str,
                                   user_id: str,
                                   user_response: str,
                                   context: Optional[Dict[str, Any]] = None,
                                   background_tasks: Optional[Any] = None) -> Dict[str, Any]:
        """
        处理企业画像生成过程中的消息 - 使用智能对话管理
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            user_response: 用户的回答
            context: 消息上下文
            
        Returns:
            智能生成的下一个问题或企业画像结果
        """
        try:
            # 获取智能企业画像Agent
            profile_agent = await self._get_or_create_agent("company_profile")
            
            # 创建智能消息
            message = A2AMessage(
                message_id=f"msg_{uuid.uuid4()}",
                conversation_id=conversation_id,
                task_id=str(uuid.uuid4()),
                from_agent="user",
                to_agent="company_profile",
                message_type=MessageType.REQUEST,
                action="continue_profile_conversation",
                payload={
                    "response": user_response,
                    "user_id": user_id,
                    "context": context or {}
                },
                context={"user_id": user_id},
                timestamp=None,
                priority="normal"
            )
            
            # 智能处理消息
            response = await profile_agent._process_message(message)
            
            # 如果需要生成报告，则创建后台任务
            if response and response.get("type") == "generating" and background_tasks:
                self.logger.info(f"Scheduling background task for report generation: {conversation_id}")
                background_tasks.add_task(self.generate_profile_report, conversation_id, user_id)

            self.logger.info(
                f"✅ Handled profile message with AI",
                extra={
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "response_type": response.get("type") if response else "unknown",
                    "agent_type": "CompanyProfileAgent"
                }
            )
            
            return response or {
                "type": "question",
                "conversation_id": conversation_id,
                "question": "感谢您的回答！请继续告诉我更多关于您企业的信息。",
                "progress": "继续收集中",
                "stage": "信息收集阶段"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to handle profile message: {e}")
            return {
                "type": "error",
                "conversation_id": conversation_id,
                "error": str(e),
                "stage": "处理错误"
            }
    
    async def generate_profile_report(self, conversation_id: str, user_id: str):
        """
        后台任务：生成并保存企业画像报告
        """
        try:
            self.logger.info(f"Starting background report generation for {conversation_id}")
            profile_agent = await self._get_or_create_agent("company_profile")
            
            # 使用Agent内部方法来生成报告，这需要agent能访问自己的状态
            # 我们需要确保agent能拿到正确的conversation_state
            # 注意：这里的实现需要agent能从持久化存储中加载状态
            await profile_agent.generate_and_save_profile(conversation_id)
            
            self.logger.info(f"✅ Successfully generated and saved report for {conversation_id}")

        except Exception as e:
            self.logger.error(f"❌ Background report generation failed for {conversation_id}: {e}")
            # 可以在这里更新对话状态为 "generation_failed"
            # ...

    @cached(ttl=10, prefix="profile_status")
    async def get_profile_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取企业画像生成状态
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话状态信息
        """
        try:
            profile_agent = await self._get_or_create_agent("company_profile")
            
            # 创建状态查询消息
            message = A2AMessage(
                message_id=f"status_{uuid.uuid4()}",
                conversation_id=conversation_id,
                task_id=str(uuid.uuid4()),
                from_agent="user",
                to_agent="company_profile",
                message_type=MessageType.REQUEST,
                action="get_profile_status",
                payload={"conversation_id": conversation_id},
                context={},
                timestamp=None,
                priority="low"
            )
            
            # 获取对话状态
            response = await profile_agent._process_message(message)
            
            if response and response.get("status") != "not_found":
                return response
            else:
                return None
            
        except Exception as e:
            self.logger.error(f"Failed to get profile status: {e}")
            return None
    
    async def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """获取所有智能Agent的状态"""
        try:
            statuses = []
            self.logger.info(f"Getting status for {len(self.agents)} agents")
            
            for agent_id, agent in self.agents.items():
                try:
                    if hasattr(agent, 'get_health_status'):
                        status = agent.get_health_status()
                        status["agent_type"] = agent.__class__.__name__
                        statuses.append(status)
                        self.logger.debug(f"Got status for agent {agent_id}")
                    else:
                        self.logger.warning(f"Agent {agent_id} does not have get_health_status method")
                except Exception as agent_error:
                    self.logger.error(f"Failed to get status for agent {agent_id}: {agent_error}")
                    # 添加一个错误状态而不是跳过
                    statuses.append({
                        "agent_id": agent_id,
                        "agent_type": agent.__class__.__name__,
                        "is_running": False,
                        "error": str(agent_error),
                        "error_stats": {"total_errors": 1, "last_error": str(agent_error)},
                        "performance_stats": {},
                        "handlers_count": 0
                    })
            
            self.logger.info(f"Returning status for {len(statuses)} agents")
            return statuses
        except Exception as e:
            self.logger.error(f"Failed to get all agents status: {e}", exc_info=True)
            return []
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取指定智能Agent的状态"""
        try:
            agent = await self._get_agent(agent_id)
            if not agent or not hasattr(agent, 'get_health_status'):
                return None
                
            status = agent.get_health_status()
            status["agent_type"] = agent.__class__.__name__
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get agent status for {agent_id}: {e}")
            return None
    
    async def reset_agent(self, agent_id: str) -> bool:
        """
        重置智能Agent状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功重置
        """
        try:
            agent = await self._get_agent(agent_id)
            if not agent:
                return False
                
            # 停止并重新启动Agent
            if hasattr(agent, 'stop'):
                await agent.stop()
            if hasattr(agent, 'reset_error_stats'):
                agent.reset_error_stats()
            if hasattr(agent, 'reset_performance_stats'):
                agent.reset_performance_stats()
            if hasattr(agent, 'start'):
                await agent.start()
            
            self.logger.info(f"✅ Reset intelligent agent {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to reset agent {agent_id}: {e}")
            return False
    
    async def _get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取Agent实例"""
        return self.agents.get(agent_id)
    
    async def _get_or_create_agent(self, agent_id: str) -> BaseAgent:
        """
        获取或创建智能Agent实例 - 真正的AI-first架构
        
        Args:
            agent_id: Agent标识符
            
        Returns:
            智能Agent实例
        """
        # 如果Agent已存在，直接返回
        if agent_id in self.agents:
            return self.agents[agent_id]
            
        # 创建智能Agent
        agent = None
        
        try:
            if agent_id == "company_profile":
                if CompanyProfileAgent:
                    agent = CompanyProfileAgent("company_profile")
                    self.logger.info("✅ Created CompanyProfileAgent with LLM intelligence")
                else:
                    raise ImportError("CompanyProfileAgent not available")
                    
            elif agent_id == "esg_assessment":
                if ESGAssessmentAgent:
                    agent = ESGAssessmentAgent("esg_assessment")
                    self.logger.info("✅ Created ESGAssessmentAgent with LLM intelligence")
                else:
                    raise ImportError("ESGAssessmentAgent not available")
                    
            elif agent_id == "esg_report":
                if ESGReportAgent:
                    agent = ESGReportAgent("esg_report")
                    self.logger.info("✅ Created ESGReportAgent with LLM intelligence")
                else:
                    raise ImportError("ESGReportAgent not available")
            else:
                # 通用BaseAgent
                if BaseAgent:
                    agent = BaseAgent(agent_id)
                    self.logger.info(f"✅ Created BaseAgent: {agent_id}")
                else:
                    raise ImportError("BaseAgent not available")
            
            # 配置Agent
            if agent and self.message_bus:
                agent.message_bus = self.message_bus
                
                # 初始化Agent
                if hasattr(agent, 'initialize'):
                    await agent.initialize()
                
                # 启动Agent
                if hasattr(agent, 'start'):
                    await agent.start()
                    
                self.logger.info(f"🚀 Agent {agent_id} started successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create intelligent agent {agent_id}: {e}")
            
            # 如果智能Agent创建失败，不要回退到硬编码MockAgent
            # 直接抛出异常，让调用者知道系统有问题
            raise RuntimeError(f"Failed to create intelligent agent {agent_id}: {e}")
        
        # 存储并返回智能Agent
        if agent:
            self.agents[agent_id] = agent
            return agent
        else:
            raise RuntimeError(f"Failed to create agent {agent_id}")


# 单例实例
_agent_service_instance: Optional["AgentService"] = None

async def get_agent_service() -> AgentService:
    """获取Agent服务实例"""
    global _agent_service_instance
    if _agent_service_instance is None:
        try:
            message_bus = get_message_bus()
            if message_bus is None:
                raise ValueError("Failed to get a valid MessageBus instance.")
            _agent_service_instance = AgentService(message_bus)
            logger.info("✅ AgentService initialized successfully with a message bus.")
        except Exception as e:
            logger.critical(f"❌ CRITICAL: Failed to initialize AgentService with message bus: {e}", exc_info=True)
            # 在这种严重错误下，我们不应该提供一个残缺的服务
            raise RuntimeError("AgentService could not be initialized due to a MessageBus failure.") from e
            
    return _agent_service_instance
