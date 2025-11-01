# 📊 COMPREHENSIVE DATABASE STRUCTURE DOCUMENTATION

## 🎯 Overview
This document provides a complete analysis of the Procurement Decision Support System (DSS) database structure, including all 20 tables, their relationships, constraints, and business logic.

---

## 📋 TABLE INVENTORY

### Core Business Tables (8)
1. **users** - User management and authentication
2. **projects** - Project definitions and budgets
3. **project_items** - Items within projects
4. **procurement_options** - Available procurement choices
5. **finalized_decisions** - Final procurement decisions
6. **suppliers** - Supplier information and management
7. **currencies** - Currency definitions
8. **budget_data** - Monthly budget allocations

### Supporting Tables (7)
9. **delivery_options** - Delivery timing and scheduling
10. **items_master** - Master item catalog
11. **cashflow_events** - Financial transaction tracking
12. **exchange_rates** - Currency conversion rates
13. **decision_factor_weights** - Optimization weighting factors
14. **optimization_runs** - Optimization execution tracking
15. **optimization_results** - Optimization output data

### Management Tables (5)
16. **project_assignments** - User-project assignments
17. **project_phases** - Project phase management
18. **supplier_contacts** - Supplier contact information
19. **supplier_documents** - Supplier document storage
20. **supplier_payments** - Supplier payment tracking

---

## 🔗 RELATIONSHIP DIAGRAM

```
users (1) ──→ (N) projects
users (1) ──→ (N) project_items
users (1) ──→ (N) procurement_options
users (1) ──→ (N) finalized_decisions
users (1) ──→ (N) suppliers
users (1) ──→ (N) currencies
users (1) ──→ (N) cashflow_events

projects (1) ──→ (N) project_items
projects (1) ──→ (N) finalized_decisions
projects (1) ──→ (N) optimization_results
projects (1) ──→ (N) project_assignments
projects (1) ──→ (N) project_phases
projects (1) ──→ (N) supplier_payments

project_items (1) ──→ (N) delivery_options
project_items (1) ──→ (N) finalized_decisions
project_items (1) ──→ (1) items_master

procurement_options (1) ──→ (N) finalized_decisions
procurement_options (1) ──→ (N) optimization_results
procurement_options (1) ──→ (1) suppliers
procurement_options (1) ──→ (1) currencies
procurement_options (1) ──→ (1) delivery_options

finalized_decisions (1) ──→ (N) cashflow_events
finalized_decisions (1) ──→ (N) supplier_payments
finalized_decisions (1) ──→ (1) optimization_runs

suppliers (1) ──→ (N) supplier_contacts
suppliers (1) ──→ (N) supplier_documents
```

---

## 📊 DETAILED TABLE ANALYSIS

### 1. **users** - User Management
**Purpose:** System user authentication and role management

**Key Fields:**
- `id` (PK) - Unique user identifier
- `username` (UNIQUE) - Login username
- `password_hash` - Encrypted password
- `role` - User role (admin, procurement, project_manager, etc.)
- `is_active` - Account status

**Relationships:**
- Referenced by 15+ tables for audit trails and ownership
- Central to all user-related operations

**Constraints:**
- Username must be unique
- Role-based access control

---

### 2. **projects** - Project Definitions
**Purpose:** Project management and budget allocation

**Key Fields:**
- `id` (PK) - Unique project identifier
- `project_code` (UNIQUE) - Project code
- `name` - Project name
- `priority_weight` (1-10) - Project priority
- `budget_amount` (NUMERIC(15,2)) - Project budget
- `budget_currency` - Budget currency (default: IRR)
- `is_active` - Project status

**Relationships:**
- **Parent of:** project_items, finalized_decisions, optimization_results
- **Child of:** users (created by)

**Business Logic:**
- Projects contain multiple items
- Budget tracking at project level
- Priority weighting for optimization

---

### 3. **project_items** - Project Items
**Purpose:** Individual items within projects

**Key Fields:**
- `id` (PK) - Unique item identifier
- `project_id` (FK) - Parent project
- `item_code` - Item identifier
- `item_name` - Item name
- `quantity` - Required quantity
- `delivery_options` (JSON) - Delivery preferences
- `status` (ENUM) - Item status
- `master_item_id` (FK) - Link to master catalog
- `is_finalized` - Finalization status
- `finalized_by` (FK) - User who finalized

**Relationships:**
- **Parent of:** delivery_options, finalized_decisions
- **Child of:** projects, items_master, users

**Business Logic:**
- Items belong to specific projects
- Can be linked to master catalog
- Track finalization workflow

---

### 4. **procurement_options** - Procurement Choices
**Purpose:** Available procurement options for items

**Key Fields:**
- `id` (PK) - Unique option identifier
- `item_code` - Related item code
- `supplier_name` - Supplier name
- `supplier_id` (FK) - Supplier reference
- `base_cost` (NUMERIC(15,2)) - Base cost
- `cost_amount` (NUMERIC(15,2)) - Total cost
- `cost_currency` - Cost currency
- `shipping_cost` (NUMERIC(15,2)) - Shipping cost
- `currency_id` (FK) - Currency reference
- `lomc_lead_time` - Lead time (deprecated)
- `expected_delivery_date` - Delivery date
- `delivery_option_id` (FK) - Delivery option
- `payment_terms` (JSON) - Payment conditions
- `is_active` - Option status
- `is_finalized` - Finalization status

**Relationships:**
- **Parent of:** finalized_decisions, optimization_results
- **Child of:** suppliers, currencies, delivery_options

**Business Logic:**
- Multiple options per item
- Cost and delivery tracking
- Supplier and currency relationships

---

### 5. **finalized_decisions** - Final Decisions
**Purpose:** Final procurement decisions and execution tracking

**Key Fields:**
- `id` (PK) - Unique decision identifier
- `run_id` (FK) - Optimization run reference
- `project_id` (FK) - Project reference
- `project_item_id` (FK) - Item reference
- `item_code` - Item code
- `procurement_option_id` (FK) - Chosen option
- `purchase_date` - Purchase date
- `delivery_date` - Delivery date
- `quantity` - Quantity
- `final_cost` (NUMERIC(12,2)) - Final cost
- `status` - Decision status
- `delivery_option_id` (FK) - Delivery option
- `forecast_invoice_*` - Invoice forecasting fields
- `actual_invoice_*` - Actual invoice fields
- `actual_payment_*` - Payment tracking fields
- `delivery_status` - Delivery status
- `currency_id` (FK) - Currency reference
- `is_final_invoice` - Final invoice flag

**Relationships:**
- **Parent of:** cashflow_events, supplier_payments
- **Child of:** optimization_runs, projects, project_items, procurement_options, delivery_options, currencies, users

**Business Logic:**
- Central decision tracking
- Invoice and payment management
- Delivery status tracking
- Multi-user workflow

---

### 6. **suppliers** - Supplier Management
**Purpose:** Comprehensive supplier information and management

**Key Fields:**
- `id` (PK) - Unique supplier identifier
- `supplier_id` (UNIQUE) - Supplier code
- `company_name` - Company name
- `legal_entity_type` - Legal structure
- `registration_number` - Registration number
- `tax_id` - Tax identification
- `established_year` - Year established
- `country`, `city`, `address` - Location
- `website`, `domain` - Web presence
- `primary_email`, `main_phone` - Contact info
- `linkedin_url`, `wechat_id`, `telegram_id` - Social media
- `category`, `industry` - Classification
- `product_service_lines` (JSON) - Services
- `main_brands_represented` (JSON) - Brands
- `main_markets_regions` (JSON) - Markets
- `certifications` (JSON) - Certifications
- `ownership_type` - Ownership structure
- `annual_revenue_range` - Revenue range
- `number_of_employees` - Employee count
- `warehouse_locations` (JSON) - Locations
- `key_clients_references` (JSON) - References
- `payment_terms` - Payment terms
- `currency_preference` - Preferred currency
- `shipping_methods` (JSON) - Shipping options
- `incoterms` (JSON) - Incoterms
- `average_lead_time_days` - Lead time
- `quality_assurance_process` - QA process
- `warranty_policy` - Warranty terms
- `after_sales_policy` - After-sales support
- `delivery_accuracy_percent` - Delivery accuracy
- `response_time_hours` - Response time
- `business_license_path` - License file
- `tax_certificate_path` - Tax certificate
- `iso_certificates_path` - ISO certificates
- `financial_report_path` - Financial reports
- `supplier_evaluation_path` - Evaluation forms
- `compliance_status` (ENUM) - Compliance status
- `last_review_date` - Last review
- `last_audit_date` - Last audit
- `status` (ENUM) - Supplier status
- `risk_level` (ENUM) - Risk assessment
- `internal_rating` (NUMERIC(3,2)) - Internal rating
- `performance_metrics` (JSON) - Performance data
- `notes` - Additional notes
- `created_by_id` (FK) - Creator
- `last_updated_by_id` (FK) - Last updater

**Relationships:**
- **Parent of:** supplier_contacts, supplier_documents, procurement_options
- **Child of:** users (created_by, last_updated_by)

**Business Logic:**
- Comprehensive supplier profiles
- Compliance and risk management
- Performance tracking
- Document management

---

### 7. **currencies** - Currency Management
**Purpose:** Currency definitions and base currency settings

**Key Fields:**
- `id` (PK) - Unique currency identifier
- `code` (UNIQUE) - Currency code (USD, IRR, EUR)
- `name` - Currency name
- `symbol` - Currency symbol
- `is_base_currency` - Base currency flag
- `is_active` - Active status
- `decimal_places` - Decimal precision
- `created_by_id` (FK) - Creator

**Relationships:**
- **Child of:** users
- **Parent of:** procurement_options, finalized_decisions

**Business Logic:**
- Multi-currency support
- Base currency designation
- Exchange rate integration

---

### 8. **budget_data** - Budget Management
**Purpose:** Monthly budget allocations and tracking

**Key Fields:**
- `id` (PK) - Unique budget identifier
- `budget_date` (UNIQUE) - Budget date
- `available_budget` (NUMERIC(15,2)) - Available amount
- `multi_currency_budget` (JSONB) - Multi-currency data
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

**Relationships:**
- Standalone table (no foreign keys)

**Business Logic:**
- Monthly budget tracking
- Multi-currency budget support
- Budget analysis integration

---

### 9. **delivery_options** - Delivery Scheduling
**Purpose:** Delivery timing and scheduling options

**Key Fields:**
- `id` (PK) - Unique delivery option identifier
- `project_item_id` (FK) - Related project item
- `delivery_slot` - Delivery slot number
- `delivery_date` - Delivery date
- `invoice_timing_type` - Invoice timing
- `invoice_issue_date` - Invoice issue date
- `invoice_days_after_delivery` - Days after delivery
- `invoice_amount_per_unit` (NUMERIC(12,2)) - Invoice amount
- `preference_rank` - Preference ranking
- `notes` - Additional notes
- `is_active` - Active status

**Relationships:**
- **Child of:** project_items
- **Parent of:** procurement_options, finalized_decisions

**Business Logic:**
- Multiple delivery options per item
- Invoice timing coordination
- Preference ranking system

---

### 10. **items_master** - Master Item Catalog
**Purpose:** Master catalog of all available items

**Key Fields:**
- `id` (PK) - Unique item identifier
- `item_code` (UNIQUE) - Item code
- `company` - Company name
- `item_name` - Item name
- `model` - Model number
- `specifications` (JSON) - Technical specs
- `category` - Item category
- `unit` - Unit of measure
- `description` - Item description
- `is_active` - Active status
- `created_by_id` (FK) - Creator

**Relationships:**
- **Child of:** users
- **Parent of:** project_items

**Business Logic:**
- Central item catalog
- Reusable across projects
- Specification management

---

### 11. **cashflow_events** - Financial Tracking
**Purpose:** Cash flow event tracking and forecasting

**Key Fields:**
- `id` (PK) - Unique event identifier
- `related_decision_id` (FK) - Related decision
- `event_type` (ENUM) - INFLOW/OUTFLOW
- `forecast_type` (ENUM) - FORECAST/ACTUAL
- `event_date` - Event date
- `amount` (NUMERIC(15,2)) - Amount
- `amount_value` (NUMERIC(15,2)) - Amount value
- `amount_currency` - Amount currency
- `description` - Event description
- `is_cancelled` - Cancellation status
- `cancelled_at` - Cancellation timestamp
- `cancelled_by_id` (FK) - Cancelled by user
- `cancellation_reason` - Cancellation reason

**Relationships:**
- **Child of:** finalized_decisions, users

**Business Logic:**
- Cash flow forecasting
- Actual vs forecast tracking
- Event cancellation support

---

### 12. **exchange_rates** - Currency Conversion
**Purpose:** Exchange rate management for currency conversion

**Key Fields:**
- `id` (PK) - Unique rate identifier
- `date` - Rate date
- `from_currency` - Source currency
- `to_currency` - Target currency
- `rate` - Exchange rate
- `is_active` - Active status
- `created_by_id` (FK) - Creator

**Relationships:**
- **Child of:** users

**Business Logic:**
- Historical rate tracking
- Multi-currency conversion
- Rate validation

---

### 13. **decision_factor_weights** - Optimization Weights
**Purpose:** Weighting factors for optimization algorithms

**Key Fields:**
- `id` (PK) - Unique weight identifier
- `factor_name` - Factor name
- `weight_value` - Weight value
- `is_active` - Active status
- `created_at` - Creation timestamp

**Relationships:**
- Standalone table

**Business Logic:**
- Optimization parameter tuning
- Factor weighting system

---

### 14. **optimization_runs** - Optimization Tracking
**Purpose:** Optimization execution tracking

**Key Fields:**
- `run_id` (PK, UUID) - Unique run identifier
- `run_timestamp` - Run timestamp
- `request_parameters` (JSON) - Request parameters
- `status` - Run status

**Relationships:**
- **Parent of:** finalized_decisions

**Business Logic:**
- Optimization execution tracking
- Parameter logging
- Result correlation

---

### 15. **optimization_results** - Optimization Output
**Purpose:** Optimization algorithm results

**Key Fields:**
- `id` (PK) - Unique result identifier
- `run_id` (FK) - Optimization run
- `run_timestamp` - Run timestamp
- `project_id` (FK) - Project reference
- `item_code` - Item code
- `procurement_option_id` (FK) - Chosen option
- `purchase_time` - Purchase timing
- `delivery_time` - Delivery timing
- `quantity` - Quantity
- `final_cost` (NUMERIC(12,2)) - Final cost

**Relationships:**
- **Child of:** optimization_runs, projects, procurement_options

**Business Logic:**
- Optimization result storage
- Cost and timing optimization
- Decision support data

---

### 16. **project_assignments** - User-Project Assignments
**Purpose:** User assignment to projects

**Key Fields:**
- `id` (PK) - Unique assignment identifier
- `project_id` (FK) - Project reference
- `user_id` (FK) - User reference
- `role` - Assignment role
- `assigned_at` - Assignment timestamp

**Relationships:**
- **Child of:** projects, users

**Business Logic:**
- Project team management
- Role-based access
- Assignment tracking

---

### 17. **project_phases** - Project Phase Management
**Purpose:** Project phase tracking

**Key Fields:**
- `id` (PK) - Unique phase identifier
- `project_id` (FK) - Project reference
- `phase_name` - Phase name
- `phase_description` - Phase description
- `start_date` - Start date
- `end_date` - End date
- `status` - Phase status

**Relationships:**
- **Child of:** projects

**Business Logic:**
- Project lifecycle management
- Phase tracking
- Timeline management

---

### 18. **supplier_contacts** - Supplier Contact Management
**Purpose:** Supplier contact information

**Key Fields:**
- `id` (PK) - Unique contact identifier
- `supplier_id` (FK) - Supplier reference
- `full_name` - Contact name
- `job_title` - Job title
- `department` - Department
- `email` - Email address
- `phone` - Phone number
- `language_preference` - Language preference
- `timezone` - Timezone
- `working_hours` - Working hours
- `notes` - Additional notes
- `created_by_id` (FK) - Creator

**Relationships:**
- **Child of:** suppliers, users

**Business Logic:**
- Contact management
- Communication preferences
- Multi-contact support

---

### 19. **supplier_documents** - Document Management
**Purpose:** Supplier document storage and management

**Key Fields:**
- `id` (PK) - Unique document identifier
- `supplier_id` (FK) - Supplier reference
- `document_type` - Document type
- `document_name` - Document name
- `file_path` - File path
- `file_size` - File size
- `upload_date` - Upload date
- `is_active` - Active status
- `created_by_id` (FK) - Creator

**Relationships:**
- **Child of:** suppliers, users

**Business Logic:**
- Document storage
- File management
- Compliance tracking

---

### 20. **supplier_payments** - Payment Tracking
**Purpose:** Supplier payment management

**Key Fields:**
- `id` (PK) - Unique payment identifier
- `decision_id` (FK) - Related decision
- `project_id` (FK) - Project reference
- `supplier_id` (FK) - Supplier reference
- `payment_amount` (NUMERIC(15,2)) - Payment amount
- `payment_currency` - Payment currency
- `payment_date` - Payment date
- `payment_method` - Payment method
- `payment_status` - Payment status
- `notes` - Payment notes
- `created_by_id` (FK) - Creator

**Relationships:**
- **Child of:** finalized_decisions, projects, suppliers, users

**Business Logic:**
- Payment tracking
- Multi-currency payments
- Status management

---

## 🔄 DATA FLOW ANALYSIS

### Primary Workflow
1. **Project Creation** → projects
2. **Item Addition** → project_items
3. **Delivery Options** → delivery_options
4. **Procurement Options** → procurement_options
5. **Optimization** → optimization_runs → optimization_results
6. **Decision Finalization** → finalized_decisions
7. **Cash Flow Tracking** → cashflow_events
8. **Payment Processing** → supplier_payments

### Supporting Workflows
- **Supplier Management**: suppliers → supplier_contacts → supplier_documents
- **Currency Management**: currencies → exchange_rates
- **Budget Management**: budget_data
- **User Management**: users → project_assignments

---

## 🎯 KEY BUSINESS RULES

### 1. **Project-Item Relationship**
- Projects contain multiple items
- Items belong to exactly one project
- Items can be linked to master catalog

### 2. **Procurement Decision Flow**
- Items have multiple procurement options
- Options link to suppliers and delivery options
- Optimization selects best options
- Decisions are finalized and tracked

### 3. **Financial Tracking**
- Multi-currency support throughout
- Cash flow forecasting vs actual
- Budget allocation and tracking
- Payment processing

### 4. **Supplier Management**
- Comprehensive supplier profiles
- Contact and document management
- Performance and risk tracking
- Compliance management

### 5. **User and Security**
- Role-based access control
- Audit trails for all operations
- User-project assignments
- Multi-user workflows

---

## 📈 PERFORMANCE CONSIDERATIONS

### Indexes
- Primary keys on all tables
- Foreign key indexes
- Unique constraints on critical fields
- Composite indexes for common queries

### Data Types
- NUMERIC(15,2) for monetary values
- JSON/JSONB for flexible data
- ENUMs for controlled vocabularies
- UUIDs for optimization runs

### Relationships
- CASCADE deletes for dependent data
- RESTRICT deletes for referenced data
- Proper foreign key constraints

---

## 🔧 MAINTENANCE NOTES

### Regular Tasks
- Exchange rate updates
- Budget data maintenance
- Supplier compliance reviews
- Performance metric updates

### Data Integrity
- Foreign key constraints
- Check constraints for valid ranges
- Unique constraints for business keys
- Audit trail maintenance

---

## 📊 SUMMARY STATISTICS

- **Total Tables**: 20
- **Core Business Tables**: 8
- **Supporting Tables**: 7
- **Management Tables**: 5
- **Total Relationships**: 50+
- **Foreign Key Constraints**: 30+
- **Unique Constraints**: 15+
- **Check Constraints**: 10+

This database structure supports a comprehensive procurement decision support system with full lifecycle management from project planning through payment processing.
