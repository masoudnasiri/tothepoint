# 🏗️ Items Master Refactoring Plan

## 🎯 **Objective:**

Create a **centralized Items Master catalog** where all items are defined once with unique codes, then referenced across all projects.

---

## 📋 **Current Architecture (BEFORE):**

```
┌─────────────────────────┐
│ Project Items           │
│ ├─ item_code: "STEEL-1" │ ← Defined per project
│ ├─ item_name: "Steel"   │ ← Can be inconsistent
│ ├─ description: "..."   │ ← Mix of item + project info
│ └─ quantity: 50         │
└─────────────────────────┘
         ↓
┌─────────────────────────┐
│ Procurement Options     │
│ ├─ item_code: "STEEL-1" │ ← References string
│ └─ supplier: "..."      │
└─────────────────────────┘
```

**Problems:**
- ❌ Same item code can have different names across projects
- ❌ Item codes not standardized
- ❌ No guarantee of uniqueness
- ❌ Descriptions mix item specs + project context
- ❌ Hard to maintain consistency

---

## 📋 **New Architecture (AFTER):**

```
┌──────────────────────────────────┐
│ Items Master (NEW!)              │
│ ├─ id: 1                         │
│ ├─ item_code: "ACME-STEEL-A36"   │ ← Auto-generated
│ ├─ company: "ACME"               │
│ ├─ item_name: "Steel Beam"       │
│ ├─ model: "A36"                  │
│ └─ specs: {"length": "10m", ...} │ ← Standard specs
└──────────────────────────────────┘
         ↓ (references)
┌──────────────────────────────────┐
│ Project Items                    │
│ ├─ id: 1                         │
│ ├─ master_item_id: 1 (FK)       │ ← References master
│ ├─ project_id: 5                 │
│ ├─ quantity: 50                  │
│ ├─ description: "For columns..." │ ← Project-specific context
│ └─ delivery_options: [...]       │
└──────────────────────────────────┘
         ↓ (joins with master)
┌──────────────────────────────────┐
│ Procurement View                 │
│ ├─ Item: ACME-STEEL-A36          │ ← From master
│ ├─ Name: Steel Beam              │ ← From master
│ ├─ Model: A36                    │ ← From master
│ ├─ Qty: 50                       │ ← From project
│ └─ Context: "For columns..."     │ ← From project
└──────────────────────────────────┘
```

**Benefits:**
- ✅ Unique item codes (enforced by system)
- ✅ Standardized naming
- ✅ Consistent across all projects
- ✅ Clear separation: Item specs vs. Project context
- ✅ Easier procurement (standard items)

---

## 🗄️ **Database Schema Changes:**

### **1. NEW Table: items_master**
```sql
CREATE TABLE items_master (
    id SERIAL PRIMARY KEY,
    item_code VARCHAR(100) UNIQUE NOT NULL,  -- Auto-generated: COMPANY-NAME-MODEL
    company VARCHAR(100) NOT NULL,           -- e.g., "ACME", "XYZ Corp"
    item_name VARCHAR(200) NOT NULL,         -- e.g., "Steel Beam", "Cable"
    model VARCHAR(100),                      -- e.g., "A36", "10mm²"
    specifications JSONB,                    -- Standard specs (length, weight, etc.)
    category VARCHAR(100),                   -- e.g., "Construction", "Electrical"
    unit VARCHAR(50),                        -- e.g., "piece", "meter", "kg"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by_id INT REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT unique_item_code UNIQUE (item_code),
    CONSTRAINT unique_company_name_model UNIQUE (company, item_name, model)
);

CREATE INDEX idx_items_master_code ON items_master(item_code);
CREATE INDEX idx_items_master_company ON items_master(company);
CREATE INDEX idx_items_master_active ON items_master(is_active);
```

### **2. UPDATED Table: project_items**
```sql
ALTER TABLE project_items
ADD COLUMN master_item_id INT REFERENCES items_master(id) ON DELETE RESTRICT;

-- Migration: Set master_item_id for existing items
-- Will need to create master items from existing project_items
```

**Changes:**
- Add `master_item_id` (Foreign Key to items_master)
- Keep `item_code` for backward compatibility (denormalized)
- Keep `item_name` for backward compatibility
- `description` becomes project-specific context
- Remove file attachment fields (move to master if needed)

### **3. Dependencies Check:**
```sql
-- These tables reference item_code (string):
procurement_options (item_code VARCHAR)       -- OK (uses code from master)
finalized_decisions (item_code VARCHAR)       -- OK (uses code from master)
delivery_options (project_item_id INT FK)     -- OK (unchanged)
```

**No breaking changes needed** - They reference `item_code` string which will come from master!

---

## 📊 **Data Flow:**

### **Creating Item Master:**
```
Admin/PM/Finance creates item in Items Master:
├─> Company: "ACME"
├─> Name: "Steel Beam"
├─> Model: "A36"
└─> System generates: item_code = "ACME-STEEL-BEAM-A36"
    └─> Saved in items_master table
```

### **Adding Item to Project:**
```
PM adds item to project:
├─> Selects from Items Master dropdown
├─> Chooses: "ACME-STEEL-BEAM-A36"
├─> System fills: item_code, item_name (from master)
├─> PM adds: 
│   ├─> Quantity: 50
│   ├─> Description: "For ground floor columns, north wing"
│   └─> Delivery dates: [2025-01-15, 2025-02-15]
└─> Saved in project_items table
    ├─> master_item_id: 1 (references master)
    ├─> item_code: "ACME-STEEL-BEAM-A36" (denormalized)
    ├─> description: "For ground floor columns..."
    └─> quantity: 50
```

### **Procurement View:**
```
Procurement adds option:
├─> Sees item: "ACME-STEEL-BEAM-A36"
├─> Item Info (from master):
│   ├─> Company: ACME
│   ├─> Name: Steel Beam
│   ├─> Model: A36
│   └─> Standard Specs: {...}
├─> Project Context (from project_item):
│   ├─> Quantity: 50 units
│   └─> Description: "For ground floor columns, north wing"
└─> Creates quote with full context!
```

---

## 🔄 **Dependency Chain Analysis:**

### **Affected Components:**

```
1. Items Master (NEW)
   ├─> Backend Model
   ├─> Backend API (CRUD + Excel)
   ├─> Frontend Page
   └─> Frontend API service

2. Project Items (UPDATED)
   ├─> Backend Model (add master_item_id FK)
   ├─> Backend API (change create logic)
   ├─> Frontend Page (change from create to select)
   └─> Frontend API (update schemas)

3. Procurement (UPDATED)
   ├─> Backend API (join with master for details)
   ├─> Frontend (show master + project info)
   └─> Display logic updated

4. Optimization (UNCHANGED)
   ├─> Uses item_code (string)
   └─> No changes needed!

5. Finalized Decisions (UNCHANGED)
   ├─> Uses item_code (string)
   └─> No changes needed!

6. Cashflow Events (UNCHANGED)
   ├─> Indirect reference
   └─> No changes needed!

7. Excel Import/Export (UPDATED)
   ├─> Items Master: New templates
   ├─> Project Items: Update templates
   └─> Backward compatibility maintained
```

---

## 📝 **Implementation Steps:**

### **Phase 1: Backend - Items Master** ✅ (Priority)
1. Create `ItemsMaster` model in `models.py`
2. Create schemas in `schemas.py`
3. Create CRUD operations in `crud.py`
4. Create router `routers/items_master.py`
5. Add Excel import/export for items master
6. Register router in `main.py`

### **Phase 2: Backend - Update Project Items** ✅
1. Add `master_item_id` to `ProjectItem` model
2. Update `ProjectItem` schemas
3. Update create/update logic in `routers/items.py`
4. Update procurement router to join with master

### **Phase 3: Database Migration** ✅
1. Create migration SQL to add `items_master` table
2. Create migration SQL to add `master_item_id` to `project_items`
3. Create data migration script (existing items → master)
4. Create rollback script (safety)

### **Phase 4: Frontend - Items Master Page** ✅
1. Create `ItemsMasterPage.tsx`
2. Add to navigation (admin, pm, finance only)
3. CRUD interface
4. Excel import/export
5. Auto-generate item code on form

### **Phase 5: Frontend - Update Project Items** ✅
1. Change from text input to dropdown selection
2. Fetch items from master
3. Add description field (project-specific)
4. Update form logic

### **Phase 6: Frontend - Update Procurement** ✅
1. Show master item details
2. Show project-specific description
3. Label: "Project Context" or "Quantity: 50 - [description]"

### **Phase 7: Testing** ✅
1. Test item master CRUD
2. Test project item selection
3. Test procurement view
4. Test optimization (no changes needed)
5. Test finalized decisions (no changes needed)
6. Test complete workflow
7. Test Excel import/export

### **Phase 8: Documentation** ✅
1. User guide for Items Master
2. Migration guide
3. Updated workflow documentation
4. API documentation

---

## 🎯 **Item Code Generation:**

### **Format:**
```
{COMPANY}-{NAME}-{MODEL}
```

### **Examples:**
```
Company: "ACME"
Name: "Steel Beam"
Model: "A36"
→ Item Code: "ACME-STEEL-BEAM-A36"

Company: "TechCo"
Name: "Electrical Cable"
Model: "10mm²"
→ Item Code: "TECHCO-ELECTRICAL-CABLE-10MM2"
```

### **Generation Rules:**
- Uppercase all parts
- Replace spaces with hyphens
- Remove special characters (keep alphanumeric + hyphen)
- Limit length to 100 chars
- Ensure uniqueness (database constraint)

### **Implementation:**
```python
def generate_item_code(company: str, item_name: str, model: str = "") -> str:
    """Generate unique item code"""
    import re
    
    # Clean and uppercase
    company_clean = re.sub(r'[^A-Z0-9]+', '', company.upper())
    name_clean = re.sub(r'[^A-Z0-9]+', '-', item_name.upper()).strip('-')
    model_clean = re.sub(r'[^A-Z0-9]+', '', model.upper()) if model else ""
    
    # Combine
    if model_clean:
        code = f"{company_clean}-{name_clean}-{model_clean}"
    else:
        code = f"{company_clean}-{name_clean}"
    
    # Limit length
    return code[:100]
```

---

## 📊 **Data Separation:**

### **Items Master (Standard Catalog):**
```json
{
  "item_code": "ACME-STEEL-BEAM-A36",
  "company": "ACME",
  "item_name": "Steel Beam",
  "model": "A36",
  "specifications": {
    "length": "10m",
    "cross_section": "H-beam 300x300mm",
    "weight": "450kg",
    "coating": "Hot-dip galvanized",
    "standard": "ASTM A36/A36M"
  },
  "category": "Construction",
  "unit": "piece"
}
```

### **Project Items (Project-Specific Usage):**
```json
{
  "master_item_id": 1,
  "item_code": "ACME-STEEL-BEAM-A36",  // Denormalized from master
  "item_name": "Steel Beam",            // Denormalized from master
  "project_id": 5,
  "quantity": 50,
  "description": "For ground floor columns, north wing, installation date Feb 15",  // Project-specific!
  "delivery_options": ["2025-02-15", "2025-03-01"]
}
```

### **Procurement View (Combined):**
```
📦 ACME-STEEL-BEAM-A36

Master Item Info:
├─ Company: ACME
├─ Name: Steel Beam
├─ Model: A36
├─ Specs: Length 10m, H-beam 300x300mm...

Project Context (Qty: 50 units):
└─ Description: "For ground floor columns, north wing, installation date Feb 15"
```

---

## 🔗 **Dependency Chain:**

### **Forward References (Who uses Items Master):**
```
Items Master (id, item_code)
    ↓ (FK: master_item_id)
Project Items (master_item_id)
    ↓ (string: item_code)
Procurement Options (item_code)
    ↓ (FK: procurement_option_id)
Finalized Decisions (item_code)
    ↓ (FK: related_decision_id)
Cashflow Events
```

### **What Breaks If Not Handled:**
- ✅ Procurement: Must join with master + project for full info
- ✅ Project Items: Must select from master (not free text)
- ✅ Item Code: Must come from master (generated)
- ✅ Excel Import: Must reference master items
- ✅ Optimization: Uses item_code (no change needed!)
- ✅ Decisions: Uses item_code (no change needed!)

---

## 📦 **Migration Strategy:**

### **Step 1: Create items_master table**
```sql
CREATE TABLE items_master (
    id SERIAL PRIMARY KEY,
    item_code VARCHAR(100) UNIQUE NOT NULL,
    company VARCHAR(100) NOT NULL,
    item_name VARCHAR(200) NOT NULL,
    model VARCHAR(100),
    specifications JSONB,
    category VARCHAR(100),
    unit VARCHAR(50) DEFAULT 'piece',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    created_by_id INT REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE
);
```

### **Step 2: Migrate existing data**
```sql
-- Insert unique items from project_items into items_master
INSERT INTO items_master (item_code, company, item_name, model, is_active)
SELECT DISTINCT 
    item_code,
    'LEGACY' as company,  -- Default company
    COALESCE(item_name, item_code) as item_name,
    '' as model,
    true as is_active
FROM project_items
WHERE item_code NOT IN (SELECT item_code FROM items_master)
ON CONFLICT (item_code) DO NOTHING;
```

### **Step 3: Add master_item_id to project_items**
```sql
ALTER TABLE project_items
ADD COLUMN master_item_id INT REFERENCES items_master(id) ON DELETE RESTRICT;

-- Link existing project items to master
UPDATE project_items pi
SET master_item_id = (
    SELECT id FROM items_master
    WHERE item_code = pi.item_code
    LIMIT 1
);

-- Make it required after migration (optional)
-- ALTER TABLE project_items ALTER COLUMN master_item_id SET NOT NULL;
```

### **Step 4: Data cleanup**
```sql
-- Move generic descriptions to master
-- Keep project-specific descriptions in project_items
-- (Manual review recommended)
```

---

## 🎨 **New Pages:**

### **1. Items Master Page**
```
┌────────────────────────────────────────┐
│ Items Master Catalog                   │
│ [➕ Create Item] [📥 Template]        │
│ [📤 Import] [📊 Export]               │
├────────────────────────────────────────┤
│                                        │
│ ┌──────────────────────────────────┐  │
│ │ Code | Company | Name | Model    │  │
│ │──────┼─────────┼──────┼──────────│  │
│ │ ACME-│  ACME   │Steel │   A36    │  │
│ │ STEEL│         │Beam  │          │  │
│ │──────┼─────────┼──────┼──────────│  │
│ │ TECH-│ TechCo  │Cable │  10mm²   │  │
│ │ CABLE│         │      │          │  │
│ └──────────────────────────────────┘  │
└────────────────────────────────────────┘

Create Dialog:
┌────────────────────────────────┐
│ Create Master Item             │
├────────────────────────────────┤
│ Company: [___________]         │
│ Item Name: [___________]       │
│ Model: [___________]           │
│                                │
│ Generated Code:                │
│ ACME-STEEL-BEAM-A36           │ ← Auto-generated!
│                                │
│ Category: [___________]        │
│ Unit: [piece ▼]               │
│                                │
│ [Cancel] [Create Item]         │
└────────────────────────────────┘
```

### **2. Updated Project Items Page**
```
Add Item Dialog:
┌────────────────────────────────┐
│ Add Item to Project            │
├────────────────────────────────┤
│ Select Item:                   │
│ [ACME-STEEL-BEAM-A36 ▼]      │ ← Dropdown from master
│                                │
│ 📦 Selected Item:              │
│ Company: ACME                  │
│ Name: Steel Beam               │
│ Model: A36                     │
│                                │
│ Quantity: [___]                │
│                                │
│ Project Description:           │ ← NEW label
│ ┌──────────────────────────┐  │
│ │ For ground floor columns,│  │
│ │ north wing, special      │  │
│ │ handling required        │  │
│ └──────────────────────────┘  │
│                                │
│ Delivery Dates: [...]          │
│                                │
│ [Cancel] [Add to Project]      │
└────────────────────────────────┘
```

### **3. Updated Procurement View**
```
Add Procurement Option Dialog:
┌────────────────────────────────┐
│ Add Procurement Option         │
├────────────────────────────────┤
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ 📦 ACME-STEEL-BEAM-A36   ┃ │
│ ┃ Company: ACME            ┃ │ ← From master
│ ┃ Name: Steel Beam         ┃ │
│ ┃ Model: A36               ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                │
│ 💬 Project Context (Qty: 50): │ ← From project
│ "For ground floor columns,     │
│  north wing, special handling" │
│                                │
│ Supplier Name: [___]           │
│ ...                            │
└────────────────────────────────┘
```

---

## 🎯 **Excel Templates:**

### **Items Master Template:**
```excel
| company | item_name    | model | category      | unit  | specifications |
|---------|--------------|-------|---------------|-------|----------------|
| ACME    | Steel Beam   | A36   | Construction  | piece | {"length":"10m"}|
| TechCo  | Cable        | 10mm² | Electrical    | meter | {"copper":true} |
```

**Item code auto-generated on import!**

### **Updated Project Items Template:**
```excel
| project_id | item_code              | quantity | description                | delivery_options |
|------------|------------------------|----------|----------------------------|------------------|
| 1          | ACME-STEEL-BEAM-A36   | 50       | For ground floor columns   | 2025-01-15,...  |
| 1          | TECHCO-CABLE-10MM2    | 100      | Main electrical panel      | 2025-02-01      |
```

**Must use existing item codes from Items Master!**

---

## 🔐 **Permissions:**

### **Items Master:**
- **Create:** Admin, PM, Finance
- **Read:** All users
- **Update:** Admin, PM, Finance
- **Delete:** Admin only (with safety checks)

### **Why PM Can Create Items:**
- PM knows project needs
- Can define new items during planning
- Standardizes items for organization

---

## ⚠️ **Breaking Changes:**

### **None! (Backward Compatible)**

**Why?**
- `project_items.item_code` remains (denormalized)
- Procurement uses `item_code` string (works as before)
- Optimization uses `item_code` string (works as before)
- Decisions use `item_code` string (works as before)

**Migration:**
- Existing data converted to master items
- Existing relationships preserved
- No data loss

---

## 📊 **Benefits:**

### **For Organization:**
- ✅ **Standardized catalog** of all items
- ✅ **Unique codes** generated by system
- ✅ **Consistent naming** across projects
- ✅ **Centralized management**
- ✅ **Reusable items** across projects

### **For Project Managers:**
- ✅ **Select from catalog** (no typos)
- ✅ **Add project-specific context** in description
- ✅ **Faster item addition** (no need to define specs)
- ✅ **Consistent items** across projects

### **For Procurement:**
- ✅ **Standard item specs** from master
- ✅ **Project context** from project items
- ✅ **Complete information** for quotes
- ✅ **Better quotes** with full specs

### **For Finance:**
- ✅ **Accurate optimization** with standard items
- ✅ **Better reporting** (group by item)
- ✅ **Cost tracking** by item across projects

---

## 🚀 **Implementation Timeline:**

| Phase | Tasks | Time | Priority |
|-------|-------|------|----------|
| **1. Backend - Master** | Model, API, CRUD, Excel | 2 hours | High |
| **2. Backend - Project Items** | Update model, API | 1 hour | High |
| **3. Migration** | SQL scripts, data migration | 1 hour | Critical |
| **4. Frontend - Master** | Page, forms, Excel | 2 hours | High |
| **5. Frontend - Project** | Update selection | 1 hour | High |
| **6. Frontend - Procurement** | Update display | 30 min | Medium |
| **7. Testing** | Full workflow test | 1 hour | Critical |
| **8. Documentation** | Guides, migration docs | 30 min | Medium |

**Total Estimated Time:** 9 hours
**Critical Path:** Backend → Migration → Frontend

---

## ✅ **Success Criteria:**

### **Must Work:**
1. ✅ Create item in master with auto-generated code
2. ✅ Select master item when adding to project
3. ✅ Add project-specific description
4. ✅ Procurement sees both master + project info
5. ✅ Optimization works (uses item_code)
6. ✅ Decisions work (uses item_code)
7. ✅ Excel import/export for both
8. ✅ Existing data migrated
9. ✅ No data loss
10. ✅ Backward compatible

---

## 🎊 **Next Steps:**

I'll now implement this in order:

1. **Backend Models & API** (Items Master)
2. **Database Migration** (Add tables/columns)
3. **Frontend Pages** (Items Master, Update Project Items)
4. **Integration** (Procurement, Excel, etc.)
5. **Testing & Documentation**

**Ready to proceed with implementation?**

This is a major improvement that will make your system much more professional and maintainable!

---

**Let me start implementing now...**

