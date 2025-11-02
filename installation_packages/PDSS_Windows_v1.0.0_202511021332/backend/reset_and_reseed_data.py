"""
Reset and Reseed Database with New Data Structure
Wipes operational data and creates fresh test data with USD and Rials pricing
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timedelta
import random

# Database connection
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/procurement_dss"

async def reset_database():
    """Wipe all operational data while preserving structure"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("🗑️  Deleting operational data...")
        
        # Delete in correct order (respecting foreign keys)
        await session.execute(text("DELETE FROM decisions"))
        await session.execute(text("DELETE FROM delivery_options"))
        await session.execute(text("DELETE FROM procurement_options"))
        await session.execute(text("DELETE FROM project_items"))
        await session.execute(text("DELETE FROM projects"))
        await session.execute(text("DELETE FROM items_master"))
        await session.execute(text("DELETE FROM exchange_rates"))
        await session.execute(text("DELETE FROM currencies"))
        await session.execute(text("DELETE FROM users WHERE username != 'admin'"))
        
        await session.commit()
        print("✅ Operational data deleted")
    
    await engine.dispose()


async def seed_new_data():
    """Seed database with new data structure including USD and Rials"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n🌱 Seeding new data...")
        
        # 1. Create Currencies
        print("\n💰 Creating currencies...")
        
        # USD as base currency
        await session.execute(text("""
            INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
            VALUES ('USD', 'US Dollar', '$', true, true, 2)
            ON CONFLICT (code) DO NOTHING
        """))
        
        # Iranian Rial
        await session.execute(text("""
            INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
            VALUES ('IRR', 'Iranian Rial', '﷼', false, true, 0)
            ON CONFLICT (code) DO NOTHING
        """))
        
        await session.commit()
        
        # Get currency IDs
        result = await session.execute(text("SELECT id, code FROM currencies"))
        currencies = {row[1]: row[0] for row in result}
        print(f"✅ Currencies created: {currencies}")
        
        # 2. Create Exchange Rates
        print("\n💱 Creating exchange rates...")
        
        # Current rate: 1 USD = 42,000 IRR (approximate)
        await session.execute(text("""
            INSERT INTO exchange_rates (currency_id, rate, effective_date, is_active)
            VALUES (:currency_id, 42000.0, :date, true)
        """), {"currency_id": currencies['IRR'], "date": datetime.now()})
        
        await session.commit()
        print("✅ Exchange rates created")
        
        # 3. Create Users
        print("\n👥 Creating users...")
        
        # Admin already exists, create others
        users_data = [
            ('pmo_user', 'pmo123', 'pmo'),
            ('pm1', 'pm123', 'pm'),
            ('pm2', 'pm123', 'pm'),
            ('procurement1', 'proc123', 'procurement'),
            ('finance1', 'finance123', 'finance'),
        ]
        
        for username, password, role in users_data:
            # Hash password using bcrypt
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed = pwd_context.hash(password)
            
            await session.execute(text("""
                INSERT INTO users (username, password_hash, role, is_active)
                VALUES (:username, :password_hash, :role, true)
                ON CONFLICT (username) DO NOTHING
            """), {"username": username, "password_hash": hashed, "role": role})
        
        await session.commit()
        print("✅ Users created")
        
        # Get user IDs
        result = await session.execute(text("SELECT id, username FROM users"))
        users = {row[1]: row[0] for row in result}
        
        # 4. Create Items Master (IT Equipment)
        print("\n📦 Creating items master catalog...")
        
        items_master = [
            # Dell Items
            ('Dell', 'Latitude 5540 Laptop', 'Latest Model', 
             '{"processor": "Intel Core i7-1365U", "ram": "16GB", "storage": "512GB SSD", "screen": "15.6 inch FHD"}', 
             'Laptops', 'piece'),
            ('Dell', 'OptiPlex 7010 Desktop', 'Tower', 
             '{"processor": "Intel Core i7-13700", "ram": "32GB", "storage": "1TB SSD"}', 
             'Desktops', 'piece'),
            ('Dell', 'PowerEdge R750 Server', 'Rack Server', 
             '{"processor": "Dual Intel Xeon", "ram": "128GB", "storage": "8TB", "raid": "RAID 10"}', 
             'Servers', 'piece'),
            ('Dell', 'UltraSharp U2723DE Monitor', '27 inch', 
             '{"size": "27 inch", "resolution": "2560x1440", "panel": "IPS", "features": "USB-C Hub"}', 
             'Monitors', 'piece'),
            
            # HP Items
            ('HP', 'EliteBook 840 G10', 'Business Laptop', 
             '{"processor": "Intel Core i7-1355U", "ram": "16GB", "storage": "512GB SSD", "screen": "14 inch"}', 
             'Laptops', 'piece'),
            ('HP', 'ProDesk 600 G9', 'Small Form Factor', 
             '{"processor": "Intel Core i7-13700", "ram": "32GB", "storage": "512GB SSD"}', 
             'Desktops', 'piece'),
            ('HP', 'ProLiant DL380 Gen11', 'Rack Server', 
             '{"processor": "Dual AMD EPYC", "ram": "256GB", "storage": "16TB", "raid": "RAID 6"}', 
             'Servers', 'piece'),
            
            # Lenovo Items
            ('Lenovo', 'ThinkPad X1 Carbon Gen 11', 'Ultrabook', 
             '{"processor": "Intel Core i7-1365U", "ram": "32GB", "storage": "1TB SSD", "screen": "14 inch", "weight": "1.12kg"}', 
             'Laptops', 'piece'),
            ('Lenovo', 'ThinkCentre M90a Pro', 'All-in-One', 
             '{"processor": "Intel Core i7-13700", "ram": "16GB", "storage": "512GB SSD", "screen": "23.8 inch"}', 
             'Desktops', 'piece'),
            
            # Network Equipment
            ('Cisco', 'Catalyst 9300 Switch', '48 Port', 
             '{"ports": "48x 1Gb", "uplink": "4x 10Gb SFP+", "poe": "PoE+", "stacking": "Yes"}', 
             'Networking', 'piece'),
            ('Cisco', 'ISR 4331 Router', 'Integrated Services', 
             '{"throughput": "300 Mbps", "ports": "3x GE", "vpn": "Yes", "firewall": "Yes"}', 
             'Networking', 'piece'),
            
            # Storage
            ('Synology', 'DS1823xs+ NAS', '8-Bay', 
             '{"bays": "8", "cpu": "AMD Ryzen V1780B", "ram": "32GB", "raid": "Multiple RAID"}', 
             'Storage', 'piece'),
            ('Western Digital', 'Gold Enterprise HDD', '18TB', 
             '{"capacity": "18TB", "rpm": "7200", "interface": "SATA", "mtbf": "2.5M hours"}', 
             'Storage', 'piece'),
            
            # Printers & Accessories
            ('HP', 'LaserJet Pro M479fdw', 'Color Laser MFP', 
             '{"type": "Laser", "color": "Yes", "speed": "28 ppm", "features": "Print/Scan/Copy/Fax"}', 
             'Printers', 'piece'),
            ('APC', 'Smart-UPS 1500VA', 'LCD 120V', 
             '{"capacity": "1500VA/1000W", "runtime": "Variable", "outlets": "8", "lcd": "Yes"}', 
             'Power', 'piece'),
        ]
        
        for company, item_name, model, specs, category, unit in items_master:
            await session.execute(text("""
                INSERT INTO items_master (company, item_name, model, specifications, category, unit, description)
                VALUES (:company, :item_name, :model, :specs::jsonb, :category, :unit, :description)
            """), {
                "company": company,
                "item_name": item_name,
                "model": model,
                "specs": specs,
                "category": category,
                "unit": unit,
                "description": f"{company} {item_name} - {model}"
            })
        
        await session.commit()
        print("✅ Items master catalog created")
        
        # Get items master IDs
        result = await session.execute(text("SELECT id, company, item_name FROM items_master"))
        items_master_dict = {f"{row[1]}-{row[2]}": row[0] for row in result}
        
        # 5. Create Projects
        print("\n🏢 Creating projects...")
        
        projects_data = [
            ('IT Infrastructure Upgrade 2025', 250000.00, 
             'Complete IT infrastructure upgrade including servers, networking, and workstations',
             '2025-01-01', '2025-12-31'),
            ('Office Equipment Procurement', 150000.00,
             'New office equipment for headquarters expansion',
             '2025-02-01', '2025-08-31'),
            ('Data Center Expansion', 500000.00,
             'Expansion of data center facilities with enterprise equipment',
             '2025-03-01', '2025-11-30'),
        ]
        
        project_ids = []
        for name, budget, desc, start, end in projects_data:
            result = await session.execute(text("""
                INSERT INTO projects (name, budget, description, start_date, end_date)
                VALUES (:name, :budget, :desc, :start, :end)
                RETURNING id
            """), {"name": name, "budget": budget, "desc": desc, "start": start, "end": end})
            project_ids.append(result.scalar())
        
        await session.commit()
        print(f"✅ Projects created: {project_ids}")
        
        # 6. Create Project Items
        print("\n📋 Creating project items...")
        
        # Project 1: IT Infrastructure Upgrade
        project1_items = [
            (items_master_dict.get('Dell-Latitude 5540 Laptop'), 'Dell-Latitude 5540 Laptop', 'Latitude 5540 Laptop', 25, 
             ['2025-04-15', '2025-05-15'], False, 'For software development team'),
            (items_master_dict.get('Dell-PowerEdge R750 Server'), 'Dell-PowerEdge R750 Server', 'PowerEdge R750 Server', 3, 
             ['2025-03-30', '2025-04-30'], False, 'Primary application servers'),
            (items_master_dict.get('Cisco-Catalyst 9300 Switch'), 'Cisco-Catalyst 9300 Switch', 'Catalyst 9300 Switch', 5, 
             ['2025-03-15', '2025-04-15'], False, 'Core network switches'),
            (items_master_dict.get('Synology-DS1823xs+ NAS'), 'Synology-DS1823xs+ NAS', 'DS1823xs+ NAS', 2, 
             ['2025-04-01'], False, 'Backup and file storage'),
            (items_master_dict.get('APC-Smart-UPS 1500VA'), 'APC-Smart-UPS 1500VA', 'Smart-UPS 1500VA', 10, 
             ['2025-03-20'], False, 'UPS for critical equipment'),
        ]
        
        # Project 2: Office Equipment
        project2_items = [
            (items_master_dict.get('HP-EliteBook 840 G10'), 'HP-EliteBook 840 G10', 'EliteBook 840 G10', 30, 
             ['2025-04-01', '2025-05-01'], False, 'For management team'),
            (items_master_dict.get('Dell-UltraSharp U2723DE Monitor'), 'Dell-UltraSharp U2723DE Monitor', 'UltraSharp U2723DE Monitor', 50, 
             ['2025-04-15'], False, 'Dual monitor setup for employees'),
            (items_master_dict.get('HP-LaserJet Pro M479fdw'), 'HP-LaserJet Pro M479fdw', 'LaserJet Pro M479fdw', 8, 
             ['2025-03-25'], False, 'Department printers'),
            (items_master_dict.get('Lenovo-ThinkCentre M90a Pro'), 'Lenovo-ThinkCentre M90a Pro', 'ThinkCentre M90a Pro', 15, 
             ['2025-04-20'], False, 'For reception and common areas'),
        ]
        
        # Project 3: Data Center Expansion
        project3_items = [
            (items_master_dict.get('HP-ProLiant DL380 Gen11'), 'HP-ProLiant DL380 Gen11', 'ProLiant DL380 Gen11', 8, 
             ['2025-06-01', '2025-07-01'], False, 'Enterprise database servers'),
            (items_master_dict.get('Dell-PowerEdge R750 Server'), 'Dell-PowerEdge R750 Server', 'PowerEdge R750 Server', 6, 
             ['2025-06-01'], False, 'Application servers'),
            (items_master_dict.get('Cisco-ISR 4331 Router'), 'Cisco-ISR 4331 Router', 'ISR 4331 Router', 4, 
             ['2025-05-15'], False, 'Data center routers'),
            (items_master_dict.get('Western Digital-Gold Enterprise HDD'), 'Western Digital-Gold Enterprise HDD', 'Gold Enterprise HDD', 50, 
             ['2025-05-20'], False, 'Storage expansion'),
        ]
        
        all_items = [
            (project_ids[0], project1_items),
            (project_ids[1], project2_items),
            (project_ids[2], project3_items),
        ]
        
        item_ids = []
        for project_id, items in all_items:
            for master_id, item_code, item_name, qty, delivery, external, desc in items:
                result = await session.execute(text("""
                    INSERT INTO project_items 
                    (project_id, master_item_id, item_code, item_name, quantity, 
                     delivery_options, external_purchase, description, status, 
                     is_finalized, finalized_by, finalized_at)
                    VALUES 
                    (:project_id, :master_id, :item_code, :item_name, :qty, 
                     :delivery::jsonb, :external, :desc, 'PENDING', 
                     true, :finalized_by, :finalized_at)
                    RETURNING id
                """), {
                    "project_id": project_id,
                    "master_id": master_id,
                    "item_code": item_code,
                    "item_name": item_name,
                    "qty": qty,
                    "delivery": str(delivery).replace("'", '"'),
                    "external": external,
                    "desc": desc,
                    "finalized_by": users.get('pmo_user'),
                    "finalized_at": datetime.now() - timedelta(days=random.randint(1, 10))
                })
                item_ids.append(result.scalar())
        
        await session.commit()
        print(f"✅ Project items created: {len(item_ids)} items")
        
        # 7. Create Procurement Options with USD and IRR pricing
        print("\n💰 Creating procurement options with USD and IRR pricing...")
        
        # Get all project items
        result = await session.execute(text("SELECT id, item_code, quantity FROM project_items WHERE is_finalized = true"))
        items = list(result)
        
        # Pricing data (mixed USD and IRR)
        pricing_templates = {
            'Dell-Latitude 5540 Laptop': [
                ('Dell Direct USA', 1200.00, 'USD', 15, 0.02),
                ('Local IT Distributor', 52000000.00, 'IRR', 20, 0.00),
                ('Import Specialist', 1150.00, 'USD', 25, 0.03),
            ],
            'Dell-PowerEdge R750 Server': [
                ('Dell Enterprise', 8500.00, 'USD', 30, 0.02),
                ('Server Solutions Iran', 370000000.00, 'IRR', 45, 0.00),
                ('Global IT Supplier', 8200.00, 'USD', 40, 0.03),
            ],
            'Cisco-Catalyst 9300 Switch': [
                ('Cisco Authorized', 12000.00, 'USD', 20, 0.02),
                ('Network Equipment Co', 520000000.00, 'IRR', 30, 0.00),
            ],
            'HP-EliteBook 840 G10': [
                ('HP Store', 1300.00, 'USD', 15, 0.02),
                ('Tehran Computer Market', 56000000.00, 'IRR', 10, 0.00),
                ('Corporate Supplier', 1250.00, 'USD', 20, 0.02),
            ],
            'Dell-UltraSharp U2723DE Monitor': [
                ('Dell Official', 450.00, 'USD', 10, 0.02),
                ('Monitor Supplier Iran', 19500000.00, 'IRR', 7, 0.00),
            ],
            'HP-ProLiant DL380 Gen11': [
                ('HP Enterprise', 15000.00, 'USD', 35, 0.02),
                ('Data Center Equipment', 650000000.00, 'IRR', 50, 0.00),
            ],
            'Synology-DS1823xs+ NAS': [
                ('Synology Direct', 3500.00, 'USD', 20, 0.02),
                ('Storage Solutions', 152000000.00, 'IRR', 25, 0.00),
            ],
            'Cisco-ISR 4331 Router': [
                ('Cisco Partner', 4500.00, 'USD', 25, 0.02),
                ('Network Pro Iran', 195000000.00, 'IRR', 30, 0.00),
            ],
            'Western Digital-Gold Enterprise HDD': [
                ('WD Authorized', 420.00, 'USD', 10, 0.02),
                ('Storage Depot', 18200000.00, 'IRR', 15, 0.00),
            ],
            'HP-LaserJet Pro M479fdw': [
                ('HP Direct', 650.00, 'USD', 10, 0.02),
                ('Office Equipment Co', 28000000.00, 'IRR', 7, 0.00),
            ],
            'APC-Smart-UPS 1500VA': [
                ('APC Authorized', 850.00, 'USD', 15, 0.02),
                ('Power Solutions Iran', 37000000.00, 'IRR', 20, 0.00),
            ],
            'Lenovo-ThinkCentre M90a Pro': [
                ('Lenovo Store', 1100.00, 'USD', 15, 0.02),
                ('Computer Center', 48000000.00, 'IRR', 10, 0.00),
            ],
        }
        
        for item_id, item_code, quantity in items:
            # Find matching pricing template
            pricing = None
            for key, value in pricing_templates.items():
                if key in item_code:
                    pricing = value
                    break
            
            if not pricing:
                continue
            
            for supplier, base_cost, currency_code, lead_time, discount_pct in pricing:
                # Get currency ID
                currency_id = currencies.get(currency_code)
                
                # Calculate shipping cost (5% of base cost)
                shipping_cost = base_cost * 0.05
                
                # Bundle discount
                bundle_threshold = max(5, int(quantity * 0.3))
                bundle_discount = random.choice([5.0, 7.5, 10.0])
                
                # Payment terms
                payment_terms = random.choice([
                    '{"type": "cash", "discount_percent": ' + str(discount_pct) + '}',
                    '{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 30, "percent": 30}, {"due_offset": 60, "percent": 40}]}'
                ])
                
                await session.execute(text("""
                    INSERT INTO procurement_options
                    (project_item_id, item_code, supplier_name, base_cost, currency_id,
                     shipping_cost, lomc_lead_time, discount_bundle_threshold, 
                     discount_bundle_percent, payment_terms, is_finalized)
                    VALUES
                    (:item_id, :item_code, :supplier, :base_cost, :currency_id,
                     :shipping, :lead_time, :bundle_threshold, :bundle_discount,
                     :payment_terms::jsonb, false)
                """), {
                    "item_id": item_id,
                    "item_code": item_code,
                    "supplier": supplier,
                    "base_cost": base_cost,
                    "currency_id": currency_id,
                    "shipping": shipping_cost,
                    "lead_time": lead_time,
                    "bundle_threshold": bundle_threshold,
                    "bundle_discount": bundle_discount,
                    "payment_terms": payment_terms
                })
        
        await session.commit()
        print("✅ Procurement options created with USD and IRR pricing")
        
        # 8. Summary
        print("\n📊 Data Summary:")
        result = await session.execute(text("SELECT COUNT(*) FROM currencies"))
        print(f"  - Currencies: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        print(f"  - Users: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM items_master"))
        print(f"  - Items Master: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM projects"))
        print(f"  - Projects: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM project_items"))
        print(f"  - Project Items: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM project_items WHERE is_finalized = true"))
        print(f"  - Finalized Items: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM procurement_options"))
        print(f"  - Procurement Options: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM procurement_options WHERE currency_id = :usd_id"), 
                                      {"usd_id": currencies['USD']})
        print(f"  - Options in USD: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM procurement_options WHERE currency_id = :irr_id"), 
                                      {"irr_id": currencies['IRR']})
        print(f"  - Options in IRR: {result.scalar()}")
    
    await engine.dispose()


async def main():
    """Main execution"""
    print("=" * 80)
    print("PDSS DATA RESET AND RESEED")
    print("=" * 80)
    print("\n⚠️  This will DELETE all operational data and create fresh test data!")
    print("    - Users (except admin)")
    print("    - Projects")
    print("    - Items")
    print("    - Procurement options")
    print("    - Currencies")
    print()
    
    confirm = input("Type 'YES' to confirm: ")
    if confirm != 'YES':
        print("❌ Aborted")
        return
    
    try:
        # Step 1: Reset
        await reset_database()
        
        # Step 2: Reseed
        await seed_new_data()
        
        print("\n" + "=" * 80)
        print("✅ DATABASE RESET AND RESEEDED SUCCESSFULLY!")
        print("=" * 80)
        print("\n📝 Login Credentials:")
        print("  - Admin: admin / admin123")
        print("  - PMO: pmo_user / pmo123")
        print("  - PM: pm1 / pm123")
        print("  - Procurement: procurement1 / proc123")
        print("  - Finance: finance1 / finance123")
        print("\n💰 Currency Configuration:")
        print("  - Base Currency: USD")
        print("  - Exchange Rate: 1 USD = 42,000 IRR")
        print("\n📦 Data Created:")
        print("  - 3 Projects with realistic IT equipment")
        print("  - 13 Project items (all finalized)")
        print("  - ~30+ Procurement options with mixed USD/IRR pricing")
        print("\n🚀 Ready to use! Restart the application:")
        print("  docker-compose restart backend")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

