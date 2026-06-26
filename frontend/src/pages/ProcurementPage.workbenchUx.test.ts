import fs from 'fs';
import path from 'path';

describe('procurement assignment workbench UX (5E-R2)', () => {
  const managementSource = fs.readFileSync(
    path.join(__dirname, '../components/procurement/ProcurementAssignmentManagementPanel.tsx'),
    'utf8'
  );
  const projectViewSource = fs.readFileSync(
    path.join(__dirname, '../components/procurement/ProcurementAssignmentProjectView.tsx'),
    'utf8'
  );
  const itemViewSource = fs.readFileSync(
    path.join(__dirname, '../components/procurement/ProcurementAssignmentItemView.tsx'),
    'utf8'
  );
  const projectItemsSource = fs.readFileSync(
    path.join(__dirname, 'ProjectItemsPage.tsx'),
    'utf8'
  );

  it('does not expose complete assignment as a primary management action', () => {
    expect(managementSource).not.toContain('handleComplete');
    expect(managementSource).not.toContain('completeDialogOpen');
    expect(managementSource).not.toContain('CompleteIcon');
    expect(managementSource).not.toContain('procurementAssignmentsAPI.complete');
    expect(projectViewSource).not.toContain('completeAssignment');
    expect(itemViewSource).not.toContain('completeAssignment');
  });

  it('includes workbench view modes and finalization helper text', () => {
    expect(managementSource).toContain('viewByProject');
    expect(managementSource).toContain('viewByItem');
    expect(managementSource).toContain('finalizationHint');
    expect(managementSource).toContain('ProcurementAssignmentProjectView');
    expect(managementSource).toContain('ProcurementAssignmentItemView');
  });

  it('uses bulk cancel for remove selected assignments', () => {
    expect(managementSource).toContain('cancelAssignmentsInBulk');
    expect(managementSource).toContain('removeSelectedAssignments');
    expect(managementSource).toContain('procurementAssignmentsAPI.cancel');
  });

  it('supports assign all project items via bulk create', () => {
    expect(managementSource).toContain('handleAssignAllItems');
    expect(managementSource).toContain('bulkCreate');
    expect(projectViewSource).toContain('assignAllProjectItems');
    expect(projectViewSource).toContain('projectLevelPartialRemovalHint');
  });

  it('keeps project items as summary-only surface', () => {
    expect(projectItemsSource).toContain('ProjectAssignmentSummaryPanel');
    expect(projectItemsSource).not.toContain('ProcurementAssignmentManagementPanel');
  });
});
