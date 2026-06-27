import {
  canCancelProcurementAssignments,
  canCreateProcurementAssignments,
  canDeleteProcurementAssignments,
  canEditProcurementAssignments,
  canManageProcurementAssignments,
  canViewAllProcurementAssignments,
  canViewProcurementAssignments,
  canCompleteProcurementAssignments,
} from './permissions.ts';

const adminUser = {
  id: 1,
  username: 'admin',
  role: 'admin',
  created_at: '',
  is_active: true,
};

const procViewUser = {
  id: 2,
  username: 'proc',
  role: 'procurement',
  created_at: '',
  is_active: true,
  permissions: ['procurement.assignments.view'],
};

const pmoUser = {
  id: 3,
  username: 'pmo',
  role: 'pmo',
  created_at: '',
  is_active: true,
  permissions: [
    'procurement.assignments.view',
    'procurement.assignments.create',
    'procurement.assignments.edit',
    'procurement.assignments.complete',
    'procurement.assignments.cancel',
  ],
};

const financeUser = {
  id: 4,
  username: 'fin',
  role: 'finance',
  created_at: '',
  is_active: true,
  permissions: ['finance.view'],
};

const accessControlAdminUser = {
  id: 5,
  username: 'ac_admin',
  role: 'pm',
  created_at: '',
  is_active: true,
  permissions: [
    'access_control.roles.view',
    'access_control.roles.manage',
    'access_control.permissions.manage',
    'access_control.user_roles.edit',
  ],
};

describe('procurement assignment permissions', () => {
  it('allows admin legacy bypass', () => {
    expect(canViewProcurementAssignments(adminUser)).toBe(true);
    expect(canCreateProcurementAssignments(adminUser)).toBe(true);
    expect(canManageProcurementAssignments(adminUser)).toBe(true);
  });

  it('allows view-only procurement specialist', () => {
    expect(canViewProcurementAssignments(procViewUser)).toBe(true);
    expect(canCreateProcurementAssignments(procViewUser)).toBe(false);
    expect(canViewAllProcurementAssignments(procViewUser)).toBe(false);
  });

  it('allows PMO manager permissions', () => {
    expect(canCreateProcurementAssignments(pmoUser)).toBe(true);
    expect(canEditProcurementAssignments(pmoUser)).toBe(true);
    expect(canCompleteProcurementAssignments(pmoUser)).toBe(true);
    expect(canCancelProcurementAssignments(pmoUser)).toBe(true);
    expect(canViewAllProcurementAssignments(pmoUser)).toBe(true);
  });

  it('denies finance user without assignment keys', () => {
    expect(canViewProcurementAssignments(financeUser)).toBe(false);
    expect(canDeleteProcurementAssignments(financeUser)).toBe(false);
    expect(canManageProcurementAssignments(financeUser)).toBe(false);
  });

  it('denies access-control admin from assignment actions without explicit assignment keys', () => {
    expect(canViewProcurementAssignments(accessControlAdminUser)).toBe(false);
    expect(canCancelProcurementAssignments(accessControlAdminUser)).toBe(false);
    expect(canManageProcurementAssignments(accessControlAdminUser)).toBe(false);
  });
});
