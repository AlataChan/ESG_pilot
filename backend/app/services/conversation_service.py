"""
对话状态持久化服务

这个服务提供了一个专用的接口，用于将Agent的对话状态（ConversationState）
保存到数据库或从数据库中加载。

它将数据库操作与Agent的核心逻辑分离开来，使得代码更清晰、更易于维护。
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from app.models.conversation_state import ConversationState

logger = logging.getLogger(__name__)

def serialize_datetime(obj):
    """JSON序列化时处理datetime对象"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def serialize_state_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """递归序列化状态数据中的datetime对象"""
    if isinstance(data, dict):
        return {k: serialize_state_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_state_data(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

class ConversationService:
    """处理对话状态的加载和保存"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def save_state(self, state_data: Dict[str, Any]) -> ConversationState:
        """
        将字典形式的对话状态保存到数据库。
        如果已存在，则更新；如果不存在，则创建。
        """
        conversation_id = state_data.get("conversation_id")
        if not conversation_id:
            raise ValueError("conversation_id is required to save state")

        db_state = self.db.query(ConversationState).filter(
            ConversationState.conversation_id == conversation_id
        ).first()

        if db_state:
            # 更新现有状态
            for key, value in state_data.items():
                 if key != "id": # 避免修改主键
                    setattr(db_state, key, value)
            logger.info(f"Updating conversation state for {conversation_id}")
        else:
            # 创建新状态
            db_state = ConversationState(**state_data)
            self.db.add(db_state)
            logger.info(f"Creating new conversation state for {conversation_id}")
        
        try:
            self.db.commit()
            self.db.refresh(db_state)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to save state for {conversation_id}: {e}")
            raise
        
        return db_state

    def load_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        从数据库加载对话状态，并将其转换为字典。
        """
        db_state = self.db.query(ConversationState).filter(
            ConversationState.conversation_id == conversation_id
        ).first()

        if db_state:
            logger.info(f"Loaded conversation state for {conversation_id}")
            # 将SQLAlchemy模型对象转换为字典
            return {c.name: getattr(db_state, c.name) for c in db_state.__table__.columns}
        
        logger.warning(f"No conversation state found for {conversation_id}")
        return None 