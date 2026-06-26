export type ProcurementAssignmentStatus = 'active' | 'completed' | 'cancelled';
export type ProcurementAssignmentScope = 'project' | 'project_item';

export interface ProcurementAssignment {
  id: number;
  project_id: number;
  project_item_id?: number | null;
  assignee_user_id: number;
  assigned_by_user_id: number;
  status: ProcurementAssignmentStatus;
  assignment_scope: ProcurementAssignmentScope;
  note?: string | null;
  created_at: string;
  updated_at?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
  cancelled_reason?: string | null;
}

export interface ProcurementAssignmentCreate {
  project_id: number;
  project_item_id?: number | null;
  assignee_user_id: number;
  note?: string | null;
}

export interface ProcurementAssignmentUpdate {
  note?: string | null;
}

export interface ProcurementAssignmentBulkCreate {
  project_id: number;
  assignee_user_ids: number[];
  project_item_ids?: number[] | null;
  note?: string | null;
}

export interface ProcurementAssignmentFilters {
  project_id?: number;
  project_item_id?: number;
  assignee_user_id?: number;
  status?: ProcurementAssignmentStatus;
  assignment_scope?: ProcurementAssignmentScope;
}
