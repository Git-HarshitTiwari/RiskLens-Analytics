from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from api.auth import authenticate_user, create_access_token
from api.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    Login endpoint — returns JWT access token.
    Use this token in Authorization: Bearer <token> header
    to access protected endpoints.
    """
    if not authenticate_user(request.username, request.password):
        logger.warning("Failed login attempt", extra={
            "username": request.username
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    token = create_access_token(data={"sub": request.username})

    logger.info("Successful login", extra={
        "username": request.username
    })

    from config.settings import settings
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.jwt_expire_minutes
    )


@router.get("/me")
def get_current_user_info(
    user: dict = __import__(
        'fastapi', fromlist=['Depends']
    ).Depends(
        __import__('api.auth', fromlist=['get_current_user']).get_current_user
    )
):
    """Returns info about the currently authenticated user."""
    return {
        "username": user["username"],
        "message": "Authenticated successfully"
    }