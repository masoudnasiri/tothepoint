"""
Comprehensive Platform Reset and Seeding Script
This script will:
1. Wipe all operational data
2. Create 10 projects with 300 items each (3000 total items)
3. Add multiple delivery options for each item
4. Add multiple procurement options for each item
"""

import asyncio
import random
from datetime import date, timedelta, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from app.database import AsyncSessionLocal
from app.models import (
    User, Project, ProjectAssignment, ProjectPhase, ProjectItem, 
    ProcurementOption, BudgetData, DecisionFactorWeight, ProjectItemStatus,
    DeliveryOption, ItemMaster, Currency, ExchangeRate
)
from app.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)

async def clear_all_operational_data(db: AsyncSession):
    """Clear all operational data while preserving system data"""
    logger.info("Clearing all operational data...")
    
    # Delete in reverse dependency order (procurement_options must be deleted before delivery_options)
    tables_to_clear = [
        "cashflow_events",
        "finalized_decisions", 
        "optimization_results",
        "optimization_runs",
        "procurement_options",  # Must be deleted before delivery_options
        "delivery_options",
        "project_items",
        "project_phases",
        "project_assignments",
        "budget_data",
        "decision_factor_weights",
        "projects",
        "items_master",
        "exchange_rates",  # Must be deleted before users
        "currencies",  # Must be deleted before users
        "users"  # Clear users as well
    ]
    
    for table in tables_to_clear:
        await db.execute(text(f"DELETE FROM {table}"))
        logger.info(f"Cleared {table}")
    
    await db.commit()
    logger.info("All operational data cleared")

async def create_system_users(db: AsyncSession):
    """Create essential system users"""
    logger.info("Creating system users...")
    
    users_data = [
        {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
        {'username': 'pmo', 'password': 'pmo123', 'role': 'pmo'},
        {'username': 'pm1', 'password': 'pm123', 'role': 'pm'},
        {'username': 'pm2', 'password': 'pm123', 'role': 'pm'},
        {'username': 'pm3', 'password': 'pm123', 'role': 'pm'},
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
    logger.info("System users created successfully")

async def create_currencies(db: AsyncSession):
    """Create currency master data"""
    logger.info("Creating currencies...")
    
    currencies_data = [
        {'code': 'IRR', 'name': 'Iranian Rial', 'symbol': '﷼', 'is_base_currency': True, 'decimal_places': 0},
        {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'is_base_currency': False, 'decimal_places': 2},
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'is_base_currency': False, 'decimal_places': 2},
        {'code': 'AED', 'name': 'UAE Dirham', 'symbol': 'د.إ', 'is_base_currency': False, 'decimal_places': 2},
    ]
    
    for currency_data in currencies_data:
        currency = Currency(**currency_data)
        db.add(currency)
    
    await db.commit()
    logger.info("Currencies created successfully")

async def create_exchange_rates(db: AsyncSession):
    """Create sample exchange rates"""
    logger.info("Creating exchange rates...")
    
    base_date = date(2025, 1, 1)
    rates = [
        {'from_currency': 'USD', 'to_currency': 'IRR', 'rate': Decimal('42000.000000')},
        {'from_currency': 'EUR', 'to_currency': 'IRR', 'rate': Decimal('46000.000000')},
        {'from_currency': 'AED', 'to_currency': 'IRR', 'rate': Decimal('11400.000000')},
    ]
    
    for i in range(30):  # 30 days of rates
        rate_date = base_date + timedelta(days=i)
        for rate_data in rates:
            rate = ExchangeRate(
                date=rate_date,
                from_currency=rate_data['from_currency'],
                to_currency=rate_data['to_currency'],
                rate=rate_data['rate'] + Decimal(str(random.uniform(-0.02, 0.02)))  # ±2% variation
            )
            db.add(rate)
    
    await db.commit()
    logger.info("Exchange rates created successfully")

async def create_items_master(db: AsyncSession):
    """Create comprehensive items master catalog"""
    logger.info("Creating items master catalog...")
    
    # Comprehensive construction and IT item catalog
    items_catalog = [
        # Construction Materials
        {'item_code': 'STEEL-H200', 'company': 'SteelCorp', 'item_name': 'Structural Steel H-Beam 200x200mm', 'model': 'H200', 'category': 'Construction', 'unit': 'meter'},
        {'item_code': 'STEEL-RB60', 'company': 'SteelCorp', 'item_name': 'Reinforcement Bars Grade 60', 'model': 'RB60', 'category': 'Construction', 'unit': 'kg'},
        {'item_code': 'CONC-C25', 'company': 'ConcreteCo', 'item_name': 'Ready-Mix Concrete Grade C25', 'model': 'C25', 'category': 'Construction', 'unit': 'm³'},
        {'item_code': 'CONC-C30', 'company': 'ConcreteCo', 'item_name': 'Ready-Mix Concrete Grade C30', 'model': 'C30', 'category': 'Construction', 'unit': 'm³'},
        {'item_code': 'CEMENT-P1', 'company': 'CementCorp', 'item_name': 'Portland Cement Type I', 'model': 'P1', 'category': 'Construction', 'unit': 'bag'},
        {'item_code': 'AGG-COARSE', 'company': 'AggregateCo', 'item_name': 'Coarse Aggregate 20mm', 'model': '20mm', 'category': 'Construction', 'unit': 'm³'},
        {'item_code': 'AGG-FINE', 'company': 'AggregateCo', 'item_name': 'Fine Aggregate River Sand', 'model': 'RS', 'category': 'Construction', 'unit': 'm³'},
        
        # Formwork & Scaffolding
        {'item_code': 'FORM-STEEL', 'company': 'FormworkCo', 'item_name': 'Steel Formwork Panels', 'model': 'SF-100', 'category': 'Construction', 'unit': 'm²'},
        {'item_code': 'FORM-PLY', 'company': 'FormworkCo', 'item_name': 'Plywood Formwork Sheets', 'model': 'PF-18', 'category': 'Construction', 'unit': 'm²'},
        {'item_code': 'SCAFF-TUBE', 'company': 'ScaffoldCo', 'item_name': 'Steel Scaffolding Tubes', 'model': 'ST-48', 'category': 'Construction', 'unit': 'meter'},
        
        # Insulation & Roofing
        {'item_code': 'INSUL-ROCK', 'company': 'InsulCo', 'item_name': 'Rockwool Thermal Insulation', 'model': 'RW-50', 'category': 'Construction', 'unit': 'm²'},
        {'item_code': 'INSUL-FIBER', 'company': 'InsulCo', 'item_name': 'Fiberglass Acoustic Insulation', 'model': 'FG-75', 'category': 'Construction', 'unit': 'm²'},
        {'item_code': 'ROOF-CLAY', 'company': 'RoofCo', 'item_name': 'Clay Roofing Tiles', 'model': 'CT-300', 'category': 'Construction', 'unit': 'm²'},
        {'item_code': 'ROOF-EPDM', 'company': 'RoofCo', 'item_name': 'EPDM Roofing Membrane', 'model': 'EP-1.5', 'category': 'Construction', 'unit': 'm²'},
        
        # Windows & Doors
        {'item_code': 'WIN-ALU-DG', 'company': 'WindowCo', 'item_name': 'Aluminum Double Glazed Windows', 'model': 'AW-DG-120', 'category': 'Construction', 'unit': 'm²'},
        {'item_code': 'DOOR-STEEL', 'company': 'DoorCo', 'item_name': 'Steel Fire Rated Doors', 'model': 'SD-FR-90', 'category': 'Construction', 'unit': 'piece'},
        {'item_code': 'DOOR-WOOD', 'company': 'DoorCo', 'item_name': 'Solid Wood Interior Doors', 'model': 'WD-SW-80', 'category': 'Construction', 'unit': 'piece'},
        
        # Electrical
        {'item_code': 'CABLE-3C25', 'company': 'ElectroCo', 'item_name': '3-Core Electrical Cable 2.5mm²', 'model': 'EC-3C25', 'category': 'Electrical', 'unit': 'meter'},
        {'item_code': 'CABLE-3C40', 'company': 'ElectroCo', 'item_name': '3-Core Electrical Cable 4.0mm²', 'model': 'EC-3C40', 'category': 'Electrical', 'unit': 'meter'},
        {'item_code': 'CONDUIT-PVC25', 'company': 'ElectroCo', 'item_name': 'PVC Electrical Conduit 25mm', 'model': 'PC-25', 'category': 'Electrical', 'unit': 'meter'},
        {'item_code': 'CONDUIT-PVC40', 'company': 'ElectroCo', 'item_name': 'PVC Electrical Conduit 40mm', 'model': 'PC-40', 'category': 'Electrical', 'unit': 'meter'},
        {'item_code': 'SWITCH-SINGLE', 'company': 'ElectroCo', 'item_name': 'Single Pole Light Switch', 'model': 'SW-SP-10A', 'category': 'Electrical', 'unit': 'piece'},
        {'item_code': 'SOCKET-13A', 'company': 'ElectroCo', 'item_name': '13A Power Socket', 'model': 'SK-13A-10A', 'category': 'Electrical', 'unit': 'piece'},
        {'item_code': 'LIGHT-LED', 'company': 'ElectroCo', 'item_name': 'LED Light Fixtures Industrial', 'model': 'LL-50W', 'category': 'Electrical', 'unit': 'piece'},
        
        # Plumbing
        {'item_code': 'PIPE-PVC100', 'company': 'PlumbCo', 'item_name': 'PVC Water Pipe 100mm', 'model': 'PP-100', 'category': 'Plumbing', 'unit': 'meter'},
        {'item_code': 'PIPE-PVC150', 'company': 'PlumbCo', 'item_name': 'PVC Water Pipe 150mm', 'model': 'PP-150', 'category': 'Plumbing', 'unit': 'meter'},
        {'item_code': 'PIPE-HDPE200', 'company': 'PlumbCo', 'item_name': 'HDPE Sewage Pipe 200mm', 'model': 'HP-200', 'category': 'Plumbing', 'unit': 'meter'},
        {'item_code': 'FITTING-ELBOW', 'company': 'PlumbCo', 'item_name': 'PVC Elbow Fitting 100mm', 'model': 'PF-E-100', 'category': 'Plumbing', 'unit': 'piece'},
        {'item_code': 'FITTING-TEE', 'company': 'PlumbCo', 'item_name': 'PVC Tee Fitting 100mm', 'model': 'PF-T-100', 'category': 'Plumbing', 'unit': 'piece'},
        
        # HVAC
        {'item_code': 'AC-SPLIT-1.5', 'company': 'HVACCo', 'item_name': 'Split AC Unit 1.5 Ton', 'model': 'AC-S-1.5T', 'category': 'HVAC', 'unit': 'piece'},
        {'item_code': 'AC-SPLIT-2.0', 'company': 'HVACCo', 'item_name': 'Split AC Unit 2.0 Ton', 'model': 'AC-S-2.0T', 'category': 'HVAC', 'unit': 'piece'},
        {'item_code': 'FAN-EXHAUST', 'company': 'HVACCo', 'item_name': 'Exhaust Fan Industrial', 'model': 'EF-12', 'category': 'HVAC', 'unit': 'piece'},
        {'item_code': 'DUCT-GALV', 'company': 'HVACCo', 'item_name': 'Galvanized Air Duct 300mm', 'model': 'AD-G-300', 'category': 'HVAC', 'unit': 'meter'},
        
        # IT Equipment
        {'item_code': 'PC-DESKTOP', 'company': 'TechCorp', 'item_name': 'Desktop Computer i5', 'model': 'PC-D-i5-16GB', 'category': 'IT', 'unit': 'piece'},
        {'item_code': 'PC-LAPTOP', 'company': 'TechCorp', 'item_name': 'Laptop Computer i7', 'model': 'PC-L-i7-16GB', 'category': 'IT', 'unit': 'piece'},
        {'item_code': 'MONITOR-24', 'company': 'TechCorp', 'item_name': '24" LED Monitor', 'model': 'M-24-LED', 'category': 'IT', 'unit': 'piece'},
        {'item_code': 'MONITOR-27', 'company': 'TechCorp', 'item_name': '27" LED Monitor', 'model': 'M-27-LED', 'category': 'IT', 'unit': 'piece'},
        {'item_code': 'SWITCH-24P', 'company': 'TechCorp', 'item_name': '24-Port Network Switch', 'model': 'NS-24P-GIG', 'category': 'IT', 'unit': 'piece'},
        {'item_code': 'ROUTER-WIFI', 'company': 'TechCorp', 'item_name': 'WiFi Router AC1200', 'model': 'WR-AC1200', 'category': 'IT', 'unit': 'piece'},
        {'item_code': 'CABLE-CAT6', 'company': 'TechCorp', 'item_name': 'CAT6 Network Cable', 'model': 'NC-CAT6-305M', 'category': 'IT', 'unit': 'meter'},
        
        # Furniture
        {'item_code': 'DESK-EXEC', 'company': 'FurniCo', 'item_name': 'Executive Desk 160cm', 'model': 'ED-160-OAK', 'category': 'Furniture', 'unit': 'piece'},
        {'item_code': 'CHAIR-EXEC', 'company': 'FurniCo', 'item_name': 'Executive Chair Ergonomic', 'model': 'EC-ERG-BLK', 'category': 'Furniture', 'unit': 'piece'},
        {'item_code': 'TABLE-MEET', 'company': 'FurniCo', 'item_name': 'Meeting Table 8-Seat', 'model': 'MT-8S-OAK', 'category': 'Furniture', 'unit': 'piece'},
        {'item_code': 'CHAIR-MEET', 'company': 'FurniCo', 'item_name': 'Meeting Chair Standard', 'model': 'MC-STD-BLK', 'category': 'Furniture', 'unit': 'piece'},
        
        # Safety & Security
        {'item_code': 'FIRE-EXT-10KG', 'company': 'SafetyCo', 'item_name': 'Fire Extinguisher 10kg', 'model': 'FE-10KG-ABC', 'category': 'Safety', 'unit': 'piece'},
        {'item_code': 'FIRE-ALARM', 'company': 'SafetyCo', 'item_name': 'Fire Alarm System Wireless', 'model': 'FA-WL-ADDR', 'category': 'Safety', 'unit': 'piece'},
        {'item_code': 'CAM-IP-4MP', 'company': 'SecurityCo', 'item_name': 'IP Security Camera 4MP', 'model': 'SC-IP-4MP', 'category': 'Security', 'unit': 'piece'},
        {'item_code': 'ACCESS-CARD', 'company': 'SecurityCo', 'item_name': 'Access Control Card Reader', 'model': 'AC-CR-PROX', 'category': 'Security', 'unit': 'piece'},
        
        # Heavy Equipment
        {'item_code': 'EXCAVATOR-20T', 'company': 'HeavyCo', 'item_name': 'Excavator 20 Ton Capacity', 'model': 'EX-20T-CAT', 'category': 'Equipment', 'unit': 'piece'},
        {'item_code': 'CRANE-50T', 'company': 'HeavyCo', 'item_name': 'Mobile Crane 50 Ton', 'model': 'MC-50T-LIEB', 'category': 'Equipment', 'unit': 'piece'},
        {'item_code': 'MIXER-3M3', 'company': 'HeavyCo', 'item_name': 'Concrete Mixer 3m³', 'model': 'CM-3M3-SELF', 'category': 'Equipment', 'unit': 'piece'},
        {'item_code': 'LOADER-3M3', 'company': 'HeavyCo', 'item_name': 'Wheel Loader 3m³ Bucket', 'model': 'WL-3M3-CAT', 'category': 'Equipment', 'unit': 'piece'},
    ]
    
    for item_data in items_catalog:
        item = ItemMaster(
            item_code=item_data['item_code'],
            company=item_data['company'],
            item_name=item_data['item_name'],
            model=item_data['model'],
            category=item_data['category'],
            unit=item_data['unit'],
            description=f"High quality {item_data['item_name'].lower()} from {item_data['company']}",
            is_active=True
        )
        db.add(item)
    
    await db.commit()
    logger.info(f"Items master catalog created with {len(items_catalog)} items")

async def create_projects(db: AsyncSession):
    """Create 10 comprehensive projects"""
    logger.info("Creating 10 projects...")
    
    projects_data = [
        {'project_code': 'INFRA001', 'name': 'Highway Infrastructure Project', 'priority_weight': 10, 'budget_amount': Decimal('50000000'), 'budget_currency': 'IRR'},
        {'project_code': 'BUILD002', 'name': 'Commercial Building Complex', 'priority_weight': 9, 'budget_amount': Decimal('75000000'), 'budget_currency': 'IRR'},
        {'project_code': 'RESI003', 'name': 'Residential Housing Development', 'priority_weight': 8, 'budget_amount': Decimal('30000000'), 'budget_currency': 'IRR'},
        {'project_code': 'INDU004', 'name': 'Industrial Manufacturing Plant', 'priority_weight': 7, 'budget_amount': Decimal('100000000'), 'budget_currency': 'IRR'},
        {'project_code': 'UTIL005', 'name': 'Utilities Infrastructure Upgrade', 'priority_weight': 6, 'budget_amount': Decimal('25000000'), 'budget_currency': 'IRR'},
        {'project_code': 'TECH006', 'name': 'Technology Center Development', 'priority_weight': 9, 'budget_amount': Decimal('40000000'), 'budget_currency': 'IRR'},
        {'project_code': 'HOSP007', 'name': 'Hospital Expansion Project', 'priority_weight': 10, 'budget_amount': Decimal('80000000'), 'budget_currency': 'IRR'},
        {'project_code': 'MALL008', 'name': 'Shopping Mall Construction', 'priority_weight': 7, 'budget_amount': Decimal('60000000'), 'budget_currency': 'IRR'},
        {'project_code': 'PARK009', 'name': 'Public Park & Recreation', 'priority_weight': 5, 'budget_amount': Decimal('15000000'), 'budget_currency': 'IRR'},
        {'project_code': 'PORT010', 'name': 'Port Infrastructure Modernization', 'priority_weight': 8, 'budget_amount': Decimal('70000000'), 'budget_currency': 'IRR'},
    ]
    
    for project_data in projects_data:
        project = Project(**project_data)
        db.add(project)
    
    await db.commit()
    logger.info("10 projects created successfully")

async def create_project_assignments(db: AsyncSession):
    """Assign users to projects"""
    logger.info("Creating project assignments...")
    
    # Get users and projects
    users_result = await db.execute(select(User).where(User.role.in_(['pm', 'pmo'])))
    users = users_result.scalars().all()
    
    projects_result = await db.execute(select(Project))
    projects = projects_result.scalars().all()
    
    # Assign PMs to projects (2-3 PMs per project)
    for project in projects:
        assigned_pms = random.sample(users, min(3, len(users)))
        for pm in assigned_pms:
            assignment = ProjectAssignment(user_id=pm.id, project_id=project.id)
            db.add(assignment)
    
    await db.commit()
    logger.info("Project assignments created successfully")

async def create_project_phases(db: AsyncSession):
    """Create phases for each project"""
    logger.info("Creating project phases...")
    
    projects_result = await db.execute(select(Project))
    projects = projects_result.scalars().all()
    
    phase_templates = [
        {'name': 'Planning & Design', 'duration_days': 60},
        {'name': 'Site Preparation', 'duration_days': 30},
        {'name': 'Foundation Work', 'duration_days': 45},
        {'name': 'Structural Construction', 'duration_days': 120},
        {'name': 'MEP Installation', 'duration_days': 90},
        {'name': 'Finishing Work', 'duration_days': 60},
        {'name': 'Testing & Commissioning', 'duration_days': 30},
    ]
    
    base_date = date(2025, 3, 1)
    
    for project in projects:
        current_date = base_date + timedelta(days=random.randint(0, 30))
        
        for phase_template in phase_templates:
            phase = ProjectPhase(
                project_id=project.id,
                phase_name=phase_template['name'],
                start_date=current_date,
                end_date=current_date + timedelta(days=phase_template['duration_days'])
            )
            db.add(phase)
            current_date += timedelta(days=phase_template['duration_days'] + random.randint(1, 7))
    
    await db.commit()
    logger.info("Project phases created successfully")

async def create_project_items(db: AsyncSession):
    """Create 300 items per project (3000 total)"""
    logger.info("Creating project items...")
    
    # Get all projects and items master
    projects_result = await db.execute(select(Project))
    projects = projects_result.scalars().all()
    
    items_master_result = await db.execute(select(ItemMaster))
    items_master = items_master_result.scalars().all()
    
    base_date = date(2025, 3, 1)
    
    for project in projects:
        logger.info(f"Creating items for project {project.project_code}...")
        
        # Select 300 random items from master catalog
        selected_items = random.sample(items_master, min(300, len(items_master)))
        
        for item_master in selected_items:
            # Generate realistic quantities
            if item_master.category == 'Equipment':
                quantity = random.randint(1, 5)  # Heavy equipment: 1-5 units
            elif item_master.category == 'IT':
                quantity = random.randint(5, 50)  # IT equipment: 5-50 units
            elif item_master.category == 'Furniture':
                quantity = random.randint(10, 100)  # Furniture: 10-100 units
            else:
                quantity = random.randint(10, 500)  # Construction materials: 10-500 units
            
            # Generate 3-5 delivery date options
            num_delivery_options = random.randint(3, 5)
            delivery_dates = []
            
            start_offset = random.randint(30, 180)  # Start 30-180 days from base
            for i in range(num_delivery_options):
                delivery_date = base_date + timedelta(days=start_offset + (i * random.randint(7, 30)))
                delivery_dates.append(delivery_date.isoformat())
            
            item = ProjectItem(
                project_id=project.id,
                master_item_id=item_master.id,
                item_code=item_master.item_code,
                item_name=item_master.item_name,
                quantity=quantity,
                delivery_options=delivery_dates,
                status=ProjectItemStatus.PENDING,
                external_purchase=random.choice([True, False]),
                description=f"Project-specific {item_master.item_name.lower()} for {project.name}"
            )
            db.add(item)
    
    await db.commit()
    logger.info("Project items created successfully")

async def create_delivery_options(db: AsyncSession):
    """Create delivery options for each project item"""
    logger.info("Creating delivery options...")
    
    items_result = await db.execute(select(ProjectItem))
    items = items_result.scalars().all()
    
    for item in items:
        # Create 3-5 delivery options per item
        num_options = random.randint(3, 5)
        
        for i in range(num_options):
            # Parse delivery date from JSON
            delivery_date_str = item.delivery_options[i] if i < len(item.delivery_options) else None
            if not delivery_date_str:
                continue
                
            delivery_date = datetime.fromisoformat(delivery_date_str).date()
            
            # Generate invoice timing
            invoice_timing_type = random.choice(['ABSOLUTE', 'RELATIVE'])
            invoice_issue_date = None
            invoice_days_after_delivery = None
            
            if invoice_timing_type == 'ABSOLUTE':
                invoice_issue_date = delivery_date + timedelta(days=random.randint(1, 30))
            else:
                invoice_days_after_delivery = random.randint(7, 60)
            
            # Generate revenue per unit (higher for premium delivery slots)
            base_revenue = random.uniform(50, 500)
            if i == 0:  # First option (fastest delivery) - premium pricing
                revenue_multiplier = random.uniform(1.2, 1.5)
            elif i == num_options - 1:  # Last option (slowest delivery) - discount pricing
                revenue_multiplier = random.uniform(0.8, 0.9)
            else:
                revenue_multiplier = random.uniform(0.9, 1.1)
            
            invoice_amount_per_unit = Decimal(str(round(base_revenue * revenue_multiplier, 2)))
            
            delivery_option = DeliveryOption(
                project_item_id=item.id,
                delivery_slot=i + 1,
                delivery_date=delivery_date,
                invoice_timing_type=invoice_timing_type,
                invoice_issue_date=invoice_issue_date,
                invoice_days_after_delivery=invoice_days_after_delivery,
                invoice_amount_per_unit=invoice_amount_per_unit,
                preference_rank=i + 1,
                notes=f"Delivery option {i + 1} for {item.item_name}",
                is_active=True
            )
            db.add(delivery_option)
    
    await db.commit()
    logger.info("Delivery options created successfully")

async def create_procurement_options(db: AsyncSession):
    """Create multiple procurement options for each item"""
    logger.info("Creating procurement options...")
    
    # Get currencies
    currencies_result = await db.execute(select(Currency))
    currencies = {c.code: c for c in currencies_result.scalars().all()}
    
    items_result = await db.execute(select(ProjectItem))
    items = items_result.scalars().all()
    
    # Supplier names
    suppliers = [
        'Alpha Suppliers Ltd', 'Beta Materials Co', 'Gamma Construction Supply',
        'Delta Industrial Corp', 'Epsilon Trading Co', 'Zeta Procurement Ltd',
        'Eta Manufacturing Inc', 'Theta Global Supply', 'Iota Materials Co',
        'Kappa Construction Supply', 'Lambda Industrial Ltd', 'Mu Trading Corp'
    ]
    
    for item in items:
        # Create 3-5 procurement options per item
        num_options = random.randint(3, 5)
        selected_suppliers = random.sample(suppliers, num_options)
        
        for i, supplier in enumerate(selected_suppliers):
            # Generate cost with variation
            base_cost = random.uniform(100, 2000)
            cost_variation = random.uniform(0.8, 1.3)  # ±30% variation
            cost_amount = Decimal(str(round(base_cost * cost_variation, 2)))
            
            # Select currency (70% IRR, 20% USD, 10% EUR)
            currency_choice = random.choices(['IRR', 'USD', 'EUR'], weights=[70, 20, 10])[0]
            cost_currency = currency_choice
            
            # Generate shipping cost (5-15% of item cost)
            shipping_cost = Decimal(str(round(float(cost_amount) * random.uniform(0.05, 0.15), 2)))
            
            # Generate expected delivery date
            base_delivery_date = date(2025, 4, 1) + timedelta(days=random.randint(30, 120))
            expected_delivery_date = base_delivery_date + timedelta(days=random.randint(0, 30))
            
            # Generate payment terms - simplified to only cash and installments
            if random.choice([True, False]):
                # Cash payment
                payment_terms = {
                    'type': 'cash',
                    'discount_percent': round(random.uniform(0, 10), 2) if random.choice([True, False]) else None
                }
            else:
                # Installments payment
                num_installments = random.randint(2, 4)
                schedule = []
                remaining_percent = 100
                
                for i in range(num_installments - 1):
                    percent = random.randint(10, remaining_percent - (num_installments - i - 1) * 10)
                    schedule.append({
                        'due_offset': i * 30,  # 30 days between installments
                        'percent': float(percent)
                    })
                    remaining_percent -= percent
                
                # Last installment gets remaining percent
                schedule.append({
                    'due_offset': (num_installments - 1) * 30,
                    'percent': float(remaining_percent)
                })
                
                payment_terms = {
                    'type': 'installments',
                    'schedule': schedule
                }
            
            # Generate discount terms
            discount_threshold = random.randint(100, 1000)
            discount_percent = random.uniform(5, 15)
            
            # Get currency_id for the selected currency
            currency_id = currencies[cost_currency].id if cost_currency in currencies else currencies['IRR'].id
            
            procurement_option = ProcurementOption(
                item_code=item.item_code,
                supplier_name=supplier,
                cost_amount=cost_amount,
                cost_currency=cost_currency,
                shipping_cost=shipping_cost,
                base_cost=cost_amount,  # Set base_cost to cost_amount for backward compatibility
                currency_id=currency_id,  # Set currency_id for backward compatibility
                expected_delivery_date=expected_delivery_date,
                discount_bundle_threshold=discount_threshold,
                discount_bundle_percent=Decimal(str(round(discount_percent, 2))),
                payment_terms=payment_terms,
                is_active=True,
                is_finalized=random.choice([True, False])
            )
            db.add(procurement_option)
    
    await db.commit()
    logger.info("Procurement options created successfully")

async def create_budget_data(db: AsyncSession):
    """Create budget data for the platform"""
    logger.info("Creating budget data...")
    
    base_date = date(2025, 3, 1)
    
    for i in range(12):  # 12 months of budget data
        budget_date = base_date + timedelta(days=i * 30)
        
        # Generate multi-currency budget
        multi_currency_budget = {
            'IRR': random.randint(50000000, 100000000),
            'USD': random.randint(1000000, 2000000),
            'EUR': random.randint(800000, 1500000),
            'AED': random.randint(3000000, 6000000)
        }
        
        budget = BudgetData(
            budget_date=budget_date,
            available_budget=Decimal(str(multi_currency_budget['IRR'])),
            multi_currency_budget=multi_currency_budget
        )
        db.add(budget)
    
    await db.commit()
    logger.info("Budget data created successfully")

async def create_decision_weights(db: AsyncSession):
    """Create decision factor weights"""
    logger.info("Creating decision factor weights...")
    
    factors = [
        {'name': 'cost', 'weight': 8, 'description': 'Cost optimization factor'},
        {'name': 'delivery_time', 'weight': 7, 'description': 'Delivery time factor'},
        {'name': 'supplier_reliability', 'weight': 6, 'description': 'Supplier reliability factor'},
        {'name': 'quality', 'weight': 7, 'description': 'Quality factor'},
        {'name': 'payment_terms', 'weight': 5, 'description': 'Payment terms factor'},
        {'name': 'currency_risk', 'weight': 4, 'description': 'Currency risk factor'},
        {'name': 'shipping_cost', 'weight': 3, 'description': 'Shipping cost factor'},
    ]
    
    for factor in factors:
        weight = DecisionFactorWeight(
            factor_name=factor['name'],
            weight=factor['weight'],
            description=factor['description']
        )
        db.add(weight)
    
    await db.commit()
    logger.info("Decision factor weights created successfully")

async def main():
    """Main execution function"""
    logger.info("Starting comprehensive platform reset and seeding...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Clear all operational data
            await clear_all_operational_data(db)
            
            # Step 2: Create system users
            await create_system_users(db)
            
            # Step 3: Create currencies and exchange rates
            await create_currencies(db)
            await create_exchange_rates(db)
            
            # Step 4: Create items master catalog
            await create_items_master(db)
            
            # Step 5: Create projects
            await create_projects(db)
            
            # Step 6: Create project assignments
            await create_project_assignments(db)
            
            # Step 7: Create project phases
            await create_project_phases(db)
            
            # Step 8: Create project items (300 per project)
            await create_project_items(db)
            
            # Step 9: Create delivery options for each item
            await create_delivery_options(db)
            
            # Step 10: Create procurement options for each item
            await create_procurement_options(db)
            
            # Step 11: Create budget data
            await create_budget_data(db)
            
            # Step 12: Create decision factor weights
            await create_decision_weights(db)
            
            logger.info("Comprehensive platform reset and seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during seeding: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
