"""Authentication and authorization module for HTTP server.

This module provides JWT-based authentication and API key support
for the PDF RAG HTTP server.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Security configuration
# SECURITY: Require JWT secret key from environment - no fallback
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable must be set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour (reduced from 24 hours)
API_KEY_HEADER_NAME = "X-API-Key"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

# SECURITY: Load users from environment or config file, not hardcoded
# In production, use a proper database (PostgreSQL, Redis, etc.)
DEMO_USERS = {}

# Load admin user from environment if provided
if os.environ.get("ADMIN_USERNAME") and os.environ.get("ADMIN_PASSWORD_HASH"):
    DEMO_USERS[os.environ["ADMIN_USERNAME"]] = {
        "username": os.environ["ADMIN_USERNAME"],
        "hashed_password": os.environ["ADMIN_PASSWORD_HASH"],
        "is_active": True,
        "is_admin": True,
    }

# API Keys for service-to-service auth
# SECURITY: Load from environment only, no defaults
API_KEYS = {}
if os.environ.get("API_KEYS"):
    # Format: "key1:name1:limit1,key2:name2:limit2"
    for key_config in os.environ["API_KEYS"].split(","):
        parts = key_config.strip().split(":")
        if len(parts) == 3:
            key, name, limit = parts
            API_KEYS[key] = {
                "name": name,
                "is_active": True,
                "rate_limit": int(limit),
            }

# Rate limiting storage (in-memory for demo)
rate_limit_storage: Dict[str, Dict[str, Any]] = {}


class User(BaseModel):
    """User model."""
    username: str
    is_active: bool = True
    is_admin: bool = False


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user with username and password."""
    user = DEMO_USERS.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def check_rate_limit(identifier: str, limit: int = 100) -> bool:
    """Check rate limit for an identifier (user or API key).
    
    Args:
        identifier: User ID or API key
        limit: Maximum requests per hour
        
    Returns:
        True if within limit, False otherwise
    """
    now = datetime.now(timezone.utc)
    hour_ago = now - timedelta(hours=1)
    
    if identifier not in rate_limit_storage:
        rate_limit_storage[identifier] = {
            "requests": [],
            "count": 0
        }
    
    # Clean old requests
    user_data = rate_limit_storage[identifier]
    user_data["requests"] = [
        req_time for req_time in user_data["requests"]
        if req_time > hour_ago
    ]
    
    # Check limit
    if len(user_data["requests"]) >= limit:
        return False
    
    # Add current request
    user_data["requests"].append(now)
    return True


async def get_current_user_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[User]:
    """Get current user from JWT token."""
    if not credentials:
        return None
        
    try:
        payload = decode_token(credentials.credentials)
        username: str = payload.get("sub")
        if username is None:
            return None
            
        user_data = DEMO_USERS.get(username)
        if user_data is None:
            return None
            
        # Check rate limit
        if not check_rate_limit(username, limit=100):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
            
        return User(**user_data)
        
    except HTTPException:
        raise
    except Exception:
        return None


async def get_current_user_api_key(
    api_key: Optional[str] = Depends(api_key_scheme)
) -> Optional[User]:
    """Get current user from API key."""
    if not api_key:
        return None
        
    key_data = API_KEYS.get(api_key)
    if not key_data or not key_data["is_active"]:
        return None
        
    # Check rate limit
    rate_limit = key_data.get("rate_limit", 100)
    if not check_rate_limit(api_key, limit=rate_limit):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
        
    # Return a synthetic user for API key auth
    return User(
        username=f"api_key_{key_data['name']}",
        is_active=True,
        is_admin=False
    )


async def get_current_user(
    jwt_user: Optional[User] = Depends(get_current_user_jwt),
    api_key_user: Optional[User] = Depends(get_current_user_api_key)
) -> User:
    """Get current user from either JWT or API key."""
    # Try JWT first, then API key
    user = jwt_user or api_key_user
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
        
    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Authentication endpoints to be added to the main app
from fastapi import APIRouter

auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])


@auth_router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Login with username and password to get JWT token."""
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user["username"]})
    return Token(access_token=access_token)


@auth_router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user