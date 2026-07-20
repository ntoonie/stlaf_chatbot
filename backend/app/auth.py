"""
auth.py - Verifies Supabase-issued JWTs on protected FastAPI routes.

Uses JWKS-based verification (asymmetric ES256), matching Supabase's
current default signing method for new projects - not the legacy
HS256 shared-secret system.
"""

import os
import jwt
from jwt import PyJWKClient
from fastapi import Header, HTTPException

SUPABASE_URL = os.environ.get("SUPABASE_URL")
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json" if SUPABASE_URL else None

_jwks_client: PyJWKClient | None = None


def get_jwks_client() -> PyJWKClient:
    """PyJWKClient fetches and caches Supabase's public signing keys
    automatically, refreshing them if a token references an unknown
    key ID (e.g. after Supabase rotates keys)."""
    global _jwks_client
    if _jwks_client is None:
        if not JWKS_URL:
            raise RuntimeError("SUPABASE_URL not set in .env")
        _jwks_client = PyJWKClient(JWKS_URL)
    return _jwks_client


def verify_jwt(authorization: str = Header(...)) -> dict:
    """FastAPI dependency: verifies the Bearer token on a protected route."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {e}")

    return payload