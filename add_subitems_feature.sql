-- Add Sub-Items Feature Migration
-- 1) Add part_number to items_master
ALTER TABLE items_master
    ADD COLUMN IF NOT EXISTS part_number TEXT NULL;

-- 2) Create item_subitems table
CREATE TABLE IF NOT EXISTS item_subitems (
    id SERIAL PRIMARY KEY,
    item_master_id INTEGER NOT NULL REFERENCES items_master(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NULL,
    part_number TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS idx_item_subitems_master ON item_subitems(item_master_id);

-- 3) Create project_item_subitems table
CREATE TABLE IF NOT EXISTS project_item_subitems (
    id SERIAL PRIMARY KEY,
    project_item_id INTEGER NOT NULL REFERENCES project_items(id) ON DELETE CASCADE,
    item_subitem_id INTEGER NOT NULL REFERENCES item_subitems(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_proj_subitems_project ON project_item_subitems(project_item_id);
CREATE INDEX IF NOT EXISTS idx_proj_subitems_sub ON project_item_subitems(item_subitem_id);

-- 4) Trigger to update updated_at on item_subitems
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'set_item_subitems_updated_at'
    ) THEN
        CREATE OR REPLACE FUNCTION set_item_subitems_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_item_subitems_updated_at'
    ) THEN
        CREATE TRIGGER trg_item_subitems_updated_at
        BEFORE UPDATE ON item_subitems
        FOR EACH ROW
        EXECUTE FUNCTION set_item_subitems_updated_at();
    END IF;
END$$;


