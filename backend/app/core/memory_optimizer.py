"""
内存使用优化模块
提供内存监控、垃圾回收优化和内存泄漏检测功能
"""
import gc
import os
import sys
import psutil
import logging
import asyncio
import weakref
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import wraps
import tracemalloc

from app.core.logging_config import log_performance

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """内存统计信息"""
    rss_mb: float          # 常驻内存集大小 (MB)
    vms_mb: float          # 虚拟内存大小 (MB)  
    percent: float         # 内存使用百分比
    available_mb: float    # 可用内存 (MB)
    gc_objects: int        # 垃圾回收对象数量
    timestamp: datetime    # 统计时间戳


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, alert_threshold: float = 80.0, check_interval: int = 60):
        """
        初始化内存监控器
        
        Args:
            alert_threshold: 内存使用警告阈值 (%)
            check_interval: 检查间隔 (秒)
        """
        self.alert_threshold = alert_threshold
        self.check_interval = check_interval
        self.process = psutil.Process(os.getpid())
        self.stats_history: List[MemoryStats] = []
        self.max_history = 100  # 保留最近100条记录
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # 启用内存跟踪
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            
        logger.info(f"Memory monitor initialized - Alert threshold: {alert_threshold}%")
    
    def get_current_stats(self) -> MemoryStats:
        """获取当前内存统计信息"""
        try:
            # 进程内存信息
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # 系统内存信息
            system_memory = psutil.virtual_memory()
            
            # 垃圾回收信息
            gc_stats = gc.get_stats()
            total_objects = sum(stat.get('collections', 0) for stat in gc_stats)
            
            return MemoryStats(
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=memory_percent,
                available_mb=system_memory.available / 1024 / 1024,
                gc_objects=total_objects,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return MemoryStats(0, 0, 0, 0, 0, datetime.now())
    
    def log_memory_stats(self, context: str = "general"):
        """记录内存统计信息"""
        stats = self.get_current_stats()
        
        # 记录到历史
        self.stats_history.append(stats)
        if len(self.stats_history) > self.max_history:
            self.stats_history.pop(0)
        
        # 记录性能指标
        log_performance(
            f"memory_usage.{context}",
            stats.percent,
            {
                "rss_mb": stats.rss_mb,
                "vms_mb": stats.vms_mb,
                "available_mb": stats.available_mb,
                "gc_objects": stats.gc_objects
            }
        )
        
        # 检查是否超过警告阈值
        if stats.percent > self.alert_threshold:
            logger.warning(
                f"High memory usage detected: {stats.percent:.1f}% "
                f"(RSS: {stats.rss_mb:.1f}MB, Available: {stats.available_mb:.1f}MB)"
            )
    
    async def start_monitoring(self):
        """启动内存监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Memory monitoring started")
    
    async def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Memory monitoring stopped")
    
    async def _monitoring_loop(self):
        """内存监控循环"""
        while self.monitoring:
            try:
                self.log_memory_stats("background_monitor")
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                await asyncio.sleep(5)  # 错误时短暂暂停
    
    def get_memory_trend(self, minutes: int = 30) -> Dict[str, Any]:
        """获取内存使用趋势"""
        if not self.stats_history:
            return {"trend": "no_data", "stats": []}
        
        # 获取指定时间范围内的统计
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_stats = [s for s in self.stats_history if s.timestamp >= cutoff_time]
        
        if len(recent_stats) < 2:
            return {"trend": "insufficient_data", "stats": recent_stats}
        
        # 计算趋势
        first_stat = recent_stats[0]
        last_stat = recent_stats[-1]
        
        memory_change = last_stat.percent - first_stat.percent
        rss_change = last_stat.rss_mb - first_stat.rss_mb
        
        # 判断趋势
        if memory_change > 5:
            trend = "increasing"
        elif memory_change < -5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "memory_change_percent": memory_change,
            "rss_change_mb": rss_change,
            "stats_count": len(recent_stats),
            "current_percent": last_stat.percent,
            "current_rss_mb": last_stat.rss_mb
        }


class GarbageCollectionOptimizer:
    """垃圾回收优化器"""
    
    def __init__(self):
        self.original_thresholds = gc.get_threshold()
        self.collection_stats = {"manual": 0, "automatic": 0}
        
    def optimize_gc_settings(self):
        """优化垃圾回收设置"""
        # 调整垃圾回收阈值，减少频繁的小对象回收
        # 增加第一代阈值，减少频繁回收
        new_thresholds = (1000, 15, 15)  # 默认是 (700, 10, 10)
        gc.set_threshold(*new_thresholds)
        
        logger.info(f"GC thresholds updated from {self.original_thresholds} to {new_thresholds}")
    
    def force_collection(self, generation: Optional[int] = None) -> int:
        """
        强制执行垃圾回收
        
        Args:
            generation: 垃圾回收代数 (0, 1, 2)，None表示全部
            
        Returns:
            回收的对象数量
        """
        before_count = len(gc.get_objects())
        
        if generation is None:
            collected = gc.collect()
        else:
            collected = gc.collect(generation)
        
        after_count = len(gc.get_objects())
        actual_collected = before_count - after_count
        
        self.collection_stats["manual"] += 1
        
        logger.debug(f"Manual GC collected {collected} references, {actual_collected} objects freed")
        return actual_collected
    
    def get_gc_stats(self) -> Dict[str, Any]:
        """获取垃圾回收统计信息"""
        stats = gc.get_stats()
        counts = gc.get_count()
        
        return {
            "generation_stats": stats,
            "current_counts": counts,
            "thresholds": gc.get_threshold(),
            "collection_stats": self.collection_stats,
            "total_objects": len(gc.get_objects())
        }
    
    def restore_original_settings(self):
        """恢复原始垃圾回收设置"""
        gc.set_threshold(*self.original_thresholds)
        logger.info(f"GC thresholds restored to {self.original_thresholds}")


class MemoryLeakDetector:
    """内存泄漏检测器"""
    
    def __init__(self):
        self.snapshots = {}
        self.tracked_objects = weakref.WeakSet()
        
    def take_snapshot(self, name: str):
        """拍摄内存快照"""
        if not tracemalloc.is_tracing():
            logger.warning("Memory tracing not enabled, starting now")
            tracemalloc.start()
        
        snapshot = tracemalloc.take_snapshot()
        self.snapshots[name] = snapshot
        logger.info(f"Memory snapshot '{name}' taken")
    
    def compare_snapshots(self, snapshot1: str, snapshot2: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        比较两个内存快照
        
        Args:
            snapshot1: 第一个快照名称
            snapshot2: 第二个快照名称  
            limit: 返回结果数量限制
            
        Returns:
            内存差异统计列表
        """
        if snapshot1 not in self.snapshots or snapshot2 not in self.snapshots:
            logger.error(f"Snapshot not found: {snapshot1} or {snapshot2}")
            return []
        
        snap1 = self.snapshots[snapshot1]
        snap2 = self.snapshots[snapshot2]
        
        # 比较快照
        top_stats = snap2.compare_to(snap1, 'lineno')
        
        results = []
        for stat in top_stats[:limit]:
            results.append({
                "file": stat.traceback.format()[-1] if stat.traceback else "unknown",
                "size_diff_mb": stat.size_diff / 1024 / 1024,
                "count_diff": stat.count_diff,
                "size_mb": stat.size / 1024 / 1024,
                "count": stat.count
            })
        
        return results
    
    def track_object(self, obj: Any, name: str = None):
        """跟踪对象的内存使用"""
        self.tracked_objects.add(obj)
        if name:
            setattr(obj, '_memory_tracker_name', name)
    
    def get_tracked_objects_count(self) -> int:
        """获取当前跟踪的对象数量"""
        return len(self.tracked_objects)


# 全局实例
memory_monitor = MemoryMonitor()
gc_optimizer = GarbageCollectionOptimizer()
leak_detector = MemoryLeakDetector()


def memory_profile(func_name: Optional[str] = None):
    """
    内存分析装饰器
    记录函数执行前后的内存变化
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            # 执行前内存状态
            before_stats = memory_monitor.get_current_stats()
            
            try:
                result = await func(*args, **kwargs)
                
                # 执行后内存状态
                after_stats = memory_monitor.get_current_stats()
                
                # 计算内存变化
                memory_diff = after_stats.rss_mb - before_stats.rss_mb
                
                # 记录内存使用情况
                log_performance(
                    f"memory_profile.{name}",
                    memory_diff,
                    {
                        "before_rss_mb": before_stats.rss_mb,
                        "after_rss_mb": after_stats.rss_mb,
                        "memory_diff_mb": memory_diff,
                        "status": "success"
                    }
                )
                
                return result
                
            except Exception as e:
                # 即使出错也记录内存变化
                after_stats = memory_monitor.get_current_stats()
                memory_diff = after_stats.rss_mb - before_stats.rss_mb
                
                log_performance(
                    f"memory_profile.{name}",
                    memory_diff,
                    {
                        "before_rss_mb": before_stats.rss_mb,
                        "after_rss_mb": after_stats.rss_mb,
                        "memory_diff_mb": memory_diff,
                        "status": "error",
                        "error": str(e)
                    }
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            
            before_stats = memory_monitor.get_current_stats()
            
            try:
                result = func(*args, **kwargs)
                after_stats = memory_monitor.get_current_stats()
                memory_diff = after_stats.rss_mb - before_stats.rss_mb
                
                log_performance(
                    f"memory_profile.{name}",
                    memory_diff,
                    {
                        "before_rss_mb": before_stats.rss_mb,
                        "after_rss_mb": after_stats.rss_mb,
                        "memory_diff_mb": memory_diff,
                        "status": "success"
                    }
                )
                
                return result
            except Exception as e:
                after_stats = memory_monitor.get_current_stats()
                memory_diff = after_stats.rss_mb - before_stats.rss_mb
                
                log_performance(
                    f"memory_profile.{name}",
                    memory_diff,
                    {
                        "before_rss_mb": before_stats.rss_mb,
                        "after_rss_mb": after_stats.rss_mb,
                        "memory_diff_mb": memory_diff,
                        "status": "error",
                        "error": str(e)
                    }
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


async def optimize_memory():
    """执行内存优化操作"""
    logger.info("Starting memory optimization")
    
    # 1. 强制垃圾回收
    collected = gc_optimizer.force_collection()
    
    # 2. 优化GC设置
    gc_optimizer.optimize_gc_settings()
    
    # 3. 记录当前状态
    memory_monitor.log_memory_stats("optimization")
    
    logger.info(f"Memory optimization completed - Collected {collected} objects")
    
    return {
        "objects_collected": collected,
        "gc_stats": gc_optimizer.get_gc_stats(),
        "memory_stats": memory_monitor.get_current_stats()
    }


def get_memory_health_report() -> Dict[str, Any]:
    """获取内存健康报告"""
    current_stats = memory_monitor.get_current_stats()
    trend = memory_monitor.get_memory_trend()
    gc_stats = gc_optimizer.get_gc_stats()
    
    # 判断健康状态
    if current_stats.percent > 90:
        health_status = "critical"
    elif current_stats.percent > 75:
        health_status = "warning"
    elif current_stats.percent > 50:
        health_status = "moderate"
    else:
        health_status = "good"
    
    recommendations = []
    if current_stats.percent > 80:
        recommendations.append("内存使用率过高，建议执行垃圾回收")
    if trend["trend"] == "increasing":
        recommendations.append("内存使用持续增长，检查是否存在内存泄漏")
    if current_stats.available_mb < 500:
        recommendations.append("系统可用内存不足，考虑增加内存或优化应用")
    if not recommendations:
        recommendations.append("内存使用状况良好")
    
    return {
        "health_status": health_status,
        "current_stats": current_stats.__dict__,
        "trend": trend,
        "gc_stats": gc_stats,
        "tracked_objects": leak_detector.get_tracked_objects_count(),
        "recommendations": recommendations
    } 