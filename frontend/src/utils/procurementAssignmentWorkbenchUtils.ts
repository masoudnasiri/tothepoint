import type { ProjectItem } from '../../types/index.ts';
import type { ProcurementAssignment } from '../../types/procurementAssignments.ts';

export type WorkbenchViewMode = 'project' | 'item';

export interface ProjectAssignmentSummary {
  projectId: number;
  activeCount: number;
  itemAssignmentCount: number;
  projectLevelAssignments: ProcurementAssignment[];
  itemLevelAssignments: ProcurementAssignment[];
  assigneeIds: number[];
}

export function isActiveAssignment(assignment: ProcurementAssignment): boolean {
  return assignment.status === 'active';
}

export function isSelectableForRemoval(assignment: ProcurementAssignment): boolean {
  return isActiveAssignment(assignment);
}

export function groupAssignmentsByProject(
  assignments: ProcurementAssignment[]
): Record<number, ProcurementAssignment[]> {
  const grouped: Record<number, ProcurementAssignment[]> = {};
  assignments.forEach((assignment) => {
    if (!grouped[assignment.project_id]) {
      grouped[assignment.project_id] = [];
    }
    grouped[assignment.project_id].push(assignment);
  });
  return grouped;
}

export function summarizeProjectAssignments(
  projectId: number,
  assignments: ProcurementAssignment[]
): ProjectAssignmentSummary {
  const projectRows = assignments.filter((a) => a.project_id === projectId);
  const activeRows = projectRows.filter(isActiveAssignment);
  const projectLevelAssignments = projectRows.filter((a) => a.assignment_scope === 'project');
  const itemLevelAssignments = projectRows.filter((a) => a.assignment_scope === 'project_item');
  const assigneeIds = Array.from(new Set(activeRows.map((a) => a.assignee_user_id)));

  return {
    projectId,
    activeCount: activeRows.length,
    itemAssignmentCount: itemLevelAssignments.filter(isActiveAssignment).length,
    projectLevelAssignments,
    itemLevelAssignments,
    assigneeIds,
  };
}

export function assignmentsForProjectItem(
  assignments: ProcurementAssignment[],
  projectItemId: number
): ProcurementAssignment[] {
  return assignments.filter(
    (a) => a.assignment_scope === 'project_item' && a.project_item_id === projectItemId
  );
}

export function isProjectItemAssignableForAssignment(
  projectId: number,
  projectItemId: number,
  assignments: ProcurementAssignment[]
): boolean {
  const hasActiveProjectLevelAssignment = assignments.some(
    (assignment) =>
      assignment.project_id === projectId &&
      assignment.assignment_scope === 'project' &&
      isActiveAssignment(assignment)
  );
  if (hasActiveProjectLevelAssignment) {
    return false;
  }
  return !assignments.some(
    (assignment) =>
      assignment.project_id === projectId &&
      assignment.assignment_scope === 'project_item' &&
      assignment.project_item_id === projectItemId &&
      isActiveAssignment(assignment)
  );
}

export function getAssignableProjectItemIds(
  projectId: number,
  projectItemIds: number[],
  assignments: ProcurementAssignment[]
): number[] {
  return projectItemIds.filter((projectItemId) =>
    isProjectItemAssignableForAssignment(projectId, projectItemId, assignments)
  );
}

export function itemLabel(item: ProjectItem): string {
  return `${item.item_code} — ${item.item_name}`;
}

export interface BulkCancelResult {
  successCount: number;
  failureCount: number;
  failedIds: number[];
}

export async function cancelAssignmentsInBulk(
  assignmentIds: number[],
  reason: string,
  cancelFn: (id: number, payload: { cancelled_reason: string }) => Promise<unknown>
): Promise<BulkCancelResult> {
  let successCount = 0;
  let failureCount = 0;
  const failedIds: number[] = [];

  for (const id of assignmentIds) {
    try {
      await cancelFn(id, { cancelled_reason: reason });
      successCount += 1;
    } catch {
      failureCount += 1;
      failedIds.push(id);
    }
  }

  return { successCount, failureCount, failedIds };
}
