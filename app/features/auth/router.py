from fastapi import APIRouter, Depends, HTTPException, status

from app.features.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.features.auth.service import AuthService
from app.features.auth.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    """Register a new user. Returns a JWT token immediately."""
    try:
        return service.register(payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    """Login with email and password. Returns a JWT token."""
    try:
        return service.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))