"""
LLM工厂类 - 统一管理LLM实例创建
支持DeepSeek API和OpenAI兼容接口
"""
import logging
from typing import List, Optional

from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class DashScopeEmbeddings(Embeddings):
    """DashScope embedding adapter using the OpenAI-compatible embeddings API."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str,
        dimensions: int,
        batch_size: int = 32,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        embeddings: List[List[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = [str(text) for text in texts[start : start + self.batch_size]]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
                dimensions=self.dimensions,
            )
            embeddings.extend(item.embedding for item in response.data)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=str(text),
            dimensions=self.dimensions,
        )
        return response.data[0].embedding


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
    def create_embedding_model() -> Embeddings:
        """
        Create Embedding model instance using DashScope (Qwen3)
        via OpenAI-compatible API.
        Configured entirely from env vars via settings.
        """
        embedding_api_key = (
            settings.EMBEDDING_API_KEY.get_secret_value().strip()
            if settings.EMBEDDING_API_KEY
            else ""
        )

        if not embedding_api_key:
            raise ValueError(
                "EMBEDDING_API_KEY is not configured. "
                "Set it in .env to a valid DashScope API key."
            )

        logger.info(
            f"Creating embedding model: {settings.EMBEDDING_MODEL_NAME} "
            f"via {settings.EMBEDDING_BASE_URL}"
        )

        return DashScopeEmbeddings(
            model=settings.EMBEDDING_MODEL_NAME,
            api_key=embedding_api_key,
            base_url=settings.EMBEDDING_BASE_URL,
            dimensions=settings.EMBEDDING_DIM,
        )

# 全局LLM工厂实例
llm_factory = LLMFactory() 
