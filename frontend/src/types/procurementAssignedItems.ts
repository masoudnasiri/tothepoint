export interface ProcurementAssignedItemAssignmentInfo {
  assignment_id: number;
  assignment_scope: 'project' | 'project_item';
  assignment_status: string;
  assignee_user_id: number;
  assignee_username?: string | null;
}

export interface ProcurementAssignedItemSummary {
  project_id: number;
  project_code: string;
  project_name: string;
  project_item_id: number;
  item_code: string;
  item_name?: string | null;
  description?: string | null;
  quantity: number;
  delivery_options: string[];
  item_status?: string | null;
  external_purchase: boolean;
  is_finalized: boolean;
  covered_by_project_assignment: boolean;
  assignments: ProcurementAssignedItemAssignmentInfo[];
}
