"""
FastAPI Dependencies Module

Provides authentication, authorization, and common dependencies.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Header, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from pydantic import BaseModel

from guardstack.services.auth import (
    get_jwt_service,
    get_api_key_service,
    JWTAuthService,
    APIKeyAuthService,
)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class CurrentUser(BaseModel):
    """Authenticated user context."""
    user_id: str
    username: str
    email: Optional[str] = None
    roles: list[str] = []
    permissions: list[str] = []
    tenant_id: Optional[str] = None
    is_service_account: bool = False


class TokenPayload(BaseModel):
    """JWT Token payload."""
    sub: str
    username: str
    email: Optional[str] = None
    roles: list[str] = []
    permissions: list[str] = []
    tenant_id: Optional[str] = None
    aud: Optional[str] = None
    iss: Optional[str] = None
    exp: int
    iat: int


async def validate_jwt_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> Optional[TokenPayload]:
    """
    Validate JWT token from Authorization header.
    
    Uses JWTAuthService for actual token validation with RS256/HS256.
    """
    if not credentials:
        return None
    
    jwt_service = get_jwt_service()
    
    try:
        payload = jwt_service.validate_token(credentials.credentials)
        
        return TokenPayload(
            sub=payload.sub,
            username=payload.username,
            email=payload.email,
            roles=payload.roles,
            permissions=payload.permissions,
            tenant_id=payload.tenant_id,
            aud=payload.aud,
            iss=payload.iss,
            exp=payload.exp,
            iat=payload.iat,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def validate_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Validate API key from X-API-Key header.
    
    Uses APIKeyAuthService for key validation.
    Returns the key ID if valid.
    """
    if not api_key:
        return None
    
    api_key_service = get_api_key_service()
    
    try:
        key_info = api_key_service.validate_key(api_key)
        if not key_info:
            return None
        return key_info.key_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


async def get_current_user(
    token: Optional[TokenPayload] = Depends(validate_jwt_token),
    api_key_id: Optional[str] = Depends(validate_api_key),
) -> CurrentUser:
    """
    Get current authenticated user from JWT or API key.
    
    Supports both JWT tokens (for UI users) and API keys (for service accounts).
    """
    if token:
        # JWT authentication
        return CurrentUser(
            user_id=token.sub,
            username=token.username,
            email=token.email,
            roles=token.roles,
            permissions=token.permissions,
            tenant_id=token.tenant_id,
            is_service_account=False,
        )
    
    if api_key_id:
        # API key authentication (service account)
        api_key_service = get_api_key_service()
        key_info = api_key_service.get_key_info(api_key_id)
        
        if key_info:
            return CurrentUser(
                user_id=f"service:{api_key_id}",
                username=key_info.name,
                email=None,
                roles=["service"],
                permissions=key_info.scopes,
                tenant_id=key_info.tenant_id,
                is_service_account=True,
            )
    
    # No valid authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    token: Optional[TokenPayload] = Depends(validate_jwt_token),
    api_key_id: Optional[str] = Depends(validate_api_key),
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, otherwise return None.
    
    Useful for endpoints that support both authenticated and anonymous access.
    """
    try:
        return await get_current_user(token, api_key_id)
    except HTTPException:
        return None


def require_role(required_roles: list[str]):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(["admin"]))])
    """
    async def check_roles(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
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
    async def check_permissions(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not any(perm in user.permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permissions: {required_permissions}",
            )
        return user
    return check_permissions


def require_tenant(tenant_id: str):
    """
    Dependency factory for tenant-based access control.
    
    Usage:
        @router.get("/tenant/{tenant_id}/data", dependencies=[Depends(require_tenant)])
    """
    async def check_tenant(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.tenant_id != tenant_id and "admin" not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant",
            )
        return user
    return check_tenant


# Common dependencies for easy import
RequireAdmin = Depends(require_role(["admin"]))
RequireUser = Depends(require_role(["user", "admin"]))
RequireReadOnly = Depends(require_permission(["read"]))
