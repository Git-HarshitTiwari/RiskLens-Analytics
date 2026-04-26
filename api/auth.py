from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.settings import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.
    Token expires after jwt_expire_minutes (default 60 min).
    """
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload.update({"exp": expire})
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises HTTPException if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(username: str, password: str) -> bool:
    """
    Validate credentials against .env admin credentials.
    Simple single-user auth — sufficient for demo/portfolio purposes.
    In production this would query a users table.
    """
    return (
        username == settings.admin_username
        and password == settings.admin_password
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    FastAPI dependency — protects any route it's added to.
    Usage: add `user = Depends(get_current_user)` to route function.
    Extracts and validates Bearer token from Authorization header.
    """
    token = credentials.credentials
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    return {"username": username}