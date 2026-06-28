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
  const enSource = fs.readFileSync(path.join(__dirname, '../i18n/en.json'), 'utf8');
  const faSource = fs.readFileSync(path.join(__dirname, '../i18n/fa.json'), 'utf8');
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
    expect(managementSource).toContain('finalizedOnlyItemAssignmentHint');
    expect(managementSource).toContain('ProcurementAssignmentProjectView');
    expect(managementSource).toContain('ProcurementAssignmentItemView');
  });

  it('uses bulk cancel for remove selected assignments', () => {
    expect(managementSource).toContain('cancelAssignmentsInBulk');
    expect(managementSource).toContain('canCancel && selectedRemovableCount > 0');
    expect(managementSource).toContain('removeSelectedAssignments');
    expect(managementSource).toContain('procurementAssignmentsAPI.cancel');
    expect(managementSource).toContain('selectedAssignableItemsCount');
    expect(managementSource).toContain('selectedRemovableAssignmentsCount');
    expect(managementSource).toContain('bulkRemoveFailedIds');
    expect(managementSource).toContain('removeSelectedConfirmCount');
  });

  it('supports assign all project items via bulk create', () => {
    expect(managementSource).toContain('handleAssignAllItems');
    expect(managementSource).toContain('bulkCreate');
    expect(managementSource).toContain('getAssignableProjectItemIds');
    expect(managementSource).toContain('noAssignableItemsSelected');
    expect(projectViewSource).toContain('assignAllFinalizedProjectItems');
    expect(projectViewSource).toContain('projectLevelPartialRemovalHint');
    expect(projectViewSource).toContain('noFinalizedItemsForItemAssignment');
    expect(managementSource).toContain('is_finalized: true');
  });

  it('supports project-level and item-level assignment removal selection', () => {
    expect(projectViewSource).toContain('summary.projectLevelAssignments.filter(isSelectableForRemoval)');
    expect(projectViewSource).toContain('onToggleAssignmentSelection(assignment.id)');
    expect(projectViewSource).toContain('disabled={!assignableForAssignment}');
    expect(itemViewSource).toContain('isSelectableForRemoval(row)');
  });

  it('keeps assignees, status, and remove action in separate table columns', () => {
    expect(projectViewSource).toContain("t('procurementAssignments.assignedProcurementUsers')");
    expect(projectViewSource).toContain("t('procurementAssignments.assignmentStatus')");
    expect(projectViewSource).toContain("t('procurement.actions')");
    expect(projectViewSource).toContain("key={`remove-${assignment.id}`}");

    const assigneeColumnBlock = projectViewSource.match(
      /<TableCell sx=\{\{ textAlign: isFa \? 'right' : 'left', verticalAlign: 'top' \}\}>[\s\S]*?itemAssignments\.map\(\(assignment\) => \([\s\S]*?<\/TableCell>/
    );
    expect(assigneeColumnBlock?.[0]).toBeTruthy();
    expect(assigneeColumnBlock?.[0]).not.toContain('onRemoveAssignment');

    expect(itemViewSource).toContain("t('procurement.actions')");
    expect(itemViewSource).toContain("t('procurementAssignments.assignedUser')");
    expect(itemViewSource).toContain("t('procurementAssignments.assignmentStatus')");
  });

  it('keeps project items as summary-only surface', () => {
    expect(projectItemsSource).toContain('ProjectAssignmentSummaryPanel');
    expect(projectItemsSource).not.toContain('ProcurementAssignmentManagementPanel');
  });

  it('uses finalized-only assignment wording in both locales', () => {
    expect(enSource).toContain('Assign all finalized project items');
    expect(enSource).toContain(
      'Only finalized project items are available for item-level procurement assignment.'
    );
    expect(enSource).toContain('No finalized items are available for item-level assignment yet.');
    expect(faSource).toContain('تخصیص همه اقلام نهایی‌شده پروژه');
    expect(faSource).toContain(
      'فقط اقلام نهایی‌شده پروژه برای تخصیص آیتمی تأمین نمایش داده می‌شوند.'
    );
    expect(faSource).toContain('هنوز هیچ قلم نهایی‌شده‌ای برای تخصیص آیتمی وجود ندارد.');
  });
});
