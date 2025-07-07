import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Coroutine, Optional, Set, Any
import logging
import time
from datetime import datetime, timedelta

from .schemas import A2AMessage

class MessageBus:
    """
    An in-memory, asynchronous message bus for agent communication.
    增强版本，支持消息去重、并发安全和处理状态跟踪。
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[A2AMessage], Coroutine]]] = defaultdict(list)
        self._queue: Optional[asyncio.Queue] = None
        self._dispatch_task: Optional[asyncio.Task] = None
        
        # 消息去重和状态跟踪
        self._processed_messages: Set[str] = set()
        self._processing_messages: Set[str] = set()
        self._message_timestamps: Dict[str, float] = {}
        
        # 并发控制
        self._dispatch_lock = asyncio.Lock()
        self._processing_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # 配置参数
        self._message_ttl = 300  # 消息TTL为5分钟
        self._cleanup_interval = 60  # 清理间隔1分钟
        
        # 统计信息
        self._stats = {
            "total_messages": 0,
            "processed_messages": 0,
            "duplicate_messages": 0,
            "failed_messages": 0
        }
        
        logging.info("Enhanced MessageBus initialized with deduplication and concurrency control")

    def _get_queue(self) -> asyncio.Queue:
        """Ensures the queue is initialized for the current event loop."""
        if self._queue is None:
            self._queue = asyncio.Queue()
        return self._queue

    def _generate_message_key(self, message: A2AMessage) -> str:
        """生成消息的唯一标识符"""
        return f"{message.conversation_id}:{message.action}:{message.message_id}"

    def _is_duplicate_message(self, message: A2AMessage) -> bool:
        """检查是否为重复消息"""
        message_key = self._generate_message_key(message)
        return message_key in self._processed_messages or message_key in self._processing_messages

    def _mark_message_processing(self, message: A2AMessage):
        """标记消息正在处理中"""
        message_key = self._generate_message_key(message)
        self._processing_messages.add(message_key)
        self._message_timestamps[message_key] = time.time()

    def _mark_message_processed(self, message: A2AMessage):
        """标记消息处理完成"""
        message_key = self._generate_message_key(message)
        self._processing_messages.discard(message_key)
        self._processed_messages.add(message_key)
        self._message_timestamps[message_key] = time.time()

    def _cleanup_old_messages(self):
        """清理过期的消息记录"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._message_timestamps.items()
            if current_time - timestamp > self._message_ttl
        ]
        
        for key in expired_keys:
            self._processed_messages.discard(key)
            self._processing_messages.discard(key)
            del self._message_timestamps[key]
        
        if expired_keys:
            logging.debug(f"Cleaned up {len(expired_keys)} expired message records")

    async def subscribe(self, agent_id: str, handler: Callable[[A2AMessage], Coroutine]):
        """
        Subscribe an agent to receive messages.
        """
        async with self._dispatch_lock:
            self._subscribers[agent_id].append(handler)
            logging.info(f"Agent {agent_id} subscribed to message bus")

    async def unsubscribe(self, agent_id: str, handler: Callable[[A2AMessage], Coroutine]):
        """
        Unsubscribe an agent from receiving messages.
        """
        async with self._dispatch_lock:
            if handler in self._subscribers.get(agent_id, []):
                self._subscribers[agent_id].remove(handler)
                logging.info(f"Agent {agent_id} unsubscribed from message bus")

    async def publish(self, message: A2AMessage):
        """
        Publish a message to the bus with deduplication.
        """
        self._stats["total_messages"] += 1
        
        # 检查重复消息
        if self._is_duplicate_message(message):
            self._stats["duplicate_messages"] += 1
            logging.warning(f"Duplicate message detected: {self._generate_message_key(message)}")
            return False
        
        # 标记消息正在处理
        self._mark_message_processing(message)
        
        try:
            await self._get_queue().put(message)
            logging.debug(f"Message published: {message.action} from {message.from_agent} to {message.to_agent}")
            return True
        except Exception as e:
            # 如果发布失败，从处理中移除
            message_key = self._generate_message_key(message)
            self._processing_messages.discard(message_key)
            logging.error(f"Failed to publish message: {e}")
            raise

    async def _handle_message_safely(self, message: A2AMessage, handler: Callable[[A2AMessage], Coroutine]):
        """
        安全处理单个消息，包含错误处理和状态管理
        """
        agent_id = message.to_agent
        message_key = self._generate_message_key(message)
        
        try:
            # 使用 Agent 级别的锁防止同一个 Agent 的并发处理
            async with self._processing_locks[agent_id]:
                logging.debug(f"Processing message {message_key} for agent {agent_id}")
                
                # 再次检查重复（防止竞态条件）
                if message_key in self._processed_messages:
                    logging.warning(f"Message {message_key} already processed, skipping")
                    return
                
                # 执行处理器
                await handler(message)
                
                # 标记处理完成
                self._mark_message_processed(message)
                self._stats["processed_messages"] += 1
                
                logging.debug(f"Message {message_key} processed successfully")
                
        except asyncio.CancelledError:
            logging.warning(f"Message processing cancelled: {message_key}")
            raise
        except Exception as e:
            self._stats["failed_messages"] += 1
            logging.error(f"Error processing message {message_key}: {e}")
            
            # 即使处理失败也要标记为已处理，避免无限重试
            self._mark_message_processed(message)
            
            # 可以在这里添加错误通知机制
            raise

    async def _dispatch(self):
        """
        Continuously get messages from the queue and dispatch them to subscribers.
        增强版本，支持并发安全和重复检测。
        """
        queue = self._get_queue()
        last_cleanup = time.time()
        
        while True:
            try:
                # 定期清理过期消息
                current_time = time.time()
                if current_time - last_cleanup > self._cleanup_interval:
                    self._cleanup_old_messages()
                    last_cleanup = current_time
                
                # 获取消息（带超时，以便定期清理）
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    continue  # 超时后继续循环，执行清理
                
                message_key = self._generate_message_key(message)
                
                # 检查目标 Agent 是否存在
                if message.to_agent not in self._subscribers:
                    logging.warning(f"No subscribers for agent {message.to_agent}, message: {message_key}")
                    queue.task_done()
                    continue
                
                # 检查重复消息
                if message_key in self._processed_messages:
                    logging.warning(f"Skipping already processed message: {message_key}")
                    queue.task_done()
                    continue
                
                # 并发处理所有订阅者
                handlers = self._subscribers[message.to_agent]
                if handlers:
                    # 为每个处理器创建任务
                    tasks = [
                        asyncio.create_task(self._handle_message_safely(message, handler))
                        for handler in handlers
                    ]
                    
                    # 等待所有处理器完成
                    try:
                        await asyncio.gather(*tasks, return_exceptions=True)
                    except Exception as e:
                        logging.error(f"Error in message handlers for {message_key}: {e}")
                
                queue.task_done()
                
            except asyncio.CancelledError:
                logging.info("Message bus dispatch cancelled")
                break
            except Exception as e:
                logging.error(f"Unexpected error in message dispatch: {e}")
                # 继续运行，不要让单个错误停止整个消息总线

    async def start(self):
        """
        Start the message bus's dispatch loop as a background task.
        """
        if self._dispatch_task is None or self._dispatch_task.done():
            self._dispatch_task = asyncio.create_task(self._dispatch())
            logging.info("Enhanced message bus started with deduplication and concurrency control")

    async def stop(self):
        """
        Stop the message bus's dispatch loop.
        """
        if self._dispatch_task and not self._dispatch_task.done():
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
            logging.info("Message bus stopped")
        
        # 清理状态
        self._queue = None
        self._processed_messages.clear()
        self._processing_messages.clear()
        self._message_timestamps.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取消息总线统计信息"""
        return {
            **self._stats,
            "active_subscribers": len(self._subscribers),
            "processing_messages": len(self._processing_messages),
            "processed_messages_cache": len(self._processed_messages),
            "queue_size": self._queue.qsize() if self._queue else 0
        }

    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            "total_messages": 0,
            "processed_messages": 0,
            "duplicate_messages": 0,
            "failed_messages": 0
        }
        logging.info("Message bus statistics reset")

# 全局单例
_message_bus_instance: Optional[MessageBus] = None

def get_message_bus() -> "MessageBus":
    """
    获取全局唯一的 MessageBus 实例 (单例模式)。
    """
    global _message_bus_instance
    if _message_bus_instance is None:
        _message_bus_instance = MessageBus()
    return _message_bus_instance

# message_bus = MessageBus()
# message_bus.start() # Removed: Should be started by the application entrypoint. 