import {
  cancelAssignmentsInBulk,
  getAssignableProjectItemIds,
  groupAssignmentsByProject,
  isProjectItemAssignableForAssignment,
  isSelectableForRemoval,
  summarizeProjectAssignments,
} from './procurementAssignmentWorkbenchUtils.ts';
import type { ProcurementAssignment } from '../types/procurementAssignments.ts';

const baseAssignment = (overrides: Partial<ProcurementAssignment>): ProcurementAssignment => ({
  id: 1,
  project_id: 10,
  project_item_id: null,
  assignee_user_id: 2,
  assigned_by_user_id: 3,
  status: 'active',
  assignment_scope: 'project',
  created_at: '2026-01-01T00:00:00Z',
  ...overrides,
});

describe('procurementAssignmentWorkbenchUtils', () => {
  it('groups assignments by project', () => {
    const grouped = groupAssignmentsByProject([
      baseAssignment({ id: 1, project_id: 10 }),
      baseAssignment({ id: 2, project_id: 20 }),
      baseAssignment({ id: 3, project_id: 10, assignment_scope: 'project_item', project_item_id: 5 }),
    ]);
    expect(Object.keys(grouped)).toEqual(['10', '20']);
    expect(grouped[10]).toHaveLength(2);
  });

  it('summarizes project assignments', () => {
    const summary = summarizeProjectAssignments(10, [
      baseAssignment({ id: 1, assignment_scope: 'project' }),
      baseAssignment({
        id: 2,
        assignment_scope: 'project_item',
        project_item_id: 5,
        assignee_user_id: 4,
      }),
      baseAssignment({ id: 3, status: 'cancelled', assignment_scope: 'project_item', project_item_id: 6 }),
    ]);
    expect(summary.activeCount).toBe(2);
    expect(summary.itemAssignmentCount).toBe(1);
    expect(summary.projectLevelAssignments).toHaveLength(1);
  });

  it('allows removal selection only for active assignments', () => {
    expect(isSelectableForRemoval(baseAssignment({ status: 'active' }))).toBe(true);
    expect(isSelectableForRemoval(baseAssignment({ status: 'completed' }))).toBe(false);
    expect(isSelectableForRemoval(baseAssignment({ status: 'cancelled' }))).toBe(false);
  });

  it('treats rows with active assignment as not assignable', () => {
    const assignments: ProcurementAssignment[] = [
      baseAssignment({
        id: 10,
        project_id: 50,
        assignment_scope: 'project_item',
        project_item_id: 501,
        status: 'active',
      }),
      baseAssignment({
        id: 11,
        project_id: 50,
        assignment_scope: 'project_item',
        project_item_id: 502,
        status: 'cancelled',
      }),
    ];
    expect(isProjectItemAssignableForAssignment(50, 501, assignments)).toBe(false);
    expect(isProjectItemAssignableForAssignment(50, 502, assignments)).toBe(true);
  });

  it('treats active project-level assignment as non-assignable for all rows', () => {
    const assignments: ProcurementAssignment[] = [
      baseAssignment({
        id: 12,
        project_id: 90,
        assignment_scope: 'project',
        project_item_id: null,
        status: 'active',
      }),
      baseAssignment({
        id: 13,
        project_id: 90,
        assignment_scope: 'project_item',
        project_item_id: 901,
        status: 'cancelled',
      }),
    ];
    expect(getAssignableProjectItemIds(90, [901, 902], assignments)).toEqual([]);
  });

  it('cancels assignments in bulk with partial failure summary', async () => {
    const cancelFn = jest
      .fn()
      .mockResolvedValueOnce({})
      .mockRejectedValueOnce(new Error('fail'));

    const result = await cancelAssignmentsInBulk([1, 2], 'reason', cancelFn);
    expect(result.successCount).toBe(1);
    expect(result.failureCount).toBe(1);
    expect(result.failedIds).toEqual([2]);
    expect(cancelFn).toHaveBeenCalledTimes(2);
  });
});
