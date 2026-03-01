"""
JWT Authentication — Replaces plaintext API-Key auth.

Uses:
- bcrypt_sha256 for password hashing (CLAUDE.md Regel!)
- python-jose for JWT token creation/verification
- Access + Refresh token pattern

IMPORTANT: Uses bcrypt_sha256, NOT bcrypt (known login issues with bcrypt alone).
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)

# Configuration
from app.config import settings

_INSECURE_DEFAULT = "rechnungswerk-secret-change-in-production"

# Startup check: refuse to run with insecure secret when auth is enabled
if settings.require_api_key and (
    not settings.jwt_secret_key or settings.jwt_secret_key == _INSECURE_DEFAULT
):
    raise RuntimeError(
        "JWT_SECRET_KEY is not set or still uses the insecure default. "
        "Set a strong JWT_SECRET_KEY in your environment or .env file."
    )

SECRET_KEY = settings.jwt_secret_key or _INSECURE_DEFAULT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _get_password_hasher():
    """Get passlib CryptContext with bcrypt_sha256 (CLAUDE.md Pflicht!)."""
    from passlib.context import CryptContext
    return CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt_sha256."""
    pwd_context = _get_password_hasher()
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    pwd_context = _get_password_hasher()
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    from jose import jwt

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token (longer expiry)."""
    from jose import jwt

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    from jose import jwt, JWTError

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token ungueltig: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    """FastAPI dependency to get current authenticated user from JWT."""
    # If JWT auth is not enabled, allow access (dev mode)
    if not settings.require_api_key:
        return {"user_id": "dev-user", "email": "dev@localhost", "role": "member"}

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentifizierung erforderlich",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungueltiger Token-Typ",
        )

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "user"),
        "org_id": payload.get("org_id"),
    }


def ensure_invoice_belongs_to_org(invoice, org_id: str | None) -> None:
    """Raise 403 if the invoice does not belong to the caller's organization.

    In dev mode (org_id is None) or when the invoice has no organization_id,
    the check is skipped to maintain backwards compatibility.
    """
    if org_id is None:
        return
    if getattr(invoice, "organization_id", None) is None:
        return
    if str(invoice.organization_id) != str(org_id):
        raise HTTPException(
            status_code=403,
            detail="Kein Zugriff auf diese Rechnung",
        )
