"""
Unit tests for Phase 3 validators
"""

import pytest
from app.validators.package_validators import (
    validate_package_or_legacy_reference,
    validate_supplier_reference,
    resolve_package_from_project_item
)
from fastapi import HTTPException


class TestPackageOrLegacyReference:
    """Tests for validate_package_or_legacy_reference"""
    
    def test_package_id_only(self):
        """Test with package_id only"""
        result = validate_package_or_legacy_reference(
            package_id=1,
            project_item_id=None,
            item_code=None
        )
        assert result["reference_type"] == "package"
        assert result["package_id"] == 1
    
    def test_project_item_id_only(self):
        """Test with project_item_id only"""
        result = validate_package_or_legacy_reference(
            package_id=None,
            project_item_id=1,
            item_code=None
        )
        assert result["reference_type"] == "project_item"
        assert result["project_item_id"] == 1
    
    def test_item_code_only(self):
        """Test with item_code only"""
        result = validate_package_or_legacy_reference(
            package_id=None,
            project_item_id=None,
            item_code="TEST-001"
        )
        assert result["reference_type"] == "item_code"
        assert result["item_code"] == "TEST-001"
    
    def test_no_reference(self):
        """Test with no reference (should raise error)"""
        with pytest.raises(HTTPException) as exc_info:
            validate_package_or_legacy_reference(
                package_id=None,
                project_item_id=None,
                item_code=None
            )
        assert exc_info.value.status_code == 400
        assert "at least one of" in exc_info.value.detail.lower()
    
    def test_package_preferred(self):
        """Test that package_id is preferred when multiple are provided"""
        result = validate_package_or_legacy_reference(
            package_id=1,
            project_item_id=2,
            item_code="TEST-001"
        )
        assert result["reference_type"] == "package"
        assert result["package_id"] == 1


class TestSupplierReference:
    """Tests for validate_supplier_reference"""
    
    @pytest.mark.asyncio
    async def test_supplier_id_only(self, db_session, test_supplier):
        """Test with supplier_id only"""
        result = await validate_supplier_reference(
            db_session,
            supplier_id=test_supplier.id,
            supplier_name=None
        )
        assert result["supplier_id"] == test_supplier.id
        assert result["supplier_name"] == test_supplier.company_name
    
    @pytest.mark.asyncio
    async def test_supplier_name_only(self, db_session, test_supplier):
        """Test with supplier_name only (not enforced)"""
        result = await validate_supplier_reference(
            db_session,
            supplier_id=None,
            supplier_name=test_supplier.company_name
        )
        assert result["supplier_name"] == test_supplier.company_name
    
    @pytest.mark.asyncio
    async def test_no_supplier_reference(self, db_session):
        """Test with no supplier reference (should raise error)"""
        with pytest.raises(HTTPException) as exc_info:
            await validate_supplier_reference(
                db_session,
                supplier_id=None,
                supplier_name=None
            )
        assert exc_info.value.status_code == 400
        assert "supplier_id or supplier_name" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_unmatched_supplier_name(self, db_session):
        """Test with unmatched supplier_name (should log)"""
        result = await validate_supplier_reference(
            db_session,
            supplier_id=None,
            supplier_name="Non-existent Supplier"
        )
        assert result["supplier_id"] is None
        assert result["supplier_name"] == "Non-existent Supplier"


class TestResolvePackage:
    """Tests for resolve_package_from_project_item"""
    
    @pytest.mark.asyncio
    async def test_resolve_existing_package(
        self, db_session, test_project_item, test_package
    ):
        """Test resolving existing package"""
        # Enable package procurement flag for this test
        from app.config import settings
        original_value = settings.enable_package_procurement
        settings.enable_package_procurement = True
        
        try:
            result = await resolve_package_from_project_item(
                db_session,
                test_project_item.id,
                create_if_missing=False
            )
            assert result == test_package.id
        finally:
            settings.enable_package_procurement = original_value
    
    @pytest.mark.asyncio
    async def test_resolve_missing_package_no_create(
        self, db_session, test_project_item
    ):
        """Test resolving missing package without create"""
        # Enable package procurement flag for this test
        from app.config import settings
        original_value = settings.enable_package_procurement
        settings.enable_package_procurement = True
        
        try:
            # Delete package if exists
            from sqlalchemy import select
            from app.models import ProcurementPackage
            result = await db_session.execute(
                select(ProcurementPackage).where(
                    ProcurementPackage.project_item_id == test_project_item.id
                )
            )
            packages = result.scalars().all()
            for pkg in packages:
                await db_session.delete(pkg)
            await db_session.commit()
            
            result = await resolve_package_from_project_item(
                db_session,
                test_project_item.id,
                create_if_missing=False
            )
            assert result is None
        finally:
            settings.enable_package_procurement = original_value
    
    @pytest.mark.asyncio
    async def test_resolve_missing_package_with_create(
        self, db_session, test_project_item
    ):
        """Test resolving missing package with create"""
        # Enable package procurement flag for this test
        from app.config import settings
        original_value = settings.enable_package_procurement
        settings.enable_package_procurement = True
        
        try:
            # Delete package if exists
            from sqlalchemy import select
            from app.models import ProcurementPackage
            result = await db_session.execute(
                select(ProcurementPackage).where(
                    ProcurementPackage.project_item_id == test_project_item.id
                )
            )
            packages = result.scalars().all()
            for pkg in packages:
                await db_session.delete(pkg)
            await db_session.commit()
            
            result = await resolve_package_from_project_item(
                db_session,
                test_project_item.id,
                create_if_missing=True
            )
            assert result is not None
            
            # Verify package was created
            result = await db_session.execute(
                select(ProcurementPackage).where(
                    ProcurementPackage.id == result
                )
            )
            package = result.scalar_one_or_none()
            assert package is not None
            assert package.package_type == "FULL"
        finally:
            settings.enable_package_procurement = original_value

