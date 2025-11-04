"""
User management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user, require_admin, require_pmo
from app.crud import get_users, get_user, create_user, update_user, delete_user
from app.models import User
from app.schemas import User as UserSchema, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema)
async def create_new_user(
    user: UserCreate,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)"""
    try:
        return await create_user(db, user)
    except Exception as e:
        # Check for duplicate username
        if 'duplicate key' in str(e).lower() or 'unique constraint' in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user.username}' already exists. Please choose a different username."
            )
        # Re-raise other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/", response_model=List[UserSchema])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Get list of users (admin only)"""
    users = await get_users(db, skip=skip, limit=limit)
    return users


@router.get("/pm-list", response_model=List[UserSchema])
async def list_pm_users(
    current_user: User = Depends(require_pmo()),
    db: AsyncSession = Depends(get_db)
):
    """Get list of PM and PMO users for project assignment (PMO or admin only)"""
    from sqlalchemy import select
    result = await db.execute(
        select(User)
        .where(User.role.in_(['pm', 'pmo']))
        .where(User.is_active == True)
        .order_by(User.username)
    )
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserSchema)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)"""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user_by_id(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    try:
        user = await update_user(db, user_id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        # Check for duplicate username
        if 'duplicate key' in str(e).lower() or 'unique constraint' in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username already exists. Please choose a different username."
            )
        # Re-raise other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deleted successfully"}
