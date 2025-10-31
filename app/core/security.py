"""
Security module for authentication and authorization.

This module provides JWT token creation/validation and password hashing utilities.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password.
        hashed_password: The hashed password to verify against.

    Returns:
        bool: True if password matches, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("password_verification_error", error=str(e))
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a plain password.

    Args:
        password: The plain text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token.
        expires_delta: Optional expiration time delta. If not provided,
                      uses ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        str: The encoded JWT token.

    Example:
        ```python
        token = create_access_token(
            data={"sub": "user@example.com"},
            expires_delta=timedelta(minutes=30)
        )
        ```
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        logger.info("access_token_created", subject=data.get("sub"))
        return encoded_jwt
    except Exception as e:
        logger.error("token_creation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create access token"
        )


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT token to decode.

    Returns:
        Dict[str, Any]: The decoded token payload.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        logger.error("token_decode_error", error=str(e))
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency for extracting current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials with JWT token.

    Returns:
        Dict[str, Any]: The decoded token payload with user information.

    Raises:
        HTTPException: If token is invalid or expired.

    Example:
        ```python
        @app.get("/protected")
        async def protected_route(user: Dict = Depends(get_current_user)):
            return {"message": f"Hello {user['sub']}"}
        ```
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def create_api_key() -> str:
    """
    Create a random API key for external integrations.

    Returns:
        str: A random API key.
    """
    import secrets
    return secrets.token_urlsafe(32)


def validate_api_key(api_key: str, stored_api_key: str) -> bool:
    """
    Validate an API key against a stored key using constant-time comparison.

    Args:
        api_key: The API key to validate.
        stored_api_key: The stored API key to compare against.

    Returns:
        bool: True if keys match, False otherwise.
    """
    import secrets
    return secrets.compare_digest(api_key, stored_api_key)


class RateLimiter:
    """
    Simple in-memory rate limiter.

    This is a basic implementation. For production, use Redis-based rate limiting.
    """

    def __init__(self, max_requests: int = 100, period: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the period.
            period: Time period in seconds.
        """
        self.max_requests = max_requests
        self.period = period
        self.requests: Dict[str, list[datetime]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if a request from the identifier is allowed.

        Args:
            identifier: Unique identifier (e.g., IP address, user ID).

        Returns:
            bool: True if request is allowed, False if rate limit exceeded.
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.period)

        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff
            ]
        else:
            self.requests[identifier] = []

        # Check rate limit
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                request_count=len(self.requests[identifier])
            )
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests,
    period=settings.rate_limit_period
)
