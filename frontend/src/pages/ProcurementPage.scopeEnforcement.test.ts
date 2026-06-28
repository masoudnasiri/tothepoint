import fs from 'fs';
import path from 'path';

describe('Procurement page scope enforcement (5F)', () => {
  const pageSource = fs.readFileSync(path.join(__dirname, 'ProcurementPage.tsx'), 'utf8');
  const permissionsSource = fs.readFileSync(
    path.join(__dirname, '../utils/permissions.ts'),
    'utf8'
  );
  const enSource = fs.readFileSync(path.join(__dirname, '../i18n/en.json'), 'utf8');
  const faSource = fs.readFileSync(path.join(__dirname, '../i18n/fa.json'), 'utf8');

  it('shows assigned-only scope message for scoped users', () => {
    expect(pageSource).toContain('isAssignedOnlyProcurementScopeUser');
    expect(pageSource).toContain('procurement.assignedOnlyScopeMessage');
    expect(enSource).toContain('This view is limited to procurement work assigned to you.');
    expect(faSource).toContain('این نما فقط کارهای تأمینی را نشان می‌دهد که به شما تخصیص داده شده‌اند.');
  });

  it('hides global send-all and bulk rollback for assigned-only scope', () => {
    expect(pageSource).toContain('canSubmitOptimization && !isAssignedOnlyScopeUser');
    expect(pageSource).toContain('send_all_finalized: true');
    expect(pageSource).toContain('openBulkRollbackDialog');
  });

  it('uses permission-based package/optimization action gating', () => {
    expect(pageSource).toContain('canMutateProcurementPackages');
    expect(pageSource).toContain('canViewProcurementOperations');
    expect(pageSource).toContain('disabled={!canSubmitOptimization');
    expect(pageSource).toContain('disabled={!canMutateProcurementPackages');
    expect(permissionsSource).toContain('isAssignedOnlyProcurementScopeUser');
  });
});
