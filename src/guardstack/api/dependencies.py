"""
API Dependencies

FastAPI dependency injection utilities for authentication, database connections, etc.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from guardstack.config import settings
from guardstack.services.auth import get_jwt_service, get_api_key_service

# Security scheme
security = HTTPBearer(auto_error=False)


class User(BaseModel):
    """User model for authentication."""
    id: str
    username: str
    email: Optional[str] = None
    roles: list[str] = []
    permissions: list[str] = []
    is_active: bool = True


async def get_db():
    """
    Get database session.
    
    Yields an async database session that is automatically closed
    when the request is complete.
    """
    try:
        from guardstack.services.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    except ImportError:
        # Database not configured, yield None
        yield None


async def get_redis():
    """Get Redis client instance."""
    try:
        from guardstack.services.cache import redis_client
        return await redis_client()
    except ImportError:
        return None


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """
    Get current user if authenticated.
    
    Returns None if no valid authentication is provided.
    """
    if credentials is None:
        return None
    
    jwt_service = get_jwt_service()
    
    try:
        payload = jwt_service.validate_token(credentials.credentials)
        return User(
            id=payload.sub,
            username=payload.username,
            email=payload.email,
            roles=payload.roles,
            permissions=payload.permissions,
            is_active=True,
        )
    except ValueError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """
    Get current authenticated user.
    
    Raises HTTPException if authentication fails.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    jwt_service = get_jwt_service()
    
    try:
        payload = jwt_service.validate_token(credentials.credentials)
        return User(
            id=payload.sub,
            username=payload.username,
            email=payload.email,
            roles=payload.roles,
            permissions=payload.permissions,
            is_active=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.
    
    Verifies that the user is active.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return user


def require_role(required_roles: list[str]):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(["admin"]))])
    """
    async def check_roles(user: User = Depends(get_current_user)) -> User:
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {required_roles}",
            )
        return user
    return check_roles


def require_permission(required_permissions: list[str]):
    """
    Dependency factory for permission-based access control.
    
    Usage:
        @router.post("/models", dependencies=[Depends(require_permission(["models:write"]))])
    """
    async def check_permissions(user: User = Depends(get_current_user)) -> User:
        if not any(perm in user.permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permissions: {required_permissions}",
            )
        return user
    return check_permissions


# Common role dependencies
RequireAdmin = Depends(require_role(["admin"]))
RequireUser = Depends(require_role(["user", "admin"]))
