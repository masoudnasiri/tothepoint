-- Migration script to add Supplier Management tables
-- Run this script to create the supplier-related tables

-- Create suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    supplier_id VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    legal_entity_type VARCHAR(50),
    registration_number VARCHAR(100),
    tax_id VARCHAR(100),
    established_year INTEGER,
    
    -- Location Information
    country VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    website VARCHAR(200),
    
    -- Business Information (JSON fields for flexibility)
    product_service_lines JSON,
    main_brands_represented JSON,
    main_markets_regions JSON,
    certifications JSON,
    ownership_type VARCHAR(50),
    annual_revenue_range VARCHAR(50),
    number_of_employees VARCHAR(50),
    warehouse_locations JSON,
    
    -- Operational Information
    key_clients_references JSON,
    payment_terms VARCHAR(100),
    currency_preference VARCHAR(10) DEFAULT 'IRR',
    shipping_methods JSON,
    incoterms JSON,
    average_lead_time_days INTEGER,
    
    -- Quality and Service Information
    quality_assurance_process TEXT,
    warranty_policy TEXT,
    after_sales_policy TEXT,
    delivery_accuracy_percent NUMERIC(5, 2),
    response_time_hours INTEGER,
    
    -- Status and Ratings
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    compliance_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    risk_level VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    internal_rating NUMERIC(3, 2),
    system_rating NUMERIC(3, 2),
    
    -- Additional Information
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id),
    
    -- Indexes
    CONSTRAINT suppliers_status_check CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING_APPROVAL')),
    CONSTRAINT suppliers_compliance_status_check CHECK (compliance_status IN ('APPROVED', 'PENDING', 'REJECTED', 'UNDER_REVIEW')),
    CONSTRAINT suppliers_risk_level_check CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT suppliers_established_year_check CHECK (established_year >= 1800 AND established_year <= 2030),
    CONSTRAINT suppliers_internal_rating_check CHECK (internal_rating >= 1.0 AND internal_rating <= 5.0),
    CONSTRAINT suppliers_system_rating_check CHECK (system_rating >= 1.0 AND system_rating <= 5.0),
    CONSTRAINT suppliers_delivery_accuracy_check CHECK (delivery_accuracy_percent >= 0 AND delivery_accuracy_percent <= 100),
    CONSTRAINT suppliers_response_time_check CHECK (response_time_hours >= 0 AND response_time_hours <= 168),
    CONSTRAINT suppliers_lead_time_check CHECK (average_lead_time_days >= 0 AND average_lead_time_days <= 365)
);

-- Create indexes for suppliers table
CREATE INDEX IF NOT EXISTS idx_suppliers_supplier_id ON suppliers(supplier_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_company_name ON suppliers(company_name);
CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status);
CREATE INDEX IF NOT EXISTS idx_suppliers_compliance_status ON suppliers(compliance_status);
CREATE INDEX IF NOT EXISTS idx_suppliers_risk_level ON suppliers(risk_level);
CREATE INDEX IF NOT EXISTS idx_suppliers_country ON suppliers(country);
CREATE INDEX IF NOT EXISTS idx_suppliers_city ON suppliers(city);
CREATE INDEX IF NOT EXISTS idx_suppliers_created_by ON suppliers(created_by_id);

-- Create supplier_contacts table
CREATE TABLE IF NOT EXISTS supplier_contacts (
    id SERIAL PRIMARY KEY,
    contact_id VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    
    -- Contact Information
    full_name VARCHAR(200) NOT NULL,
    job_title VARCHAR(100),
    role VARCHAR(100),
    department VARCHAR(100),
    
    -- Communication Details
    email VARCHAR(200),
    phone VARCHAR(50),
    whatsapp_id VARCHAR(50),
    telegram_id VARCHAR(50),
    
    -- Preferences
    language_preference VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50),
    working_hours VARCHAR(100),
    
    -- Status
    is_primary_contact BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Additional Information
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id),
    
    -- Indexes
    CONSTRAINT supplier_contacts_language_preference_check CHECK (language_preference IN ('en', 'fa', 'ar', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'zh', 'ja', 'ko'))
);

-- Create indexes for supplier_contacts table
CREATE INDEX IF NOT EXISTS idx_supplier_contacts_contact_id ON supplier_contacts(contact_id);
CREATE INDEX IF NOT EXISTS idx_supplier_contacts_supplier_id ON supplier_contacts(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_contacts_email ON supplier_contacts(email);
CREATE INDEX IF NOT EXISTS idx_supplier_contacts_is_primary ON supplier_contacts(is_primary_contact);
CREATE INDEX IF NOT EXISTS idx_supplier_contacts_is_active ON supplier_contacts(is_active);
CREATE INDEX IF NOT EXISTS idx_supplier_contacts_created_by ON supplier_contacts(created_by_id);

-- Create supplier_documents table
CREATE TABLE IF NOT EXISTS supplier_documents (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    
    -- Document Information
    document_name VARCHAR(200) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Document Details
    description TEXT,
    document_number VARCHAR(100),
    issued_by VARCHAR(200),
    issued_date DATE,
    expiry_date DATE,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Additional Information
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT supplier_documents_file_size_check CHECK (file_size >= 0),
    CONSTRAINT supplier_documents_expiry_date_check CHECK (expiry_date IS NULL OR expiry_date >= issued_date)
);

-- Create indexes for supplier_documents table
CREATE INDEX IF NOT EXISTS idx_supplier_documents_document_id ON supplier_documents(document_id);
CREATE INDEX IF NOT EXISTS idx_supplier_documents_supplier_id ON supplier_documents(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_documents_document_type ON supplier_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_supplier_documents_is_active ON supplier_documents(is_active);
CREATE INDEX IF NOT EXISTS idx_supplier_documents_is_verified ON supplier_documents(is_verified);
CREATE INDEX IF NOT EXISTS idx_supplier_documents_issued_date ON supplier_documents(issued_date);
CREATE INDEX IF NOT EXISTS idx_supplier_documents_expiry_date ON supplier_documents(expiry_date);
CREATE INDEX IF NOT EXISTS idx_supplier_documents_created_by ON supplier_documents(created_by_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_supplier_contacts_updated_at BEFORE UPDATE ON supplier_contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_supplier_documents_updated_at BEFORE UPDATE ON supplier_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO suppliers (
    supplier_id, company_name, legal_entity_type, country, city, 
    status, compliance_status, risk_level, currency_preference
) VALUES 
    ('SUP-00001', 'Tech Solutions Inc.', 'Corporation', 'United States', 'New York', 'ACTIVE', 'APPROVED', 'LOW', 'USD'),
    ('SUP-00002', 'Global Electronics Ltd.', 'Limited Company', 'Germany', 'Berlin', 'ACTIVE', 'PENDING', 'MEDIUM', 'EUR'),
    ('SUP-00003', 'Asian Manufacturing Co.', 'Corporation', 'China', 'Shanghai', 'ACTIVE', 'APPROVED', 'MEDIUM', 'CNY'),
    ('SUP-00004', 'Middle East Trading', 'LLC', 'UAE', 'Dubai', 'PENDING_APPROVAL', 'UNDER_REVIEW', 'HIGH', 'AED'),
    ('SUP-00005', 'European Components AG', 'AG', 'Switzerland', 'Zurich', 'ACTIVE', 'APPROVED', 'LOW', 'CHF')
ON CONFLICT (supplier_id) DO NOTHING;

-- Insert sample contacts
INSERT INTO supplier_contacts (
    contact_id, supplier_id, full_name, job_title, email, phone, is_primary_contact
) VALUES 
    ('CONT-00001', 1, 'John Smith', 'Sales Manager', 'john.smith@techsolutions.com', '+1-555-0123', TRUE),
    ('CONT-00002', 1, 'Sarah Johnson', 'Technical Support', 'sarah.johnson@techsolutions.com', '+1-555-0124', FALSE),
    ('CONT-00003', 2, 'Hans Mueller', 'Account Manager', 'hans.mueller@globalelectronics.de', '+49-30-123456', TRUE),
    ('CONT-00004', 3, 'Li Wei', 'Procurement Manager', 'li.wei@asianmanufacturing.cn', '+86-21-87654321', TRUE),
    ('CONT-00005', 4, 'Ahmed Al-Rashid', 'Business Development', 'ahmed@middleeasttrading.ae', '+971-4-1234567', TRUE)
ON CONFLICT (contact_id) DO NOTHING;

-- Insert sample documents
INSERT INTO supplier_documents (
    document_id, supplier_id, document_name, document_type, file_name, file_path, 
    document_number, issued_by, issued_date, expiry_date
) VALUES 
    ('DOC-00001', 1, 'ISO 9001:2015 Certificate', 'Certificate', 'iso9001_techsolutions.pdf', '/uploads/supplier_documents/iso9001_techsolutions.pdf', 'ISO-9001-2023-001', 'ISO Certification Body', '2023-01-15', '2026-01-15'),
    ('DOC-00002', 2, 'CE Marking Certificate', 'Certificate', 'ce_marking_globalelectronics.pdf', '/uploads/supplier_documents/ce_marking_globalelectronics.pdf', 'CE-2023-002', 'European Commission', '2023-02-20', '2028-02-20'),
    ('DOC-00003', 3, 'Quality Management System', 'Documentation', 'qms_asianmanufacturing.pdf', '/uploads/supplier_documents/qms_asianmanufacturing.pdf', 'QMS-2023-003', 'Internal Quality Team', '2023-03-10', NULL),
    ('DOC-00004', 4, 'Trade License', 'License', 'trade_license_middleeast.pdf', '/uploads/supplier_documents/trade_license_middleeast.pdf', 'TL-2023-004', 'Dubai Chamber of Commerce', '2023-01-01', '2024-12-31'),
    ('DOC-00005', 5, 'Swiss Quality Certificate', 'Certificate', 'swiss_quality_european.pdf', '/uploads/supplier_documents/swiss_quality_european.pdf', 'SQ-2023-005', 'Swiss Quality Institute', '2023-04-05', '2026-04-05')
ON CONFLICT (document_id) DO NOTHING;

-- Create uploads directory structure (this would need to be done at the OS level)
-- mkdir -p uploads/supplier_documents

COMMIT;
