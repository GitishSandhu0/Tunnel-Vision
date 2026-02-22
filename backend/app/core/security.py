from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=True)


def verify_supabase_token(token: str, settings: Settings | None = None) -> Dict[str, Any]:
    """
    Verify a Supabase-issued JWT and return its decoded payload.

    Supabase signs JWTs with HS256 using the project's JWT secret.
    The audience claim is always "authenticated" for logged-in users.

    Raises:
        HTTPException 401 if the token is invalid or expired.
    """
    if settings is None:
        settings = get_settings()

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not settings.SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET is not configured")
        raise credentials_exception

    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
    except JWTError as exc:
        logger.warning("JWT verification failed: %s", exc)
        raise credentials_exception from exc

    # Supabase stores the user UUID in the "sub" claim
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_exception

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts and validates the Bearer token from the
    Authorization header, returning the decoded JWT payload.

    Usage:
        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user)):
            user_id = user["sub"]
    """
    return verify_supabase_token(credentials.credentials, settings)
