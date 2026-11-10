from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import bearer_scheme, get_current_user
from app.models.models import User
from app.redis_client import delete_session
from app.schemas.auth import LoginRequest, OtpRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = AuthService.register(db, payload.username, payload.password, payload.email)
    return {"username": user.username}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.start_login(db, payload.identifier, payload.password)


@router.post("/verify-otp")
def verify_otp(payload: OtpRequest, db: Session = Depends(get_db)):
    return AuthService.finish_login(db, payload.username, payload.otp)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"username": user.username}


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user: User = Depends(get_current_user),
):
    delete_session(credentials.credentials)
    return {"success": True}
