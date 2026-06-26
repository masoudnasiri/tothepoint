import fs from 'fs';
import path from 'path';

describe('procurement assignment UX relocation (5E-R1)', () => {
  const projectItemsSource = fs.readFileSync(
    path.join(__dirname, 'ProjectItemsPage.tsx'),
    'utf8'
  );
  const procurementSource = fs.readFileSync(
    path.join(__dirname, 'ProcurementPage.tsx'),
    'utf8'
  );
  const summarySource = fs.readFileSync(
    path.join(__dirname, '../components/procurement/ProjectAssignmentSummaryPanel.tsx'),
    'utf8'
  );

  it('does not mount the old project-items assignment management panel', () => {
    expect(projectItemsSource).not.toContain('ProcurementAssignmentsPanel');
    expect(projectItemsSource).not.toContain('assignSelectedItems');
    expect(projectItemsSource).toContain('ProjectAssignmentSummaryPanel');
    expect(summarySource).toContain('procurementAssignments.manageInProcurement');
  });

  it('places assignment management inside Procurement page', () => {
    expect(procurementSource).toContain('ProcurementAssignmentManagementPanel');
    expect(procurementSource).toContain("value: 'operations' | 'assignments'");
    expect(procurementSource).toContain('procurementAssignments.title');
  });

  it('keeps My Assignments available for view-only users on Procurement tab', () => {
    expect(procurementSource).toContain('MyProcurementAssignmentsPanel');
    expect(procurementSource).toContain('showAssignmentManagement');
  });
});
