"""
Pytest configuration and fixtures for Phase 3 tests
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

from app.database import Base, get_db
from app.config import Settings
# Import all models to ensure they're registered with Base
from app.models import (
    User, Project, ProjectItem, Supplier, ProcurementPackage, Currency,
    ProcurementOption, DeliveryOption, FinalizedDecision
)
# Import invoice/payment models to ensure they're registered
import app.models_invoice_payment
from decimal import Decimal
from datetime import date


# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import String
    import sqlalchemy.dialects.sqlite
    
    # Map UUID to String for SQLite compatibility
    def visit_UUID(self, type_, **kw):
        return "TEXT"
    
    SQLiteTypeCompiler.visit_UUID = visit_UUID
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Phase 3 audit service writes to this SQL migration table directly.
        # Create it for SQLite tests to avoid rollback side effects in CRUD paths.
        await conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS migration_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_step TEXT NOT NULL,
                    records_processed INTEGER DEFAULT 0,
                    records_succeeded INTEGER DEFAULT 0,
                    records_failed INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        username="test_user",
        password_hash="hashed_password",
        role="PM"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession) -> Project:
    """Create a test project"""
    project = Project(
        project_code="TEST-PROJ-001",
        name="Test Project"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_project_item(db_session: AsyncSession, test_project: Project) -> ProjectItem:
    """Create a test project item"""
    item = ProjectItem(
        project_id=test_project.id,
        item_code="TEST-001",
        item_name="Test Item",
        quantity=1,
        delivery_options=[],
        status="PENDING"
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest_asyncio.fixture
async def test_supplier(db_session: AsyncSession) -> Supplier:
    """Create a test supplier"""
    supplier = Supplier(
        supplier_id="SUP-TEST-001",
        company_name="Test Supplier",
        status="ACTIVE"
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


@pytest_asyncio.fixture
async def test_package(
    db_session: AsyncSession, 
    test_project_item: ProjectItem
) -> ProcurementPackage:
    """Create a test procurement package"""
    package = ProcurementPackage(
        project_item_id=test_project_item.id,
        package_name="FULL Package for TEST-001",
        package_type="FULL",
        is_active=True
    )
    db_session.add(package)
    await db_session.commit()
    await db_session.refresh(package)
    return package


@pytest_asyncio.fixture
async def test_currency(db_session: AsyncSession) -> Currency:
    """Create a test currency for procurement option tests."""
    currency = Currency(
        code="USD",
        name="US Dollar",
        symbol="$",
        is_base_currency=True,
        is_active=True,
        decimal_places=2
    )
    db_session.add(currency)
    await db_session.commit()
    await db_session.refresh(currency)
    return currency


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    return Settings(
        enable_package_procurement=False,
        legacy_project_item_fallback=True,
        supplier_normalization_enforced=False,
        enable_package_based_optimization=False,
        require_package_id_for_new_options=False
    )

