# 对话状态持久化数据模型
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Boolean, Index
from sqlalchemy.sql import func
from app.db.base_class import Base

class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"
    
    id = Column(String(100), primary_key=True, index=True)  # conversation_id
    agent_type = Column(String(50), nullable=False, index=True)  # agent类型
    user_id = Column(String(100), nullable=True, index=True)  # 用户ID
    stage = Column(String(50), nullable=False, default="opening")  # 对话阶段
    status = Column(String(20), nullable=False, default="active")  # active, completed, error
    
    # 对话状态数据
    extracted_info = Column(JSON, nullable=False, default=dict)  # 提取的信息
    user_context = Column(JSON, nullable=False, default=dict)  # 用户上下文
    conversation_metadata = Column(JSON, nullable=False, default=dict)  # 其他元数据
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 索引优化
    __table_args__ = (
        Index('idx_conversations_agent_status', 'agent_type', 'status'),
        Index('idx_conversations_user_created', 'user_id', 'created_at'),
    )

class ConversationMessage(Base):
    """对话消息表"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(100), nullable=False, index=True)  # 关联conversation
    
    # 消息内容
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)  # 消息内容
    message_type = Column(String(20), nullable=False, default="text")  # text, question, response
    
    # 消息元数据
    stage = Column(String(50), nullable=True)  # 消息所属阶段
    message_metadata = Column(JSON, nullable=False, default=dict)  # 消息元数据
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 索引优化
    __table_args__ = (
        Index('idx_conversation_messages_conv_created', 'conversation_id', 'created_at'),
        Index('idx_conversation_messages_role_type', 'role', 'message_type'),
    ) 