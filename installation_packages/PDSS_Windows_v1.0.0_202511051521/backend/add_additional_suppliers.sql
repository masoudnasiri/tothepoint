-- Add 12 additional suppliers to the database
INSERT INTO suppliers (
    supplier_id, company_name, legal_entity_type, country, city, 
    primary_email, main_phone, category, industry, status, 
    compliance_status, risk_level, created_at
) VALUES 
    ('SUP-00008', 'Iota Materials Co', 'Corporation', 'United States', 'New York', 'contact@iotamaterials.com', '+1-555-0108', 'Materials', 'Manufacturing', 'ACTIVE', 'APPROVED', 'LOW', NOW()),
    ('SUP-00009', 'Beta Materials Co', 'LLC', 'Canada', 'Toronto', 'info@betamaterials.ca', '+1-416-555-0109', 'Materials', 'Manufacturing', 'ACTIVE', 'APPROVED', 'LOW', NOW()),
    ('SUP-00010', 'Epsilon Trading Co', 'Corporation', 'United Kingdom', 'London', 'sales@epsilontrading.co.uk', '+44-20-555-0110', 'Trading', 'Distribution', 'ACTIVE', 'APPROVED', 'MEDIUM', NOW()),
    ('SUP-00011', 'Kappa Construction Supply', 'Corporation', 'Germany', 'Berlin', 'orders@kappaconstruction.de', '+49-30-555-0111', 'Construction', 'Building Materials', 'ACTIVE', 'APPROVED', 'MEDIUM', NOW()),
    ('SUP-00012', 'Mu Trading Corp', 'Corporation', 'Japan', 'Tokyo', 'contact@mutrading.jp', '+81-3-555-0112', 'Trading', 'Distribution', 'ACTIVE', 'APPROVED', 'MEDIUM', NOW()),
    ('SUP-00013', 'Lambda Industrial Ltd', 'Limited', 'Australia', 'Sydney', 'sales@lambdaindustrial.com.au', '+61-2-555-0113', 'Industrial', 'Manufacturing', 'ACTIVE', 'APPROVED', 'LOW', NOW()),
    ('SUP-00014', 'Theta Global Supply', 'Corporation', 'Singapore', 'Singapore', 'info@thetaglobal.sg', '+65-555-0114', 'Global', 'Supply Chain', 'ACTIVE', 'APPROVED', 'LOW', NOW()),
    ('SUP-00015', 'Alpha Suppliers Ltd', 'Limited', 'India', 'Mumbai', 'contact@alphasuppliers.in', '+91-22-555-0115', 'Suppliers', 'Distribution', 'ACTIVE', 'APPROVED', 'MEDIUM', NOW()),
    ('SUP-00016', 'Zeta Procurement Ltd', 'Limited', 'South Africa', 'Cape Town', 'procurement@zetaprocurement.co.za', '+27-21-555-0116', 'Procurement', 'Services', 'ACTIVE', 'APPROVED', 'MEDIUM', NOW()),
    ('SUP-00017', 'Eta Manufacturing Inc', 'Corporation', 'Brazil', 'São Paulo', 'manufacturing@etamanufacturing.com.br', '+55-11-555-0117', 'Manufacturing', 'Production', 'ACTIVE', 'APPROVED', 'LOW', NOW()),
    ('SUP-00018', 'Gamma Construction Supply', 'Corporation', 'France', 'Paris', 'supply@gammaconstruction.fr', '+33-1-555-0118', 'Construction', 'Building Materials', 'ACTIVE', 'APPROVED', 'MEDIUM', NOW()),
    ('SUP-00019', 'Delta Industrial Corp', 'Corporation', 'Italy', 'Milan', 'industrial@deltaindustrial.it', '+39-02-555-0119', 'Industrial', 'Manufacturing', 'ACTIVE', 'APPROVED', 'LOW', NOW());
