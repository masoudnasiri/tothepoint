"""
Auto Reset and Reseed Database - No Confirmation Required
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timedelta
import random
import os

# Database connection from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/procurement_dss")

async def reset_and_reseed():
    """Reset and reseed database"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("🗑️  Deleting operational data...")
        
        # Delete in correct order
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
        
        print("\n🌱 Seeding new data...")
        
        # 1. Currencies
        print("💰 Creating currencies...")
        await session.execute(text("""
            INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
            VALUES ('USD', 'US Dollar', '$', true, true, 2)
            ON CONFLICT (code) DO NOTHING
        """))
        await session.execute(text("""
            INSERT INTO currencies (code, name, symbol, is_base_currency, is_active, decimal_places)
            VALUES ('IRR', 'Iranian Rial', '﷼', false, true, 0)
            ON CONFLICT (code) DO NOTHING
        """))
        await session.commit()
        
        result = await session.execute(text("SELECT id, code FROM currencies"))
        currencies = {row[1]: row[0] for row in result}
        print(f"✅ Currencies: {currencies}")
        
        # 2. Exchange Rates
        print("💱 Creating exchange rates...")
        await session.execute(text("""
            INSERT INTO exchange_rates (currency_id, rate, effective_date, is_active)
            VALUES (:currency_id, 42000.0, :date, true)
        """), {"currency_id": currencies['IRR'], "date": datetime.now()})
        await session.commit()
        
        # 3. Users
        print("👥 Creating users...")
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        users_data = [
            ('pmo_user', 'pmo123', 'pmo'),
            ('pm1', 'pm123', 'pm'),
            ('procurement1', 'proc123', 'procurement'),
            ('finance1', 'finance123', 'finance'),
        ]
        
        for username, password, role in users_data:
            hashed = pwd_context.hash(password)
            await session.execute(text("""
                INSERT INTO users (username, password_hash, role, is_active)
                VALUES (:username, :password_hash, :role, true)
                ON CONFLICT (username) DO NOTHING
            """), {"username": username, "password_hash": hashed, "role": role})
        await session.commit()
        
        result = await session.execute(text("SELECT id, username FROM users"))
        users = {row[1]: row[0] for row in result}
        
        # 4. Items Master
        print("📦 Creating items master...")
        items_data = [
            ('Dell', 'Latitude 5540 Laptop', 'Latest Model', 'Laptops'),
            ('Dell', 'PowerEdge R750 Server', 'Rack Server', 'Servers'),
            ('Cisco', 'Catalyst 9300 Switch', '48 Port', 'Networking'),
            ('HP', 'EliteBook 840 G10', 'Business Laptop', 'Laptops'),
            ('HP', 'ProLiant DL380 Gen11', 'Rack Server', 'Servers'),
        ]
        
        for company, item_name, model, category in items_data:
            await session.execute(text("""
                INSERT INTO items_master (company, item_name, model, category, unit, description)
                VALUES (:company, :item_name, :model, :category, 'piece', :desc)
            """), {
                "company": company,
                "item_name": item_name,
                "model": model,
                "category": category,
                "desc": f"{company} {item_name}"
            })
        await session.commit()
        
        result = await session.execute(text("SELECT id, company, item_name FROM items_master"))
        items_master = {f"{row[1]}-{row[2]}": row[0] for row in result}
        
        # 5. Projects
        print("🏢 Creating projects...")
        projects_data = [
            ('IT Infrastructure Upgrade 2025', 250000.00, 'Complete IT upgrade', '2025-01-01', '2025-12-31'),
            ('Office Equipment Procurement', 150000.00, 'New office equipment', '2025-02-01', '2025-08-31'),
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
        
        # 6. Project Items (Finalized)
        print("📋 Creating project items...")
        project_items = [
            (project_ids[0], items_master.get('Dell-Latitude 5540 Laptop'), 'Dell-Latitude 5540 Laptop', 'Latitude 5540 Laptop', 25, ['2025-04-15'], 'Development team'),
            (project_ids[0], items_master.get('Dell-PowerEdge R750 Server'), 'Dell-PowerEdge R750 Server', 'PowerEdge R750 Server', 3, ['2025-03-30'], 'Application servers'),
            (project_ids[0], items_master.get('Cisco-Catalyst 9300 Switch'), 'Cisco-Catalyst 9300 Switch', 'Catalyst 9300 Switch', 5, ['2025-03-15'], 'Core network'),
            (project_ids[1], items_master.get('HP-EliteBook 840 G10'), 'HP-EliteBook 840 G10', 'EliteBook 840 G10', 30, ['2025-04-01'], 'Management team'),
            (project_ids[1], items_master.get('HP-ProLiant DL380 Gen11'), 'HP-ProLiant DL380 Gen11', 'ProLiant DL380 Gen11', 8, ['2025-06-01'], 'Database servers'),
        ]
        
        item_ids = []
        for proj_id, master_id, item_code, item_name, qty, delivery, desc in project_items:
            result = await session.execute(text("""
                INSERT INTO project_items 
                (project_id, master_item_id, item_code, item_name, quantity, delivery_options, 
                 description, status, is_finalized, finalized_by, finalized_at, external_purchase)
                VALUES 
                (:proj_id, :master_id, :item_code, :item_name, :qty, :delivery::jsonb,
                 :desc, 'PENDING', true, :finalized_by, :finalized_at, false)
                RETURNING id
            """), {
                "proj_id": proj_id,
                "master_id": master_id,
                "item_code": item_code,
                "item_name": item_name,
                "qty": qty,
                "delivery": str(delivery).replace("'", '"'),
                "desc": desc,
                "finalized_by": users.get('pmo_user'),
                "finalized_at": datetime.now() - timedelta(days=5)
            })
            item_ids.append(result.scalar())
        await session.commit()
        
        # 7. Procurement Options (Mixed USD/IRR)
        print("💰 Creating procurement options...")
        
        # Get project items
        result = await session.execute(text("SELECT id, item_code FROM project_items WHERE is_finalized = true"))
        items = list(result)
        
        pricing = {
            'Dell-Latitude 5540 Laptop': [
                ('Dell Direct USA', 1200.00, 'USD', 15),
                ('Local IT Distributor', 52000000.00, 'IRR', 20),
            ],
            'Dell-PowerEdge R750 Server': [
                ('Dell Enterprise', 8500.00, 'USD', 30),
                ('Server Solutions Iran', 370000000.00, 'IRR', 45),
            ],
            'Cisco-Catalyst 9300 Switch': [
                ('Cisco Authorized', 12000.00, 'USD', 20),
                ('Network Equipment Co', 520000000.00, 'IRR', 30),
            ],
            'HP-EliteBook 840 G10': [
                ('HP Store', 1300.00, 'USD', 15),
                ('Tehran Computer Market', 56000000.00, 'IRR', 10),
            ],
            'HP-ProLiant DL380 Gen11': [
                ('HP Enterprise', 15000.00, 'USD', 35),
                ('Data Center Equipment', 650000000.00, 'IRR', 50),
            ],
        }
        
        for item_id, item_code in items:
            prices = None
            for key, val in pricing.items():
                if key in item_code:
                    prices = val
                    break
            
            if not prices:
                continue
                
            for supplier, cost, curr, lead_time in prices:
                await session.execute(text("""
                    INSERT INTO procurement_options
                    (project_item_id, item_code, supplier_name, base_cost, currency_id,
                     shipping_cost, lomc_lead_time, payment_terms, is_finalized)
                    VALUES
                    (:item_id, :item_code, :supplier, :cost, :curr_id, :shipping, :lead_time,
                     '{"type": "cash", "discount_percent": 0.02}'::jsonb, false)
                """), {
                    "item_id": item_id,
                    "item_code": item_code,
                    "supplier": supplier,
                    "cost": cost,
                    "curr_id": currencies[curr],
                    "shipping": cost * 0.05,
                    "lead_time": lead_time
                })
        await session.commit()
        
        # Summary
        print("\n📊 Data Summary:")
        result = await session.execute(text("SELECT COUNT(*) FROM project_items WHERE is_finalized = true"))
        print(f"  ✅ Finalized Items: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM procurement_options"))
        print(f"  ✅ Procurement Options: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM procurement_options WHERE currency_id = :usd"), 
                                      {"usd": currencies['USD']})
        print(f"  ✅ Options in USD: {result.scalar()}")
        
        result = await session.execute(text("SELECT COUNT(*) FROM procurement_options WHERE currency_id = :irr"), 
                                      {"irr": currencies['IRR']})
        print(f"  ✅ Options in IRR: {result.scalar()}")
    
    await engine.dispose()


async def main():
    print("=" * 80)
    print("PDSS AUTO DATA RESET AND RESEED")
    print("=" * 80)
    print("✅ Running automatically without confirmation...")
    print()
    
    try:
        await reset_and_reseed()
        
        print("\n" + "=" * 80)
        print("✅ SUCCESS! Database reset and reseeded")
        print("=" * 80)
        print("\n📝 Credentials:")
        print("  - Admin: admin / admin123")
        print("  - PMO: pmo_user / pmo123")
        print("  - PM: pm1 / pm123")
        print("  - Procurement: procurement1 / proc123")
        print("  - Finance: finance1 / finance123")
        print("\n💰 Currencies: USD (base) and IRR (1 USD = 42,000 IRR)")
        print("\n✅ Ready! Refresh your browser to see the new data.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())

