from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import bcrypt
from jose import jwt, JWTError

from src.core.config import settings


# bcrypt has a maximum password length of 72 bytes
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    # Truncate to bcrypt's 72-byte limit to prevent errors
    password_bytes = password.encode('utf-8')[:MAX_PASSWORD_BYTES]
    
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds is the recommended minimum
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Truncate to bcrypt's 72-byte limit to match hashing behavior
        password_bytes = plain_password.encode('utf-8')[:MAX_PASSWORD_BYTES]
        hashed_bytes = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, AttributeError):
        # Invalid hash format or other bcrypt errors
        return False


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    
    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Add expiration claim
    to_encode.update({"exp": expire})
    
    # Encode and return JWT
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        # Token is invalid, expired, or malformed
        return None
