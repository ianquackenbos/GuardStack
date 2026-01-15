"""
JWT Authentication Service

Service for JWT token validation and user authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from pydantic import BaseModel

from guardstack.config import settings

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # Subject (user ID)
    email: Optional[str] = None
    name: Optional[str] = None
    is_admin: bool = False
    permissions: list[str] = []
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


class User(BaseModel):
    """Authenticated user model."""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    permissions: list[str] = []


class JWTAuthService:
    """
    Service for JWT authentication.
    
    Provides:
    - Token generation
    - Token validation
    - Token refresh
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key or getattr(settings, 'jwt_secret', 'guardstack-secret-key-change-in-production')
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(
        self,
        user_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        is_admin: bool = False,
        permissions: Optional[list[str]] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a new access token.
        
        Args:
            user_id: User identifier
            email: User email
            name: User display name
            is_admin: Admin flag
            permissions: List of permissions
            expires_delta: Custom expiration
        
        Returns:
            Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        
        now = datetime.utcnow()
        expire = now + expires_delta
        
        payload = {
            "sub": user_id,
            "email": email,
            "name": name,
            "is_admin": is_admin,
            "permissions": permissions or [],
            "exp": expire,
            "iat": now,
            "type": "access",
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a new refresh token.
        
        Args:
            user_id: User identifier
            expires_delta: Custom expiration
        
        Returns:
            Encoded JWT refresh token
        """
        if expires_delta is None:
            expires_delta = timedelta(days=self.refresh_token_expire_days)
        
        now = datetime.utcnow()
        expire = now + expires_delta
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "type": "refresh",
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_token(self, token: str) -> Optional[TokenPayload]:
        """
        Validate and decode a JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            TokenPayload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            return TokenPayload(
                sub=payload["sub"],
                email=payload.get("email"),
                name=payload.get("name"),
                is_admin=payload.get("is_admin", False),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload["exp"]) if "exp" in payload else None,
                iat=datetime.fromtimestamp(payload["iat"]) if "iat" in payload else None,
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def validate_access_token(self, token: str) -> Optional[TokenPayload]:
        """Validate an access token specifically."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            if payload.get("type") != "access":
                logger.warning("Token is not an access token")
                return None
            
            return TokenPayload(
                sub=payload["sub"],
                email=payload.get("email"),
                name=payload.get("name"),
                is_admin=payload.get("is_admin", False),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload["exp"]) if "exp" in payload else None,
                iat=datetime.fromtimestamp(payload["iat"]) if "iat" in payload else None,
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Access token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            return None
    
    def validate_refresh_token(self, token: str) -> Optional[str]:
        """
        Validate a refresh token.
        
        Args:
            token: Refresh token
        
        Returns:
            User ID if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            if payload.get("type") != "refresh":
                logger.warning("Token is not a refresh token")
                return None
            
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user object from a valid token.
        
        Args:
            token: JWT token
        
        Returns:
            User object if valid
        """
        payload = self.validate_access_token(token)
        
        if payload is None:
            return None
        
        return User(
            id=payload.sub,
            email=payload.email,
            name=payload.name,
            is_active=True,
            is_admin=payload.is_admin,
            permissions=payload.permissions,
        )
    
    def refresh_access_token(
        self,
        refresh_token: str,
        user_data: Optional[dict[str, Any]] = None,
    ) -> Optional[tuple[str, str]]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            user_data: Additional user data to include
        
        Returns:
            Tuple of (access_token, new_refresh_token) or None
        """
        user_id = self.validate_refresh_token(refresh_token)
        
        if user_id is None:
            return None
        
        user_data = user_data or {}
        
        access_token = self.create_access_token(
            user_id=user_id,
            email=user_data.get("email"),
            name=user_data.get("name"),
            is_admin=user_data.get("is_admin", False),
            permissions=user_data.get("permissions", []),
        )
        
        new_refresh_token = self.create_refresh_token(user_id)
        
        return access_token, new_refresh_token


# API Key authentication for service-to-service
class APIKeyAuthService:
    """Service for API key authentication."""
    
    def __init__(self):
        # In production, these would be stored in a database
        self._api_keys: dict[str, dict[str, Any]] = {}
    
    def register_api_key(
        self,
        api_key: str,
        service_name: str,
        permissions: Optional[list[str]] = None,
    ) -> None:
        """Register an API key for a service."""
        self._api_keys[api_key] = {
            "service_name": service_name,
            "permissions": permissions or [],
            "created_at": datetime.utcnow().isoformat(),
        }
    
    def validate_api_key(self, api_key: str) -> Optional[dict[str, Any]]:
        """Validate an API key."""
        return self._api_keys.get(api_key)
    
    def has_permission(self, api_key: str, permission: str) -> bool:
        """Check if an API key has a specific permission."""
        key_data = self._api_keys.get(api_key)
        if not key_data:
            return False
        return permission in key_data.get("permissions", [])


# Global service instances
_jwt_auth_service: Optional[JWTAuthService] = None
_api_key_auth_service: Optional[APIKeyAuthService] = None


def get_jwt_auth_service() -> JWTAuthService:
    """Get the global JWT auth service."""
    global _jwt_auth_service
    if _jwt_auth_service is None:
        _jwt_auth_service = JWTAuthService()
    return _jwt_auth_service


def get_api_key_auth_service() -> APIKeyAuthService:
    """Get the global API key auth service."""
    global _api_key_auth_service
    if _api_key_auth_service is None:
        _api_key_auth_service = APIKeyAuthService()
    return _api_key_auth_service
