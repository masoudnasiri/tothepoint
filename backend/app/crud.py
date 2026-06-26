"""
CRUD operations for database interactions
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.models import (
    User, Project, ProjectAssignment, ProjectPhase, ProjectItem, 
    ProcurementOption, BudgetData, OptimizationResult, DecisionFactorWeight,
    DeliveryOption, FinalizedDecision, CashflowEvent, ItemSubItem, ProjectItemSubItem, AuditLog
)
from app.schemas import (
    UserCreate, UserUpdate, ProjectCreate, ProjectUpdate,
    ProjectPhaseCreate, ProjectPhaseUpdate,
    ProjectItemCreate, ProjectItemUpdate, ProcurementOptionCreate,
    ProcurementOptionUpdate, BudgetDataCreate, BudgetDataUpdate,
    DecisionFactorWeightCreate, DecisionFactorWeightUpdate,
    DeliveryOptionCreate, DeliveryOptionUpdate
)
from app.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)
async def log_audit(
    db: AsyncSession,
    *,
    user_id: Optional[int],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Write an audit log row. Non-blocking best-effort (errors ignored)."""
    try:
        log_row = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log_row)
        # Keep audit writes inside caller transaction scope.
        await db.flush()
    except Exception as e:
        # Don't break main flow due to audit failures
        logger.warning(f"Audit log write failed: {e}")



# User CRUD operations
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Create a new user"""
    from app.services.rbac_service import assign_user_system_role_for_legacy

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    await assign_user_system_role_for_legacy(db, db_user)
    await db.commit()
    return db_user


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Get list of users with pagination"""
    result = await db.execute(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    return result.scalars().all()


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user"""
    from app.models import Role, UserRole
    from app.security.permission_registry import LEGACY_ROLE_TO_SYSTEM_ROLE
    from app.services.rbac_service import assign_user_system_role_for_legacy

    update_data = user_update.dict(exclude_unset=True)
    if not update_data:
        return await get_user(db, user_id)
    
    # Hash password if it's being updated
    if 'password' in update_data and update_data['password']:
        update_data['password_hash'] = get_password_hash(update_data['password'])
        del update_data['password']  # Remove plain password
    
    await db.execute(
        update(User).where(User.id == user_id).values(**update_data)
    )
    await db.commit()
    user = await get_user(db, user_id)
    if user and 'role' in update_data:
        system_code = LEGACY_ROLE_TO_SYSTEM_ROLE.get(user.role)
        if system_code:
            role_result = await db.execute(select(Role).where(Role.code == system_code))
            role = role_result.scalar_one_or_none()
            if role:
                await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
                await assign_user_system_role_for_legacy(db, user)
                await db.commit()
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Delete user"""
    result = await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return result.rowcount > 0


# Project CRUD operations
async def create_project(db: AsyncSession, project: ProjectCreate) -> Project:
    """Create a new project"""
    db_project = Project(**project.dict())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


async def get_project(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Get project by ID with related phases"""
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.project_items),
            selectinload(Project.phases)
        )
        .where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def get_projects(db: AsyncSession, skip: int = 0, limit: int = 100, 
                      user_projects: Optional[List[int]] = None) -> List[Project]:
    """Get list of projects with optional filtering for user access"""
    query = select(Project).where(Project.is_active == True)
    
    if user_projects is not None:
        query = query.where(Project.id.in_(user_projects))
    
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Project.created_at.desc())
    )
    return result.scalars().all()


async def update_project(db: AsyncSession, project_id: int, project_update: ProjectUpdate) -> Optional[Project]:
    """Update project"""
    update_data = project_update.dict(exclude_unset=True)
    if not update_data:
        return await get_project(db, project_id)
    
    await db.execute(
        update(Project).where(Project.id == project_id).values(**update_data)
    )
    await db.commit()
    return await get_project(db, project_id)


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    """Delete project"""
    result = await db.execute(delete(Project).where(Project.id == project_id))
    await db.commit()
    return result.rowcount > 0


# Project Assignment CRUD operations
async def assign_user_to_project(db: AsyncSession, user_id: int, project_id: int) -> ProjectAssignment:
    """Assign user to project"""
    assignment = ProjectAssignment(user_id=user_id, project_id=project_id)
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def remove_user_from_project(db: AsyncSession, user_id: int, project_id: int) -> bool:
    """Remove user from project"""
    result = await db.execute(
        delete(ProjectAssignment).where(
            and_(ProjectAssignment.user_id == user_id, 
                 ProjectAssignment.project_id == project_id)
        )
    )
    await db.commit()
    return result.rowcount > 0


async def get_user_project_assignments(db: AsyncSession, user_id: int) -> List[ProjectAssignment]:
    """Get user's project assignments"""
    result = await db.execute(
        select(ProjectAssignment)
        .options(selectinload(ProjectAssignment.project))
        .where(ProjectAssignment.user_id == user_id)
    )
    return result.scalars().all()


# Project Item CRUD operations
async def create_project_item(db: AsyncSession, item: ProjectItemCreate) -> ProjectItem:
    """
    Create a new project item
    
    If master_item_id is provided:
    - Fetches master item and denormalizes item_code and item_name
    If not provided (backward compatibility):
    - Uses provided item_code and item_name
    """
    from app.models import ItemMaster
    
    item_dict = item.dict()
    
    # If master_item_id is provided, denormalize from master
    if item_dict.get('master_item_id'):
        master_result = await db.execute(
            select(ItemMaster).where(ItemMaster.id == item_dict['master_item_id'])
        )
        master_item = master_result.scalar_one_or_none()
        
        if not master_item:
            raise ValueError(f"Master item #{item_dict['master_item_id']} not found")
        
        if not master_item.is_active:
            raise ValueError(f"Master item {master_item.item_code} is inactive")
        
        # Denormalize fields from master
        item_dict['item_code'] = master_item.item_code
        item_dict['item_name'] = master_item.item_name
    
    # Extract sub-items quantities if present
    sub_items_payload = item_dict.pop('sub_items', None)

    # Create project item
    db_item = ProjectItem(**item_dict)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    # Create project sub-item rows
    if sub_items_payload:
        for entry in sub_items_payload:
            sub_id = entry.get('sub_item_id')
            qty = entry.get('quantity', 0)
            if sub_id is None:
                continue
            # Ensure sub-item exists
            exists_result = await db.execute(select(ItemSubItem).where(ItemSubItem.id == sub_id))
            if exists_result.scalar_one_or_none() is None:
                continue
            db_rel = ProjectItemSubItem(
                project_item_id=db_item.id,
                item_subitem_id=sub_id,
                quantity=qty or 0,
            )
            db.add(db_rel)
        await db.commit()

    return db_item


async def get_project_item(db: AsyncSession, item_id: int) -> Optional[ProjectItem]:
    """Get project item by ID"""
    result = await db.execute(
        select(ProjectItem)
        .options(selectinload(ProjectItem.project))
        .where(ProjectItem.id == item_id)
    )
    return result.scalar_one_or_none()


async def get_project_items(db: AsyncSession, project_id: int, skip: int = 0, limit: int = 100) -> List[ProjectItem]:
    """Get project items for a specific project"""
    result = await db.execute(
        select(ProjectItem)
        .where(ProjectItem.project_id == project_id)
        .offset(skip)
        .limit(limit)
        .order_by(ProjectItem.created_at.desc())
    )
    return result.scalars().all()


async def update_project_item(db: AsyncSession, item_id: int, item_update: ProjectItemUpdate) -> Optional[ProjectItem]:
    """Update project item"""
    update_data = item_update.dict(exclude_unset=True)
    if not update_data:
        return await get_project_item(db, item_id)
    
    # Pull out sub-items payload if provided
    sub_items_payload = update_data.pop('sub_items', None)

    await db.execute(
        update(ProjectItem).where(ProjectItem.id == item_id).values(**update_data)
    )
    await db.commit()

    if sub_items_payload is not None:
        # Replace strategy: delete and reinsert
        await db.execute(delete(ProjectItemSubItem).where(ProjectItemSubItem.project_item_id == item_id))
        for entry in sub_items_payload:
            sub_id = entry.get('sub_item_id')
            qty = entry.get('quantity', 0)
            if sub_id is None:
                continue
            exists_result = await db.execute(select(ItemSubItem).where(ItemSubItem.id == sub_id))
            if exists_result.scalar_one_or_none() is None:
                continue
            db_rel = ProjectItemSubItem(
                project_item_id=item_id,
                item_subitem_id=sub_id,
                quantity=qty or 0,
            )
            db.add(db_rel)
        await db.commit()

    return await get_project_item(db, item_id)


async def delete_project_item(db: AsyncSession, item_id: int) -> bool:
    """Delete project item"""
    result = await db.execute(delete(ProjectItem).where(ProjectItem.id == item_id))
    await db.commit()
    return result.rowcount > 0


async def finalize_project_item(db: AsyncSession, item_id: int, finalized_by: int, finalize_data: 'ProjectItemFinalize') -> Optional[ProjectItem]:
    """Finalize a project item (PMO only) - makes it visible in procurement"""
    from datetime import datetime
    from app.schemas import ProjectItemFinalize
    
    # Get the current item
    result = await db.execute(select(ProjectItem).where(ProjectItem.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        return None
    
    # Update finalization fields
    item.is_finalized = finalize_data.is_finalized
    item.finalized_by = finalized_by
    item.finalized_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(item)
    return item


# Procurement Option CRUD operations
async def create_procurement_option(db: AsyncSession, option: ProcurementOptionCreate) -> ProcurementOption:
    """Create a new procurement option with Phase 3 dual-mode validation"""
    from app.validators.package_validators import (
        validate_package_or_legacy_reference,
        validate_supplier_reference,
        resolve_package_from_project_item,
        log_feature_flag_usage
    )
    from app.services.audit_service import log_phase3_operation
    from app.services.procurement_financials_service import (
        apply_procurement_option_persistence_contract,
        synchronize_procurement_option_legacy_pricing_fields,
    )
    from app.config import settings
    from app.models import User
    
    # Phase 3: Validate package/legacy reference
    try:
        ref_info = validate_package_or_legacy_reference(
            package_id=getattr(option, 'package_id', None),
            project_item_id=getattr(option, 'project_item_id', None),
            item_code=getattr(option, 'item_code', None),
            context="procurement option"
        )
    except Exception as e:
        raise ValueError(str(e))
    
    # Phase 3: Resolve package_id from project_item_id if needed
    package_id_to_use = ref_info.get('package_id')
    if not package_id_to_use and ref_info.get('project_item_id') and settings.enable_package_procurement:
        package_id_to_use = await resolve_package_from_project_item(
            db, ref_info['project_item_id'], create_if_missing=False
        )
        if package_id_to_use:
            ref_info['package_id'] = package_id_to_use
    
    # Phase 3: Validate supplier reference
    supplier_info = await validate_supplier_reference(
        db,
        supplier_id=getattr(option, 'supplier_id', None),
        supplier_name=getattr(option, 'supplier_name', None),
        context="procurement option"
    )
    
    # Convert to dict and handle Decimal serialization for JSON fields
    option_data = option.dict()
    
    # Phase 3: Set package_id from ref_info (preserves provided package_id even if flag is off)
    if ref_info.get('package_id'):
        option_data['package_id'] = ref_info['package_id']
    
    # Phase 3: Set supplier_id if validated
    if supplier_info.get('supplier_id'):
        option_data['supplier_id'] = supplier_info['supplier_id']
        if not option_data.get('supplier_name'):
            option_data['supplier_name'] = supplier_info.get('supplier_name')
    
    # Backward-compatible financial mapping:
    # keep legacy base_cost/currency_id while populating required new columns.
    if option_data.get('base_cost') is not None and option_data.get('cost_amount') is None:
        option_data['cost_amount'] = option_data['base_cost']

    if not option_data.get('cost_currency'):
        currency_code = 'IRR'
        currency_id = option_data.get('currency_id')
        if currency_id is not None:
            from app.models import Currency
            currency_result = await db.execute(
                select(Currency.code).where(Currency.id == currency_id)
            )
            resolved_code = currency_result.scalar_one_or_none()
            if resolved_code:
                currency_code = resolved_code
        option_data['cost_currency'] = currency_code

    # Convert Decimal values in payment_terms to float for JSON serialization
    if 'payment_terms' in option_data and option_data['payment_terms']:
        payment_terms = option_data['payment_terms'].copy()
        for key, value in payment_terms.items():
            if hasattr(value, '__float__'):  # Convert Decimal to float
                payment_terms[key] = float(value)
        option_data['payment_terms'] = payment_terms
    
    db_option = ProcurementOption(**option_data)
    db.add(db_option)
    await db.flush()
    await synchronize_procurement_option_legacy_pricing_fields(
        option_id=db_option.id,
        db=db,
        require_base_price=False,
    )
    await apply_procurement_option_persistence_contract(option_id=db_option.id, db=db)
    await db.commit()
    await db.refresh(db_option)
    created_option_id = int(db_option.id)
    
    # Phase 3: Log operation
    try:
        await log_phase3_operation(
            db,
            operation="create",
            record_type="procurement_option",
            record_id=db_option.id,
            used_package_id=bool(ref_info.get('package_id')),
            used_legacy_reference=bool(ref_info.get('project_item_id') or ref_info.get('item_code')),
            user_id=None,
            metadata={"ref_type": ref_info.get('reference_type')}
        )
    except Exception:
        pass

    # Reload after telemetry write to avoid returning an expired ORM row.
    return await get_procurement_option(db, created_option_id)


async def get_procurement_option(db: AsyncSession, option_id: int) -> Optional[ProcurementOption]:
    """Get procurement option by ID"""
    from sqlalchemy.orm import joinedload
    
    result = await db.execute(
        select(ProcurementOption)
        .execution_options(populate_existing=True)
        .options(joinedload(ProcurementOption.supplier))
        .where(ProcurementOption.id == option_id)
    )
    return result.scalar_one_or_none()


async def get_procurement_options(db: AsyncSession, skip: int = 0, limit: int = 100, 
                                 item_code: Optional[str] = None) -> List[ProcurementOption]:
    """Get procurement options with optional filtering by item_code"""
    from sqlalchemy.orm import joinedload
    
    query = select(ProcurementOption).options(joinedload(ProcurementOption.supplier)).where(ProcurementOption.is_active == True)
    
    if item_code:
        query = query.where(ProcurementOption.item_code == item_code)
    
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(ProcurementOption.item_code, ProcurementOption.created_at.desc())
    )
    return result.scalars().all()


async def get_unique_item_codes(db: AsyncSession) -> List[str]:
    """Get list of unique item codes"""
    result = await db.execute(
        select(ProcurementOption.item_code)
        .where(ProcurementOption.is_active == True)
        .distinct()
        .order_by(ProcurementOption.item_code)
    )
    return [row[0] for row in result.fetchall()]


async def update_procurement_option(db: AsyncSession, option_id: int, 
                                  option_update: ProcurementOptionUpdate) -> Optional[ProcurementOption]:
    """Update procurement option with Phase 3 dual-mode validation"""
    from app.validators.package_validators import (
        validate_package_or_legacy_reference,
        validate_supplier_reference,
        resolve_package_from_project_item
    )
    from app.services.audit_service import log_phase3_operation
    from app.services.procurement_financials_service import (
        apply_procurement_option_persistence_contract,
        synchronize_procurement_option_legacy_pricing_fields,
    )
    from app.config import settings
    
    # Get existing option to preserve current values
    existing = await get_procurement_option(db, option_id)
    if not existing:
        return None
    
    update_data = option_update.dict(exclude_unset=True)
    if not update_data:
        return existing
    
    # Phase 3: Validate package/legacy reference if provided
    if 'package_id' in update_data or 'project_item_id' in update_data or 'item_code' in update_data:
        try:
            ref_info = validate_package_or_legacy_reference(
                package_id=update_data.get('package_id', existing.package_id),
                project_item_id=update_data.get('project_item_id', existing.project_item_id),
                item_code=update_data.get('item_code', existing.item_code),
                context="procurement option update"
            )
            # Resolve package_id if needed
            resolved_package_id = ref_info.get('package_id')
            if not resolved_package_id and ref_info.get('project_item_id') and settings.enable_package_procurement:
                resolved_package_id = await resolve_package_from_project_item(
                    db, ref_info['project_item_id'], create_if_missing=False
                )
                if resolved_package_id:
                    update_data['package_id'] = resolved_package_id
        except Exception as e:
            raise ValueError(str(e))
    
    # Phase 3: Validate supplier reference if provided
    if 'supplier_id' in update_data or 'supplier_name' in update_data:
        supplier_info = await validate_supplier_reference(
            db,
            supplier_id=update_data.get('supplier_id', existing.supplier_id),
            supplier_name=update_data.get('supplier_name', existing.supplier_name),
            context="procurement option update"
        )
        if supplier_info.get('supplier_id'):
            update_data['supplier_id'] = supplier_info['supplier_id']
    
    # Convert Decimal values in payment_terms to float for JSON serialization
    if 'payment_terms' in update_data and update_data['payment_terms']:
        payment_terms = update_data['payment_terms'].copy()
        for key, value in payment_terms.items():
            if hasattr(value, '__float__'):  # Convert Decimal to float
                payment_terms[key] = float(value)
        update_data['payment_terms'] = payment_terms

    # Keep required financial field in sync when legacy base_cost is updated.
    if 'base_cost' in update_data and 'cost_amount' not in update_data:
        update_data['cost_amount'] = update_data['base_cost']
    
    await db.execute(
        update(ProcurementOption).where(ProcurementOption.id == option_id).values(**update_data)
    )
    await synchronize_procurement_option_legacy_pricing_fields(
        option_id=option_id,
        db=db,
        require_base_price=False,
    )
    await apply_procurement_option_persistence_contract(option_id=option_id, db=db)
    await db.commit()
    
    updated = await get_procurement_option(db, option_id)
    
    # Phase 3: Log operation
    try:
        await log_phase3_operation(
            db,
            operation="update",
            record_type="procurement_option",
            record_id=option_id,
            used_package_id=bool(updated.package_id if updated else False),
            used_legacy_reference=bool((updated.project_item_id if updated else None) or (updated.item_code if updated else None)),
            user_id=None
        )
    except Exception:
        pass

    # Reload after audit telemetry write to avoid returning an expired ORM row.
    return await get_procurement_option(db, option_id)


async def delete_procurement_option(db: AsyncSession, option_id: int) -> bool:
    """Delete procurement option and related optimization results and finalized decisions"""
    # First delete all optimization results that reference this procurement option
    await db.execute(delete(OptimizationResult).where(OptimizationResult.procurement_option_id == option_id))
    
    # Delete finalized decisions that reference this procurement option
    await db.execute(delete(FinalizedDecision).where(FinalizedDecision.procurement_option_id == option_id))
    
    # Then delete the procurement option
    result = await db.execute(delete(ProcurementOption).where(ProcurementOption.id == option_id))
    await db.commit()
    return result.rowcount > 0


# Budget Data CRUD operations
async def create_budget_data(db: AsyncSession, budget: BudgetDataCreate) -> BudgetData:
    """Create new budget data"""
    budget_data = budget.dict()
    
    # Convert Decimal values in multi_currency_budget to float for JSON serialization
    if budget_data.get('multi_currency_budget'):
        multi_currency_budget = {}
        for currency_code, amount in budget_data['multi_currency_budget'].items():
            if isinstance(amount, Decimal):
                multi_currency_budget[currency_code] = float(amount)
            else:
                multi_currency_budget[currency_code] = amount
        budget_data['multi_currency_budget'] = multi_currency_budget
    
    db_budget = BudgetData(**budget_data)
    db.add(db_budget)
    await db.commit()
    await db.refresh(db_budget)
    return db_budget


async def get_budget_data(db: AsyncSession, budget_date: str) -> Optional[BudgetData]:
    """Get budget data by budget date"""
    from datetime import date
    budget_date_obj = date.fromisoformat(budget_date)
    result = await db.execute(select(BudgetData).where(BudgetData.budget_date == budget_date_obj))
    return result.scalar_one_or_none()


async def get_all_budget_data(db: AsyncSession) -> List[BudgetData]:
    """Get all budget data ordered by budget date"""
    result = await db.execute(
        select(BudgetData).order_by(BudgetData.budget_date)
    )
    return result.scalars().all()


async def update_budget_data(db: AsyncSession, budget_date: str, 
                           budget_update: BudgetDataUpdate) -> Optional[BudgetData]:
    """Update budget data"""
    from datetime import date
    budget_date_obj = date.fromisoformat(budget_date)
    
    update_data = budget_update.dict(exclude_unset=True)
    if not update_data:
        return await get_budget_data(db, budget_date)
    
    # Convert Decimal values in multi_currency_budget to float for JSON serialization
    if 'multi_currency_budget' in update_data and update_data['multi_currency_budget']:
        multi_currency_budget = {}
        for currency_code, amount in update_data['multi_currency_budget'].items():
            if isinstance(amount, Decimal):
                multi_currency_budget[currency_code] = float(amount)
            else:
                multi_currency_budget[currency_code] = amount
        update_data['multi_currency_budget'] = multi_currency_budget
    
    await db.execute(
        update(BudgetData).where(BudgetData.budget_date == budget_date_obj).values(**update_data)
    )
    await db.commit()
    return await get_budget_data(db, budget_date)


async def delete_budget_data(db: AsyncSession, budget_date: str) -> bool:
    """Delete budget data"""
    from datetime import date
    budget_date_obj = date.fromisoformat(budget_date)
    result = await db.execute(delete(BudgetData).where(BudgetData.budget_date == budget_date_obj))
    await db.commit()
    return result.rowcount > 0


# Delivery Option CRUD operations
async def create_delivery_option(db: AsyncSession, delivery_option: DeliveryOptionCreate) -> DeliveryOption:
    """Create a new delivery option with Phase 3 dual-mode validation"""
    from app.validators.package_validators import (
        validate_package_or_legacy_reference,
        resolve_package_from_project_item
    )
    from app.services.audit_service import log_phase3_operation
    from app.config import settings
    
    # Phase 3: Validate package/legacy reference
    try:
        ref_info = validate_package_or_legacy_reference(
            package_id=getattr(delivery_option, 'package_id', None),
            project_item_id=getattr(delivery_option, 'project_item_id', None),
            item_code=None,
            context="delivery option"
        )
    except Exception as e:
        raise ValueError(str(e))
    
    # Phase 3: Resolve package_id from project_item_id if needed
    package_id_to_use = ref_info.get('package_id')
    if not package_id_to_use and ref_info.get('project_item_id') and settings.enable_package_procurement:
        package_id_to_use = await resolve_package_from_project_item(
            db, ref_info['project_item_id'], create_if_missing=False
        )
        if package_id_to_use:
            ref_info['package_id'] = package_id_to_use
    
    option_data = delivery_option.dict()
    
    # Phase 3: Set package_id from ref_info (preserves provided package_id even if flag is off)
    if ref_info.get('package_id'):
        option_data['package_id'] = ref_info['package_id']
    
    # Ensure project_item_id is set if package_id is used (for backward compatibility)
    if ref_info.get('package_id') and not option_data.get('project_item_id'):
        from app.models import ProcurementPackage
        from sqlalchemy import select
        result = await db.execute(
            select(ProcurementPackage).where(ProcurementPackage.id == ref_info.get('package_id'))
        )
        package = result.scalar_one_or_none()
        if package:
            option_data['project_item_id'] = package.project_item_id
    
    db_option = DeliveryOption(**option_data)
    db.add(db_option)
    await db.commit()
    await db.refresh(db_option)
    
    # Phase 3: Log operation
    try:
        await log_phase3_operation(
        db,
        operation="create",
        record_type="delivery_option",
        record_id=db_option.id,
        used_package_id=bool(ref_info.get('package_id')),
        used_legacy_reference=bool(ref_info.get('project_item_id')),
        user_id=None,
        metadata={"ref_type": ref_info.get('reference_type')}
    )
    except Exception:
        pass
    
    return db_option


async def get_delivery_options_by_item(db: AsyncSession, project_item_id: int) -> List[DeliveryOption]:
    """Get all delivery options for a specific project item"""
    result = await db.execute(
        select(DeliveryOption)
        .where(DeliveryOption.project_item_id == project_item_id)
        .where(DeliveryOption.is_active == True)
        .order_by(DeliveryOption.preference_rank.asc().nullslast(), DeliveryOption.delivery_date.asc())
    )
    return result.scalars().all()


async def get_delivery_option(db: AsyncSession, option_id: int) -> Optional[DeliveryOption]:
    """Get a specific delivery option by ID"""
    result = await db.execute(
        select(DeliveryOption).where(DeliveryOption.id == option_id)
    )
    return result.scalar_one_or_none()


async def update_delivery_option(db: AsyncSession, option_id: int, 
                                option_update: DeliveryOptionUpdate) -> Optional[DeliveryOption]:
    """Update a delivery option"""
    update_data = option_update.dict(exclude_unset=True)
    if not update_data:
        return await get_delivery_option(db, option_id)
    
    await db.execute(
        update(DeliveryOption)
        .where(DeliveryOption.id == option_id)
        .values(**update_data)
    )
    await db.commit()
    return await get_delivery_option(db, option_id)


async def delete_delivery_option(db: AsyncSession, option_id: int) -> bool:
    """Delete a delivery option"""
    result = await db.execute(
        delete(DeliveryOption).where(DeliveryOption.id == option_id)
    )
    await db.commit()
    return result.rowcount > 0


# Optimization Result CRUD operations
async def get_optimization_results(db: AsyncSession, run_id: Optional[str] = None, 
                                 skip: int = 0, limit: int = 100) -> List[OptimizationResult]:
    """Get optimization results with optional filtering by run_id"""
    query = select(OptimizationResult)
    
    if run_id:
        query = query.where(OptimizationResult.run_id == run_id)
    
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(OptimizationResult.run_timestamp.desc())
    )
    return result.scalars().all()


async def get_latest_optimization_run(db: AsyncSession) -> Optional[str]:
    """Get the latest optimization run ID"""
    result = await db.execute(
        select(OptimizationResult.run_id)
        .order_by(OptimizationResult.run_timestamp.desc())
        .limit(1)
    )
    row = result.fetchone()
    return str(row[0]) if row else None


# Dashboard and Analytics functions
async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get dashboard statistics"""
    # Count active projects
    projects_count = await db.scalar(
        select(func.count(Project.id)).where(Project.is_active == True)
    )
    
    # Count total items across all projects
    items_count = await db.scalar(select(func.count(ProjectItem.id)))
    
    # Count active procurement options
    options_count = await db.scalar(
        select(func.count(ProcurementOption.id)).where(ProcurementOption.is_active == True)
    )
    
    # Sum total budget from projects (not monthly budget data)
    total_budget = await db.scalar(select(func.sum(Project.budget_amount)))
    total_budget = total_budget or 0
    
    # Get last optimization timestamp
    last_opt = await db.scalar(
        select(OptimizationResult.run_timestamp)
        .order_by(OptimizationResult.run_timestamp.desc())
        .limit(1)
    )
    
    return {
        "total_projects": projects_count,
        "total_items": items_count,
        "total_procurement_options": options_count,
        "total_budget": total_budget,
        "last_optimization": last_opt,
        "pending_items": 0  # Could be calculated based on business logic
    }


async def get_project_summaries(db: AsyncSession, user_projects: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Get project summaries with item counts and estimated costs"""
    query = select(Project).where(Project.is_active == True)
    
    if user_projects is not None:
        query = query.where(Project.id.in_(user_projects))
    
    projects = await db.execute(query)
    project_rows = list(projects.scalars())
    summaries = []

    project_ids = [project.id for project in project_rows]

    # Keep project-page revenue aligned with dashboard forecast inflow by using
    # active FORECAST INFLOW cashflow events as the primary source.
    forecast_revenue_by_project: Dict[int, Decimal] = {}
    if project_ids:
        forecast_revenue_result = await db.execute(
            select(
                FinalizedDecision.project_id,
                func.coalesce(func.sum(func.coalesce(CashflowEvent.amount_value, CashflowEvent.amount)), 0).label("forecast_revenue")
            )
            .join(CashflowEvent, CashflowEvent.related_decision_id == FinalizedDecision.id)
            .where(FinalizedDecision.project_id.in_(project_ids))
            .where(FinalizedDecision.status == "LOCKED")
            .where(CashflowEvent.is_cancelled == False)
            .where(CashflowEvent.event_type == "INFLOW")
            .where(CashflowEvent.forecast_type == "FORECAST")
            .group_by(FinalizedDecision.project_id)
        )
        forecast_revenue_by_project = {
            int(row.project_id): Decimal(str(row.forecast_revenue or 0))
            for row in forecast_revenue_result.fetchall()
        }
    
    for project in project_rows:
        # Count items for this project
        item_count = await db.scalar(
            select(func.count(ProjectItem.id)).where(ProjectItem.project_id == project.id)
        )
        
        # Sum quantities for this project
        total_quantity = await db.scalar(
            select(func.sum(ProjectItem.quantity)).where(ProjectItem.project_id == project.id)
        )
        
        # Calculate estimated cost and revenue
        # Get all items for this project with their delivery options
        items_result = await db.execute(
            select(ProjectItem)
            .options(selectinload(ProjectItem.delivery_options_rel))
            .where(ProjectItem.project_id == project.id)
        )
        project_items = items_result.scalars().all()
        
        # OPTIMIZED: Calculate average costs for all items in ONE query
        avg_costs_query = await db.execute(
            select(
                ProcurementOption.item_code,
                func.avg(ProcurementOption.base_cost).label('avg_cost')
            )
            .where(ProcurementOption.is_active == True)
            .where(ProcurementOption.item_code.in_([item.item_code for item in project_items]))
            .group_by(ProcurementOption.item_code)
        )
        avg_costs_dict = {row.item_code: row.avg_cost for row in avg_costs_query.fetchall()}
        
        estimated_cost = Decimal('0')
        estimated_revenue = Decimal('0')
        
        for item in project_items:
            # Use pre-calculated average cost
            avg_cost = avg_costs_dict.get(item.item_code)
            if avg_cost:
                estimated_cost += Decimal(str(avg_cost)) * item.quantity
            
            # Legacy fallback revenue from delivery options (used only when the
            # project has no generated forecast inflow cashflow events yet).
            if hasattr(item, 'delivery_options_rel') and item.delivery_options_rel:
                first_delivery = item.delivery_options_rel[0]
                estimated_revenue += first_delivery.invoice_amount_per_unit * item.quantity
            elif avg_cost:
                estimated_revenue += Decimal(str(avg_cost)) * item.quantity * Decimal('1.20')

        # Primary source: dashboard-aligned forecast inflow from cashflow events.
        # Fallback: legacy per-item estimate when no forecast events are available.
        project_forecast_revenue = forecast_revenue_by_project.get(project.id)
        if project_forecast_revenue is not None:
            estimated_revenue = project_forecast_revenue
        
        summaries.append({
            "id": project.id,
            "project_code": project.project_code,
            "name": project.name,
            "item_count": item_count or 0,
            "total_quantity": total_quantity or 0,
            "estimated_cost": float(estimated_cost) if estimated_cost else 0.0,
            "estimated_revenue": float(estimated_revenue) if estimated_revenue else 0.0
        })
    
    return summaries


# ProjectPhase CRUD operations
async def create_project_phase(db: AsyncSession, phase: ProjectPhaseCreate) -> ProjectPhase:
    """Create a new project phase"""
    db_phase = ProjectPhase(**phase.dict())
    db.add(db_phase)
    await db.commit()
    await db.refresh(db_phase)
    return db_phase


async def get_project_phase(db: AsyncSession, phase_id: int) -> Optional[ProjectPhase]:
    """Get project phase by ID"""
    result = await db.execute(
        select(ProjectPhase)
        .options(selectinload(ProjectPhase.project))
        .where(ProjectPhase.id == phase_id)
    )
    return result.scalar_one_or_none()


async def get_project_phases(db: AsyncSession, project_id: int) -> List[ProjectPhase]:
    """Get all phases for a specific project"""
    result = await db.execute(
        select(ProjectPhase)
        .where(ProjectPhase.project_id == project_id)
        .order_by(ProjectPhase.start_date)
    )
    return result.scalars().all()


async def update_project_phase(db: AsyncSession, phase_id: int, phase_update: ProjectPhaseUpdate) -> Optional[ProjectPhase]:
    """Update project phase"""
    update_data = phase_update.dict(exclude_unset=True)
    if not update_data:
        return await get_project_phase(db, phase_id)
    
    await db.execute(
        update(ProjectPhase).where(ProjectPhase.id == phase_id).values(**update_data)
    )
    await db.commit()
    return await get_project_phase(db, phase_id)


async def delete_project_phase(db: AsyncSession, phase_id: int) -> bool:
    """Delete project phase"""
    result = await db.execute(delete(ProjectPhase).where(ProjectPhase.id == phase_id))
    await db.commit()
    return result.rowcount > 0


# DecisionFactorWeight CRUD operations
async def create_decision_factor_weight(db: AsyncSession, weight: DecisionFactorWeightCreate) -> DecisionFactorWeight:
    """Create a new decision factor weight"""
    db_weight = DecisionFactorWeight(**weight.dict())
    db.add(db_weight)
    await db.commit()
    await db.refresh(db_weight)
    return db_weight


async def get_decision_factor_weight(db: AsyncSession, weight_id: int) -> Optional[DecisionFactorWeight]:
    """Get decision factor weight by ID"""
    result = await db.execute(
        select(DecisionFactorWeight).where(DecisionFactorWeight.id == weight_id)
    )
    return result.scalar_one_or_none()


async def get_decision_factor_weights(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DecisionFactorWeight]:
    """Get all decision factor weights"""
    result = await db.execute(
        select(DecisionFactorWeight)
        .offset(skip)
        .limit(limit)
        .order_by(DecisionFactorWeight.weight.desc())
    )
    return result.scalars().all()


async def update_decision_factor_weight(db: AsyncSession, weight_id: int, weight_update: DecisionFactorWeightUpdate) -> Optional[DecisionFactorWeight]:
    """Update decision factor weight"""
    update_data = weight_update.dict(exclude_unset=True)
    if not update_data:
        return await get_decision_factor_weight(db, weight_id)
    
    await db.execute(
        update(DecisionFactorWeight).where(DecisionFactorWeight.id == weight_id).values(**update_data)
    )
    await db.commit()
    return await get_decision_factor_weight(db, weight_id)


async def delete_decision_factor_weight(db: AsyncSession, weight_id: int) -> bool:
    """Delete decision factor weight"""
    result = await db.execute(delete(DecisionFactorWeight).where(DecisionFactorWeight.id == weight_id))
    await db.commit()
    return result.rowcount > 0
