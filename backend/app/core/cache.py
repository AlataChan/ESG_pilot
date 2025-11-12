"""
缓存系统模块 - Week 3 Day 1-2: Enhanced Performance Caching
提供内存和Redis两种缓存策略，用于优化查询性能
支持统计、监控和自动降级
"""
import json
import time
import logging
import hashlib
import asyncio
import pickle
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


class CacheStats:
    """✅ Week 3: Cache performance metrics tracking"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_requests = 0

    def record_hit(self):
        self.hits += 1
        self.total_requests += 1

    def record_miss(self):
        self.misses += 1
        self.total_requests += 1

    def record_error(self):
        self.errors += 1

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def get_stats(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "total_requests": self.total_requests,
            "hit_rate": f"{self.hit_rate:.2%}",
        }

    def reset(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_requests = 0

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
    """内存缓存实现 - Week 3: Enhanced with statistics"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._clean_task = None
        self.stats = CacheStats()  # ✅ Week 3: Add statistics
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        try:
            self._clean_task = asyncio.create_task(self._clean_expired_entries())
        except RuntimeError:
            # 如果没有运行中的事件循环，则跳过
            pass
    
    async def get(self, key: str) -> Optional[T]:
        """从缓存获取值 - Week 3: Track statistics"""
        if key not in self._cache:
            self.stats.record_miss()  # ✅ Week 3
            return None

        cache_item = self._cache[key]

        # 检查是否过期
        if cache_item['expires_at'] and datetime.now() > cache_item['expires_at']:
            await self.delete(key)
            self.stats.record_miss()  # ✅ Week 3
            return None

        self.stats.record_hit()  # ✅ Week 3
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


class RedisCache(BaseCache[T]):
    """✅ Week 3: Redis cache implementation for production"""

    def __init__(self):
        self._redis = None
        self.stats = CacheStats()
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            import redis.asyncio as redis
            from app.core.config import settings

            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle serialization
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            logger.info(f"✅ Redis cache initialized: {redis_url}")
        except ImportError:
            logger.warning("⚠️ redis package not installed, using memory cache only")
            self._redis = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis: {e}")
            self._redis = None

    @property
    def is_available(self) -> bool:
        return self._redis is not None

    async def get(self, key: str) -> Optional[T]:
        """Get value from Redis"""
        if not self.is_available:
            self.stats.record_miss()
            return None

        try:
            value = await self._redis.get(key)
            if value is None:
                self.stats.record_miss()
                return None

            self.stats.record_hit()
            return pickle.loads(value)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self.stats.record_error()
            return None

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value in Redis with optional TTL"""
        if not self.is_available:
            return

        try:
            serialized = pickle.dumps(value)
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self.stats.record_error()

    async def delete(self, key: str) -> None:
        """Delete key from Redis"""
        if not self.is_available:
            return

        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            self.stats.record_error()

    async def clear(self) -> None:
        """Clear all keys (use with caution!)"""
        if not self.is_available:
            return

        try:
            await self._redis.flushdb()
            logger.warning("⚠️ Redis cache cleared (flushdb)")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            self.stats.record_error()


class HybridCache(BaseCache[T]):
    """✅ Week 3: Hybrid cache with Redis + Memory fallback"""

    def __init__(self):
        self.memory_cache = MemoryCache()
        self.redis_cache = RedisCache()
        self._use_redis = self.redis_cache.is_available

        if self._use_redis:
            logger.info("✅ Using Redis cache for production")
        else:
            logger.info("⚠️ Using memory cache (Redis unavailable)")

    @property
    def stats(self) -> CacheStats:
        """Get stats from active cache backend"""
        if self._use_redis:
            return self.redis_cache.stats
        return self.memory_cache.stats

    async def get(self, key: str) -> Optional[T]:
        """Get value from cache (Redis or memory)"""
        if self._use_redis:
            value = await self.redis_cache.get(key)
            # Fallback to memory if Redis fails
            if value is None:
                return await self.memory_cache.get(key)
            return value
        return await self.memory_cache.get(key)

    async def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """Set value in both caches"""
        if self._use_redis:
            await self.redis_cache.set(key, value, ttl)
        await self.memory_cache.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        """Delete from both caches"""
        if self._use_redis:
            await self.redis_cache.delete(key)
        await self.memory_cache.delete(key)

    async def clear(self) -> None:
        """Clear both caches"""
        if self._use_redis:
            await self.redis_cache.clear()
        await self.memory_cache.clear()


# 单例缓存实例 - Week 3: Use hybrid cache for production
memory_cache = MemoryCache()
hybrid_cache = HybridCache()


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


# ✅ Week 3: Helper functions for cache management
async def invalidate_cache(prefix: str, *args, **kwargs):
    """
    Manually invalidate cache entry

    Usage:
        await invalidate_cache("doc_extraction", document_id="doc123")
    """
    # Build cache key
    cache_args = {f"arg_{i}": str(arg) for i, arg in enumerate(args)}
    cache_kwargs = {k: str(v) for k, v in kwargs.items()}
    cache_key = CacheKey.generate(prefix, **{**cache_args, **cache_kwargs})

    await hybrid_cache.delete(cache_key)
    logger.info(f"✅ Cache invalidated: {cache_key}")


async def get_cache_stats() -> dict:
    """Get cache performance statistics"""
    return hybrid_cache.stats.get_stats()


async def clear_all_cache():
    """Clear all cache entries (use with caution!)"""
    await hybrid_cache.clear()
    logger.warning("⚠️ All cache cleared")


def get_cache() -> HybridCache:
    """Get global hybrid cache instance"""
    return hybrid_cache
