# Supplier Management System Documentation

## Overview

The Supplier Management System is a comprehensive solution for managing supplier profiles, contacts, and compliance information in a centralized system. It provides full CRUD operations, document management, contact management, and advanced filtering capabilities.

## Features

### Core Functionality
- **Supplier Management**: Create, read, update, delete supplier profiles
- **Contact Management**: Manage multiple contacts per supplier with role designation
- **Document Management**: Upload, store, and manage compliance documents
- **Search & Filtering**: Advanced search and filtering capabilities
- **Pagination**: Efficient data loading with pagination
- **Role-based Access**: Different access levels for different user roles

### Business Information Management
- Company details and legal entity information
- Location and contact information
- Business capabilities and certifications
- Operational information (payment terms, shipping methods)
- Quality and service information
- Risk assessment and compliance status

## Database Schema

### Tables

#### `suppliers`
Main table storing supplier information:
- **Basic Info**: supplier_id, company_name, legal_entity_type
- **Location**: country, city, address, website
- **Business**: product_service_lines, certifications, ownership_type
- **Operational**: payment_terms, shipping_methods, lead_times
- **Quality**: quality_assurance_process, warranty_policy
- **Status**: status, compliance_status, risk_level, ratings

#### `supplier_contacts`
Contact information for suppliers:
- **Contact Details**: full_name, job_title, role, department
- **Communication**: email, phone, whatsapp_id, telegram_id
- **Preferences**: language_preference, timezone, working_hours
- **Status**: is_primary_contact, is_active

#### `supplier_documents`
Document management for suppliers:
- **Document Info**: document_name, document_type, file_name, file_path
- **Details**: document_number, issued_by, issued_date, expiry_date
- **Status**: is_active, is_verified

## API Endpoints

### Supplier Management
```
GET    /suppliers/                    # List suppliers with filters
POST   /suppliers/                    # Create new supplier
GET    /suppliers/{id}                # Get supplier by ID
PUT    /suppliers/{id}                # Update supplier
DELETE /suppliers/{id}                # Delete supplier
```

### Contact Management
```
GET    /suppliers/{id}/contacts       # List supplier contacts
POST   /suppliers/{id}/contacts       # Create new contact
PUT    /suppliers/{id}/contacts/{contact_id}  # Update contact
DELETE /suppliers/{id}/contacts/{contact_id} # Delete contact
```

### Document Management
```
GET    /suppliers/{id}/documents      # List supplier documents
POST   /suppliers/{id}/documents      # Upload document
GET    /suppliers/{id}/documents/{doc_id}/download  # Download document
PUT    /suppliers/{id}/documents/{doc_id}  # Update document metadata
DELETE /suppliers/{id}/documents/{doc_id}  # Delete document
```

### Utility Endpoints
```
GET    /suppliers/categories/list     # Get unique categories
GET    /suppliers/industries/list      # Get unique industries
GET    /suppliers/countries/list       # Get unique countries
```

## Frontend Components

### SuppliersPage.tsx
Main page component with:
- **Data Table**: Displays suppliers with sorting and filtering
- **Create/Edit Dialogs**: Forms for supplier management
- **View Dialog**: Tabbed interface for overview, contacts, documents
- **Contact Management**: Add/edit contacts within supplier context
- **Document Upload**: File upload with metadata management

### Key Features
- **Responsive Design**: Works on desktop and mobile
- **Internationalization**: Full English and Persian support
- **Material-UI Components**: Consistent design language
- **Error Handling**: Comprehensive error handling and user feedback
- **Loading States**: Proper loading indicators

## Installation & Setup

### Backend Setup
1. **Apply Database Migration**:
   ```bash
   # Windows
   apply_supplier_migration.bat
   
   # Or manually with psql
   psql -U postgres -d procurement_dss -f create_supplier_tables.sql
   ```

2. **Install Dependencies**:
   ```bash
   pip install aiohttp==3.9.1
   ```

3. **Restart Backend Service**:
   ```bash
   docker-compose restart backend
   ```

### Frontend Setup
1. **Navigation**: Already added to Layout.tsx
2. **Routes**: Already added to App.tsx
3. **Translations**: Already added to i18n files
4. **API Service**: Already added to api.ts

### File Storage Setup
1. **Create Upload Directory**:
   ```bash
   mkdir -p uploads/supplier_documents
   chmod 755 uploads/supplier_documents
   ```

## Usage Guide

### Creating a Supplier
1. Navigate to Suppliers page
2. Click "Add Supplier" button
3. Fill in basic information (company name is required)
4. Add location, business, and operational information
5. Set status, compliance, and risk levels
6. Click "Create" to save

### Managing Contacts
1. Open supplier details (click View button)
2. Go to "Contacts" tab
3. Click "Add Contact" button
4. Fill in contact information
5. Set as primary contact if needed
6. Save contact

### Document Management
1. Open supplier details
2. Go to "Documents" tab
3. Click "Upload Document" button
4. Fill in document metadata
5. Select file to upload
6. Document will be stored and linked to supplier

### Search and Filtering
- **Search**: Use the search box to find suppliers by name, ID, location
- **Status Filter**: Filter by Active, Inactive, Suspended, Pending Approval
- **Compliance Filter**: Filter by Approved, Pending, Rejected, Under Review
- **Risk Filter**: Filter by Low, Medium, High risk levels
- **Country Filter**: Filter by specific countries

## Testing

### Automated Testing
Run the comprehensive test suite:
```bash
python test_supplier_system.py
```

### Manual Testing Checklist
- [ ] Create new supplier
- [ ] Edit existing supplier
- [ ] View supplier details
- [ ] Add contact to supplier
- [ ] Upload document to supplier
- [ ] Search suppliers
- [ ] Filter suppliers by status
- [ ] Delete supplier (with cascade)
- [ ] Test pagination
- [ ] Test error handling

## Security Considerations

### Authentication & Authorization
- All endpoints require authentication
- Role-based access control implemented
- Admin, PMO, PM, Procurement, Finance roles supported

### File Upload Security
- File type validation (PDF, DOC, XLS, images, TXT)
- File size limits (10MB maximum)
- Unique filename generation to prevent conflicts
- Secure file storage outside web root

### Data Validation
- Input validation on all fields
- SQL injection prevention through SQLAlchemy ORM
- XSS prevention through proper escaping
- CSRF protection through authentication tokens

## Performance Considerations

### Database Optimization
- Proper indexing on frequently queried fields
- Foreign key constraints for data integrity
- JSON fields for flexible data storage
- Pagination to handle large datasets

### File Storage
- Local filesystem storage (can be migrated to cloud)
- File size limits to prevent storage issues
- Cleanup on supplier deletion

## Troubleshooting

### Common Issues

#### Database Connection Issues
- Ensure PostgreSQL is running
- Check database credentials
- Verify database exists

#### File Upload Issues
- Check uploads directory permissions
- Verify file size limits
- Check file type restrictions

#### API Errors
- Check authentication token
- Verify user permissions
- Check request format

### Error Messages
- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource doesn't exist
- **400 Bad Request**: Invalid input data
- **500 Internal Server Error**: Server-side error

## Future Enhancements

### Planned Features
- **Supplier Performance Tracking**: Track delivery performance, quality metrics
- **Contract Management**: Link contracts to suppliers
- **Supplier Portal**: Self-service portal for suppliers
- **Integration APIs**: Connect with external supplier databases
- **Advanced Analytics**: Supplier performance dashboards
- **Bulk Operations**: Import/export supplier data
- **Notification System**: Alerts for document expiry, compliance issues

### Technical Improvements
- **Cloud Storage**: Migrate to AWS S3 or similar
- **Caching**: Implement Redis caching for better performance
- **API Versioning**: Add API versioning for backward compatibility
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Audit Logging**: Track all changes for compliance

## Support

For technical support or questions about the Supplier Management System:
1. Check this documentation first
2. Review error logs
3. Run the test suite
4. Contact the development team

## Version History

- **v1.0.0**: Initial release with core functionality
  - Supplier CRUD operations
  - Contact management
  - Document management
  - Search and filtering
  - Role-based access control
