from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response" 
    EVENT = "event"
    ERROR = "error"

class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class A2AMessage:
    """
    Standard message format for Agent-to-Agent (A2A) communication.
    """
    # Required fields
    conversation_id: str
    task_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    action: str
    payload: Dict[str, Any]

    # Fields with default values
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: Priority = Priority.NORMAL
    expires_at: Optional[datetime] = None
    status: str = "pending"  # pending, processing, completed, failed
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.message_type, str):
            self.message_type = MessageType(self.message_type)
        if isinstance(self.priority, int):
            self.priority = Priority(self.priority) 