from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from datetime import timedelta

from api.auth import verify_password, create_access_token, get_current_admin
from config import JWT_EXPIRY_HOURS

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class AdminResponse(BaseModel):
    username: str
    authenticated: bool


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with admin password
    Returns JWT token on success
    """
    if not verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": "admin"},
        expires_delta=timedelta(hours=JWT_EXPIRY_HOURS)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRY_HOURS * 3600
    }


@router.post("/logout")
async def logout(current_admin: dict = Depends(get_current_admin)):
    """
    Logout current admin session
    Note: With JWT, this is handled client-side by removing the token
    """
    return {"success": True, "message": "Выход выполнен успешно"}


@router.get("/me", response_model=AdminResponse)
async def get_current_admin_info(current_admin: dict = Depends(get_current_admin)):
    """
    Get current admin information
    """
    return current_admin
