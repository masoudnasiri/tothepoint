import fs from 'fs';
import path from 'path';

describe('secure procurement assigned item visibility (5E-R2-Fix)', () => {
  const myAssignmentsSource = fs.readFileSync(
    path.join(__dirname, '../components/procurement/MyProcurementAssignmentsPanel.tsx'),
    'utf8'
  );
  const assignedDialogSource = fs.readFileSync(
    path.join(__dirname, '../components/procurement/AssignedProcurementItemsDialog.tsx'),
    'utf8'
  );
  const appSource = fs.readFileSync(path.join(__dirname, '../App.tsx'), 'utf8');
  const permissionsSource = fs.readFileSync(
    path.join(__dirname, '../utils/permissions.ts'),
    'utf8'
  );
  const projectItemsSource = fs.readFileSync(
    path.join(__dirname, 'ProjectItemsPage.tsx'),
    'utf8'
  );

  it('gates open project items link behind project item management permission', () => {
    expect(myAssignmentsSource).toContain('canViewProjectItems(user) ? (');
    expect(myAssignmentsSource).toContain('viewAssignedItems');
    expect(myAssignmentsSource).toContain('openProjectItems');
    expect(myAssignmentsSource).toContain('AssignedProcurementItemsDialog');
  });

  it('uses sanitized assigned-items API in read-only dialog', () => {
    expect(assignedDialogSource).toContain('listProjectAssignedItems');
    expect(assignedDialogSource).toContain('listMyAssignedItems');
    expect(assignedDialogSource).not.toContain('itemsAPI');
    expect(assignedDialogSource).not.toContain('AddIcon');
    expect(assignedDialogSource).not.toContain('EditIcon');
    expect(assignedDialogSource).not.toContain('DeleteIcon');
    expect(assignedDialogSource).not.toContain('FinalizeIcon');
    expect(assignedDialogSource).not.toContain('sale_price');
    expect(assignedDialogSource).not.toContain('customer_price');
  });

  it('wraps project items route with permission guard', () => {
    expect(appSource).toContain('ProjectItemsRoute');
    expect(permissionsSource).toContain('canViewProjectItems');
  });

  it('preserves assignment workbench surfaces from 5E-R2', () => {
    const managementSource = fs.readFileSync(
      path.join(__dirname, '../components/procurement/ProcurementAssignmentManagementPanel.tsx'),
      'utf8'
    );
    expect(managementSource).toContain('viewByProject');
    expect(managementSource).toContain('viewByItem');
    expect(managementSource).toContain('removeSelectedAssignments');
    expect(projectItemsSource).toContain('ProjectAssignmentSummaryPanel');
    expect(projectItemsSource).not.toContain('ProcurementAssignmentManagementPanel');
  });
});
