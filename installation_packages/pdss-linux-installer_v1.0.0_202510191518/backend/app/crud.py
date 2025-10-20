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
    DeliveryOption
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


# User CRUD operations
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
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
    update_data = user_update.dict(exclude_unset=True)
    if not update_data:
        return await get_user(db, user_id)
    
    await db.execute(
        update(User).where(User.id == user_id).values(**update_data)
    )
    await db.commit()
    return await get_user(db, user_id)


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
    
    # Create project item
    db_item = ProjectItem(**item_dict)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
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
    
    await db.execute(
        update(ProjectItem).where(ProjectItem.id == item_id).values(**update_data)
    )
    await db.commit()
    return await get_project_item(db, item_id)


async def delete_project_item(db: AsyncSession, item_id: int) -> bool:
    """Delete project item"""
    result = await db.execute(delete(ProjectItem).where(ProjectItem.id == item_id))
    await db.commit()
    return result.rowcount > 0


# Procurement Option CRUD operations
async def create_procurement_option(db: AsyncSession, option: ProcurementOptionCreate) -> ProcurementOption:
    """Create a new procurement option"""
    # Convert to dict and handle Decimal serialization for JSON fields
    option_data = option.dict()
    
    # Convert Decimal values in payment_terms to float for JSON serialization
    if 'payment_terms' in option_data and option_data['payment_terms']:
        payment_terms = option_data['payment_terms'].copy()
        for key, value in payment_terms.items():
            if hasattr(value, '__float__'):  # Convert Decimal to float
                payment_terms[key] = float(value)
        option_data['payment_terms'] = payment_terms
    
    db_option = ProcurementOption(**option_data)
    db.add(db_option)
    await db.commit()
    await db.refresh(db_option)
    return db_option


async def get_procurement_option(db: AsyncSession, option_id: int) -> Optional[ProcurementOption]:
    """Get procurement option by ID"""
    result = await db.execute(select(ProcurementOption).where(ProcurementOption.id == option_id))
    return result.scalar_one_or_none()


async def get_procurement_options(db: AsyncSession, skip: int = 0, limit: int = 100, 
                                 item_code: Optional[str] = None) -> List[ProcurementOption]:
    """Get procurement options with optional filtering by item_code"""
    query = select(ProcurementOption).where(ProcurementOption.is_active == True)
    
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
    """Update procurement option"""
    update_data = option_update.dict(exclude_unset=True)
    if not update_data:
        return await get_procurement_option(db, option_id)
    
    # Convert Decimal values in payment_terms to float for JSON serialization
    if 'payment_terms' in update_data and update_data['payment_terms']:
        payment_terms = update_data['payment_terms'].copy()
        for key, value in payment_terms.items():
            if hasattr(value, '__float__'):  # Convert Decimal to float
                payment_terms[key] = float(value)
        update_data['payment_terms'] = payment_terms
    
    await db.execute(
        update(ProcurementOption).where(ProcurementOption.id == option_id).values(**update_data)
    )
    await db.commit()
    return await get_procurement_option(db, option_id)


async def delete_procurement_option(db: AsyncSession, option_id: int) -> bool:
    """Delete procurement option"""
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
    """Create a new delivery option for a project item"""
    db_option = DeliveryOption(**delivery_option.dict())
    db.add(db_option)
    await db.commit()
    await db.refresh(db_option)
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
    
    # Sum total budget
    total_budget = await db.scalar(select(func.sum(BudgetData.available_budget)))
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
    summaries = []
    
    for project in projects.scalars():
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
            
            # Get revenue from delivery options (invoice amounts)
            if hasattr(item, 'delivery_options_rel') and item.delivery_options_rel:
                # Use first delivery option's invoice amount
                first_delivery = item.delivery_options_rel[0]
                estimated_revenue += first_delivery.invoice_amount_per_unit * item.quantity
            elif avg_cost:
                # Fallback: Use 20% markup on cost
                estimated_revenue += Decimal(str(avg_cost)) * item.quantity * Decimal('1.20')
        
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
