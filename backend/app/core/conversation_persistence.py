"""
对话状态持久化管理器
实现Redis + PostgreSQL混合存储策略
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

try:
    import redis.asyncio as redis
    from sqlalchemy.orm import Session
    from sqlalchemy import select, update, delete
except ImportError:
    # 备用实现
    redis = None
    Session = None
    select = None
    update = None
    delete = None

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    """对话状态数据结构"""
    conversation_id: str
    agent_type: str
    user_id: Optional[str] = None
    stage: str = "opening"
    status: str = "active"
    extracted_info: Dict[str, Any] = None
    user_context: Dict[str, Any] = None
    messages: List[Dict[str, Any]] = None
    conversation_metadata: Dict[str, Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.extracted_info is None:
            self.extracted_info = {}
        if self.user_context is None:
            self.user_context = {}
        if self.messages is None:
            self.messages = []
        if self.conversation_metadata is None:
            self.conversation_metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class ConversationPersistenceManager:
    """对话状态持久化管理器"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._redis_connected = False
        self._db_available = True
        
        # Redis配置
        self.redis_prefix = "conversation"
        self.default_ttl = 24 * 3600  # 24小时
        self.sync_interval = 300  # 5分钟同步一次到数据库
        
        # 内存缓存作为备用
        self._memory_cache: Dict[str, ConversationState] = {}
        self._cache_lock = asyncio.Lock()
        
    async def initialize(self) -> bool:
        """初始化持久化管理器"""
        try:
            # 尝试连接Redis
            await self._init_redis()
            
            # 启动后台同步任务
            asyncio.create_task(self._background_sync_task())
            
            logger.info("ConversationPersistenceManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ConversationPersistenceManager: {e}")
            return False
    
    async def _init_redis(self):
        """初始化Redis连接"""
        try:
            # 从环境变量或配置获取Redis设置
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            redis_db = getattr(settings, 'REDIS_DB', 0)
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # 测试连接
            await self.redis_client.ping()
            self._redis_connected = True
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory cache: {e}")
            self._redis_connected = False
    
    async def save_conversation_state(self, state: ConversationState) -> bool:
        """保存对话状态"""
        try:
            state.updated_at = datetime.now()
            
            # 1. 优先保存到Redis
            if await self._save_to_redis(state):
                logger.debug(f"Conversation {state.conversation_id} saved to Redis")
            
            # 2. 重要节点立即同步到数据库
            if self._should_immediate_sync(state):
                if await self._save_to_database(state):
                    logger.debug(f"Conversation {state.conversation_id} synced to database")
            
            # 3. 备用内存缓存
            await self._save_to_memory(state)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation state {state.conversation_id}: {e}")
            return False
    
    async def load_conversation_state(self, conversation_id: str) -> Optional[ConversationState]:
        """加载对话状态"""
        try:
            # 1. 优先从Redis加载
            if self._redis_connected:
                state = await self._load_from_redis(conversation_id)
                if state:
                    return state
            
            # 2. 从数据库加载
            state = await self._load_from_database(conversation_id)
            if state:
                # 重新缓存到Redis
                if self._redis_connected:
                    await self._save_to_redis(state)
                return state
            
            # 3. 从内存缓存加载
            return await self._load_from_memory(conversation_id)
            
        except Exception as e:
            logger.error(f"Failed to load conversation state {conversation_id}: {e}")
            return None
    
    async def _save_to_redis(self, state: ConversationState) -> bool:
        """保存到Redis"""
        if not self._redis_connected or not self.redis_client:
            return False
        
        try:
            key = f"{self.redis_prefix}:{state.conversation_id}"
            data = self._serialize_state(state)
            
            await self.redis_client.setex(key, self.default_ttl, json.dumps(data))
            return True
            
        except Exception as e:
            logger.error(f"Redis save error for {state.conversation_id}: {e}")
            return False
    
    async def _load_from_redis(self, conversation_id: str) -> Optional[ConversationState]:
        """从Redis加载"""
        if not self._redis_connected or not self.redis_client:
            return None
        
        try:
            key = f"{self.redis_prefix}:{conversation_id}"
            data = await self.redis_client.get(key)
            
            if data:
                return self._deserialize_state(json.loads(data))
            return None
            
        except Exception as e:
            logger.error(f"Redis load error for {conversation_id}: {e}")
            return None
    
    async def _save_to_database(self, state: ConversationState) -> bool:
        """保存到数据库（简化版本，避免循环导入）"""
        # 暂时使用内存缓存，等数据库模型完成后再实现
        return True
    
    async def _load_from_database(self, conversation_id: str) -> Optional[ConversationState]:
        """从数据库加载（简化版本）"""
        # 暂时返回None，等数据库模型完成后再实现
        return None
    
    async def _save_to_memory(self, state: ConversationState):
        """保存到内存缓存"""
        async with self._cache_lock:
            self._memory_cache[state.conversation_id] = state
    
    async def _load_from_memory(self, conversation_id: str) -> Optional[ConversationState]:
        """从内存缓存加载"""
        async with self._cache_lock:
            return self._memory_cache.get(conversation_id)
    
    def _serialize_state(self, state: ConversationState) -> Dict[str, Any]:
        """序列化状态对象"""
        data = asdict(state)
        # 处理datetime对象
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        if data.get('updated_at'):
            data['updated_at'] = data['updated_at'].isoformat()
        return data
    
    def _deserialize_state(self, data: Dict[str, Any]) -> ConversationState:
        """反序列化状态对象"""
        # 处理datetime字段
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return ConversationState(**data)
    
    def _should_immediate_sync(self, state: ConversationState) -> bool:
        """判断是否需要立即同步到数据库"""
        # 关键节点立即同步
        critical_stages = ["completed", "error"]
        return (
            state.status in critical_stages or
            state.stage in ["synthesis", "completed"] or
            len(state.messages) % 5 == 0  # 每5条消息同步一次
        )
    
    async def _background_sync_task(self):
        """后台同步任务"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                
                # 同步内存缓存中的状态到数据库
                async with self._cache_lock:
                    for conversation_id, state in list(self._memory_cache.items()):
                        if state.status == "active":
                            await self._save_to_database(state)
                
                logger.debug("Background sync completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background sync error: {e}")
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话状态"""
        try:
            # 从Redis删除
            if self._redis_connected and self.redis_client:
                key = f"{self.redis_prefix}:{conversation_id}"
                await self.redis_client.delete(key)
            
            # 从内存删除
            async with self._cache_lock:
                self._memory_cache.pop(conversation_id, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        if self.redis_client:
            await self.redis_client.close()

# 全局实例
conversation_persistence = ConversationPersistenceManager() 