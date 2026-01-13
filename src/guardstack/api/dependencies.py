"""
API Dependencies

FastAPI dependency injection utilities for authentication, database connections, etc.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from guardstack.config import settings
from guardstack.services.database import AsyncSessionLocal, User
from guardstack.services.cache import redis_client

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.
    
    Yields an async database session that is automatically closed
    when the request is complete.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> Redis:
    """Get Redis client instance."""
    return await redis_client()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated.
    
    Returns None if no valid authentication is provided.
    """
    if credentials is None:
        return None
    
    try:
        # Validate token and get user
        # In a production app, this would verify JWT tokens
        token = credentials.credentials
        
        # For development/demo, accept any bearer token
        if settings.environment == "development":
            # Return a mock user in development
            return User(
                id="dev-user-id",
                email="dev@guardstack.local",
                name="Development User",
                is_active=True,
                is_admin=True,
            )
        
        # TODO: Implement proper JWT validation
        # user = await validate_jwt(token, db)
        # return user
        
        return None
        
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user.
    
    Raises 401 if no valid authentication is provided.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        
        # For development/demo
        if settings.environment == "development":
            return User(
                id="dev-user-id",
                email="dev@guardstack.local",
                name="Development User",
                is_active=True,
                is_admin=True,
            )
        
        # TODO: Implement proper JWT validation
        # user = await validate_jwt(token, db)
        # if user is None:
        #     raise HTTPException(...)
        # return user
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Get current user if they are an admin.
    
    Raises 403 if user is not an admin.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def check_permissions(*required_permissions: str):
    """
    Dependency factory for checking user permissions.
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(check_permissions("admin"))])
    """
    async def permission_checker(
        user: User = Depends(get_current_user),
    ) -> bool:
        # Check if user has all required permissions
        user_permissions = getattr(user, 'permissions', []) or []
        
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )
        
        return True
    
    return permission_checker


class Paginator:
    """
    Pagination dependency for list endpoints.
    
    Usage:
        @router.get("/items")
        async def list_items(pagination: Paginator = Depends()):
            items = await get_items(
                skip=pagination.skip,
                limit=pagination.limit,
            )
    """
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)  # Limit to 100
        
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size
