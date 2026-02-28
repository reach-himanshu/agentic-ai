"""
Authentication middleware with JWT validation and role-based access control.
For POC, this uses mock tokens. In production, integrate with Entra ID.
"""
from typing import Annotated, Callable
from functools import wraps

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Decoded token data."""
    sub: str  # User ID
    name: str
    email: str
    roles: list[str]


# Mock users for POC (matches frontend demo accounts)
MOCK_USERS = {
    "mock-admin-token": TokenData(
        sub="user-001",
        name="John Smith",
        email="john.smith@company.com",
        roles=["APP_ROLE_ADMIN", "APP_ROLE_SALES"],
    ),
    "mock-sales-token": TokenData(
        sub="user-002",
        name="Sarah Wilson",
        email="sarah.wilson@company.com",
        roles=["APP_ROLE_SALES"],
    ),
    "mock-viewer-token": TokenData(
        sub="user-003",
        name="Mike Johnson",
        email="mike.johnson@company.com",
        roles=["APP_ROLE_VIEWER"],
    ),
    "mock-user-token": TokenData(
        sub="user-004",
        name="General User",
        email="user@company.com",
        roles=["APP_ROLE_USER"],
    ),
    "MOCK_TOKEN": TokenData(
        sub="user-001",
        name="Dev User",
        email="dev@opsiq.local",
        roles=["APP_ROLE_ADMIN", "APP_ROLE_SALES"],
    ),
}


def decode_token(token: str) -> TokenData:
    """
    Decode and validate JWT token.
    For POC, accepts mock tokens. Production would validate against Entra ID.
    """
    # Check for mock tokens first (POC mode)
    if settings.use_mock_data and token in MOCK_USERS:
        return MOCK_USERS[token]
    
    # Try to decode as real JWT
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenData(
            sub=payload.get("sub", ""),
            name=payload.get("name", "Unknown"),
            email=payload.get("email", ""),
            roles=payload.get("roles", []),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TokenData:
    """
    Dependency to get current authenticated user from token.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return decode_token(credentials.credentials)


def require_roles(*required_roles: str):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(user: Annotated[TokenData, Depends(require_roles("APP_ROLE_ADMIN"))]):
            ...
    """
    async def role_checker(
        user: Annotated[TokenData, Depends(get_current_user)],
    ) -> TokenData:
        # Check if user has at least one of the required roles
        user_roles = set(user.roles)
        required = set(required_roles)
        
        if not user_roles.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {list(required_roles)}",
            )
        
        return user
    
    return role_checker


# Convenience dependencies
CurrentUser = Annotated[TokenData, Depends(get_current_user)]
AdminUser = Annotated[TokenData, Depends(require_roles("APP_ROLE_ADMIN"))]
SalesUser = Annotated[TokenData, Depends(require_roles("APP_ROLE_ADMIN", "APP_ROLE_SALES"))]
