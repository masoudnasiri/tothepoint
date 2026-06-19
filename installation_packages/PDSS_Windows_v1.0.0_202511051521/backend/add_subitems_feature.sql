    -- Phase 1: Sub-items Feature Migration

    -- Step 1: Add part_number to items_master table
    ALTER TABLE items_master
    ADD COLUMN IF NOT EXISTS part_number TEXT;

    COMMENT ON COLUMN items_master.part_number IS 'Part number for the master item';

    -- Step 2: Create item_subitems table
    CREATE TABLE IF NOT EXISTS item_subitems (
        id SERIAL PRIMARY KEY,
        item_master_id INTEGER NOT NULL REFERENCES items_master(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT,
        part_number TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_item_subitems_item_master_id ON item_subitems(item_master_id);

    COMMENT ON TABLE item_subitems IS 'Stores sub-items linked to a master item.';
    COMMENT ON COLUMN item_subitems.item_master_id IS 'Foreign key to the parent item in items_master.';

    -- Step 3: Create project_item_subitems table
    CREATE TABLE IF NOT EXISTS project_item_subitems (
        id SERIAL PRIMARY KEY,
        project_item_id INTEGER NOT NULL REFERENCES project_items(id) ON DELETE CASCADE,
        item_subitem_id INTEGER NOT NULL REFERENCES item_subitems(id) ON DELETE CASCADE,
        quantity INTEGER NOT NULL DEFAULT 0,
        UNIQUE (project_item_id, item_subitem_id) -- Ensures a sub-item is not duplicated for the same project item
    );

    CREATE INDEX IF NOT EXISTS idx_project_item_subitems_project_item_id ON project_item_subitems(project_item_id);
    CREATE INDEX IF NOT EXISTS idx_project_item_subitems_item_subitem_id ON project_item_subitems(item_subitem_id);

    COMMENT ON TABLE project_item_subitems IS 'Stores the quantity of each sub-item for a specific project item.';
    COMMENT ON COLUMN project_item_subitems.project_item_id IS 'Foreign key to the specific item instance in a project.';
    COMMENT ON COLUMN project_item_subitems.item_subitem_id IS 'Foreign key to the sub-item definition.';
    COMMENT ON COLUMN project_item_subitems.quantity IS 'Quantity of the sub-item required for this project item.';

    -- End of migration
