"""统一API响应格式模块"""

from typing import Optional, Any, TypeVar, Generic
from pydantic import BaseModel
from datetime import datetime

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool
    code: int = 200
    message: str = "操作成功"
    data: Optional[T] = None
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)

def create_response(
    data: Optional[T] = None,
    success: bool = True,
    code: int = 200,
    message: str = "操作成功"
) -> APIResponse[T]:
    """创建统一响应格式"""
    return APIResponse[T](
        success=success,
        code=code,
        message=message,
        data=data
    )

def create_error_response(
    message: str = "操作失败",
    code: int = 500,
    data: Optional[Any] = None
) -> APIResponse:
    """创建错误响应格式"""
    return APIResponse(
        success=False,
        code=code,
        message=message,
        data=data
    )