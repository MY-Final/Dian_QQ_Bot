"""JWT 认证工具模块。

提供 JWT token 生成、验证和刷新功能。
"""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from jwt.exceptions import PyJWTError

from app.core.config import settings


# 使用一个固定的密钥（生产环境应该使用环境变量）
# 为了安全，这里使用 settings 中的一个派生值
def _get_secret_key() -> str:
    """获取 JWT 密钥。
    
    Returns:
        str: JWT 密钥字符串
    """
    # 使用数据库密码和其他信息生成一个派生密钥
    # 生产环境应该使用专门的环境变量
    base_key = getattr(settings, 'db_password', 'dian-qq-bot-secret-key-2026')
    return f"dian-qq-bot-jwt-secret-{base_key}-2026"


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """创建访问令牌。
    
    Args:
        data: 要编码的数据（通常包含 user_id, username, role 等）
        expires_delta: 可选的过期时间增量
        
    Returns:
        str: JWT 访问令牌
        
    Example:
        >>> payload = {"sub": "user_id", "username": "admin"}
        >>> token = create_access_token(payload)
    """
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 默认 24 小时过期
        expire = datetime.utcnow() + timedelta(hours=24)
    
    # 添加 JWT 标准声明
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    })
    
    # 编码 JWT
    encoded_jwt = jwt.encode(
        to_encode,
        _get_secret_key(),
        algorithm="HS256",
    )
    
    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """创建刷新令牌。
    
    Args:
        data: 要编码的数据（通常包含 user_id）
        expires_delta: 可选的过期时间增量
        
    Returns:
        str: JWT 刷新令牌
        
    Note:
        刷新令牌过期时间较长，默认 7 天
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 默认 7 天过期
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        _get_secret_key(),
        algorithm="HS256",
    )
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """验证 JWT 令牌。
    
    Args:
        token: JWT 令牌字符串
        token_type: 期望的令牌类型（"access" 或 "refresh"）
        
    Returns:
        Optional[dict]: 解码后的 payload，如果验证失败返回 None
        
    Raises:
        PyJWTError: JWT 验证失败时抛出
    """
    try:
        # 解码 JWT
        payload = jwt.decode(
            token,
            _get_secret_key(),
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        
        # 验证令牌类型
        if payload.get("type") != token_type:
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        # 令牌已过期
        return None
    except PyJWTError:
        # 其他 JWT 错误
        return None


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT 令牌（不验证类型）。
    
    Args:
        token: JWT 令牌字符串
        
    Returns:
        Optional[dict]: 解码后的 payload，如果验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            _get_secret_key(),
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return payload
    except PyJWTError:
        return None
