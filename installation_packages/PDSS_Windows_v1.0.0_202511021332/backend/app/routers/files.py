"""
File Upload Router
Handles file uploads for project items
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
import os
import uuid
from pathlib import Path
import logging

from app.database import get_db
from app.models import User, ProjectItem
from app.auth import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

# Configuration
UPLOAD_DIR = Path("/app/uploads")  # Inside Docker container
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
    '.txt', '.csv', '.jpg', '.jpeg', '.png', 
    '.gif', '.zip', '.rar', '.7z'
}

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return Path(filename).suffix.lower()


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename while preserving extension"""
    ext = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{ext}"


@router.post("/upload/project-item/{item_id}")
async def upload_project_item_file(
    item_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["admin", "pm", "pmo", "finance"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file for a project item
    
    Allowed roles: admin, pm, pmo, finance
    Max file size: 50 MB
    Allowed formats: PDF, Office docs, Images, Archives
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check if project item exists
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == item_id)
    )
    project_item = result.scalar_one_or_none()
    
    if not project_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project item #{item_id} not found"
        )
    
    # Read file content
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size (50 MB)"
        )
    
    # Delete old file if exists
    if project_item.file_path:
        old_file_path = UPLOAD_DIR / project_item.file_path
        if old_file_path.exists():
            try:
                old_file_path.unlink()
                logger.info(f"Deleted old file: {old_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete old file: {e}")
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"File saved: {file_path} ({file_size / 1024:.2f} KB)")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )
    
    # Update database
    try:
        await db.execute(
            update(ProjectItem)
            .where(ProjectItem.id == item_id)
            .values(
                file_path=unique_filename,
                file_name=file.filename
            )
        )
        await db.commit()
        logger.info(f"Updated project item #{item_id} with file info")
    except Exception as e:
        # Rollback and delete file if database update fails
        logger.error(f"Database update failed: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update database"
        )
    
    return {
        "message": "File uploaded successfully",
        "item_id": item_id,
        "file_name": file.filename,
        "file_size": file_size,
        "file_path": unique_filename
    }


@router.get("/download/project-item/{item_id}")
async def download_project_item_file(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a file attached to a project item
    
    All authenticated users can download files
    """
    
    # Get project item
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == item_id)
    )
    project_item = result.scalar_one_or_none()
    
    if not project_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project item #{item_id} not found"
        )
    
    if not project_item.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file attached to this project item"
        )
    
    file_path = UPLOAD_DIR / project_item.file_path
    
    if not file_path.exists():
        logger.error(f"File not found on disk: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Return file
    return FileResponse(
        path=str(file_path),
        filename=project_item.file_name or project_item.file_path,
        media_type='application/octet-stream'
    )


@router.delete("/delete/project-item/{item_id}")
async def delete_project_item_file(
    item_id: int,
    current_user: User = Depends(require_role(["admin", "pm", "pmo", "finance"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a file attached to a project item
    
    Allowed roles: admin, pm, pmo, finance
    """
    
    # Get project item
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == item_id)
    )
    project_item = result.scalar_one_or_none()
    
    if not project_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project item #{item_id} not found"
        )
    
    if not project_item.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file attached to this project item"
        )
    
    file_path = UPLOAD_DIR / project_item.file_path
    
    # Delete file from disk
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file from server"
            )
    
    # Update database
    try:
        await db.execute(
            update(ProjectItem)
            .where(ProjectItem.id == item_id)
            .values(
                file_path=None,
                file_name=None
            )
        )
        await db.commit()
        logger.info(f"Removed file info from project item #{item_id}")
    except Exception as e:
        logger.error(f"Database update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update database"
        )
    
    return {
        "message": "File deleted successfully",
        "item_id": item_id
    }


@router.get("/info/project-item/{item_id}")
async def get_project_item_file_info(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get file information for a project item
    
    Returns file metadata without downloading the file
    """
    
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == item_id)
    )
    project_item = result.scalar_one_or_none()
    
    if not project_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project item #{item_id} not found"
        )
    
    if not project_item.file_path:
        return {
            "has_file": False,
            "file_name": None,
            "file_size": None
        }
    
    file_path = UPLOAD_DIR / project_item.file_path
    file_size = file_path.stat().st_size if file_path.exists() else None
    
    return {
        "has_file": True,
        "file_name": project_item.file_name,
        "file_size": file_size,
        "file_exists": file_path.exists()
    }

