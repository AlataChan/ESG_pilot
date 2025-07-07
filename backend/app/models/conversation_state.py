from sqlalchemy import Column, String, JSON, DateTime, func
from app.db.base_class import Base

class ConversationState(Base):
    """
    用于存储Agent对话状态的数据库模型。
    """
    __tablename__ = 'conversation_states'

    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, index=True)
    agent_type = Column(String, default="CompanyProfileAgent")
    
    status = Column(String, default="active") # active, generating, completed, error
    stage = Column(String, default="initial") # e.g., E1-1, S2-3, completed

    extracted_info = Column(JSON, default={})
    messages = Column(JSON, default=[])
    final_report = Column(String, nullable=True)
    user_context = Column(JSON, default={})

    created_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now()) 