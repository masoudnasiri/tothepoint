from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import User as UserSchema

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT token handling
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Ensure password is not too long for bcrypt (72 bytes max)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, but try to truncate at a character boundary
        truncated = password_bytes[:72]
        # Find the last complete character
        while len(truncated) > 0 and truncated[-1] & 0x80 and not (truncated[-1] & 0x40):
            truncated = truncated[:-1]
        password = truncated.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Union[User, bool]:
    """Authenticate a user with username and password"""
    user = await get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    if not user.is_active:
        return False
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


def require_role(allowed_roles: list[str]):
    """Decorator to require specific user roles"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_admin():
    """Require admin role"""
    return require_role(["admin"])


def require_pm():
    """Require project manager or admin role"""
    return require_role(["pm", "admin"])


def require_pmo():
    """Require PMO (Project Management Office) or admin role"""
    return require_role(["pmo", "admin"])


def require_pm_or_pmo():
    """Require PM, PMO, or admin role"""
    return require_role(["pm", "pmo", "admin"])


def require_procurement():
    """Require procurement specialist or admin role"""
    return require_role(["procurement", "admin"])


def require_finance():
    """Require finance user or admin role"""
    return require_role(["finance", "admin"])


def require_analytics_access():
    """Require analytics access (admin, finance, pmo) - PM excluded"""
    return require_role(["admin", "finance", "pmo", "procurement"])


async def get_user_projects(db: AsyncSession, user: User) -> list[int]:
    """Get list of project IDs that a user has access to"""
    if user.role in ["admin", "pmo"]:
        # Admin and PMO can see all projects
        from sqlalchemy import select
        from app.models import Project
        result = await db.execute(select(Project.id).where(Project.is_active == True))
        return [row[0] for row in result.fetchall()]
    elif user.role == "pm":
        # PM can only see assigned projects
        from sqlalchemy import select
        from app.models import ProjectAssignment
        result = await db.execute(
            select(ProjectAssignment.project_id)
            .where(ProjectAssignment.user_id == user.id)
        )
        return [row[0] for row in result.fetchall()]
    else:
        # Procurement and Finance users don't have project-specific access
        return []


def can_access_project(user: User, project_id: int, user_projects: list[int]) -> bool:
    """Check if user can access a specific project"""
    if user.role in ["admin", "pmo", "procurement", "finance"]:
        return True
    elif user.role == "pm":
        return project_id in user_projects
    return False
