from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select, update
from typing import List, Optional
import os
import uuid
import logging
from datetime import datetime, date
import shutil
import mimetypes

from app.database import get_db
from app.crud import log_audit
from app.auth import get_current_user
from app.models import User, Supplier, SupplierContact, SupplierDocument, SupplierStatus, ComplianceStatus, RiskLevel
from app.schemas import (
    Supplier as SupplierSchema,
    SupplierCreate,
    SupplierUpdate,
    SupplierWithRelations,
    SupplierListResponse,
    SupplierListWithRelationsResponse,
    SupplierContact as SupplierContactSchema,
    SupplierContactCreate,
    SupplierContactUpdate,
    SupplierContactListResponse,
    SupplierDocument as SupplierDocumentSchema,
    SupplierDocumentCreate,
    SupplierDocumentUpdate,
    SupplierDocumentListResponse
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

# File upload directory
UPLOAD_DIR = "uploads/supplier_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def generate_supplier_id(db: AsyncSession) -> str:
    """Generate unique supplier ID"""
    result = await db.execute(select(func.count()).select_from(Supplier))
    count = result.scalar()
    return f"SUP-{str(count + 1).zfill(5)}"


async def generate_contact_id(db: AsyncSession) -> str:
    """Generate unique contact ID"""
    result = await db.execute(select(func.count()).select_from(SupplierContact))
    count = result.scalar()
    return f"CONT-{str(count + 1).zfill(5)}"


async def generate_document_id(db: AsyncSession) -> str:
    """Generate unique document ID"""
    result = await db.execute(select(func.count()).select_from(SupplierDocument))
    count = result.scalar()
    return f"DOC-{str(count + 1).zfill(5)}"


def validate_file(file: UploadFile) -> tuple[str, str]:
    """Validate uploaded file and return file info"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    return unique_filename, file.filename


# Supplier CRUD Operations
@router.get("/", response_model=SupplierListWithRelationsResponse)
async def list_suppliers(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[SupplierStatus] = Query(None),
    compliance_status: Optional[ComplianceStatus] = Query(None),
    risk_level: Optional[RiskLevel] = Query(None),
    country: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List suppliers with filtering and pagination"""
    query = select(Supplier).options(joinedload(Supplier.contacts), joinedload(Supplier.documents))
    
    # Apply filters
    if search:
        search_filter = or_(
            Supplier.company_name.ilike(f"%{search}%"),
            Supplier.supplier_id.ilike(f"%{search}%"),
            Supplier.country.ilike(f"%{search}%"),
            Supplier.city.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    if status:
        query = query.where(Supplier.status == status)
    
    if compliance_status:
        query = query.where(Supplier.compliance_status == compliance_status)
    
    if risk_level:
        query = query.where(Supplier.risk_level == risk_level)
    
    if country:
        query = query.where(Supplier.country.ilike(f"%{country}%"))
    
    # Count total results
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    # Execute query
    result = await db.execute(query)
    suppliers = result.scalars().unique().all()
    
    # Calculate pages
    pages = (total + size - 1) // size
    
    return SupplierListWithRelationsResponse(
        suppliers=suppliers,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


# Supplier Contact Operations - MUST come before dynamic routes
@router.get("/contacts", response_model=SupplierContactListResponse)
async def list_all_contacts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all contacts with optional filters"""
    try:
        # Build query with joinedload to include supplier data
        query = select(SupplierContact).options(joinedload(SupplierContact.supplier))
        
        # Apply filters
        if search:
            # For search, we need to join with Supplier to search by company name
            query = query.join(Supplier).where(
                or_(
                    SupplierContact.full_name.ilike(f"%{search}%"),
                    SupplierContact.email.ilike(f"%{search}%"),
                    SupplierContact.job_title.ilike(f"%{search}%"),
                    SupplierContact.department.ilike(f"%{search}%"),
                    Supplier.company_name.ilike(f"%{search}%")
                )
            )
        
        if supplier_id:
            query = query.where(SupplierContact.supplier_id == supplier_id)
        
        # Get total count - use simple count without join
        count_query = select(func.count(SupplierContact.id))
        
        # Apply same filters to count query
        if search:
            count_query = count_query.join(Supplier).where(
                or_(
                    SupplierContact.full_name.ilike(f"%{search}%"),
                    SupplierContact.email.ilike(f"%{search}%"),
                    SupplierContact.job_title.ilike(f"%{search}%"),
                    SupplierContact.department.ilike(f"%{search}%"),
                    Supplier.company_name.ilike(f"%{search}%")
                )
            )
        
        if supplier_id:
            count_query = count_query.where(SupplierContact.supplier_id == supplier_id)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # Execute query
        result = await db.execute(query)
        contacts = result.scalars().all()
        
        # Calculate pages
        pages = (total + size - 1) // size
        
        return {
            "contacts": contacts,
            "total": total,
            "page": page,
            "pages": pages,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list contacts: {str(e)}")


@router.get("/{supplier_id}", response_model=SupplierWithRelations)
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get supplier by ID with contacts and documents"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return supplier


@router.post("/", response_model=SupplierSchema)
async def create_supplier(
    supplier_data: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Create new supplier"""
    # Generate supplier ID if not provided
    if not supplier_data.supplier_id:
        supplier_data.supplier_id = await generate_supplier_id(db)
    
    # Check if supplier ID already exists
    result = await db.execute(select(Supplier).where(Supplier.supplier_id == supplier_data.supplier_id))
    existing_supplier = result.scalar_one_or_none()
    if existing_supplier:
        raise HTTPException(status_code=400, detail="Supplier ID already exists")
    
    # Create supplier
    supplier = Supplier(
        **supplier_data.dict(),
        created_by_id=current_user.id
    )
    
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    
    # Audit
    try:
        client_host = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        await log_audit(
            db,
            user_id=current_user.id if current_user else None,
            action="SUPPLIER_CREATE",
            entity_type="supplier",
            entity_id=supplier.id,
            details={"company_name": supplier.company_name, "supplier_id": supplier.supplier_id},
            ip_address=client_host,
            user_agent=ua,
        )
    except Exception:
        pass
    
    return supplier


@router.put("/{supplier_id}", response_model=SupplierSchema)
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Update supplier"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Update fields
    update_data = supplier_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    await db.commit()
    await db.refresh(supplier)
    
    # Audit
    try:
        client_host = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        await log_audit(
            db,
            user_id=current_user.id if current_user else None,
            action="SUPPLIER_UPDATE",
            entity_type="supplier",
            entity_id=supplier.id,
            details=supplier_data.dict(exclude_unset=True),
            ip_address=client_host,
            user_agent=ua,
        )
    except Exception:
        pass
    
    return supplier


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Delete supplier"""
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Guard: prevent deletion if supplier is used in any procurement options
    # ProcurementOption currently references supplier by name
    from sqlalchemy import select, func
    from app.models import ProcurementOption as ProcurementOptionModel

    po_count_result = await db.execute(
        select(func.count(ProcurementOptionModel.id)).where(
            ProcurementOptionModel.is_active == True,
            ProcurementOptionModel.supplier_name == supplier.company_name
        )
    )
    if (po_count_result.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete supplier: it is linked to existing procurement options. Set status to INACTIVE instead."
        )

    # Delete associated files
    for document in supplier.documents:
        file_path = os.path.join(UPLOAD_DIR, document.file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    await db.delete(supplier)
    await db.commit()
    
    # Audit
    try:
        client_host = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        await log_audit(
            db,
            user_id=current_user.id if current_user else None,
            action="SUPPLIER_DELETE",
            entity_type="supplier",
            entity_id=supplier_id,
            details={"company_name": supplier.company_name, "supplier_id": supplier.supplier_id},
            ip_address=client_host,
            user_agent=ua,
        )
    except Exception:
        pass
    
    return {"message": "Supplier deleted successfully"}



@router.get("/{supplier_id}/contacts", response_model=SupplierContactListResponse)
async def list_supplier_contacts(
    supplier_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List contacts for a supplier"""
    # Check if supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    query = db.query(SupplierContact).filter(SupplierContact.supplier_id == supplier_id)
    
    total = query.count()
    contacts = query.offset((page - 1) * size).limit(size).all()
    
    return SupplierContactListResponse(
        contacts=contacts,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.post("/{supplier_id}/contacts", response_model=SupplierContactSchema)
async def create_supplier_contact(
    supplier_id: int,
    contact_data: SupplierContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new contact for supplier"""
    # Check if supplier exists
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Generate contact ID if not provided
    if not contact_data.contact_id:
        contact_data.contact_id = await generate_contact_id(db)
    
    # Check if contact ID already exists
    result = await db.execute(select(SupplierContact).where(SupplierContact.contact_id == contact_data.contact_id))
    existing_contact = result.scalar_one_or_none()
    if existing_contact:
        raise HTTPException(status_code=400, detail="Contact ID already exists")
    
    # If this is set as primary contact, unset other primary contacts
    if contact_data.is_primary_contact:
        await db.execute(
            update(SupplierContact)
            .where(
                and_(
                    SupplierContact.supplier_id == supplier_id,
                    SupplierContact.is_primary_contact == True
                )
            )
            .values(is_primary_contact=False)
        )
    
    # Create contact
    contact = SupplierContact(
        **contact_data.dict(),
        supplier_id=supplier_id,
        created_by_id=current_user.id
    )
    
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    
    # Load the supplier relationship to avoid greenlet_spawn error
    await db.refresh(contact, ['supplier'])
    
    return contact


@router.put("/{supplier_id}/contacts/{contact_id}", response_model=SupplierContactSchema)
async def update_supplier_contact(
    supplier_id: int,
    contact_id: int,
    contact_data: SupplierContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update supplier contact"""
    contact = db.query(SupplierContact).filter(
        and_(
            SupplierContact.id == contact_id,
            SupplierContact.supplier_id == supplier_id
        )
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # If this is set as primary contact, unset other primary contacts
    if contact_data.is_primary_contact:
        db.query(SupplierContact).filter(
            and_(
                SupplierContact.supplier_id == supplier_id,
                SupplierContact.id != contact_id,
                SupplierContact.is_primary_contact == True
            )
        ).update({"is_primary_contact": False})
    
    # Update fields
    update_data = contact_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    db.commit()
    db.refresh(contact)
    
    return contact


@router.delete("/{supplier_id}/contacts/{contact_id}")
async def delete_supplier_contact(
    supplier_id: int,
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete supplier contact"""
    contact = db.query(SupplierContact).filter(
        and_(
            SupplierContact.id == contact_id,
            SupplierContact.supplier_id == supplier_id
        )
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    db.delete(contact)
    db.commit()
    
    return {"message": "Contact deleted successfully"}


# Supplier Document Operations
@router.get("/{supplier_id}/documents", response_model=SupplierDocumentListResponse)
async def list_supplier_documents(
    supplier_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents for a supplier"""
    # Check if supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    query = db.query(SupplierDocument).filter(SupplierDocument.supplier_id == supplier_id)
    
    total = query.count()
    documents = query.offset((page - 1) * size).limit(size).all()
    
    return SupplierDocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.post("/{supplier_id}/documents", response_model=SupplierDocumentSchema)
async def upload_supplier_document(
    supplier_id: int,
    file: UploadFile = File(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    document_number: Optional[str] = Form(None),
    issued_by: Optional[str] = Form(None),
    issued_date: Optional[date] = Form(None),
    expiry_date: Optional[date] = Form(None),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload document for supplier"""
    # Check if supplier exists
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Validate file
    unique_filename, original_filename = validate_file(file)
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file info
    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(original_filename)
    
    # Generate document ID
    document_id = await generate_document_id(db)
    
    # Create document record
    document = SupplierDocument(
        document_id=document_id,
        supplier_id=supplier_id,
        document_name=document_name,
        document_type=document_type,
        file_name=unique_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        description=description,
        document_number=document_number,
        issued_by=issued_by,
        issued_date=issued_date,
        expiry_date=expiry_date,
        notes=notes,
        created_by_id=current_user.id
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    return document


@router.get("/{supplier_id}/documents/{document_id}/download")
async def download_supplier_document(
    supplier_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download supplier document"""
    document = db.query(SupplierDocument).filter(
        and_(
            SupplierDocument.id == document_id,
            SupplierDocument.supplier_id == supplier_id
        )
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=document.file_path,
        filename=document.document_name,
        media_type=document.mime_type or 'application/octet-stream'
    )


@router.put("/{supplier_id}/documents/{document_id}", response_model=SupplierDocumentSchema)
async def update_supplier_document(
    supplier_id: int,
    document_id: int,
    document_data: SupplierDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update supplier document metadata"""
    document = db.query(SupplierDocument).filter(
        and_(
            SupplierDocument.id == document_id,
            SupplierDocument.supplier_id == supplier_id
        )
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update fields
    update_data = document_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    
    return document


@router.delete("/{supplier_id}/documents/{document_id}")
async def delete_supplier_document(
    supplier_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete supplier document"""
    document = db.query(SupplierDocument).filter(
        and_(
            SupplierDocument.id == document_id,
            SupplierDocument.supplier_id == supplier_id
        )
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from disk
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


# Utility endpoints
@router.get("/categories/list")
async def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of unique categories from suppliers"""
    categories = db.query(Supplier.product_service_lines).filter(
        Supplier.product_service_lines.isnot(None)
    ).all()
    
    unique_categories = set()
    for category_list in categories:
        if category_list:
            unique_categories.update(category_list)
    
    return {"categories": sorted(list(unique_categories))}


@router.get("/industries/list")
async def list_industries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of unique industries from suppliers"""
    industries = db.query(Supplier.main_markets_regions).filter(
        Supplier.main_markets_regions.isnot(None)
    ).all()
    
    unique_industries = set()
    for industry_list in industries:
        if industry_list:
            unique_industries.update(industry_list)
    
    return {"industries": sorted(list(unique_industries))}


@router.get("/countries/list")
async def list_countries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of unique countries from suppliers"""
    countries = db.query(Supplier.country).filter(
        Supplier.country.isnot(None)
    ).distinct().all()
    
    return {"countries": sorted([country[0] for country in countries if country[0]])}
