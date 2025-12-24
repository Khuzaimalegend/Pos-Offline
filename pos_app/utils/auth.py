import hashlib
import secrets


def hash_password(password: str) -> str:
    """Hash password using built-in hashlib (no external dependencies)"""
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Hash password with salt
    pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}:{pwd_hash}"


def check_password(password: str, hashed: str) -> bool:
    """Check password against hash using built-in hashlib"""
    try:
        if ':' not in hashed:
            return False
        salt, stored_hash = hashed.split(':', 1)
        pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        return pwd_hash == stored_hash
    except Exception:
        return False
