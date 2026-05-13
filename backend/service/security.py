import bcrypt


def mask_api_key(key: str) -> str:
    if not key or len(key) < 8:
        return "****"
    prefix_len = 3 if key.startswith("sk-") else 2
    suffix_len = 4
    return key[:prefix_len] + "****" + key[-suffix_len:]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    if not hashed_password:
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
