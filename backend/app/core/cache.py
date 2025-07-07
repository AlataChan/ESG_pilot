"""
缓存系统模块
提供内存和Redis两种缓存策略，用于优化查询性能
"""
import json
import time
import logging
import hashlib
import asyncio
from typing import Any, Dict, Optional, TypeVar, Generic, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
from abc import ABC, abstractmethod

try:
    from app.core.logging_config import log_performance
except ImportError:
    def log_performance(metric_name: str, value: float, context: Optional[Dict[str, Any]] = None):
        """备用日志函数"""
        pass

# 定义泛型类型变量
T = TypeVar('T')

logger = logging.getLogger(__name__)

class CacheKey:
    """缓存键生成器"""
    
    @staticmethod
    def generate(prefix: str, **kwargs) -> str:
        """生成缓存键"""
        # 将关键参数按字母排序并转换为JSON字符串
        sorted_items = sorted(kwargs.items(), key=lambda x: x[0])
        param_str = json.dumps(sorted_items, sort_keys=True)
        
        # 使用MD5创建一个固定长度的哈希值
        hash_obj = hashlib.md5(param_str.encode('utf-8'))
        hash_key = hash_obj.hexdigest()
        
        # 组合前缀和哈希值
        return f"{prefix}:{hash_key}"


class BaseCache(Generic[T], ABC):
    """缓存基类"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """获取缓存项"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """设置缓存项"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存项"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清除全部缓存"""
        pass
    
    async def get_or_set(self, key: str, factory: Callable[[], Union[T, asyncio.Future]], 
                        ttl: Optional[int] = None) -> T:
        """获取缓存，如果不存在则设置"""
        # 尝试获取缓存
        cached = await self.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached
        
        # 缓存未命中，调用工厂函数
        logger.debug(f"Cache miss: {key}")
        start_time = time.time()
        
        if asyncio.iscoroutinefunction(factory):
            result = await factory()
        else:
            result = factory()
            
        execution_time = time.time() - start_time
        
        # 记录性能指标
        log_performance(
            "cache_miss_execution_time", 
            execution_time,
            {"key": key, "ttl": ttl}
        )
        
        # 设置缓存
        await self.set(key, result, ttl)
        return result


class MemoryCache(BaseCache[T]):
    """内存缓存实现"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._clean_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        try:
            self._clean_task = asyncio.create_task(self._clean_expired_entries())
        except RuntimeError:
            # 如果没有运行中的事件循环，则跳过
            pass
    
    async def get(self, key: str) -> Optional[T]:
        """从缓存获取值"""
        if key not in self._cache:
            return None
        
        cache_item = self._cache[key]
        
        # 检查是否过期
        if cache_item['expires_at'] and datetime.now() > cache_item['expires_at']:
            await self.delete(key)
            return None
            
        return cache_item['value']
    
    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }
    
    async def delete(self, key: str) -> None:
        """删除缓存项"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
    
    async def _clean_expired_entries(self):
        """定期清理过期缓存项"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                now = datetime.now()
                
                keys_to_delete = []
                for key, item in self._cache.items():
                    if item['expires_at'] and now > item['expires_at']:
                        keys_to_delete.append(key)
                
                async with self._lock:
                    for key in keys_to_delete:
                        if key in self._cache:
                            del self._cache[key]
                
                if keys_to_delete:
                    logger.debug(f"Cleaned {len(keys_to_delete)} expired cache entries")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error cleaning expired cache entries: {e}")
    
    def __del__(self):
        """清理定时任务"""
        if hasattr(self, '_clean_task') and self._clean_task:
            self._clean_task.cancel()


# 单例缓存实例
memory_cache = MemoryCache()


def cached(ttl: Optional[int] = 60, prefix: str = "cache",
          key_builder: Optional[Callable] = None):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        prefix: 缓存键前缀
        key_builder: 自定义缓存键构建函数
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 添加函数名称到前缀
                func_prefix = f"{prefix}:{func.__module__}.{func.__name__}"
                # 从args和kwargs构建键
                cache_args = {f"arg_{i}": str(arg) for i, arg in enumerate(args)}
                cache_kwargs = {k: str(v) for k, v in kwargs.items()}
                cache_key = CacheKey.generate(func_prefix, **{**cache_args, **cache_kwargs})
            
            # 使用get_or_set模式
            return await memory_cache.get_or_set(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 同步版本直接调用原函数
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
