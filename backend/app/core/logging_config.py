"""
高级日志配置模块
提供结构化日志、性能监控和调试功能
"""
import logging
import logging.config
import sys
import os
import json
import time
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from functools import wraps
import asyncio


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式器 - 输出JSON格式的日志
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # 基础日志信息
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 添加额外的上下文信息
        if hasattr(record, 'agent_id'):
            log_entry["agent_id"] = record.agent_id
        if hasattr(record, 'conversation_id'):
            log_entry["conversation_id"] = record.conversation_id
        if hasattr(record, 'performance_data'):
            log_entry["performance"] = record.performance_data
        if hasattr(record, 'user_context'):
            log_entry["user_context"] = record.user_context
            
        return json.dumps(log_entry, ensure_ascii=False)


class PerformanceLogger:
    """
    性能监控日志器 - 记录执行时间和性能指标
    """
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
        self.metrics = {}
    
    def log_performance_metric(self, metric_name: str, value: float, 
                             context: Optional[Dict[str, Any]] = None):
        """记录性能指标"""
        performance_data = {
            "metric": metric_name,
            "value": value,
            "unit": "seconds" if "time" in metric_name.lower() else "count",
            "context": context or {}
        }
        
        # 创建带有性能数据的log record
        extra = {"performance_data": performance_data}
        self.logger.info(f"Performance metric: {metric_name} = {value}", extra=extra)
    
    def time_function(self, func_name: Optional[str] = None):
        """装饰器：自动记录函数执行时间"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                name = func_name or f"{func.__module__}.{func.__name__}"
                
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.log_performance_metric(
                        f"function_execution_time.{name}",
                        execution_time,
                        {"status": "success", "args_count": len(args)}
                    )
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.log_performance_metric(
                        f"function_execution_time.{name}",
                        execution_time,
                        {"status": "error", "error": str(e)}
                    )
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                name = func_name or f"{func.__module__}.{func.__name__}"
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.log_performance_metric(
                        f"function_execution_time.{name}",
                        execution_time,
                        {"status": "success", "args_count": len(args)}
                    )
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.log_performance_metric(
                        f"function_execution_time.{name}",
                        execution_time,
                        {"status": "error", "error": str(e)}
                    )
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator


class AgentLogger:
    """
    Agent专用日志器 - 提供Agent上下文的日志记录
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.performance_logger = PerformanceLogger(f"agent.{agent_id}.performance")
    
    def _add_context(self, extra: Dict[str, Any], conversation_id: Optional[str] = None):
        """添加Agent上下文信息"""
        extra["agent_id"] = self.agent_id
        if conversation_id:
            extra["conversation_id"] = conversation_id
        return extra
    
    def debug(self, message: str, conversation_id: Optional[str] = None, **kwargs):
        extra = self._add_context(kwargs, conversation_id)
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, conversation_id: Optional[str] = None, **kwargs):
        extra = self._add_context(kwargs, conversation_id)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, conversation_id: Optional[str] = None, **kwargs):
        extra = self._add_context(kwargs, conversation_id)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, conversation_id: Optional[str] = None, **kwargs):
        extra = self._add_context(kwargs, conversation_id)
        self.logger.error(message, extra=extra)
    
    def log_message_handling(self, action: str, message_id: str, 
                           conversation_id: str, status: str = "start"):
        """记录消息处理过程"""
        self.info(
            f"Message handling {status}: {action}",
            conversation_id=conversation_id,
            message_id=message_id,
            action=action,
            status=status
        )
    
    def log_profile_generation_step(self, step: str, conversation_id: str, 
                                  progress: Dict[str, Any]):
        """记录企业画像生成步骤"""
        self.info(
            f"Profile generation step: {step}",
            conversation_id=conversation_id,
            step=step,
            progress=progress
        )


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_structured_logging: bool = True,
    enable_console_logging: bool = True
) -> None:
    """
    设置全局日志配置
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径
        enable_structured_logging: 是否启用结构化日志
        enable_console_logging: 是否启用控制台日志
    """
    
    # 创建日志目录
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 日志配置字典
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {},
        "loggers": {
            "": {  # root logger
                "level": log_level,
                "handlers": []
            },
            "agent": {
                "level": log_level,
                "handlers": [],
                "propagate": False
            },
            "performance": {
                "level": "INFO",
                "handlers": [],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": [],
                "propagate": False
            }
        }
    }
    
    # 控制台处理器
    if enable_console_logging:
        logging_config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "structured" if enable_structured_logging else "simple",
            "stream": sys.stdout
        }
        logging_config["loggers"][""]["handlers"].append("console")
        logging_config["loggers"]["agent"]["handlers"].append("console")
        logging_config["loggers"]["uvicorn"]["handlers"].append("console")
    
    # 文件处理器
    if log_file:
        # 主日志文件
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "structured" if enable_structured_logging else "detailed",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8"
        }
        
        # 性能日志文件
        performance_log_file = str(Path(log_file).parent / "performance.log")
        logging_config["handlers"]["performance_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "structured" if enable_structured_logging else "detailed",
            "filename": performance_log_file,
            "maxBytes": 5 * 1024 * 1024,  # 5MB
            "backupCount": 3,
            "encoding": "utf-8"
        }
        
        # 错误日志文件
        error_log_file = str(Path(log_file).parent / "error.log")
        logging_config["handlers"]["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "structured" if enable_structured_logging else "detailed",
            "filename": error_log_file,
            "maxBytes": 5 * 1024 * 1024,  # 5MB
            "backupCount": 3,
            "encoding": "utf-8"
        }
        
        logging_config["loggers"][""]["handlers"].extend(["file", "error_file"])
        logging_config["loggers"]["agent"]["handlers"].extend(["file", "error_file"])
        logging_config["loggers"]["performance"]["handlers"].append("performance_file")
    
    # 应用配置
    logging.config.dictConfig(logging_config)
    
    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info(f"Logging system initialized - Level: {log_level}, Structured: {enable_structured_logging}")


# 全局性能日志器实例
performance_logger = PerformanceLogger()

# 便捷函数
def get_agent_logger(agent_id: str) -> AgentLogger:
    """获取Agent专用日志器"""
    return AgentLogger(agent_id)

def log_performance(metric_name: str, value: float, context: Optional[Dict[str, Any]] = None):
    """记录性能指标的便捷函数"""
    performance_logger.log_performance_metric(metric_name, value, context)

def time_it(func_name: Optional[str] = None):
    """性能计时装饰器的便捷函数"""
    return performance_logger.time_function(func_name) 