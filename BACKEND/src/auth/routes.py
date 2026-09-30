from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.auth.enums import UserRole
from src.auth.models import User
from src.auth.schemas import TokenResponse, UserCreate, UserResponse
from src.config import settings
from src.database import get_db
from src.providers.enums import VerificationStatus
from src.providers.models import ProviderProfile

router = APIRouter(prefix="/auth", tags=["auth"])
password_hash = PasswordHash.recommended()


def handle_unexpected_errors(endpoint):
    @wraps(endpoint)
    def wrapper(*args, **kwargs):
        try:
            return endpoint(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as exc:
            print(exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred",
            ) from exc

    return wrapper


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(user.id), "exp": expires_at},
        settings.secret_key,
        settings.algorithm,
    )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@handle_unexpected_errors
def register_user(user_data: UserCreate, db: Session = Depends(get_db)) -> User:
    if user_data.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is not allowed",
        )

    existing_user = db.scalar(select(User).where(User.email == user_data.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered"
        )

    user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        password_hash=password_hash.hash(user_data.password),
        role=user_data.role,
    )
    db.add(user)
    db.flush()

    if user.role == UserRole.PROVIDER:
        profile = ProviderProfile(
            user_id=user.id,
            bio=user_data.bio or "",
            experience_years=user_data.experience_years or 0,
            location=user_data.location or "",
            area=user_data.area or "",
            verification_status=VerificationStatus.PENDING,
            is_available=True,
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@handle_unexpected_errors
def login_user(
    credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == credentials.username))
    if user is None or not password_hash.verify(
        credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return TokenResponse(access_token=create_access_token(user))


@router.get("/me", response_model=UserResponse)
@handle_unexpected_errors
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
