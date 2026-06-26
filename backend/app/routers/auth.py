"""
Authentication endpoints
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.crud import log_audit
from app.auth import authenticate_user, create_access_token, get_current_user
from app.crud import create_user
from app.schemas import UserCreate, UserLogin, Token, User, UserMe, UserRoleSummary
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user (admin only)"""
    # Check if user already exists
    existing_user = await authenticate_user(db, user.username, "")
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    db_user = await create_user(db, user)
    return db_user


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Login and get access token"""
    user = await authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Audit: LOGIN
    try:
        client_host = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        await log_audit(
            db,
            user_id=user.id,
            action="LOGIN",
            entity_type="user",
            entity_id=user.id,
            details={"username": user.username},
            ip_address=client_host,
            user_agent=ua,
        )
    except Exception:
        pass

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserMe)
async def read_users_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user information including RBAC context."""
    from app.services.rbac_service import get_effective_permissions, get_user_role_summaries

    permissions = sorted(await get_effective_permissions(db, current_user))
    role_summaries = await get_user_role_summaries(db, current_user.id)
    return UserMe(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        created_at=current_user.created_at,
        is_active=current_user.is_active,
        permissions=permissions,
        roles=[UserRoleSummary(**item) for item in role_summaries],
        permission_enforcement_enabled=settings.enable_permission_enforcement,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
