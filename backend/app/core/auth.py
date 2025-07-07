"""用户认证模块"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """获取当前用户信息
    
    在实际项目中，这里应该验证JWT token并返回用户信息
    目前返回模拟用户数据用于开发测试
    """
    # 在开发阶段，返回模拟用户数据
    # 实际项目中应该验证token并从数据库获取用户信息
    return {
        "id": "dev_user_001",
        "username": "developer",
        "email": "dev@example.com",
        "role": "admin",
        "permissions": ["read", "write", "admin"]
    }

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT token
    
    在实际项目中，这里应该验证JWT token的有效性
    目前返回模拟数据用于开发测试
    """
    # 模拟token验证逻辑
    if token and len(token) > 10:  # 简单的token格式检查
        return {
            "id": "dev_user_001",
            "username": "developer",
            "email": "dev@example.com",
            "role": "admin"
        }
    return None

def create_access_token(user_data: Dict[str, Any]) -> str:
    """创建访问token
    
    在实际项目中，这里应该生成JWT token
    目前返回模拟token用于开发测试
    """
    # 模拟token生成逻辑 - 使用明显的测试格式
    return f"development-test-token-{user_data.get('id', 'unknown')}"

def require_permission(permission: str):
    """权限检查装饰器
    
    检查用户是否具有指定权限
    """
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {permission} 权限"
            )
        return current_user
    
    return permission_checker