"""
通用工具函数模块
"""
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def parse_llm_json_response(response_content: str) -> Dict[str, Any]:
    """
    安全地解析大语言模型返回的、可能包含在Markdown代码块中的JSON字符串。

    Args:
        response_content: LLM返回的原始字符串内容。

    Returns:
        解析后的字典。如果解析失败，则返回一个空字典。
    """
    try:
        # 移除可能存在的Markdown代码块标记
        if response_content.strip().startswith("```json"):
            content_cleaned = response_content.strip()[7:-3].strip()
        elif response_content.strip().startswith("```"):
             content_cleaned = response_content.strip()[3:-3].strip()
        else:
            content_cleaned = response_content.strip()
        
        # 尝试解析JSON
        return json.loads(content_cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to decode JSON from LLM response. Content: '{response_content}'. Error: {e}")
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred while parsing LLM response. Content: '{response_content}'. Error: {e}")
        return {} 