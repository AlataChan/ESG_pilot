"""
LLM工厂类 - 统一管理LLM实例创建
支持DeepSeek API和OpenAI兼容接口
"""
import logging
from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMFactory:
    """LLM工厂类，用于创建和管理LLM实例"""
    
    @staticmethod
    def create_deepseek_llm(
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        request_timeout: int = 60,
        max_retries: int = 2
    ) -> ChatOpenAI:
        """
        创建DeepSeek LLM实例
        
        Args:
            model: 模型名称，默认使用配置中的DEEPSEEK_MODEL
            temperature: 温度参数
            max_tokens: 最大token数
            request_timeout: 请求超时时间
            max_retries: 最大重试次数
        
        Returns:
            ChatOpenAI实例，配置为使用DeepSeek API
        """
        model_name = model or settings.DEEPSEEK_MODEL
        
        # 检查API密钥
        if not settings.DEEPSEEK_API_KEY:
            logger.warning("DeepSeek API密钥未配置，请检查环境变量DEEPSEEK_API_KEY")
            raise ValueError("DeepSeek API密钥未配置")
        
        logger.info(f"创建DeepSeek LLM实例: {model_name}")
        
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=request_timeout,
            max_retries=max_retries,
            openai_api_key=settings.DEEPSEEK_API_KEY.get_secret_value(),
            openai_api_base=settings.DEEPSEEK_BASE_URL,
            # DeepSeek API兼容OpenAI格式
            model_kwargs={
                "stream": False,
            }
        )
    
    @staticmethod
    def create_embedding_model() -> OpenAIEmbeddings:
        """
        创建Embedding模型实例
        目前仍使用OpenAI的embedding模型
        
        Returns:
            OpenAIEmbeddings实例
        """
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API密钥未配置，无法创建embedding模型")
            raise ValueError("OpenAI API密钥未配置")
        
        logger.info(f"创建Embedding模型: {settings.EMBEDDING_MODEL_NAME}")
        
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL_NAME,
            openai_api_key=settings.OPENAI_API_KEY.get_secret_value()
        )

# 全局LLM工厂实例
llm_factory = LLMFactory() 