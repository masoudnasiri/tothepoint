import { useMemo } from 'react';
import type { User } from '../types/index.ts';

export const ACCESS_CONTROL_MANAGE_PERMISSION = 'access_control.roles.manage';

export const ACCESS_CONTROL_MANAGE_PERMISSIONS = [
  'access_control.roles.manage',
  'access_control.permissions.manage',
  'access_control.user_roles.edit',
] as const;

export function hasPermission(user: User | null | undefined, permissionKey: string): boolean {
  if (!user) return false;
  return Boolean(user.permissions?.includes(permissionKey));
}

export function hasAnyPermission(
  user: User | null | undefined,
  permissionKeys: readonly string[] | string[]
): boolean {
  if (!user?.permissions?.length) return false;
  return permissionKeys.some((key) => user.permissions!.includes(key));
}

function isLegacyAdmin(user: User | null | undefined): boolean {
  return user?.role === 'admin';
}

/** Mirrors backend access-control manager guard during RBAC transition. */
export function canManageAccessControl(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (user.permissions?.length) {
    return hasAnyPermission(user, ACCESS_CONTROL_MANAGE_PERMISSIONS);
  }
  return false;
}

export function canViewUsersSection(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'users.view');
}

export function canCreateUsers(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'users.create');
}

export function canEditUsers(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'users.edit');
}

export function canDeleteUsers(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'users.delete');
}

export function canViewUserRoleAssignment(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasAnyPermission(user, ['access_control.user_roles.view', 'access_control.user_roles.edit']);
}

export function canEditUserRoleAssignment(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, 'access_control.user_roles.edit');
}

export function canAccessUsersAccessControlSection(user: User | null | undefined): boolean {
  return (
    canViewUsersSection(user) ||
    canManageAccessControl(user) ||
    canViewUserRoleAssignment(user)
  );
}

/**
 * Sprint 5C-R1 pilot: Items Master / Suppliers use effective RBAC permissions.
 * Legacy base role does not grant write except explicit admin bypass.
 */
export function hasPilotPermission(user: User | null | undefined, permissionKey: string): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, permissionKey);
}

export function canViewItemsMaster(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.items.view');
}

export function canCreateItemsMaster(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.items.create');
}

export function canEditItemsMaster(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.items.edit');
}

export function canDeleteItemsMaster(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.items.delete');
}

export function canViewSuppliers(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.suppliers.view');
}

export function canCreateSuppliers(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.suppliers.create');
}

export function canEditSuppliers(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.suppliers.edit');
}

export function canDeleteSuppliers(user: User | null | undefined): boolean {
  return hasPilotPermission(user, 'master_data.suppliers.delete');
}

/** True when effective RBAC grants exist — legacy role must not override pilot/master-data nav. */
export function userHasExplicitRbacGrants(user: User | null | undefined): boolean {
  return Boolean(user?.permissions?.length);
}

export function hasAnyMasterDataPermission(user: User | null | undefined): boolean {
  if (!user?.permissions?.length) return false;
  return user.permissions.some((key) => key.startsWith('master_data'));
}

export function canViewPaymentMethods(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (userHasExplicitRbacGrants(user)) {
    return hasAnyPermission(user, [
      'master_data.payment_methods.view',
      'master_data.payment_methods.create',
      'master_data.payment_methods.edit',
      'master_data.payment_methods.delete',
    ]);
  }
  return Boolean(user.role && ['admin', 'finance', 'pmo', 'procurement', 'pm'].includes(user.role));
}

export function canWritePaymentMethods(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (userHasExplicitRbacGrants(user)) {
    return hasAnyPermission(user, [
      'master_data.payment_methods.create',
      'master_data.payment_methods.edit',
      'master_data.payment_methods.delete',
    ]);
  }
  return user.role === 'admin' || user.role === 'finance';
}

export function canViewCostComponents(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (userHasExplicitRbacGrants(user)) {
    return hasAnyPermission(user, [
      'master_data.cost_components.view',
      'master_data.cost_components.create',
      'master_data.cost_components.edit',
      'master_data.cost_components.delete',
    ]);
  }
  return Boolean(user.role && ['admin', 'finance', 'pmo', 'procurement', 'pm'].includes(user.role));
}

export function canWriteCostComponents(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (userHasExplicitRbacGrants(user)) {
    return hasAnyPermission(user, [
      'master_data.cost_components.create',
      'master_data.cost_components.edit',
      'master_data.cost_components.delete',
    ]);
  }
  return user.role === 'admin' || user.role === 'finance' || user.role === 'procurement';
}

export function canSeeItemsMasterNav(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (userHasExplicitRbacGrants(user)) return canViewItemsMaster(user);
  return Boolean(user.role && ['admin', 'pmo', 'pm', 'finance'].includes(user.role));
}

export function canSeeSuppliersNav(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (userHasExplicitRbacGrants(user)) return canViewSuppliers(user);
  return Boolean(user.role && ['admin', 'pmo', 'pm', 'procurement', 'finance'].includes(user.role));
}

export function canSeeBaseInformationNav(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  if (userHasExplicitRbacGrants(user)) {
    return (
      canViewItemsMaster(user) ||
      canViewSuppliers(user) ||
      canViewPaymentMethods(user) ||
      canViewCostComponents(user) ||
      hasPermission(user, 'master_data.view')
    );
  }
  return Boolean(user.role && ['admin', 'pmo', 'pm', 'procurement', 'finance'].includes(user.role));
}

export function usePermissions(user: User | null | undefined) {
  return useMemo(
    () => ({
      hasPermission: (permissionKey: string) => hasPermission(user, permissionKey),
      hasAnyPermission: (permissionKeys: readonly string[] | string[]) =>
        hasAnyPermission(user, permissionKeys),
      canManageAccessControl: () => canManageAccessControl(user),
      canViewUsersSection: () => canViewUsersSection(user),
      canAccessUsersAccessControlSection: () => canAccessUsersAccessControlSection(user),
      hasPilotPermission: (permissionKey: string) => hasPilotPermission(user, permissionKey),
      canViewItemsMaster: () => canViewItemsMaster(user),
      canCreateItemsMaster: () => canCreateItemsMaster(user),
      canEditItemsMaster: () => canEditItemsMaster(user),
      canDeleteItemsMaster: () => canDeleteItemsMaster(user),
      canViewSuppliers: () => canViewSuppliers(user),
      canCreateSuppliers: () => canCreateSuppliers(user),
      canEditSuppliers: () => canEditSuppliers(user),
      canDeleteSuppliers: () => canDeleteSuppliers(user),
      canViewPaymentMethods: () => canViewPaymentMethods(user),
      canWritePaymentMethods: () => canWritePaymentMethods(user),
      canViewCostComponents: () => canViewCostComponents(user),
      canWriteCostComponents: () => canWriteCostComponents(user),
      canSeeBaseInformationNav: () => canSeeBaseInformationNav(user),
      canViewProcurementAssignments: () => canViewProcurementAssignments(user),
      canCreateProcurementAssignments: () => canCreateProcurementAssignments(user),
      canEditProcurementAssignments: () => canEditProcurementAssignments(user),
      canCompleteProcurementAssignments: () => canCompleteProcurementAssignments(user),
      canCancelProcurementAssignments: () => canCancelProcurementAssignments(user),
      canDeleteProcurementAssignments: () => canDeleteProcurementAssignments(user),
      canManageProcurementAssignments: () => canManageProcurementAssignments(user),
      canViewAllProcurementAssignments: () => canViewAllProcurementAssignments(user),
    }),
    [user]
  );
}

/** Sprint 5E: procurement assignment permissions (RBAC-first, admin bypass). */
function hasProcurementAssignmentPermission(
  user: User | null | undefined,
  permissionKey: string
): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasPermission(user, permissionKey);
}

export function canViewProcurementAssignments(user: User | null | undefined): boolean {
  return hasProcurementAssignmentPermission(user, 'procurement.assignments.view');
}

export function canCreateProcurementAssignments(user: User | null | undefined): boolean {
  return hasProcurementAssignmentPermission(user, 'procurement.assignments.create');
}

export function canEditProcurementAssignments(user: User | null | undefined): boolean {
  return hasProcurementAssignmentPermission(user, 'procurement.assignments.edit');
}

export function canCompleteProcurementAssignments(user: User | null | undefined): boolean {
  return hasProcurementAssignmentPermission(user, 'procurement.assignments.complete');
}

export function canCancelProcurementAssignments(user: User | null | undefined): boolean {
  return hasProcurementAssignmentPermission(user, 'procurement.assignments.cancel');
}

export function canDeleteProcurementAssignments(user: User | null | undefined): boolean {
  return hasProcurementAssignmentPermission(user, 'procurement.assignments.delete');
}

export function canManageProcurementAssignments(user: User | null | undefined): boolean {
  return (
    canCreateProcurementAssignments(user) ||
    canEditProcurementAssignments(user) ||
    canCompleteProcurementAssignments(user) ||
    canCancelProcurementAssignments(user) ||
    canDeleteProcurementAssignments(user)
  );
}

/** Managers with create/edit/complete/cancel can list all assignments; view-only users see own rows. */
export function canViewAllProcurementAssignments(user: User | null | undefined): boolean {
  if (!user) return false;
  if (isLegacyAdmin(user)) return true;
  return hasAnyPermission(user, [
    'procurement.assignments.create',
    'procurement.assignments.edit',
    'procurement.assignments.delete',
    'procurement.assignments.complete',
    'procurement.assignments.cancel',
  ]);
}
