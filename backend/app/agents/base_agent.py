"""
BaseAgent - 智能Agent基类

提供所有Agent的基础功能，包括消息处理、通信机制和错误处理。
完全移除硬编码的CompanyProfileGenerator，实现真正的AI-first架构。
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional, Callable, Coroutine, Set
from datetime import datetime

from app.bus import A2AMessage, MessageBus


class AgentError(Exception):
    """Agent基础异常类"""
    def __init__(self, message: str, error_code: str = "AGENT_ERROR", recoverable: bool = True):
        super().__init__(message)
        self.error_code = error_code
        self.recoverable = recoverable


class AgentInitializationError(AgentError):
    """Agent初始化异常"""
    def __init__(self, message: str):
        super().__init__(message, "AGENT_INIT_ERROR", recoverable=False)


class AgentCommunicationError(AgentError):
    """Agent通信异常"""
    def __init__(self, message: str):
        super().__init__(message, "AGENT_COMM_ERROR", recoverable=True)


class AgentProcessingError(AgentError):
    """Agent处理异常"""
    def __init__(self, message: str, recoverable: bool = True):
        super().__init__(message, "AGENT_PROC_ERROR", recoverable)


class BaseAgent(ABC):
    """
    智能Agent基类 - 真正的AI-first架构
    
    功能特性:
    - 异步消息处理和通信
    - 增强的错误处理和恢复机制
    - 并发安全的状态管理
    - 性能监控和健康检查
    - 可扩展的消息处理器注册
    """
    
    def __init__(self, agent_id: str):
        """
        初始化BaseAgent
        
        Args:
            agent_id: Agent唯一标识符
        """
        self.agent_id = agent_id
        self.message_bus: Optional[MessageBus] = None
        self.message_handlers: Dict[str, Callable[[A2AMessage], Coroutine]] = {}
        self.running = False
        
        # 错误处理和重试机制
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 1.0  # 秒
        
        # 错误统计
        self.error_stats: Dict[str, Any] = {
            "total_errors": 0,
            "recoverable_errors": 0,
            "critical_errors": 0,
            "last_error": None,
            "error_types": {}
        }
        
        # 性能统计
        self.performance_stats: Dict[str, Any] = {
            "messages_processed": 0,
            "messages_failed": 0,
            "average_response_time": 0.0,
            "last_activity": None
        }
        
        # 并发控制
        self._state_lock = asyncio.Lock()
        self._processing_requests: Set[str] = set()
        
        logging.info(f"BaseAgent {self.agent_id} initialized with AI-first architecture")

    async def start(self) -> None:
        """
        启动Agent并订阅消息总线
        
        Raises:
            AgentInitializationError: 启动失败时抛出
        """
        try:
            if not self.message_bus:
                raise AgentInitializationError("MessageBus not set")
            
            await self.message_bus.subscribe(self.agent_id, self._handle_message)
            self.running = True
            self.performance_stats["last_activity"] = datetime.now()
            
            logging.info(f"Agent {self.agent_id} started successfully")
            
        except Exception as e:
            self.running = False
            raise AgentInitializationError(f"Failed to start agent {self.agent_id}: {e}")

    async def stop(self) -> None:
        """
        停止Agent并取消订阅消息总线
        
        Raises:
            AgentError: 停止失败时抛出
        """
        try:
            if self.message_bus and self.running:
                await self.message_bus.unsubscribe(self.agent_id, self._handle_message)
            
            self.running = False
            logging.info(f"Agent {self.agent_id} stopped successfully")
            
        except Exception as e:
            logging.error(f"Error stopping agent {self.agent_id}: {e}")
            raise AgentError(f"Failed to stop agent {self.agent_id}: {e}")

    async def send_message(self, message: A2AMessage) -> None:
        """
        通过消息总线发送消息给其他Agent
        
        Args:
            message: 要发送的消息
            
        Raises:
            AgentCommunicationError: 发送失败时抛出
        """
        try:
            if not self.message_bus:
                raise AgentCommunicationError("MessageBus not available")
            
            if not self.running:
                raise AgentCommunicationError(f"Agent {self.agent_id} is not running")
            
            await self.message_bus.publish(message)
            logging.debug(f"Agent {self.agent_id} sent message: {message.action}")
            
        except Exception as e:
            raise AgentCommunicationError(f"Failed to send message: {e}")

    async def _handle_message(self, message: A2AMessage) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 接收到的消息
        """
        start_time = datetime.now()
        request_id = f"{message.message_id}_{start_time.timestamp()}"
        
        try:
            # 防止重复处理
            async with self._state_lock:
                if request_id in self._processing_requests:
                    logging.warning(f"Duplicate message processing detected: {request_id}")
                    return
                self._processing_requests.add(request_id)
            
            # 更新性能统计
            self.performance_stats["last_activity"] = start_time
            
            # 执行消息处理
            result = await self._execute_with_retry(
                self._process_message, message, 0
            )
            
            # 发送响应
            if result:
                await self._send_response(message, result)
            
            # 更新成功统计
            self.performance_stats["messages_processed"] += 1
            
            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_average_response_time(response_time)
            
        except AgentError as e:
            await self._handle_agent_error(message, e, start_time.timestamp())
        except Exception as e:
            # 未预期的错误
            agent_error = AgentProcessingError(f"Unexpected error: {e}", recoverable=False)
            await self._handle_agent_error(message, agent_error, start_time.timestamp())
        finally:
            # 清理处理状态
            async with self._state_lock:
                self._processing_requests.discard(request_id)

    async def _process_message(self, message: A2AMessage) -> Optional[Dict[str, Any]]:
        """
        处理具体的消息逻辑
        
        Args:
            message: 要处理的消息
            
        Returns:
            处理结果或None
        """
        if message.action in self.message_handlers:
            handler = self.message_handlers[message.action]
            return await handler(message)
        else:
            logging.warning(f"No handler for action: {message.action}")
            return {
                "type": "error",
                "conversation_id": message.conversation_id,
                "stage": "error",
                "error": f"Unknown action: {message.action}",
                "supported_actions": list(self.message_handlers.keys())
            }

    async def _execute_with_retry(self, handler: Callable, message: A2AMessage, 
                                retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """
        带重试机制的执行器
        
        Args:
            handler: 要执行的处理器
            message: 消息对象
            retry_count: 当前重试次数
            
        Returns:
            处理结果
        """
        try:
            return await handler(message)
        except AgentError as e:
            if e.recoverable and retry_count < self.max_retries:
                logging.warning(f"Retrying after error: {e} (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(self.retry_delay * (retry_count + 1))  # 指数退避
                return await self._execute_with_retry(handler, message, retry_count + 1)
            else:
                raise

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        判断错误是否可重试
        
        Args:
            error: 异常对象
            
        Returns:
            是否可重试
        """
        if isinstance(error, AgentError):
            return error.recoverable
        
        # 网络相关错误通常可重试
        retryable_errors = [
            "timeout", "connection", "network", "temporary"
        ]
        
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in retryable_errors)

    async def _handle_agent_error(self, message: A2AMessage, error: AgentError, 
                                start_time: float) -> None:
        """
        处理Agent错误
        
        Args:
            message: 原始消息
            error: 错误对象
            start_time: 开始时间戳
        """
        # 更新错误统计
        self.error_stats["total_errors"] += 1
        self.error_stats["last_error"] = {
            "error": str(error),
            "error_code": error.error_code,
            "timestamp": datetime.now().isoformat(),
            "message_action": message.action
        }
        
        if error.recoverable:
            self.error_stats["recoverable_errors"] += 1
        else:
            self.error_stats["critical_errors"] += 1
        
        # 更新错误类型统计
        error_type = error.error_code
        if error_type not in self.error_stats["error_types"]:
            self.error_stats["error_types"][error_type] = 0
        self.error_stats["error_types"][error_type] += 1
        
        # 更新失败统计
        self.performance_stats["messages_failed"] += 1
        
        # 记录错误日志
        logging.error(f"Agent {self.agent_id} error: {error}")
        
        # 发送错误响应
        error_payload = {
            "error": str(error),
            "error_code": error.error_code,
            "recoverable": error.recoverable,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_error_response(message, error_payload)

    async def _send_response(self, original_message: A2AMessage, result: Dict[str, Any]) -> None:
        """
        发送响应消息
        
        Args:
            original_message: 原始消息
            result: 处理结果
        """
        try:
            response_message = A2AMessage(
                message_id=f"resp_{original_message.message_id}",
                conversation_id=original_message.conversation_id,
                task_id=original_message.task_id,
                from_agent=self.agent_id,
                to_agent=original_message.from_agent,
                message_type=original_message.message_type,
                action=f"{original_message.action}_response",
                payload=result,
                context=original_message.context,
                timestamp=datetime.now(),
                priority=original_message.priority
            )
            
            await self.send_message(response_message)
            
        except Exception as e:
            logging.error(f"Failed to send response: {e}")

    async def _send_error_response(self, original_message: A2AMessage, 
                                 error_payload: Dict[str, Any]) -> None:
        """
        发送错误响应消息
        
        Args:
            original_message: 原始消息
            error_payload: 错误信息
        """
        try:
            error_message = A2AMessage(
                message_id=f"error_{original_message.message_id}",
                conversation_id=original_message.conversation_id,
                task_id=original_message.task_id,
                from_agent=self.agent_id,
                to_agent=original_message.from_agent,
                message_type=original_message.message_type,
                action="error",
                payload=error_payload,
                context=original_message.context,
                timestamp=datetime.now(),
                priority=original_message.priority
            )
            
            await self.send_message(error_message)
            
        except Exception as e:
            logging.error(f"Failed to send error response: {e}")

    def _update_average_response_time(self, response_time: float) -> None:
        """
        更新平均响应时间
        
        Args:
            response_time: 本次响应时间
        """
        current_avg = self.performance_stats["average_response_time"]
        total_processed = self.performance_stats["messages_processed"]
        
        if total_processed == 1:
            self.performance_stats["average_response_time"] = response_time
        else:
            # 计算移动平均
            new_avg = ((current_avg * (total_processed - 1)) + response_time) / total_processed
            self.performance_stats["average_response_time"] = round(new_avg, 3)

    def register_handler(self, action: str, handler: Callable[[A2AMessage], Coroutine]) -> None:
        """
        注册消息处理器
        
        Args:
            action: 消息动作类型
            handler: 处理器函数
        """
        self.message_handlers[action] = handler
        logging.info(f"Agent {self.agent_id} registered handler for action '{action}'")

    def get_health_status(self) -> Dict[str, Any]:
        """
        获取Agent健康状态
        
        Returns:
            健康状态信息
        """
        return {
            "agent_id": self.agent_id,
            "is_running": self.running,
            "error_stats": self.error_stats,
            "performance_stats": self.performance_stats,
            "handlers_count": len(self.message_handlers),
            "max_retries": self.max_retries,
            "active_requests": len(self._processing_requests),
            "supported_actions": list(self.message_handlers.keys())
        }

    def reset_error_stats(self) -> None:
        """重置错误统计"""
        self.error_stats = {
            "total_errors": 0,
            "recoverable_errors": 0,
            "critical_errors": 0,
            "last_error": None,
            "error_types": {}
        }
        logging.info(f"Agent {self.agent_id} error statistics reset")

    def reset_performance_stats(self) -> None:
        """重置性能统计"""
        self.performance_stats = {
            "messages_processed": 0,
            "messages_failed": 0,
            "average_response_time": 0.0,
            "last_activity": None
        }
        logging.info(f"Agent {self.agent_id} performance statistics reset")

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Agent特定的初始化逻辑
        
        Returns:
            初始化是否成功
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Agent特定的清理逻辑"""
        pass

    def __repr__(self) -> str:
        """Agent的字符串表示"""
        return f"<{self.__class__.__name__}(id={self.agent_id}, running={self.running})>"
