"""
Excel import/export endpoints for all modules
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO
from app.database import get_db
from app.auth import get_current_user, require_pm, require_procurement, require_finance
from app.excel_handler import ExcelHandler
from app.models import User
from app.schemas import ExcelImportResponse

router = APIRouter(prefix="/excel", tags=["excel-import-export"])


# Project Items Excel operations
@router.post("/import/items", response_model=ExcelImportResponse)
async def import_project_items_from_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Import project items from Excel file (PM only)"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    content = await file.read()
    return await ExcelHandler.import_project_items(db, content)


@router.get("/export/items")
async def export_project_items_to_excel(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export project items to Excel file"""
    excel_data = await ExcelHandler.export_project_items(db, project_id)
    
    filename = f"project_items_{project_id}.xlsx" if project_id else "all_project_items.xlsx"
    
    return StreamingResponse(
        BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/templates/items")
async def download_project_items_template():
    """Download project items Excel template"""
    template_data = ExcelHandler.create_project_items_template()
    
    return StreamingResponse(
        BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=project_items_template.xlsx"}
    )


# Procurement Options Excel operations
@router.post("/import/procurement", response_model=ExcelImportResponse)
async def import_procurement_options_from_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(require_procurement()),
    db: AsyncSession = Depends(get_db)
):
    """Import procurement options from Excel file (procurement specialist only)"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    content = await file.read()
    return await ExcelHandler.import_procurement_options(db, content)


@router.get("/export/procurement")
async def export_procurement_options_to_excel(
    item_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export procurement options to Excel file"""
    excel_data = await ExcelHandler.export_procurement_options(db, item_code)
    
    filename = f"procurement_options_{item_code}.xlsx" if item_code else "all_procurement_options.xlsx"
    
    return StreamingResponse(
        BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/templates/procurement")
async def download_procurement_options_template():
    """Download procurement options Excel template"""
    template_data = ExcelHandler.create_procurement_options_template()
    
    return StreamingResponse(
        BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=procurement_options_template.xlsx"}
    )
