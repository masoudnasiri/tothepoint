-- Sprint 5D: procurement assignment table (ADR-011)
-- Safe to run multiple times (IF NOT EXISTS)

CREATE TABLE IF NOT EXISTS procurement_assignments (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    project_item_id INTEGER REFERENCES project_items(id) ON DELETE CASCADE,
    assignee_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    assigned_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    assignment_scope VARCHAR(32) NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    cancelled_reason TEXT,
    CONSTRAINT chk_procurement_assignment_status
        CHECK (status IN ('active', 'completed', 'cancelled')),
    CONSTRAINT chk_procurement_assignment_scope
        CHECK (assignment_scope IN ('project', 'project_item')),
    CONSTRAINT chk_procurement_assignment_scope_item
        CHECK (
            (assignment_scope = 'project' AND project_item_id IS NULL)
            OR (assignment_scope = 'project_item' AND project_item_id IS NOT NULL)
        )
);

CREATE INDEX IF NOT EXISTS ix_procurement_assignments_project_id
    ON procurement_assignments(project_id);
CREATE INDEX IF NOT EXISTS ix_procurement_assignments_project_item_id
    ON procurement_assignments(project_item_id);
CREATE INDEX IF NOT EXISTS ix_procurement_assignments_assignee_user_id
    ON procurement_assignments(assignee_user_id);
CREATE INDEX IF NOT EXISTS ix_procurement_assignments_status
    ON procurement_assignments(status);
CREATE INDEX IF NOT EXISTS ix_procurement_assignments_assignment_scope
    ON procurement_assignments(assignment_scope);

-- Prevent duplicate active assignments (Postgres partial unique index)
CREATE UNIQUE INDEX IF NOT EXISTS uq_procurement_assignments_active_project
    ON procurement_assignments (project_id, assignee_user_id)
    WHERE status = 'active' AND assignment_scope = 'project';

CREATE UNIQUE INDEX IF NOT EXISTS uq_procurement_assignments_active_item
    ON procurement_assignments (project_id, project_item_id, assignee_user_id)
    WHERE status = 'active' AND assignment_scope = 'project_item';
