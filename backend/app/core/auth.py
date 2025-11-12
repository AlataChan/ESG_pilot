"""用户认证模块

⚠️⚠️⚠️ CRITICAL SECURITY WARNING ⚠️⚠️⚠️
===========================================
THIS IS A DEVELOPMENT-ONLY STUB!
DO NOT USE IN PRODUCTION!

Current Implementation:
- No authentication whatsoever
- Returns same fake user for ALL requests
- Anyone can access any data
- All users have admin permissions
- Token "verification" only checks length > 10 chars

This MUST be replaced with real JWT authentication before deployment.
See: Week 1 Day 2-3 implementation plan
===========================================
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """获取当前用户信息

    🔴 DEVELOPMENT STUB - NOT SECURE 🔴

    WARNING: This function bypasses ALL authentication!
    - Does not validate JWT tokens
    - Returns same fake user for everyone
    - Grants admin access to all

    ⚠️ Production deployment will FAIL if this is not replaced

    TODO: Replace with real JWT verification (Week 1 Day 2-3)
    """
    # Log warning every time this is called
    logger.warning(
        "🔴 SECURITY: Using fake authentication - not production safe!"
    )

    # In production, this should NEVER be allowed
    if settings.ENV_STATE == "production":
        raise HTTPException(
            status_code=501,
            detail={
                "error": "AuthenticationNotImplemented",
                "message": "Real JWT authentication required for production",
                "status": "Development stub active",
                "action": "Implement JWT authentication before deploying"
            }
        )

    # 开发阶段返回模拟用户数据
    return {
        "id": "dev_user_001",
        "username": "developer",
        "email": "dev@example.com",
        "role": "admin",
        "permissions": ["read", "write", "admin"]
    }

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """验证JWT token

    🔴 FAKE IMPLEMENTATION 🔴
    This does NOT verify tokens! It only checks length.
    Any 11+ character string will pass.

    TODO: Replace with jose.jwt.decode() (Week 1 Day 2-3)
    """
    logger.warning("🔴 SECURITY: Fake token verification - any string > 10 chars passes!")

    # ❌ This is NOT real verification!
    if token and len(token) > 10:
        return {
            "id": "dev_user_001",
            "username": "developer",
            "email": "dev@example.com",
            "role": "admin"
        }
    return None

def create_access_token(user_data: Dict[str, Any]) -> str:
    """创建访问token

    🔴 FAKE IMPLEMENTATION 🔴
    This does NOT create JWT tokens! Returns plain text.

    TODO: Replace with jose.jwt.encode() (Week 1 Day 2-3)
    """
    logger.warning("🔴 SECURITY: Fake token generation - not a real JWT!")

    # ❌ This is NOT a real JWT!
    return f"development-test-token-{user_data.get('id', 'unknown')}"

def require_permission(permission: str):
    """权限检查装饰器

    ✅ This implementation is correct
    (But relies on get_current_user which is fake)
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
