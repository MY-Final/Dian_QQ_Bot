"""密码工具模块。

提供密码哈希和验证功能，使用 bcrypt 算法。
"""

import bcrypt

# bcrypt 最大密码长度限制（字节）
MAX_PASSWORD_LENGTH = 72

# bcrypt 盐的轮数（cost factor）
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """对密码进行哈希加密。

    Args:
        password: 原始密码

    Returns:
        str: 加密后的密码哈希值（包含盐）

    Note:
        bcrypt 算法限制密码长度不能超过 72 字节
    """
    # 将密码转换为字节
    password_bytes = password.encode("utf-8")

    # 截断到最大长度（如果超过 72 字节）
    if len(password_bytes) > MAX_PASSWORD_LENGTH:
        password_bytes = password_bytes[:MAX_PASSWORD_LENGTH]

    # 生成盐并哈希密码
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # 返回字符串格式
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配。

    Args:
        plain_password: 原始密码
        hashed_password: bcrypt 哈希后的密码

    Returns:
        bool: 密码是否匹配

    Note:
        bcrypt 算法限制密码长度不能超过 72 字节
    """
    # 将密码转换为字节
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    # 截断到最大长度（如果超过 72 字节）
    if len(password_bytes) > MAX_PASSWORD_LENGTH:
        password_bytes = password_bytes[:MAX_PASSWORD_LENGTH]

    try:
        # 验证密码
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        # 如果哈希格式错误，返回 False
        return False
