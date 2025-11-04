"""
Comprehensive IT Company Seed Data
Creates realistic data for 10 IT projects with full procurement scenarios
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import random
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    User, Project, ProjectItem, ItemMaster, ProcurementOption,
    BudgetData, FinalizedDecision, CashflowEvent, OptimizationRun,
    ProjectAssignment, ProjectPhase, DeliveryOption, OptimizationResult
)
from app.auth import get_password_hash

# IT Company Items Master Catalog
IT_ITEMS_MASTER = [
    # Datacenter Infrastructure
    {"company": "Dell", "name": "PowerEdge Server", "model": "R750", "category": "Datacenter", "unit": "piece"},
    {"company": "Dell", "name": "PowerEdge Server", "model": "R640", "category": "Datacenter", "unit": "piece"},
    {"company": "HP", "name": "ProLiant Server", "model": "DL380", "category": "Datacenter", "unit": "piece"},
    {"company": "Cisco", "name": "Network Switch", "model": "Catalyst-9300", "category": "Networking", "unit": "piece"},
    {"company": "Cisco", "name": "Network Switch", "model": "Nexus-9000", "category": "Networking", "unit": "piece"},
    {"company": "APC", "name": "UPS System", "model": "Smart-UPS-5000", "category": "Power", "unit": "piece"},
    {"company": "APC", "name": "PDU", "model": "Rack-PDU-30A", "category": "Power", "unit": "piece"},
    {"company": "Panduit", "name": "Network Rack", "model": "42U", "category": "Infrastructure", "unit": "piece"},
    {"company": "Panduit", "name": "Cable Management", "model": "Horizontal", "category": "Infrastructure", "unit": "set"},
    {"company": "Vertiv", "name": "Precision Cooling", "model": "Liebert-20kW", "category": "Cooling", "unit": "piece"},
    
    # Security & Surveillance
    {"company": "Hikvision", "name": "IP Camera", "model": "DS-2CD2385", "category": "Security", "unit": "piece"},
    {"company": "Hikvision", "name": "NVR", "model": "DS-7732NI", "category": "Security", "unit": "piece"},
    {"company": "Dahua", "name": "PTZ Camera", "model": "SD59230U", "category": "Security", "unit": "piece"},
    {"company": "Axis", "name": "Thermal Camera", "model": "Q1941-E", "category": "Security", "unit": "piece"},
    {"company": "Milestone", "name": "VMS License", "model": "XProtect-Corporate", "category": "Software", "unit": "license"},
    {"company": "Ubiquiti", "name": "Access Point", "model": "UniFi-6-Pro", "category": "Networking", "unit": "piece"},
    
    # OCR & Document Processing
    {"company": "Fujitsu", "name": "Document Scanner", "model": "fi-7160", "category": "Scanning", "unit": "piece"},
    {"company": "Kodak", "name": "Production Scanner", "model": "i5850", "category": "Scanning", "unit": "piece"},
    {"company": "HP", "name": "Enterprise Scanner", "model": "ScanJet-N9120", "category": "Scanning", "unit": "piece"},
    {"company": "ABBYY", "name": "OCR Software", "model": "FineReader-Server", "category": "Software", "unit": "license"},
    {"company": "Microsoft", "name": "Azure OCR", "model": "Cognitive-Services", "category": "Cloud", "unit": "subscription"},
    
    # Networking & Connectivity
    {"company": "Ubiquiti", "name": "Fiber Cable", "model": "OM4-MPO", "category": "Cabling", "unit": "meter"},
    {"company": "CommScope", "name": "Cat6A Cable", "model": "Systimax", "category": "Cabling", "unit": "meter"},
    {"company": "Cisco", "name": "Firewall", "model": "ASA-5516", "category": "Security", "unit": "piece"},
    {"company": "Fortinet", "name": "Firewall", "model": "FortiGate-200F", "category": "Security", "unit": "piece"},
    {"company": "Aruba", "name": "Wireless Controller", "model": "7030", "category": "Networking", "unit": "piece"},
    
    # Storage & Backup
    {"company": "NetApp", "name": "Storage Array", "model": "FAS2750", "category": "Storage", "unit": "piece"},
    {"company": "Dell", "name": "Storage Array", "model": "PowerVault-ME4", "category": "Storage", "unit": "piece"},
    {"company": "Veeam", "name": "Backup Software", "model": "Availability-Suite", "category": "Software", "unit": "license"},
    {"company": "Commvault", "name": "Backup Solution", "model": "Complete-Backup", "category": "Software", "unit": "license"},
    
    # Workstations & Peripherals
    {"company": "Dell", "name": "Workstation", "model": "Precision-5820", "category": "Computing", "unit": "piece"},
    {"company": "HP", "name": "Monitor", "model": "Z27-4K", "category": "Display", "unit": "piece"},
    {"company": "Logitech", "name": "Keyboard-Mouse Set", "model": "MK850", "category": "Peripherals", "unit": "set"},
    
    # Software & Licenses
    {"company": "Microsoft", "name": "Windows Server", "model": "2022-Datacenter", "category": "Software", "unit": "license"},
    {"company": "Microsoft", "name": "SQL Server", "model": "2022-Enterprise", "category": "Software", "unit": "license"},
    {"company": "VMware", "name": "vSphere", "model": "Enterprise-Plus", "category": "Software", "unit": "license"},
    {"company": "Red Hat", "name": "Enterprise Linux", "model": "RHEL-8", "category": "Software", "unit": "subscription"},
]

# 10 IT Projects
IT_PROJECTS = [
    {
        "code": "DC-2025-001",
        "name": "Primary Datacenter Expansion",
        "description": "Expand datacenter capacity with 20 new server racks",
        "item_count": 85
    },
    {
        "code": "SEC-2025-001", 
        "name": "Industrial Security Camera System",
        "description": "Deploy 150 security cameras across 5 facilities",
        "item_count": 45
    },
    {
        "code": "OCR-2025-001",
        "name": "Document Digitization & OCR Platform",
        "description": "Enterprise OCR system for 50,000 documents/day",
        "item_count": 25
    },
    {
        "code": "NET-2025-001",
        "name": "Campus Network Upgrade",
        "description": "10Gbps fiber network for 3 buildings",
        "item_count": 60
    },
    {
        "code": "CLOUD-2025-001",
        "name": "Hybrid Cloud Infrastructure",
        "description": "Setup hybrid cloud with on-premise + AWS",
        "item_count": 40
    },
    {
        "code": "DR-2025-001",
        "name": "Disaster Recovery Site",
        "description": "Secondary datacenter for business continuity",
        "item_count": 70
    },
    {
        "code": "STOR-2025-001",
        "name": "Enterprise Storage Upgrade",
        "description": "1PB storage array with backup solution",
        "item_count": 30
    },
    {
        "code": "SEC-2025-002",
        "name": "Perimeter Security & Access Control",
        "description": "Integrated security system for HQ",
        "item_count": 35
    },
    {
        "code": "WORK-2025-001",
        "name": "Developer Workstation Refresh",
        "description": "200 high-performance workstations",
        "item_count": 15
    },
    {
        "code": "MON-2025-001",
        "name": "Infrastructure Monitoring System",
        "description": "Complete monitoring and alerting platform",
        "item_count": 20
    },
]

async def clear_all_data(db: AsyncSession):
    """Clear all data from database"""
    print("🗑️  Clearing existing data...")
    
    tables_to_clear = [
        CashflowEvent,
        FinalizedDecision,
        OptimizationResult,  # Must be before ProcurementOption (has FK to it)
        OptimizationRun,
        ProcurementOption,
        DeliveryOption,
        ProjectItem,
        ItemMaster,
        ProjectPhase,
        ProjectAssignment,
        Project,
        BudgetData,
        User,
    ]
    
    for table in tables_to_clear:
        await db.execute(delete(table))
    
    await db.commit()
    print("✅ All data cleared")


async def create_users(db: AsyncSession):
    """Create users"""
    print("👥 Creating users...")
    
    users_data = [
        {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
        {'username': 'pmo1', 'password': 'pmo123', 'role': 'pmo'},
        {'username': 'pm1', 'password': 'pm123', 'role': 'pm'},
        {'username': 'pm2', 'password': 'pm123', 'role': 'pm'},
        {'username': 'finance1', 'password': 'finance123', 'role': 'finance'},
        {'username': 'proc1', 'password': 'proc123', 'role': 'procurement'},
        {'username': 'proc2', 'password': 'proc123', 'role': 'procurement'},
    ]
    
    created_users = {}
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            password_hash=get_password_hash(user_data['password']),
            role=user_data['role']
        )
        db.add(user)
        created_users[user_data['username']] = user
    
    await db.commit()
    for username in created_users:
        await db.refresh(created_users[username])
    
    print(f"✅ Created {len(users_data)} users")
    return created_users


async def create_items_master(db: AsyncSession):
    """Create Items Master catalog"""
    print("📦 Creating Items Master catalog...")
    
    created_items = []
    
    for item_data in IT_ITEMS_MASTER:
        # Generate item code
        company_clean = item_data['company'].upper().replace(' ', '')
        name_clean = item_data['name'].upper().replace(' ', '-')
        model_clean = item_data.get('model', '').upper().replace(' ', '-').replace('.', '')
        
        if model_clean:
            item_code = f"{company_clean}-{name_clean}-{model_clean}"
        else:
            item_code = f"{company_clean}-{name_clean}"
        
        item = ItemMaster(
            item_code=item_code,
            company=item_data['company'],
            item_name=item_data['name'],
            model=item_data.get('model', ''),
            category=item_data['category'],
            unit=item_data['unit'],
            specifications={},
            is_active=True
        )
        db.add(item)
        created_items.append(item)
    
    await db.commit()
    for item in created_items:
        await db.refresh(item)
    
    print(f"✅ Created {len(created_items)} master items")
    return created_items


async def create_projects_with_items(db: AsyncSession, master_items, users):
    """Create 10 IT projects with items"""
    print("🏢 Creating IT projects...")
    
    projects = []
    all_project_items = []
    
    # Common delivery dates for testing same-time deliveries
    base_date = datetime.now() + timedelta(days=30)
    common_dates = [
        (base_date + timedelta(days=30)).strftime('%Y-%m-%d'),   # Month 1
        (base_date + timedelta(days=60)).strftime('%Y-%m-%d'),   # Month 2
        (base_date + timedelta(days=90)).strftime('%Y-%m-%d'),   # Month 3
        (base_date + timedelta(days=120)).strftime('%Y-%m-%d'),  # Month 4
    ]
    
    for idx, project_data in enumerate(IT_PROJECTS, 1):
        # Create project
        project = Project(
            project_code=project_data['code'],
            name=project_data['name'],
            priority_weight=random.randint(3, 8),
            is_active=True
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        projects.append(project)
        
        # Assign to PM
        pm_user = users['pm1'] if idx % 2 == 1 else users['pm2']
        assignment = ProjectAssignment(
            user_id=pm_user.id,
            project_id=project.id
        )
        db.add(assignment)
        
        # Create project phases
        phase = ProjectPhase(
            project_id=project.id,
            phase_name="Implementation Phase",
            start_date=base_date.date(),
            end_date=(base_date + timedelta(days=120)).date()
        )
        db.add(phase)
        
        # Determine how many items for this project
        item_count = project_data['item_count']
        
        # Select items for this project
        selected_items = random.sample(master_items, min(item_count, len(master_items)))
        
        # Add items to project
        for item_idx, master_item in enumerate(selected_items):
            quantity = random.randint(30, 80)
            
            # Delivery options - some use common dates, some unique
            if random.random() < 0.4:  # 40% chance of using common dates
                # Use common dates (for testing same delivery time)
                delivery_dates = random.sample(common_dates, k=random.randint(1, 2))
            else:
                # Use unique dates
                delivery_dates = [
                    (base_date + timedelta(days=random.randint(20, 150))).strftime('%Y-%m-%d')
                    for _ in range(random.randint(1, 3))
                ]
            
            # Project-specific description
            descriptions = [
                f"For {project_data['name']}, {random.choice(['Phase 1', 'Phase 2', 'Phase 3'])}",
                f"Deploy in {random.choice(['Building A', 'Building B', 'Building C', 'Main Facility'])}",
                f"Installation: {random.choice(['Ground floor', 'Second floor', 'Roof', 'Basement'])}",
                f"Priority: {random.choice(['High', 'Medium', 'Standard'])} - {random.choice(['Critical path', 'Flexible timing', 'As available'])}",
                f"Location: {random.choice(['Server Room', 'NOC', 'Data Hall', 'Equipment Room', 'Office Area'])}",
            ]
            
            project_item = ProjectItem(
                project_id=project.id,
                master_item_id=master_item.id,
                item_code=master_item.item_code,
                item_name=master_item.item_name,
                quantity=quantity,
                delivery_options=delivery_dates,
                description=random.choice(descriptions),
                external_purchase=False,
                status='PENDING'
            )
            db.add(project_item)
            all_project_items.append(project_item)
            
            # Create delivery options for this project item
            await db.commit()
            await db.refresh(project_item)
            
            for slot, delivery_date_str in enumerate(delivery_dates, 1):
                # Convert string to date object
                delivery_date_obj = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
                
                # Calculate selling price with 20-25% markup on buying price
                # Use a consistent base price for this item
                # We'll use a hash of the item code to ensure consistency
                import hashlib
                item_hash = int(hashlib.md5(project_item.item_code.encode()).hexdigest()[:8], 16)
                base_price = Decimal(str(50 + (item_hash % 1950)))  # Range: 50-2000
                
                # Apply 20-25% markup (varies by item hash for realism)
                markup_percent = Decimal('1.20') + (Decimal(str(item_hash % 6)) / Decimal('100'))  # 1.20 to 1.25
                selling_price = base_price * markup_percent
                
                delivery_option = DeliveryOption(
                    project_item_id=project_item.id,
                    delivery_date=delivery_date_obj,
                    delivery_slot=slot,
                    invoice_amount_per_unit=selling_price
                )
                db.add(delivery_option)
        
        await db.commit()
        print(f"✅ Created project: {project_data['code']} with {item_count} items")
    
    # Refresh all project items
    for item in all_project_items:
        await db.refresh(item)
    
    return projects, all_project_items


async def create_comprehensive_procurement_options(db: AsyncSession, project_items):
    """Create comprehensive procurement options for all items"""
    print("💼 Creating comprehensive procurement options...")
    
    # Supplier names for variety
    suppliers = {
        "Datacenter": ["Dell Direct", "CDW", "Insight", "SHI International", "Zones"],
        "Networking": ["Cisco Partner", "NetGear Direct", "Tech Data", "Ingram Micro"],
        "Security": ["Hikvision Distributor", "Security Solutions Inc", "IP Video Market", "ADI"],
        "Software": ["Microsoft Direct", "SoftwareOne", "Insight", "CDW Software"],
        "Storage": ["NetApp Direct", "Pure Storage", "EMC/Dell", "HPE Storage"],
        "Power": ["APC by Schneider", "Power Systems Plus", "Critical Power"],
        "Cooling": ["Vertiv Direct", "Cooling Solutions", "Data Center Cooling"],
    }
    
    options_created = 0
    
    # Group items by item_code
    items_by_code = {}
    for item in project_items:
        if item.item_code not in items_by_code:
            items_by_code[item.item_code] = []
        items_by_code[item.item_code].append(item)
    
    # Store base prices for each item to ensure consistency between buying and selling
    item_base_prices = {}
    
    # For each unique item code, create 3-5 procurement options
    for item_code, items_list in items_by_code.items():
        # Get category from first item
        first_item = items_list[0]
        category = "General" if not hasattr(first_item, 'category') else "General"
        
        # Generate consistent base price for this item (used for both buying and selling)
        # Use hash of item code to ensure same price across runs
        import hashlib
        item_hash = int(hashlib.md5(item_code.encode()).hexdigest()[:8], 16)
        base_price_for_item = Decimal(str(50 + (item_hash % 1950)))  # Range: 50-2000
        item_base_prices[item_code] = base_price_for_item
        
        # Get appropriate suppliers
        supplier_list = suppliers.get(category, ["Supplier A", "Supplier B", "Supplier C"])
        num_options = random.randint(3, 5)
        
        for i in range(num_options):
            supplier_name = random.choice(supplier_list) if i < len(supplier_list) else f"Supplier {chr(65+i)}"
            
            # Base cost varies by supplier (realistic IT equipment pricing)
            # Use the item's base price with some variation for different suppliers (±10%)
            # This ensures delivery option invoice (base_price × 1.20-1.25) is always 20-25% above avg procurement cost
            price_variation = Decimal(str(random.uniform(0.9, 1.1)))  # ±10% variation
            base_cost = base_price_for_item * price_variation
            
            # Lead time (delivery slot)
            lead_time = random.randint(1, 4)
            
            # Bundle discount (40% of options have it)
            if random.random() < 0.4:
                bundle_threshold = random.randint(20, 50)
                bundle_discount = Decimal(str(random.uniform(5, 15)))
            else:
                bundle_threshold = None
                bundle_discount = None
            
            # Payment terms (varied)
            payment_type_choice = random.random()
            
            if payment_type_choice < 0.4:  # 40% cash
                payment_terms = {
                    "type": "cash",
                    "discount_percent": float(Decimal(str(random.uniform(2, 7))))
                }
            else:  # 60% installments
                num_installments = random.randint(2, 4)
                if num_installments == 2:
                    schedule = [
                        {"due_offset": 0, "percent": 50.0},
                        {"due_offset": 30, "percent": 50.0}
                    ]
                elif num_installments == 3:
                    schedule = [
                        {"due_offset": 0, "percent": 40.0},
                        {"due_offset": 30, "percent": 30.0},
                        {"due_offset": 60, "percent": 30.0}
                    ]
                else:  # 4 installments
                    schedule = [
                        {"due_offset": 0, "percent": 25.0},
                        {"due_offset": 30, "percent": 25.0},
                        {"due_offset": 60, "percent": 25.0},
                        {"due_offset": 90, "percent": 25.0}
                    ]
                payment_terms = {
                    "type": "installments",
                    "schedule": schedule
                }
            
            option = ProcurementOption(
                item_code=item_code,
                supplier_name=supplier_name,
                base_cost=base_cost,
                lomc_lead_time=lead_time,
                discount_bundle_threshold=bundle_threshold,
                discount_bundle_percent=bundle_discount,
                payment_terms=payment_terms,
                is_active=True
            )
            db.add(option)
            options_created += 1
        
        # Commit every 50 options
        if options_created % 50 == 0:
            await db.commit()
    
    await db.commit()
    print(f"✅ Created {options_created} procurement options")


async def create_budget_data(db: AsyncSession):
    """Create monthly budget data"""
    print("💰 Creating budget data...")
    
    base_date = datetime.now()
    # Realistic IT company budgets (total ~$18M for 310 items @ avg $200/unit × 40qty = ~$2.5M needed)
    monthly_budgets = [
        2000000, 1800000, 1600000, 1500000, 1400000, 1200000,
        1000000, 900000, 800000, 700000, 650000, 600000
    ]
    
    for month_offset, budget_amount in enumerate(monthly_budgets):
        budget_date_obj = (base_date + timedelta(days=30 * month_offset)).date()
        
        budget = BudgetData(
            budget_date=budget_date_obj,
            available_budget=Decimal(str(budget_amount))
        )
        db.add(budget)
    
    await db.commit()
    print(f"✅ Created {len(monthly_budgets)} budget periods")


async def seed_it_company_data():
    """Main seeding function"""
    print("\n" + "="*60)
    print("🚀 SEEDING IT COMPANY COMPREHENSIVE DATA")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Clear all data
            await clear_all_data(db)
            
            # Step 2: Create users
            users = await create_users(db)
            
            # Step 3: Create Items Master catalog
            master_items = await create_items_master(db)
            
            # Step 4: Create projects with items
            projects, project_items = await create_projects_with_items(db, master_items, users)
            
            # Step 5: Create procurement options
            await create_comprehensive_procurement_options(db, project_items)
            
            # Step 6: Create budget data
            await create_budget_data(db)
            
            print("\n" + "="*60)
            print("🎉 IT COMPANY DATA SEEDING COMPLETE!")
            print("="*60)
            print(f"\n📊 Summary:")
            print(f"   Users: 7")
            print(f"   Projects: {len(projects)}")
            print(f"   Master Items: {len(master_items)}")
            print(f"   Project Items: {len(project_items)}")
            print(f"   Budget Periods: 12")
            print(f"\n✅ Platform ready for comprehensive testing!")
            print(f"\n🔑 Login Credentials:")
            print(f"   Admin: admin / admin123")
            print(f"   PMO: pmo1 / pmo123")
            print(f"   PM: pm1 / pm123, pm2 / pm123")
            print(f"   Finance: finance1 / finance123")
            print(f"   Procurement: proc1 / proc123, proc2 / proc123")
            print()
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_it_company_data())

