-- Enhanced Supplier Management System Migration
-- This script updates the supplier tables with comprehensive business information

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS supplier_documents CASCADE;
DROP TABLE IF EXISTS supplier_contacts CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;

-- Create suppliers table with comprehensive fields
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    supplier_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- General Information
    company_name VARCHAR(200) NOT NULL,
    legal_entity_type VARCHAR(50), -- LLC, Ltd., JV, Corp, Partnership, etc.
    registration_number VARCHAR(100),
    tax_id VARCHAR(100),
    established_year INTEGER,
    
    -- Location Information
    country VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    website VARCHAR(200),
    domain VARCHAR(200),
    
    -- Primary Contact Information
    primary_email VARCHAR(200),
    main_phone VARCHAR(50),
    
    -- Social Media Links
    linkedin_url VARCHAR(200),
    wechat_id VARCHAR(100),
    telegram_id VARCHAR(100),
    other_social_media JSON, -- Array of other social media links
    
    -- Business & Classification
    category VARCHAR(100), -- Telecom, Oil & Gas, IT Equipment, etc.
    industry VARCHAR(100),
    product_service_lines JSON, -- Array of product/service categories
    main_brands_represented JSON, -- Array of brands
    main_markets_regions JSON, -- Array of markets/regions
    certifications JSON, -- Array of certifications (ISO, CE, UL, etc.)
    ownership_type VARCHAR(50), -- Private, State-owned, Distributor, Agent, etc.
    annual_revenue_range VARCHAR(50), -- <1M, 1M-10M, 10M-100M, >100M
    number_of_employees VARCHAR(50), -- <10, 10-50, 50-200, >200
    
    -- Operational Information
    warehouse_locations JSON, -- Array of warehouse/logistics locations
    key_clients_references JSON, -- Array of key clients
    payment_terms VARCHAR(100), -- T/T, LC, Net 30, etc.
    currency_preference VARCHAR(10) DEFAULT 'IRR',
    shipping_methods JSON, -- Array of shipping methods
    incoterms JSON, -- Array of supported incoterms
    average_lead_time_days INTEGER,
    
    -- Quality and Service Information
    quality_assurance_process TEXT,
    warranty_policy TEXT,
    after_sales_policy TEXT,
    delivery_accuracy_percent NUMERIC(5, 2),
    response_time_hours INTEGER,
    
    -- Document & Compliance Tracking
    business_license_path VARCHAR(500),
    tax_certificate_path VARCHAR(500),
    iso_certificates_path VARCHAR(500),
    financial_report_path VARCHAR(500),
    supplier_evaluation_path VARCHAR(500),
    compliance_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    last_review_date DATE,
    last_audit_date DATE,
    
    -- Internal Use & Meta
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    risk_level VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    internal_rating NUMERIC(3, 2), -- 1.00 to 5.00 stars
    performance_metrics JSON, -- Delivery accuracy, response time, etc.
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id),
    last_updated_by_id INTEGER REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT suppliers_status_check CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING_APPROVAL')),
    CONSTRAINT suppliers_compliance_status_check CHECK (compliance_status IN ('APPROVED', 'PENDING', 'REJECTED', 'UNDER_REVIEW')),
    CONSTRAINT suppliers_risk_level_check CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    CONSTRAINT suppliers_established_year_check CHECK (established_year >= 1800 AND established_year <= 2030),
    CONSTRAINT suppliers_internal_rating_check CHECK (internal_rating >= 1.0 AND internal_rating <= 5.0),
    CONSTRAINT suppliers_delivery_accuracy_check CHECK (delivery_accuracy_percent >= 0 AND delivery_accuracy_percent <= 100),
    CONSTRAINT suppliers_response_time_check CHECK (response_time_hours >= 0 AND response_time_hours <= 168),
    CONSTRAINT suppliers_lead_time_check CHECK (average_lead_time_days >= 0 AND average_lead_time_days <= 365)
);

-- Create indexes for suppliers table
CREATE INDEX idx_suppliers_supplier_id ON suppliers(supplier_id);
CREATE INDEX idx_suppliers_company_name ON suppliers(company_name);
CREATE INDEX idx_suppliers_status ON suppliers(status);
CREATE INDEX idx_suppliers_compliance_status ON suppliers(compliance_status);
CREATE INDEX idx_suppliers_risk_level ON suppliers(risk_level);
CREATE INDEX idx_suppliers_country ON suppliers(country);
CREATE INDEX idx_suppliers_city ON suppliers(city);
CREATE INDEX idx_suppliers_category ON suppliers(category);
CREATE INDEX idx_suppliers_industry ON suppliers(industry);
CREATE INDEX idx_suppliers_primary_email ON suppliers(primary_email);
CREATE INDEX idx_suppliers_created_by ON suppliers(created_by_id);
CREATE INDEX idx_suppliers_last_updated_by ON suppliers(last_updated_by_id);

-- Create supplier_contacts table
CREATE TABLE supplier_contacts (
    id SERIAL PRIMARY KEY,
    contact_id VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    
    -- Contact Information
    full_name VARCHAR(200) NOT NULL,
    job_title VARCHAR(100), -- Job Title / Role
    role VARCHAR(100), -- Sales Manager, Technical Support, etc.
    department VARCHAR(100), -- Sales, Technical, Finance, etc.
    
    -- Communication Details
    email VARCHAR(200),
    phone VARCHAR(50),
    whatsapp_id VARCHAR(50),
    telegram_id VARCHAR(50),
    
    -- Preferences
    language_preference VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50),
    working_hours VARCHAR(100), -- "9:00-17:00 UTC+3"
    
    -- Status
    is_primary_contact BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Additional Information
    notes TEXT, -- Relationship Information (e.g., "Main negotiator for Cisco equipment")
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT supplier_contacts_language_preference_check CHECK (language_preference IN ('en', 'fa', 'ar', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'zh', 'ja', 'ko'))
);

-- Create indexes for supplier_contacts table
CREATE INDEX idx_supplier_contacts_contact_id ON supplier_contacts(contact_id);
CREATE INDEX idx_supplier_contacts_supplier_id ON supplier_contacts(supplier_id);
CREATE INDEX idx_supplier_contacts_email ON supplier_contacts(email);
CREATE INDEX idx_supplier_contacts_is_primary ON supplier_contacts(is_primary_contact);
CREATE INDEX idx_supplier_contacts_is_active ON supplier_contacts(is_active);
CREATE INDEX idx_supplier_contacts_created_by ON supplier_contacts(created_by_id);

-- Create supplier_documents table
CREATE TABLE supplier_documents (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    
    -- Document Information
    document_name VARCHAR(200) NOT NULL,
    document_type VARCHAR(100) NOT NULL, -- Business License, Tax Certificate, ISO Certificate, etc.
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
CREATE INDEX idx_supplier_documents_document_id ON supplier_documents(document_id);
CREATE INDEX idx_supplier_documents_supplier_id ON supplier_documents(supplier_id);
CREATE INDEX idx_supplier_documents_document_type ON supplier_documents(document_type);
CREATE INDEX idx_supplier_documents_is_active ON supplier_documents(is_active);
CREATE INDEX idx_supplier_documents_is_verified ON supplier_documents(is_verified);
CREATE INDEX idx_supplier_documents_issued_date ON supplier_documents(issued_date);
CREATE INDEX idx_supplier_documents_expiry_date ON supplier_documents(expiry_date);
CREATE INDEX idx_supplier_documents_created_by ON supplier_documents(created_by_id);

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

-- Insert comprehensive sample data for testing
INSERT INTO suppliers (
    supplier_id, company_name, legal_entity_type, registration_number, tax_id, established_year,
    country, city, address, website, domain,
    primary_email, main_phone,
    linkedin_url, wechat_id, telegram_id,
    category, industry, product_service_lines, main_brands_represented, main_markets_regions,
    certifications, ownership_type, annual_revenue_range, number_of_employees,
    warehouse_locations, key_clients_references, payment_terms, currency_preference,
    shipping_methods, incoterms, average_lead_time_days,
    quality_assurance_process, warranty_policy, after_sales_policy,
    delivery_accuracy_percent, response_time_hours,
    compliance_status, last_review_date, last_audit_date,
    status, risk_level, internal_rating, performance_metrics, notes
) VALUES 
    ('SUP-00001', 'Tech Solutions Inc.', 'Corporation', 'REG-001', 'TAX-001', 2015,
     'United States', 'New York', '123 Tech Street, New York, NY 10001', 'https://techsolutions.com', 'techsolutions.com',
     'info@techsolutions.com', '+1-555-0123',
     'https://linkedin.com/company/techsolutions', 'techsolutions', '@techsolutions',
     'IT Equipment', 'Technology', '["Hardware", "Software", "Services"]', '["Cisco", "HP", "Dell"]', '["North America", "Europe"]',
     '["ISO 9001:2015", "CE Marking"]', 'Private', '10M-100M', '50-200',
     '["New York", "California"]', '["Fortune 500 Companies", "Government Agencies"]', 'T/T, LC', 'USD',
     '["Air", "Sea", "Land"]', '["FOB", "CIF", "EXW"]', 15,
     'ISO 9001 certified quality management system', '2-year warranty on all products', '24/7 technical support',
     98.5, 4,
     'APPROVED', '2024-01-15', '2024-01-10',
     'ACTIVE', 'LOW', 4.8, '{"delivery_accuracy": 98.5, "response_time": 4, "customer_satisfaction": 4.8}', 'Leading technology solutions provider'),
     
    ('SUP-00002', 'Global Electronics Ltd.', 'Limited Company', 'REG-002', 'TAX-002', 2010,
     'Germany', 'Berlin', '456 Electronics Ave, Berlin, Germany', 'https://globalelectronics.de', 'globalelectronics.de',
     'contact@globalelectronics.de', '+49-30-123456',
     'https://linkedin.com/company/globalelectronics', 'globalelectronics', '@globalelectronics',
     'Electronics', 'Manufacturing', '["Electronic Components", "Circuit Boards", "Testing Equipment"]', '["Siemens", "Bosch", "Infineon"]', '["Europe", "Asia"]',
     '["ISO 14001", "CE Marking", "UL Certification"]', 'Private', '1M-10M', '10-50',
     '["Berlin", "Munich"]', '["Automotive Industry", "Industrial Equipment"]', 'LC, Net 30', 'EUR',
     '["Sea", "Land"]', '["FOB", "CIF"]', 21,
     'Comprehensive quality control and testing procedures', '1-year warranty with extended options', 'Technical support in German and English',
     95.0, 8,
     'PENDING', '2023-12-01', '2023-11-15',
     'ACTIVE', 'MEDIUM', 4.2, '{"delivery_accuracy": 95.0, "response_time": 8, "customer_satisfaction": 4.2}', 'Reliable electronics manufacturer'),
     
    ('SUP-00003', 'Asian Manufacturing Co.', 'Corporation', 'REG-003', 'TAX-003', 2008,
     'China', 'Shanghai', '789 Industrial Zone, Shanghai, China', 'https://asianmanufacturing.cn', 'asianmanufacturing.cn',
     'sales@asianmanufacturing.cn', '+86-21-87654321',
     'https://linkedin.com/company/asianmanufacturing', 'asianmanufacturing', '@asianmanufacturing',
     'Manufacturing', 'Industrial', '["Machinery", "Equipment", "Components"]', '["Local Brands", "OEM Products"]', '["Asia", "Middle East"]',
     '["ISO 9001:2015", "CE Marking"]', 'Private', '100M+', '200+',
     '["Shanghai", "Shenzhen", "Guangzhou"]', '["Major Corporations", "Government Projects"]', 'T/T, LC', 'CNY',
     '["Sea", "Air"]', '["FOB", "CIF", "EXW"]', 30,
     'Strict quality control with multiple inspection points', '3-year warranty on machinery', 'Comprehensive after-sales service',
     92.0, 12,
     'APPROVED', '2024-02-01', '2024-01-20',
     'ACTIVE', 'MEDIUM', 4.5, '{"delivery_accuracy": 92.0, "response_time": 12, "customer_satisfaction": 4.5}', 'Large-scale manufacturing company'),
     
    ('SUP-00004', 'Middle East Trading', 'LLC', 'REG-004', 'TAX-004', 2012,
     'UAE', 'Dubai', '321 Business Bay, Dubai, UAE', 'https://middleeasttrading.ae', 'middleeasttrading.ae',
     'info@middleeasttrading.ae', '+971-4-1234567',
     'https://linkedin.com/company/middleeasttrading', 'middleeasttrading', '@middleeasttrading',
     'Trading', 'Commerce', '["Import/Export", "Distribution", "Logistics"]', '["Various International Brands"]', '["Middle East", "Africa"]',
     '["Trade License", "ISO 9001"]', 'Private', '1M-10M', '10-50',
     '["Dubai", "Abu Dhabi"]', '["Regional Distributors", "Retail Chains"]', 'T/T, LC', 'AED',
     '["Air", "Sea", "Land"]', '["FOB", "CIF", "DDP"]', 14,
     'Quality assurance through supplier verification', 'Standard warranty terms', 'Regional support network',
     88.0, 6,
     'UNDER_REVIEW', '2023-11-01', '2023-10-15',
     'PENDING_APPROVAL', 'HIGH', 3.8, '{"delivery_accuracy": 88.0, "response_time": 6, "customer_satisfaction": 3.8}', 'Regional trading company'),
     
    ('SUP-00005', 'European Components AG', 'AG', 'REG-005', 'TAX-005', 2005,
     'Switzerland', 'Zurich', '654 Precision Street, Zurich, Switzerland', 'https://europeancomponents.ch', 'europeancomponents.ch',
     'contact@europeancomponents.ch', '+41-44-1234567',
     'https://linkedin.com/company/europeancomponents', 'europeancomponents', '@europeancomponents',
     'Precision Components', 'Manufacturing', '["Precision Parts", "Custom Components", "Prototyping"]', '["Swiss Quality Brands"]', '["Europe", "North America"]',
     '["ISO 9001:2015", "Swiss Quality Certificate"]', 'Private', '10M-100M', '50-200',
     '["Zurich", "Geneva"]', '["Aerospace Industry", "Medical Equipment"]', 'T/T, LC', 'CHF',
     '["Air", "Express"]', '["FOB", "CIF"]', 7,
     'Swiss precision standards with advanced quality control', '5-year warranty on precision components', 'Expert technical consultation',
     99.5, 2,
     'APPROVED', '2024-03-01', '2024-02-15',
     'ACTIVE', 'LOW', 4.9, '{"delivery_accuracy": 99.5, "response_time": 2, "customer_satisfaction": 4.9}', 'Premium Swiss precision components')
ON CONFLICT (supplier_id) DO NOTHING;

-- Insert sample contacts
INSERT INTO supplier_contacts (
    contact_id, supplier_id, full_name, job_title, role, department,
    email, phone, whatsapp_id, telegram_id,
    language_preference, timezone, working_hours,
    is_primary_contact, is_active, notes
) VALUES 
    ('CONT-00001', 1, 'John Smith', 'Sales Manager', 'Sales Manager', 'Sales',
     'john.smith@techsolutions.com', '+1-555-0123', 'johnsmith', '@johnsmith',
     'en', 'EST', '9:00-17:00 EST',
     TRUE, TRUE, 'Main negotiator for Cisco equipment and enterprise solutions'),
     
    ('CONT-00002', 1, 'Sarah Johnson', 'Technical Support Lead', 'Technical Support', 'Technical',
     'sarah.johnson@techsolutions.com', '+1-555-0124', 'sarahjohnson', '@sarahjohnson',
     'en', 'EST', '8:00-20:00 EST',
     FALSE, TRUE, 'Technical support contact for complex implementations'),
     
    ('CONT-00003', 2, 'Hans Mueller', 'Account Manager', 'Account Manager', 'Sales',
     'hans.mueller@globalelectronics.de', '+49-30-123456', 'hansmueller', '@hansmueller',
     'de', 'CET', '8:00-18:00 CET',
     TRUE, TRUE, 'Primary contact for European market and automotive industry'),
     
    ('CONT-00004', 3, 'Li Wei', 'Procurement Manager', 'Procurement Manager', 'Procurement',
     'li.wei@asianmanufacturing.cn', '+86-21-87654321', 'liwei', '@liwei',
     'zh', 'CST', '9:00-18:00 CST',
     TRUE, TRUE, 'Main procurement contact for machinery and equipment orders'),
     
    ('CONT-00005', 4, 'Ahmed Al-Rashid', 'Business Development Manager', 'Business Development', 'Business Development',
     'ahmed@middleeasttrading.ae', '+971-4-1234567', 'ahmedalrashid', '@ahmedalrashid',
     'ar', 'GST', '8:00-17:00 GST',
     TRUE, TRUE, 'Business development contact for Middle East and Africa markets'),
     
    ('CONT-00006', 5, 'Marie Dubois', 'Quality Manager', 'Quality Manager', 'Quality',
     'marie.dubois@europeancomponents.ch', '+41-44-1234567', 'mariedubois', '@mariedubois',
     'fr', 'CET', '8:00-17:00 CET',
     TRUE, TRUE, 'Quality assurance and precision component specialist')
ON CONFLICT (contact_id) DO NOTHING;

-- Insert sample documents
INSERT INTO supplier_documents (
    document_id, supplier_id, document_name, document_type, file_name, file_path,
    document_number, issued_by, issued_date, expiry_date,
    is_active, is_verified, notes
) VALUES 
    ('DOC-00001', 1, 'ISO 9001:2015 Certificate', 'ISO Certificate', 'iso9001_techsolutions.pdf', '/uploads/supplier_documents/iso9001_techsolutions.pdf',
     'ISO-9001-2023-001', 'ISO Certification Body', '2023-01-15', '2026-01-15',
     TRUE, TRUE, 'Quality management system certification'),
     
    ('DOC-00002', 1, 'Business License', 'Business License', 'business_license_techsolutions.pdf', '/uploads/supplier_documents/business_license_techsolutions.pdf',
     'BL-2023-001', 'New York State', '2023-01-01', '2024-12-31',
     TRUE, TRUE, 'State business license'),
     
    ('DOC-00003', 2, 'CE Marking Certificate', 'CE Certificate', 'ce_marking_globalelectronics.pdf', '/uploads/supplier_documents/ce_marking_globalelectronics.pdf',
     'CE-2023-002', 'European Commission', '2023-02-20', '2028-02-20',
     TRUE, TRUE, 'European conformity marking'),
     
    ('DOC-00004', 3, 'Quality Management System', 'Quality Documentation', 'qms_asianmanufacturing.pdf', '/uploads/supplier_documents/qms_asianmanufacturing.pdf',
     'QMS-2023-003', 'Internal Quality Team', '2023-03-10', NULL,
     TRUE, TRUE, 'Internal quality management documentation'),
     
    ('DOC-00005', 4, 'Trade License', 'Trade License', 'trade_license_middleeast.pdf', '/uploads/supplier_documents/trade_license_middleeast.pdf',
     'TL-2023-004', 'Dubai Chamber of Commerce', '2023-01-01', '2024-12-31',
     TRUE, TRUE, 'Dubai trade license'),
     
    ('DOC-00006', 5, 'Swiss Quality Certificate', 'Quality Certificate', 'swiss_quality_european.pdf', '/uploads/supplier_documents/swiss_quality_european.pdf',
     'SQ-2023-005', 'Swiss Quality Institute', '2023-04-05', '2026-04-05',
     TRUE, TRUE, 'Swiss precision quality certification')
ON CONFLICT (document_id) DO NOTHING;

COMMIT;
