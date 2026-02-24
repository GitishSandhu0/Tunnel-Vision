from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JOSEError

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=True)


@lru_cache(maxsize=4)
def _fetch_jwks(jwks_url: str) -> Dict[str, Any]:
    response = httpx.get(jwks_url, timeout=5.0)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Invalid JWKS response format")
    return data


def _get_es256_jwk(settings: Settings, key_id: str) -> Dict[str, Any] | None:
    if not settings.SUPABASE_URL:
        logger.error("SUPABASE_URL is not configured")
        return None

    jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"

    for attempt in range(2):
        try:
            jwks = _fetch_jwks(jwks_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unable to fetch Supabase JWKS: %s", exc)
            return None

        for key in jwks.get("keys", []):
            if isinstance(key, dict) and key.get("kid") == key_id:
                return key

        # Refresh cache once to support key rotation.
        if attempt == 0:
            _fetch_jwks.cache_clear()

    logger.warning("No JWKS key found for kid=%s", key_id)
    return None


def verify_supabase_token(token: str, settings: Settings | None = None) -> Dict[str, Any]:
    """
    Verify a Supabase-issued JWT and return its decoded payload.

    Supports:
    - ES256 tokens signed by Supabase Auth (verified via JWKS by `kid`)
    - HS256 tokens signed with `SUPABASE_JWT_SECRET` (legacy mode)

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

    try:
        header = jwt.get_unverified_header(token)
    except JOSEError as exc:
        logger.warning("Invalid JWT header: %s", exc)
        raise credentials_exception from exc

    algorithm = header.get("alg")
    key: str | Dict[str, Any]
    if algorithm == "ES256":
        key_id = header.get("kid")
        if not key_id:
            logger.warning("Missing kid in ES256 token header")
            raise credentials_exception
        key = _get_es256_jwk(settings, key_id)
        if key is None:
            raise credentials_exception
    elif algorithm == "HS256":
        if not settings.SUPABASE_JWT_SECRET:
            logger.error("SUPABASE_JWT_SECRET is not configured")
            raise credentials_exception
        key = settings.SUPABASE_JWT_SECRET
    else:
        logger.warning("Unsupported Supabase JWT algorithm: %s", algorithm)
        raise credentials_exception

    issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1" if settings.SUPABASE_URL else None

    decode_options: Dict[str, Any] = {"verify_exp": True}
    if not issuer:
        decode_options["verify_iss"] = False

    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=issuer,
            options=decode_options,
        )
    except JOSEError as exc:
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
