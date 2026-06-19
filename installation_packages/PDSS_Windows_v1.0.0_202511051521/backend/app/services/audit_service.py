"""
Audit and telemetry service for Phase 3 feature flag usage and migration tracking.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import json

from app.config import settings

logger = logging.getLogger(__name__)


async def log_feature_flag_event(
    db: AsyncSession,
    flag_name: str,
    flag_value: bool,
    context: str = "",
    user_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log feature flag evaluation to migration_audit_log table.
    
    Args:
        db: Database session
        flag_name: Name of feature flag (e.g., "ENABLE_PACKAGE_PROCUREMENT")
        flag_value: Flag value (True/False)
        context: Additional context (e.g., endpoint name, operation)
        user_id: User ID if available
        metadata: Additional metadata as dict
    """
    try:
        metadata_dict = {
            "flag_name": flag_name,
            "flag_value": flag_value,
            "context": context,
            "user_id": user_id,
            **(metadata or {})
        }
        # Use CURRENT_TIMESTAMP for SQLite compatibility, and handle jsonb vs TEXT
        try:
            dialect = db.bind.dialect.name if hasattr(db, 'bind') and db.bind else None
        except:
            dialect = None
        if dialect == 'sqlite':
            await db.execute(
                text("""
                    INSERT INTO migration_audit_log (
                        migration_step,
                        records_processed,
                        records_succeeded,
                        metadata,
                        created_at
                    ) VALUES (
                        :step,
                        1,
                        1,
                        :metadata,
                        CURRENT_TIMESTAMP
                    )
                """),
                {
                    "step": f"phase3_feature_flag_{flag_name.lower()}",
                    "metadata": json.dumps(metadata_dict)
                }
            )
        else:
            await db.execute(
                text("""
                    INSERT INTO migration_audit_log (
                        migration_step,
                        records_processed,
                        records_succeeded,
                        metadata,
                        created_at
                    ) VALUES (
                        :step,
                        1,
                        1,
                        CAST(:metadata AS jsonb),
                        NOW()
                    )
                """),
                {
                    "step": f"phase3_feature_flag_{flag_name.lower()}",
                    "metadata": json.dumps(metadata_dict)
                }
            )
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to log feature flag event: {e}")
        await db.rollback()


async def log_phase3_operation(
    db: AsyncSession,
    operation: str,
    record_type: str,
    record_id: Optional[int] = None,
    used_package_id: bool = False,
    used_legacy_reference: bool = False,
    user_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log Phase 3 operation (create/update/delete) with dual-mode tracking.
    
    Args:
        db: Database session
        operation: Operation type (create, update, delete, read)
        record_type: Type of record (procurement_option, delivery_option, finalized_decision)
        record_id: Record ID if available
        used_package_id: Whether package_id was used
        used_legacy_reference: Whether legacy reference (project_item_id/item_code) was used
        user_id: User ID if available
        metadata: Additional metadata
    """
    try:
        metadata_dict = {
            "operation": operation,
            "record_type": record_type,
            "record_id": record_id,
            "used_package_id": used_package_id,
            "used_legacy_reference": used_legacy_reference,
            "user_id": user_id,
            "feature_flags": {
                "enable_package_procurement": settings.enable_package_procurement,
                "legacy_project_item_fallback": settings.legacy_project_item_fallback,
                "supplier_normalization_enforced": settings.supplier_normalization_enforced
            },
            **(metadata or {})
        }
        # Use CURRENT_TIMESTAMP for SQLite compatibility, and handle jsonb vs TEXT
        try:
            dialect = db.bind.dialect.name if hasattr(db, 'bind') and db.bind else None
        except:
            dialect = None
        if dialect == 'sqlite':
            await db.execute(
                text("""
                    INSERT INTO migration_audit_log (
                        migration_step,
                        records_processed,
                        records_succeeded,
                        metadata,
                        created_at
                    ) VALUES (
                        :step,
                        1,
                        1,
                        :metadata,
                        CURRENT_TIMESTAMP
                    )
                """),
                {
                    "step": f"phase3_operation_{operation}",
                    "metadata": json.dumps(metadata_dict)
                }
            )
        else:
            await db.execute(
                text("""
                    INSERT INTO migration_audit_log (
                        migration_step,
                        records_processed,
                        records_succeeded,
                        metadata,
                        created_at
                    ) VALUES (
                        :step,
                        1,
                        1,
                        CAST(:metadata AS jsonb),
                        NOW()
                    )
                """),
                {
                    "step": f"phase3_operation_{operation}",
                    "metadata": json.dumps(metadata_dict)
                }
            )
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to log Phase 3 operation: {e}")
        await db.rollback()
