"""
Integration tests for Phase 3 CRUD operations
"""

import pytest
from decimal import Decimal
from datetime import date
from app.crud import (
    create_procurement_option,
    update_procurement_option,
    create_delivery_option
)
from app.schemas import (
    ProcurementOptionCreate,
    ProcurementOptionUpdate,
    DeliveryOptionCreate
)
from app.config import settings


class TestProcurementOptionCRUD:
    """Tests for procurement option CRUD with Phase 3 dual-mode"""
    
    @pytest.mark.asyncio
    async def test_create_with_package_id(
        self, db_session, test_project_item, test_supplier, test_package, test_currency
    ):
        """Test creating procurement option with package_id"""
        option_data = ProcurementOptionCreate(
            package_id=test_package.id,
            item_code=test_project_item.item_code,
            supplier_name=test_supplier.company_name,  # Required legacy field
            supplier_id=test_supplier.id,
            base_cost=Decimal("1000.00"),  # Required legacy field
            currency_id=test_currency.id,  # Required legacy field
            payment_terms={"type": "cash"}
        )
        
        option = await create_procurement_option(db_session, option_data)
        
        assert option.package_id == test_package.id
        assert option.supplier_id == test_supplier.id
    
    @pytest.mark.asyncio
    async def test_create_with_project_item_id(
        self, db_session, test_project_item, test_supplier, test_currency, test_package
    ):
        """Test creating procurement option with project_item_id (legacy)"""
        option_data = ProcurementOptionCreate(
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            supplier_name=test_supplier.company_name,  # Required legacy field
            supplier_id=test_supplier.id,
            base_cost=Decimal("1000.00"),  # Required legacy field
            currency_id=test_currency.id,  # Required legacy field
            payment_terms={"type": "cash"}
        )
        
        option = await create_procurement_option(db_session, option_data)
        
        assert option.project_item_id == test_project_item.id
        # Package_id may be resolved if flag enabled
        if settings.enable_package_procurement:
            assert option.package_id == test_package.id
    
    @pytest.mark.asyncio
    async def test_create_with_item_code_only(
        self, db_session, test_supplier, test_currency
    ):
        """Test creating procurement option with item_code only (legacy)"""
        option_data = ProcurementOptionCreate(
            item_code="TEST-LEGACY-001",
            supplier_name=test_supplier.company_name,  # Required legacy field
            supplier_id=test_supplier.id,
            base_cost=Decimal("1000.00"),  # Required legacy field
            currency_id=test_currency.id,  # Required legacy field
            payment_terms={"type": "cash"}
        )
        
        option = await create_procurement_option(db_session, option_data)
        
        assert option.item_code == "TEST-LEGACY-001"
        assert option.supplier_id == test_supplier.id
    
    @pytest.mark.asyncio
    async def test_create_no_reference(self, db_session, test_supplier, test_currency):
        """Empty item_code is rejected by schema validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProcurementOptionCreate(
                item_code="",  # Empty item_code
                supplier_name=test_supplier.company_name,  # Required legacy field
                supplier_id=test_supplier.id,
                base_cost=Decimal("1000.00"),  # Required legacy field
                currency_id=test_currency.id,  # Required legacy field
                payment_terms={"type": "cash"}
            )
    
    @pytest.mark.asyncio
    async def test_update_package_id(
        self, db_session, test_project_item, test_supplier, test_package, test_currency
    ):
        """Test updating procurement option to use package_id"""
        # Create with project_item_id
        option_data = ProcurementOptionCreate(
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            supplier_name=test_supplier.company_name,  # Required legacy field
            supplier_id=test_supplier.id,
            base_cost=Decimal("1000.00"),  # Required legacy field
            currency_id=test_currency.id,  # Required legacy field
            payment_terms={"type": "cash"}
        )
        option = await create_procurement_option(db_session, option_data)
        
        # Update to use package_id
        update_data = ProcurementOptionUpdate(
            package_id=test_package.id
        )
        
        updated = await update_procurement_option(
            db_session, option.id, update_data
        )
        
        assert updated.package_id == test_package.id


class TestDeliveryOptionCRUD:
    """Tests for delivery option CRUD with Phase 3 dual-mode"""
    
    @pytest.mark.asyncio
    async def test_create_with_package_id(
        self, db_session, test_project_item, test_package
    ):
        """Test creating delivery option with package_id"""
        option_data = DeliveryOptionCreate(
            package_id=test_package.id,
            project_item_id=test_project_item.id,
            delivery_date=date.today(),
            invoice_amount_per_unit=Decimal("1200.00"),
            invoice_timing_type="RELATIVE",
            invoice_days_after_delivery=30
        )
        
        option = await create_delivery_option(db_session, option_data)
        
        assert option.package_id == test_package.id
        assert option.project_item_id == test_project_item.id
    
    @pytest.mark.asyncio
    async def test_create_with_project_item_id_only(
        self, db_session, test_project_item, test_package
    ):
        """Test creating delivery option with project_item_id only (legacy)"""
        option_data = DeliveryOptionCreate(
            project_item_id=test_project_item.id,
            delivery_date=date.today(),
            invoice_amount_per_unit=Decimal("1200.00"),
            invoice_timing_type="RELATIVE",
            invoice_days_after_delivery=30
        )
        
        option = await create_delivery_option(db_session, option_data)
        
        assert option.project_item_id == test_project_item.id
        # Package_id may be resolved if flag enabled
        if settings.enable_package_procurement:
            assert option.package_id == test_package.id
    
    @pytest.mark.asyncio
    async def test_create_no_reference(self, db_session):
        """Test creating delivery option with no reference (should fail)"""
        from fastapi import HTTPException
        option_data = DeliveryOptionCreate(
            package_id=None,
            project_item_id=None,
            delivery_date=date.today(),
            invoice_amount_per_unit=Decimal("1200.00"),
            invoice_timing_type="RELATIVE",
            invoice_days_after_delivery=30
        )
        
        # This should raise ValueError (HTTPException wrapped by crud.py)
        with pytest.raises((HTTPException, ValueError)):
            await create_delivery_option(db_session, option_data)

