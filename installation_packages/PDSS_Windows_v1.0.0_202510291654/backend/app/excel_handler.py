"""
Excel import/export functionality for bulk data operations
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from io import BytesIO
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import (
    create_project_item, create_procurement_option, create_budget_data,
    get_project_items, get_procurement_options, get_all_budget_data
)
from app.schemas import ExcelImportResponse
import logging

logger = logging.getLogger(__name__)


class ExcelHandler:
    """Handle Excel import/export operations"""
    
    @staticmethod
    def create_project_items_template() -> bytes:
        """Create Excel template for project items import"""
        template_data = {
            'project_id': [1, 2],
            'item_code': ['ITEM001', 'ITEM002'],
            'item_name': ['Sample Item 1', 'Sample Item 2'],
            'quantity': [10, 5],
            'delivery_options': ['2025-01-15,2025-02-15', '2025-03-01'],
            'description': ['Structural steel beam, Grade A36', 'Electrical cable, 50m'],
            'external_purchase': [True, False]
        }
        
        df = pd.DataFrame(template_data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Project Items', index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                'Field': ['project_id', 'item_code', 'item_name', 'quantity', 'delivery_options', 'description', 'external_purchase'],
                'Description': [
                    'Project ID (integer)',
                    'Unique item code (string)',
                    'Item name/title',
                    'Required quantity (integer > 0)',
                    'Delivery dates, comma-separated (e.g., "2025-01-15,2025-02-15")',
                    'Item description, specifications, notes (optional)',
                    'Whether external purchase (True/False)'
                ],
                'Example': ['1', 'ITEM001', 'Sample Item', '10', '2025-01-15,2025-02-15', 'Grade A36 steel', 'True']
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def create_procurement_options_template() -> bytes:
        """Create Excel template for procurement options import"""
        template_data = {
            'item_code': ['ITEM001', 'ITEM001', 'ITEM002'],
            'supplier_name': ['Supplier A', 'Supplier B', 'Supplier A'],
            'base_cost': [100.00, 95.00, 150.00],
            'lomc_lead_time': [1, 2, 1],
            'discount_bundle_threshold': [50, 100, ''],
            'discount_bundle_percent': [5.0, 10.0, ''],
            'payment_type': ['cash', 'installments', 'cash'],
            'payment_discount_percent': [5.0, '', ''],
            'installment_schedule': ['', '40,30,30', '']
        }
        
        df = pd.DataFrame(template_data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Procurement Options', index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                'Field': [
                    'item_code', 'supplier_name', 'base_cost', 'lomc_lead_time',
                    'discount_bundle_threshold', 'discount_bundle_percent',
                    'payment_type', 'payment_discount_percent', 'installment_schedule'
                ],
                'Description': [
                    'Item code (must exist)',
                    'Supplier name',
                    'Base cost per unit',
                    'Lead time in periods',
                    'Minimum quantity for bundle discount',
                    'Bundle discount percentage',
                    'Payment type: "cash" or "installments"',
                    'Cash discount percentage (for cash payments)',
                    'Installment schedule as comma-separated percentages (e.g., "40,30,30")'
                ],
                'Example': ['ITEM001', 'Supplier A', '100.00', '1', '50', '5.0', 'cash', '5.0', '']
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def create_budget_template() -> bytes:
        """Create Excel template for budget data import"""
        template_data = {
            'budget_date': ['2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01'],
            'available_budget': [100000.00, 150000.00, 120000.00, 180000.00, 200000.00, 160000.00]
        }
        
        df = pd.DataFrame(template_data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Budget Data', index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                'Field': ['budget_date', 'available_budget'],
                'Description': [
                    'Time slot number (integer >= 1)',
                    'Available budget for this time slot'
                ],
                'Example': ['1', '100000.00']
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    async def import_project_items(db: AsyncSession, file_content: bytes) -> ExcelImportResponse:
        """Import project items from Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(BytesIO(file_content), sheet_name='Project Items')
            
            # Validate required columns
            required_columns = ['project_id', 'item_code', 'quantity', 'delivery_options']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return ExcelImportResponse(
                    success=False,
                    imported_count=0,
                    errors=[f"Missing required columns: {', '.join(missing_columns)}"],
                    message="Import failed due to missing columns"
                )
            
            # Process each row
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Parse delivery_options (comma-separated dates)
                    delivery_options_str = str(row['delivery_options'])
                    if pd.isna(row['delivery_options']) or delivery_options_str == '':
                        delivery_options = [pd.Timestamp.now().strftime('%Y-%m-%d')]
                    else:
                        delivery_options = [date.strip() for date in delivery_options_str.split(',')]
                    
                    # Parse optional fields
                    external_purchase = bool(row.get('external_purchase', False))
                    item_name = str(row['item_name']) if 'item_name' in row and pd.notna(row['item_name']) else None
                    description = str(row['description']) if 'description' in row and pd.notna(row['description']) else None
                    
                    item_data = {
                        'project_id': int(row['project_id']),
                        'item_code': str(row['item_code']),
                        'item_name': item_name,
                        'quantity': int(row['quantity']),
                        'delivery_options': delivery_options,
                        'description': description,
                        'external_purchase': external_purchase
                    }
                    
                    await create_project_item(db, item_data)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    logger.error(f"Error importing project item row {index + 2}: {str(e)}")
            
            return ExcelImportResponse(
                success=len(errors) == 0,
                imported_count=imported_count,
                errors=errors,
                message=f"Successfully imported {imported_count} project items"
            )
            
        except Exception as e:
            logger.error(f"Error importing project items: {str(e)}")
            return ExcelImportResponse(
                success=False,
                imported_count=0,
                errors=[str(e)],
                message="Import failed due to file processing error"
            )
    
    @staticmethod
    async def import_procurement_options(db: AsyncSession, file_content: bytes) -> ExcelImportResponse:
        """Import procurement options from Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(BytesIO(file_content), sheet_name='Procurement Options')
            
            # Validate required columns
            required_columns = ['item_code', 'supplier_name', 'base_cost']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return ExcelImportResponse(
                    success=False,
                    imported_count=0,
                    errors=[f"Missing required columns: {', '.join(missing_columns)}"],
                    message="Import failed due to missing columns"
                )
            
            # Process each row
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Parse payment terms
                    payment_type = str(row.get('payment_type', 'cash')).lower()
                    
                    if payment_type == 'cash':
                        discount_percent = row.get('payment_discount_percent', 0)
                        if pd.isna(discount_percent) or discount_percent == '':
                            discount_percent = 0
                        payment_terms = {
                            'type': 'cash',
                            'discount_percent': float(discount_percent)
                        }
                    elif payment_type == 'installments':
                        schedule_str = str(row.get('installment_schedule', ''))
                        if not schedule_str or schedule_str == '':
                            payment_terms = {
                                'type': 'installments',
                                'schedule': [{'due_offset': 0, 'percent': 100}]
                            }
                        else:
                            percentages = [float(p.strip()) for p in schedule_str.split(',')]
                            payment_terms = {
                                'type': 'installments',
                                'schedule': [
                                    {'due_offset': i, 'percent': percentages[i]}
                                    for i in range(len(percentages))
                                ]
                            }
                    else:
                        payment_terms = {'type': 'cash', 'discount_percent': 0}
                    
                    # Parse optional fields
                    lomc_lead_time = row.get('lomc_lead_time', 0)
                    if pd.isna(lomc_lead_time) or lomc_lead_time == '':
                        lomc_lead_time = 0
                    else:
                        lomc_lead_time = int(lomc_lead_time)
                    
                    discount_bundle_threshold = row.get('discount_bundle_threshold')
                    if pd.isna(discount_bundle_threshold) or discount_bundle_threshold == '':
                        discount_bundle_threshold = None
                    else:
                        discount_bundle_threshold = int(discount_bundle_threshold)
                    
                    discount_bundle_percent = row.get('discount_bundle_percent')
                    if pd.isna(discount_bundle_percent) or discount_bundle_percent == '':
                        discount_bundle_percent = None
                    else:
                        discount_bundle_percent = float(discount_bundle_percent)
                    
                    option_data = {
                        'item_code': str(row['item_code']),
                        'supplier_name': str(row['supplier_name']),
                        'base_cost': float(row['base_cost']),
                        'lomc_lead_time': lomc_lead_time,
                        'discount_bundle_threshold': discount_bundle_threshold,
                        'discount_bundle_percent': discount_bundle_percent,
                        'payment_terms': payment_terms
                    }
                    
                    await create_procurement_option(db, option_data)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    logger.error(f"Error importing procurement option row {index + 2}: {str(e)}")
            
            return ExcelImportResponse(
                success=len(errors) == 0,
                imported_count=imported_count,
                errors=errors,
                message=f"Successfully imported {imported_count} procurement options"
            )
            
        except Exception as e:
            logger.error(f"Error importing procurement options: {str(e)}")
            return ExcelImportResponse(
                success=False,
                imported_count=0,
                errors=[str(e)],
                message="Import failed due to file processing error"
            )
    
    @staticmethod
    async def import_budget_data(db: AsyncSession, file_content: bytes) -> ExcelImportResponse:
        """Import budget data from Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(BytesIO(file_content), sheet_name='Budget Data')
            
            # Validate required columns
            required_columns = ['budget_date', 'available_budget']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return ExcelImportResponse(
                    success=False,
                    imported_count=0,
                    errors=[f"Missing required columns: {', '.join(missing_columns)}"],
                    message="Import failed due to missing columns"
                )
            
            # Process each row
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    budget_data = {
                        'budget_date': str(row['budget_date']),
                        'available_budget': float(row['available_budget'])
                    }
                    
                    await create_budget_data(db, budget_data)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    logger.error(f"Error importing budget data row {index + 2}: {str(e)}")
            
            return ExcelImportResponse(
                success=len(errors) == 0,
                imported_count=imported_count,
                errors=errors,
                message=f"Successfully imported {imported_count} budget entries"
            )
            
        except Exception as e:
            logger.error(f"Error importing budget data: {str(e)}")
            return ExcelImportResponse(
                success=False,
                imported_count=0,
                errors=[str(e)],
                message="Import failed due to file processing error"
            )
    
    @staticmethod
    async def export_project_items(db: AsyncSession, project_id: Optional[int] = None) -> bytes:
        """Export project items to Excel file"""
        if project_id:
            items = await get_project_items(db, project_id)
        else:
            # Get all project items (admin only)
            from sqlalchemy import select
            from app.models import ProjectItem
            result = await db.execute(select(ProjectItem))
            items = result.scalars().all()
        
        # Convert to DataFrame
        data = []
        for item in items:
            # Convert delivery_options list to comma-separated string
            delivery_options_str = ','.join(item.delivery_options) if item.delivery_options else ''
            
            data.append({
                'project_id': item.project_id,
                'item_code': item.item_code,
                'item_name': item.item_name or '',
                'quantity': item.quantity,
                'delivery_options': delivery_options_str,
                'description': item.description or '',
                'external_purchase': item.external_purchase
            })
        
        df = pd.DataFrame(data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Project Items', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    async def export_procurement_options(db: AsyncSession, item_code: Optional[str] = None) -> bytes:
        """Export procurement options to Excel file"""
        options = await get_procurement_options(db, item_code=item_code)
        
        # Convert to DataFrame
        data = []
        for option in options:
            payment_type = option.payment_terms.get('type', 'cash')
            if payment_type == 'cash':
                discount_percent = option.payment_terms.get('discount_percent', 0)
                installment_schedule = ''
            else:
                discount_percent = ''
                schedule = option.payment_terms.get('schedule', [])
                installment_schedule = ','.join([str(s.get('percent', 0)) for s in schedule])
            
            data.append({
                'item_code': option.item_code,
                'supplier_name': option.supplier_name,
                'base_cost': float(option.base_cost),
                'lomc_lead_time': option.lomc_lead_time,
                'discount_bundle_threshold': option.discount_bundle_threshold,
                'discount_bundle_percent': float(option.discount_bundle_percent) if option.discount_bundle_percent else '',
                'payment_type': payment_type,
                'payment_discount_percent': discount_percent,
                'installment_schedule': installment_schedule
            })
        
        df = pd.DataFrame(data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Procurement Options', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    async def export_budget_data(db: AsyncSession) -> bytes:
        """Export budget data to Excel file"""
        budget_data = await get_all_budget_data(db)
        
        # Convert to DataFrame
        data = []
        for budget in budget_data:
            data.append({
                'budget_date': budget.budget_date.isoformat() if budget.budget_date else '',
                'available_budget': float(budget.available_budget)
            })
        
        df = pd.DataFrame(data)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Budget Data', index=False)
        
        buffer.seek(0)
        return buffer.getvalue()
