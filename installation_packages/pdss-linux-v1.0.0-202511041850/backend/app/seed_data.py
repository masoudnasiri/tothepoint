"""
Comprehensive test data seeding for the Procurement DSS
This module creates extensive test data for platform testing
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import (
    User, Project, ProjectAssignment, ProjectPhase, ProjectItem, 
    ProcurementOption, BudgetData, DecisionFactorWeight, ProjectItemStatus,
    DeliveryOption
)
from app.auth import get_password_hash
from decimal import Decimal
from datetime import date, timedelta
import logging
import random

logger = logging.getLogger(__name__)


async def clear_all_data(db: AsyncSession):
    """Clear all existing data for fresh start"""
    logger.info("Clearing all existing data...")
    
    # Delete in reverse dependency order using text()
    from sqlalchemy import text
    await db.execute(text("DELETE FROM cashflow_events"))
    await db.execute(text("DELETE FROM finalized_decisions"))
    await db.execute(text("DELETE FROM optimization_results"))
    await db.execute(text("DELETE FROM optimization_runs"))
    await db.execute(text("DELETE FROM delivery_options"))
    await db.execute(text("DELETE FROM procurement_options"))
    await db.execute(text("DELETE FROM project_items"))
    await db.execute(text("DELETE FROM project_phases"))
    await db.execute(text("DELETE FROM project_assignments"))
    await db.execute(text("DELETE FROM budget_data"))
    await db.execute(text("DELETE FROM decision_factor_weights"))
    await db.execute(text("DELETE FROM projects"))
    await db.execute(text("DELETE FROM users"))
    
    await db.commit()
    logger.info("All existing data cleared")


async def create_comprehensive_users(db: AsyncSession):
    """Create comprehensive user base"""
    users_data = [
        {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
        {'username': 'pmo1', 'password': 'pmo123', 'role': 'pmo'},
        {'username': 'pm1', 'password': 'pm123', 'role': 'pm'},
        {'username': 'pm2', 'password': 'pm123', 'role': 'pm'},
        {'username': 'proc1', 'password': 'proc123', 'role': 'procurement'},
        {'username': 'proc2', 'password': 'proc123', 'role': 'procurement'},
        {'username': 'finance1', 'password': 'finance123', 'role': 'finance'},
        {'username': 'finance2', 'password': 'finance123', 'role': 'finance'},
    ]
    
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            password_hash=get_password_hash(user_data['password']),
            role=user_data['role'],
            is_active=True
        )
        db.add(user)
    
    await db.commit()
    logger.info("Comprehensive users created successfully")


async def create_comprehensive_projects(db: AsyncSession):
    """Create 10 comprehensive projects for multi-currency testing"""
    projects_data = [
        {'project_code': 'INFRA001', 'name': 'Highway Infrastructure Project', 'priority_weight': 10},
        {'project_code': 'BUILD002', 'name': 'Commercial Building Complex', 'priority_weight': 9},
        {'project_code': 'RESI003', 'name': 'Residential Housing Development', 'priority_weight': 8},
        {'project_code': 'INDU004', 'name': 'Industrial Manufacturing Plant', 'priority_weight': 7},
        {'project_code': 'UTIL005', 'name': 'Utilities Infrastructure Upgrade', 'priority_weight': 6},
        {'project_code': 'TECH006', 'name': 'Technology Center Development', 'priority_weight': 9},
        {'project_code': 'HOSP007', 'name': 'Hospital Expansion Project', 'priority_weight': 10},
        {'project_code': 'MALL008', 'name': 'Shopping Mall Construction', 'priority_weight': 7},
        {'project_code': 'PARK009', 'name': 'Public Park & Recreation', 'priority_weight': 5},
        {'project_code': 'PORT010', 'name': 'Port Infrastructure Modernization', 'priority_weight': 8}
    ]
    
    for project_data in projects_data:
        project = Project(
            project_code=project_data['project_code'],
            name=project_data['name'],
            priority_weight=project_data['priority_weight'],
            is_active=True
        )
        db.add(project)
    
    await db.commit()
    logger.info("10 comprehensive projects created successfully")


async def create_project_assignments(db: AsyncSession):
    """Create project assignments for PMs"""
    pm_users = await db.execute(select(User).where(User.role == 'pm'))
    pm_users = pm_users.scalars().all()
    
    projects = await db.execute(select(Project))
    projects = projects.scalars().all()
    
    for i, project in enumerate(projects):
        pm_user = pm_users[i % len(pm_users)]  # Distribute projects among PMs
        assignment = ProjectAssignment(
            user_id=pm_user.id,
            project_id=project.id
        )
        db.add(assignment)
    
    await db.commit()
    logger.info("Project assignments created successfully")


async def create_project_phases(db: AsyncSession):
    """Create project phases for all projects"""
    projects = await db.execute(select(Project))
    projects = projects.scalars().all()
    
    base_date = date(2025, 1, 1)
    
    for idx, project in enumerate(projects):
        project_offset = idx * 60  # Each project starts 60 days apart
        
        phases_data = [
            {
                'phase_name': 'Phase 1: Planning & Design',
                'start_date': base_date + timedelta(days=project_offset),
                'end_date': base_date + timedelta(days=project_offset + 45)
            },
            {
                'phase_name': 'Phase 2: Site Preparation',
                'start_date': base_date + timedelta(days=project_offset + 46),
                'end_date': base_date + timedelta(days=project_offset + 90)
            },
            {
                'phase_name': 'Phase 3: Construction',
                'start_date': base_date + timedelta(days=project_offset + 91),
                'end_date': base_date + timedelta(days=project_offset + 180)
            },
            {
                'phase_name': 'Phase 4: Finishing & Testing',
                'start_date': base_date + timedelta(days=project_offset + 181),
                'end_date': base_date + timedelta(days=project_offset + 240)
            }
        ]
        
        for phase_data in phases_data:
            phase = ProjectPhase(
                project_id=project.id,
                phase_name=phase_data['phase_name'],
                start_date=phase_data['start_date'],
                end_date=phase_data['end_date']
            )
            db.add(phase)
    
    await db.commit()
    logger.info("Project phases created successfully")


async def create_comprehensive_project_items(db: AsyncSession):
    """Create 10 items per project (50 total) with realistic construction materials"""
    projects = await db.execute(select(Project))
    projects = projects.scalars().all()
    
    # Comprehensive construction item catalog
    item_catalog = [
        {'code': 'STEEL001', 'name': 'Structural Steel Beams - H-Beam 200x200mm', 'base_cost': 450.00},
        {'code': 'STEEL002', 'name': 'Reinforcement Bars - Grade 60', 'base_cost': 120.00},
        {'code': 'STEEL003', 'name': 'Steel Plates - 10mm Thickness', 'base_cost': 280.00},
        {'code': 'CONC001', 'name': 'Ready-Mix Concrete - Grade C25', 'base_cost': 85.00},
        {'code': 'CONC002', 'name': 'Ready-Mix Concrete - Grade C30', 'base_cost': 95.00},
        {'code': 'CONC003', 'name': 'Cement - Portland Type I', 'base_cost': 45.00},
        {'code': 'AGG001', 'name': 'Coarse Aggregate - 20mm', 'base_cost': 25.00},
        {'code': 'AGG002', 'name': 'Fine Aggregate - River Sand', 'base_cost': 35.00},
        {'code': 'FORM001', 'name': 'Formwork - Steel Panels', 'base_cost': 180.00},
        {'code': 'FORM002', 'name': 'Formwork - Plywood Sheets', 'base_cost': 65.00},
        {'code': 'INSUL001', 'name': 'Thermal Insulation - Rockwool', 'base_cost': 75.00},
        {'code': 'INSUL002', 'name': 'Acoustic Insulation - Fiberglass', 'base_cost': 55.00},
        {'code': 'ROOF001', 'name': 'Roofing Tiles - Clay', 'base_cost': 95.00},
        {'code': 'ROOF002', 'name': 'Roofing Membrane - EPDM', 'base_cost': 125.00},
        {'code': 'WINDOW001', 'name': 'Aluminum Windows - Double Glazed', 'base_cost': 350.00},
        {'code': 'DOOR001', 'name': 'Steel Doors - Fire Rated', 'base_cost': 450.00},
        {'code': 'ELEC001', 'name': 'Electrical Cables - 3-Core 2.5mm²', 'base_cost': 15.00},
        {'code': 'ELEC002', 'name': 'Electrical Conduits - PVC 25mm', 'base_cost': 8.00},
        {'code': 'PLUMB001', 'name': 'Water Pipes - PVC 100mm', 'base_cost': 25.00},
        {'code': 'PLUMB002', 'name': 'Sewage Pipes - HDPE 200mm', 'base_cost': 45.00},
        {'code': 'PAINT001', 'name': 'Exterior Paint - Weather Resistant', 'base_cost': 35.00},
        {'code': 'PAINT002', 'name': 'Interior Paint - Low VOC', 'base_cost': 28.00},
        {'code': 'TILE001', 'name': 'Ceramic Tiles - 60x60cm', 'base_cost': 25.00},
        {'code': 'TILE002', 'name': 'Marble Tiles - 30x30cm', 'base_cost': 85.00},
        {'code': 'EQUIP001', 'name': 'Excavator - 20 Ton Capacity', 'base_cost': 4500.00},
        {'code': 'EQUIP002', 'name': 'Crane - 50 Ton Capacity', 'base_cost': 8500.00},
        {'code': 'EQUIP003', 'name': 'Concrete Mixer - 3m³', 'base_cost': 1200.00},
        {'code': 'SAFETY001', 'name': 'Safety Barriers - Temporary', 'base_cost': 45.00},
        {'code': 'SAFETY002', 'name': 'Personal Protective Equipment Set', 'base_cost': 125.00},
        {'code': 'TOOL001', 'name': 'Power Tools - Construction Set', 'base_cost': 850.00},
        {'code': 'LIGHT001', 'name': 'LED Light Fixtures - Industrial', 'base_cost': 95.00},
        {'code': 'HVAC001', 'name': 'Air Conditioning Units - Split Type', 'base_cost': 650.00},
        {'code': 'HVAC002', 'name': 'Ventilation Fans - Industrial', 'base_cost': 180.00},
        {'code': 'FIRE001', 'name': 'Fire Extinguishers - 10kg', 'base_cost': 85.00},
        {'code': 'FIRE002', 'name': 'Fire Alarm System - Wireless', 'base_cost': 250.00},
        {'code': 'SECURITY001', 'name': 'Security Cameras - IP Network', 'base_cost': 350.00},
        {'code': 'SECURITY002', 'name': 'Access Control System', 'base_cost': 450.00},
        {'code': 'LAND001', 'name': 'Landscaping - Trees & Shrubs', 'base_cost': 85.00},
        {'code': 'LAND002', 'name': 'Irrigation System - Drip Type', 'base_cost': 65.00},
        {'code': 'FENCE001', 'name': 'Perimeter Fencing - Chain Link', 'base_cost': 45.00},
        {'code': 'PARK001', 'name': 'Parking Bollards - Concrete', 'base_cost': 95.00},
        {'code': 'SIGN001', 'name': 'Directional Signage - Reflective', 'base_cost': 125.00},
        {'code': 'CLEAN001', 'name': 'Cleaning Equipment - Industrial', 'base_cost': 250.00},
        {'code': 'MAINT001', 'name': 'Maintenance Tools - Complete Set', 'base_cost': 450.00},
        {'code': 'COMM001', 'name': 'Communication Equipment - Radio', 'base_cost': 350.00},
        {'code': 'FURN001', 'name': 'Office Furniture - Ergonomic', 'base_cost': 650.00},
        {'code': 'FURN002', 'name': 'Meeting Room Furniture Set', 'base_cost': 1200.00},
        {'code': 'IT001', 'name': 'Computer Equipment - Desktop', 'base_cost': 850.00},
        {'code': 'IT002', 'name': 'Network Equipment - Switch/Router', 'base_cost': 450.00}
    ]
    
    base_date = date(2025, 2, 1)
    
    for project in projects:
        # Select 10 random items for each project
        selected_items = random.sample(item_catalog, 10)
        
        for item_data in selected_items:
            # Generate realistic quantities (average 8, range 1-20)
            quantity = random.randint(1, 20)
            
            # Generate delivery date options (2-4 options per item)
            num_delivery_options = random.randint(2, 4)
            delivery_dates = []
            
            start_offset = random.randint(30, 120)  # Start 30-120 days from base
            for i in range(num_delivery_options):
                delivery_date = base_date + timedelta(days=start_offset + (i * random.randint(7, 21)))
                delivery_dates.append(delivery_date.isoformat())
            
            item = ProjectItem(
                project_id=project.id,
                item_code=item_data['code'],
                item_name=item_data['name'],
                quantity=quantity,
                delivery_options=delivery_dates,
                status=ProjectItemStatus.PENDING,
                external_purchase=random.choice([True, False])
            )
            db.add(item)
    
    await db.commit()
    logger.info("50 comprehensive project items created successfully")


async def create_comprehensive_procurement_options(db: AsyncSession):
    """Create 3 procurement options per item with mixed currencies (IRR and USD)"""
    items = await db.execute(select(ProjectItem))
    items = items.scalars().all()
    
    # Get currencies for procurement options
    from app.models import Currency
    irr_currency = await db.execute(select(Currency).where(Currency.code == 'IRR'))
    irr_currency = irr_currency.scalar_one()
    
    usd_currency = await db.execute(select(Currency).where(Currency.code == 'USD'))
    usd_currency = usd_currency.scalar_one()
    
    suppliers = [
        'Alpha Construction Supply', 'Beta Materials Corp', 'Gamma Industrial',
        'Delta Building Solutions', 'Epsilon Procurement', 'Zeta Construction',
        'Eta Materials Ltd', 'Theta Supply Chain', 'Iota Construction Co',
        'Kappa Building Materials', 'Lambda Industrial Supply', 'Mu Construction'
    ]
    
    payment_terms_options = [
        {'type': 'cash', 'discount_percent': 5},
        {'type': 'cash', 'discount_percent': 3},
        {'type': 'cash', 'discount_percent': 2},
        {
            'type': 'installments',
            'schedule': [
                {'due_offset': 0, 'percent': 50},
                {'due_offset': 1, 'percent': 50}
            ]
        },
        {
            'type': 'installments',
            'schedule': [
                {'due_offset': 0, 'percent': 40},
                {'due_offset': 1, 'percent': 30},
                {'due_offset': 2, 'percent': 30}
            ]
        },
        {
            'type': 'installments',
            'schedule': [
                {'due_offset': 0, 'percent': 30},
                {'due_offset': 1, 'percent': 30},
                {'due_offset': 2, 'percent': 20},
                {'due_offset': 3, 'percent': 20}
            ]
        }
    ]
    
    for item in items:
        # Create 3 procurement options per item
        selected_suppliers = random.sample(suppliers, 3)
        
        for i, supplier in enumerate(selected_suppliers):
            # Randomly assign currency (60% IRR, 40% USD for realistic mix)
            use_usd = random.random() < 0.4
            currency = usd_currency if use_usd else irr_currency
            currency_code = 'USD' if use_usd else 'IRR'
            
            # Base cost varies by supplier and currency
            if use_usd:
                # USD costs (smaller numbers, e.g., $100-$5000)
                base_cost = Decimal(str(round(random.uniform(100, 5000), 2)))
            else:
                # IRR costs (larger numbers, e.g., 5M-250M IRR)
                base_cost = Decimal(str(round(random.uniform(5000000, 250000000), 2)))
            
            # Lead time varies by supplier
            lead_time = random.randint(1, 7)
            
            # Bundle discount thresholds
            discount_threshold = random.choice([10, 25, 50, 100])
            discount_percent = random.choice([5, 10, 15, 20])
            
            # Payment terms
            payment_terms = random.choice(payment_terms_options)
            
            option = ProcurementOption(
                item_code=item.item_code,
                supplier_name=supplier,
                base_cost=base_cost,
                currency_id=currency.id,
                cost_amount=base_cost,
                cost_currency=currency_code,
                lomc_lead_time=lead_time,
                discount_bundle_threshold=discount_threshold,
                discount_bundle_percent=Decimal(str(discount_percent)),
                payment_terms=payment_terms,
                is_active=True
            )
            db.add(option)
    
    await db.commit()
    logger.info("Procurement options created with mixed currencies (IRR and USD)")


async def create_comprehensive_delivery_options(db: AsyncSession):
    """Create 2 delivery options per item"""
    items = await db.execute(select(ProjectItem))
    items = items.scalars().all()
    
    for item in items:
        # Create 2 delivery options per item
        for i in range(2):
            delivery_date_str = item.delivery_options[i] if i < len(item.delivery_options) else item.delivery_options[0]
            delivery_date = date.fromisoformat(delivery_date_str)
            
            # Invoice timing (30-90 days after delivery)
            invoice_days_after = random.randint(30, 90)
            invoice_date = delivery_date + timedelta(days=invoice_days_after)
            
            # Invoice amount in IRR (e.g., 7.5M-375M IRR per unit)
            invoice_per_unit = Decimal(str(round(random.uniform(7500000, 375000000), 2)))
            
            delivery_option = DeliveryOption(
                project_item_id=item.id,
                delivery_slot=i + 1,
                delivery_date=delivery_date,
                invoice_timing_type='RELATIVE',
                invoice_issue_date=invoice_date,
                invoice_days_after_delivery=invoice_days_after,
                invoice_amount_per_unit=invoice_per_unit,
                preference_rank=i + 1,
                notes=f"Delivery option {i + 1} for {item.item_name}",
                is_active=True
            )
            db.add(delivery_option)
    
    await db.commit()
    logger.info("Delivery options created successfully")


async def create_comprehensive_budget_data(db: AsyncSession):
    """Create comprehensive budget data with multi-currency support"""
    base_date = date(2025, 1, 1)
    budget_data = []
    
    # Create monthly budget allocations with mixed currencies
    # Base budgets in IRR (larger amounts)
    monthly_budgets_irr = [
        500000000000, 750000000000, 1000000000000, 1250000000000,
        1500000000000, 1750000000000, 2000000000000, 2250000000000,
        2500000000000, 2750000000000, 3000000000000, 3250000000000
    ]
    
    # Additional budgets in USD (smaller amounts) for some months
    monthly_budgets_usd = [
        10000000, 15000000, 20000000, 25000000,
        30000000, 35000000, 40000000, 45000000,
        50000000, 55000000, 60000000, 65000000
    ]
    
    for month in range(12):
        budget_date = base_date + timedelta(days=month * 30)
        budget_amount_irr = Decimal(str(monthly_budgets_irr[month]))
        
        # 50% of months also have USD budget
        multi_currency_budget = {}
        if month % 2 == 0:  # Even months have USD budget
            multi_currency_budget['USD'] = monthly_budgets_usd[month]
        
        budget_entry = BudgetData(
            budget_date=budget_date,
            available_budget=budget_amount_irr,
            multi_currency_budget=multi_currency_budget if multi_currency_budget else None
        )
        budget_data.append(budget_entry)
        db.add(budget_entry)
    
    await db.commit()
    logger.info("Budget data created with multi-currency support (IRR base + USD for some months)")


async def create_decision_factor_weights(db: AsyncSession):
    """Create comprehensive decision factor weights"""
    weights_data = [
        {
            'factor_name': 'cost_minimization',
            'weight': 9,
            'description': 'Prioritize minimizing total procurement cost'
        },
        {
            'factor_name': 'lead_time_optimization',
            'weight': 8,
            'description': 'Optimize delivery times to meet project deadlines'
        },
        {
            'factor_name': 'supplier_rating',
            'weight': 7,
            'description': 'Consider supplier reliability and quality ratings'
        },
        {
            'factor_name': 'cash_flow_balance',
            'weight': 8,
            'description': 'Balance cash outflows across time periods'
        },
        {
            'factor_name': 'bundle_discount_maximization',
            'weight': 6,
            'description': 'Maximize bulk purchase discounts when possible'
        },
        {
            'factor_name': 'quality_assurance',
            'weight': 7,
            'description': 'Ensure high-quality materials and workmanship'
        },
        {
            'factor_name': 'risk_mitigation',
            'weight': 6,
            'description': 'Minimize procurement and delivery risks'
        },
        {
            'factor_name': 'sustainability',
            'weight': 5,
            'description': 'Prefer environmentally friendly options'
        }
    ]
    
    for weight_data in weights_data:
        weight = DecisionFactorWeight(
            factor_name=weight_data['factor_name'],
            weight=weight_data['weight'],
            description=weight_data['description']
        )
        db.add(weight)
    
    await db.commit()
    logger.info("Decision factor weights created successfully")


async def seed_comprehensive_data():
    """Seed comprehensive test data - ONLY if database is empty"""
    async with AsyncSessionLocal() as db:
        try:
            # ✅ CHECK IF DATA EXISTS - Don't delete existing data!
            result = await db.execute(select(User))
            existing_users = result.scalars().all()
            
            if existing_users:
                logger.info("⏭️  Database already has data - SKIPPING seeding (data preserved!)")
                logger.info(f"   Found {len(existing_users)} existing users")
                return  # ← EXIT WITHOUT CLEARING DATA!
            
            logger.info("✅ Database is empty - Starting initial data seeding...")
            
            await clear_all_data(db)  # Only clears when DB is empty anyway
            await create_comprehensive_users(db)
            await create_comprehensive_projects(db)
            await create_project_assignments(db)
            await create_project_phases(db)
            await create_comprehensive_project_items(db)
            await create_comprehensive_procurement_options(db)
            await create_comprehensive_delivery_options(db)
            await create_comprehensive_budget_data(db)
            await create_decision_factor_weights(db)
            
            logger.info("✅ Initial test data seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Error seeding comprehensive data: {str(e)}")
            await db.rollback()
            raise


# Legacy function for backward compatibility
async def seed_sample_data():
    """Legacy function - now calls comprehensive seeding"""
    await seed_comprehensive_data()


if __name__ == "__main__":
    asyncio.run(seed_comprehensive_data())